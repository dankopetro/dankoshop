#!/usr/bin/env python3
"""
sync_helpers.py - Funciones compartidas para sincronizar inventario y canales de venta
entre instancias de Medusa v2.

Uso:
  from sync_helpers import sync_inventory, sync_sales_channels
"""

import time


def _api(url, token, method, endpoint, data=None, params=None):
    """Helper interno para requests autenticados."""
    import requests
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.request(method, f"{url}{endpoint}", headers=headers, json=data, params=params, timeout=30)
    return r


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

def get_stock_location(url, token):
    """Returns the first stock location ID, or None."""
    r = _api(url, token, "GET", "/admin/stock-locations", params={"limit": 10})
    if r.status_code == 200:
        locs = r.json().get("stock_locations", [])
        if locs:
            return locs[0]["id"]
    return None


def fetch_source_inventory(url, token):
    """
    Returns {sku: quantity} from all inventory items in the source instance.
    """
    inv_map = {}
    offset = 0
    while True:
        r = _api(url, token, "GET", "/admin/inventory-items", params={"limit": 100, "offset": offset})
        if r.status_code != 200:
            break
        items = r.json().get("inventory_items", [])
        for item in items:
            sku = item.get("sku")
            if not sku:
                continue
            levels = item.get("location_levels", []) or []
            total = sum(l.get("available_quantity", 0) or 0 for l in levels)
            inv_map[sku] = total
        if len(items) < 100:
            break
        offset += 100
    return inv_map


def sync_inventory(url, token, variant_id, sku, quantity):
    """
    Set inventory level for a variant in the destination instance.
    Creates inventory item + links to variant if needed.
    If quantity is None or <= 0, skip (no inventory item = checkout allows purchase).
    """
    if quantity is None or quantity <= 0:
        return True

    # Find or create inventory item for this variant
    r = _api(url, token, "GET", f"/admin/variants/{variant_id}", params={"expand": "inventory_items"})
    if r.status_code != 200:
        return False
    inv_items = r.json().get("variant", {}).get("inventory_items", [])

    if not inv_items:
        # Create inventory item
        r2 = _api(url, token, "POST", "/admin/inventory-items", data={"sku": sku})
        if r2.status_code != 200:
            return False
        inv_item_id = r2.json().get("inventory_item", {}).get("id")
        if not inv_item_id:
            return False
        # Link to variant
        r3 = _api(url, token, "POST", f"/admin/products/variants/{variant_id}/inventory-items",
                   data={"inventory_item_id": inv_item_id})
        if r3.status_code != 200:
            return False
        inv_items = [{"inventory_item_id": inv_item_id}]

    inv_item_id = inv_items[0]["inventory_item_id"]
    loc_id = get_stock_location(url, token)
    if not loc_id:
        return False

    # Set level (try create, if exists delete and recreate)
    r4 = _api(url, token, "POST", f"/admin/inventory-items/{inv_item_id}/location-levels",
              data={"stocked_quantity": quantity, "location_id": loc_id})
    if r4.status_code != 200:
        _api(url, token, "DELETE", f"/admin/inventory-items/{inv_item_id}/location-levels/{loc_id}")
        r4 = _api(url, token, "POST", f"/admin/inventory-items/{inv_item_id}/location-levels",
                  data={"stocked_quantity": quantity, "location_id": loc_id})
    return r4.status_code == 200


# ---------------------------------------------------------------------------
# Sales Channels
# ---------------------------------------------------------------------------

def get_or_create_sales_channel(url, token, name="DankoShop"):
    """Find or create a sales channel by name, return its ID."""
    r = _api(url, token, "GET", "/admin/sales-channels", params={"limit": 100})
    if r.status_code == 200:
        for ch in r.json().get("sales_channels", []):
            if ch.get("name", "").strip().lower() == name.strip().lower():
                return ch["id"]
    r2 = _api(url, token, "POST", "/admin/sales-channels",
              data={"name": name, "is_default": True})
    if r2.status_code == 200:
        return r2.json().get("sales_channel", {}).get("id")
    return None


def sync_sales_channels(url, token, product_id, channel_names):
    """
    Link a product to sales channels (by name, comma-separated).
    Always includes the default 'DankoShop' channel.
    """
    if not channel_names and not channel_names == "":
        return
    default_ch = get_or_create_sales_channel(url, token)
    ch_ids = set()
    if default_ch:
        ch_ids.add(default_ch)
    for name in [n.strip() for n in channel_names.split(",") if n.strip()]:
        ch_id = get_or_create_sales_channel(url, token, name)
        if ch_id:
            ch_ids.add(ch_id)
    if not ch_ids:
        return
    r = _api(url, token, "POST", f"/admin/products/{product_id}",
             data={"sales_channels": [{"id": cid} for cid in ch_ids]})
    return r.status_code == 200


# ---------------------------------------------------------------------------
# Fetch source data for inventory and channels
# ---------------------------------------------------------------------------

def fetch_source_sales_channels(url, token):
    """
    Returns {product_id: channel_names} from the source instance.
    """
    sc_map = {}
    r = _api(url, token, "GET", "/admin/sales-channels", params={"limit": 100})
    if r.status_code != 200:
        return sc_map
    channels = r.json().get("sales_channels", [])
    for ch in channels:
        ch_id, ch_name = ch["id"], ch.get("name", "")
        offset = 0
        while True:
            r2 = _api(url, token, "GET", "/admin/products",
                      params={"limit": 100, "offset": offset, "sales_channel_id": ch_id})
            if r2.status_code != 200:
                break
            prods = r2.json().get("products", [])
            for p in prods:
                existing = sc_map.get(p["id"], [])
                if ch_name not in existing:
                    existing.append(ch_name)
                sc_map[p["id"]] = existing
            if len(prods) < 100:
                break
            offset += 100
    return sc_map


def sync_product_inventory_and_channels(
    source_url, source_token, source_product,
    dest_url, dest_token, dest_product_id, dest_variants,
    sku
):
    """
    Sync inventory and sales channels for a single product from source to dest.
    - inventory: reads from source, writes to dest
    - sales channels: reads from source, links in dest
    """
    # Inventory
    src_inv = fetch_source_inventory(source_url, source_token)
    qty = src_inv.get(sku)
    if qty is not None:
        for v in dest_variants:
            vid = v.get("id")
            if vid:
                sync_inventory(dest_url, dest_token, vid, sku, qty)
                break

    # Sales channels
    src_sc = fetch_source_sales_channels(source_url, source_token)
    ch_names = src_sc.get(source_product, "")
    if ch_names:
        sync_sales_channels(dest_url, dest_token, dest_product_id, ", ".join(ch_names))
