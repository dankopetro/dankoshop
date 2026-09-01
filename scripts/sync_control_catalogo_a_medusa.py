#!/usr/bin/env python3
"""
sync_control_catalogo_a_medusa.py - Control Catálogo → Medusa sync
Lee Control_Catalogo_*.xlsx y sincroniza precios, metadata, categorías,
inventario y canales de venta a Medusa.

Diferencia con sync_excel_to_medusa.py:
  - Lee el precio de la col I (Precio Medusa) en vez de la col F del Maestro.
  - Todo lo demás es idéntico.

Columnas del Excel:
  0: SKU
  1: Artículo (product name)
  2: Categoría (solo para nuevos)
  3: Descripción (solo para nuevos)
  4: Precio Mayorista (catálogo, control only — NO se sube)
  5: Inventario (nuevos y existentes)
  6: Envío Grande (TRUE/FALSE)
  7: Canal de Venta (solo para nuevos)
  8: Precio Medusa (el que se sube a Medusa)

Usage:
  MEDUSA_ADMIN_PASSWORD=supersecret python3 scripts/sync_control_catalogo_a_medusa.py
  MEDUSA_ADMIN_PASSWORD=supersecret python3 scripts/sync_control_catalogo_a_medusa.py --dry-run
"""

import os
import sys
import json
import math
import requests
from pathlib import Path

MEDUSA_URL = os.getenv("MEDUSA_BACKEND_URL", "https://dankoshop-api-production.up.railway.app")
ADMIN_EMAIL = os.getenv("MEDUSA_ADMIN_EMAIL", "admin@dankoshop.com")
ADMIN_PASSWORD = os.getenv("MEDUSA_ADMIN_PASSWORD", "supersecret")
DRY_RUN = "--dry-run" in sys.argv
EXCEL_PATH = Path(__file__).resolve().parent.parent / "excel" / "Control_Catalogo_24_Agosto.xlsx"

_token = None
ALLOWED_METADATA_KEYS = {
    "precio_lista", "precio_efectivo", "precio_mayorista",
    "cuota_valor_3", "cuota_valor_6", "cuota_valor_12", "envio_grande",
}


def get_token():
    global _token
    if _token:
        return _token
    r = requests.post(
        f"{MEDUSA_URL}/auth/user/emailpass",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if r.status_code == 200:
        _token = r.json().get("token")
        return _token
    print(f"AUTH FAILED ({r.status_code}): {r.text[:200]}")
    return None


def api(method, endpoint, data=None, params=None):
    token = get_token()
    if not token:
        raise RuntimeError("No auth token")
    r = requests.request(
        method,
        f"{MEDUSA_URL}{endpoint}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=data,
        params=params,
        timeout=30,
    )
    return r


def parse_price(val):
    if val is None:
        return None
    try:
        return float(str(val).replace("$", "").replace(",", "").strip())
    except Exception:
        return None


def read_excel():
    import openpyxl
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active
    products = []
    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        sku = str(row[0]).strip() if row[0] else None
        name = str(row[1]).strip() if row[1] else None
        if not sku or not name:
            continue

        categoria_raw = row[2] if len(row) > 2 else None
        descripcion_raw = row[3] if len(row) > 3 else None
        precio_catalogo_raw = row[4] if len(row) > 4 else None
        inventario_raw = row[5] if len(row) > 5 else None
        envio_grande_raw = row[6] if len(row) > 6 else None
        canales_raw = row[7] if len(row) > 7 else None
        precio_medusa_raw = row[8] if len(row) > 8 else None

        precio_medusa = parse_price(precio_medusa_raw)
        if precio_medusa is None:
            print(f"  WARN row {idx}: SKU {sku} no tiene Precio Medusa (col I), se saltea")
            continue

        inventario = None
        if inventario_raw is not None:
            try:
                inventario = int(float(str(inventario_raw)))
            except (TypeError, ValueError):
                inventario = None

        products.append({
            "row": idx,
            "sku": sku,
            "name": name,
            "precio_lista": int(round(precio_medusa)),
            "precio_mayorista": precio_medusa,
            "envio_grande": str(envio_grande_raw).strip().lower() in ("true", "1", "sí", "si", "yes") if envio_grande_raw else False,
            "categoria": str(categoria_raw).strip() if categoria_raw else "",
            "inventario": inventario,
            "canales": str(canales_raw).strip() if canales_raw else "",
            "descripcion": str(descripcion_raw).strip() if descripcion_raw else "",
        })
    return products


def calc_metadata(mayorista):
    if mayorista is None:
        return {}
    m = float(mayorista)
    lista = int(round(m * 1.25))
    efectivo = int(round(m * 1.15))
    cuota_3 = int(round(lista / 3))
    cuota_6 = int(round(lista / 6))
    tasa = 0.12
    factor = ((1 + tasa) ** 12 - 1) / (tasa * (1 + tasa) ** 12)
    cuota_12 = int(round(lista / factor))
    return {
        "precio_lista": lista,
        "precio_efectivo": efectivo,
        "precio_mayorista": int(round(m)),
        "cuota_valor_3": cuota_3,
        "cuota_valor_6": cuota_6,
        "cuota_valor_12": cuota_12,
    }


def metadata_payload(metadata, envio_grande, existing_metadata):
    payload = dict(metadata)
    if envio_grande:
        payload["envio_grande"] = True
    for key in (existing_metadata or {}):
        if key not in ALLOWED_METADATA_KEYS or (key == "envio_grande" and not envio_grande):
            payload[key] = ""
    return payload


def slugify(value):
    import unicodedata
    s = unicodedata.normalize("NFD", value)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = "".join(c if c.isalnum() else "-" for c in s)
    return s.strip("-")[:200] or "producto"


# ---------------------------------------------------------------------------
# Category helpers (only for NEW products)
# ---------------------------------------------------------------------------
_category_cache = {}

def _fetch_all_categories():
    if _category_cache:
        return _category_cache
    offset = 0
    while True:
        r = api("GET", "/admin/product-categories", params={"limit": 100, "offset": offset})
        if r.status_code != 200:
            break
        for cat in r.json().get("product_categories", []):
            _category_cache[cat["name"].strip().upper()] = cat["id"]
        if len(r.json().get("product_categories", [])) < 100:
            break
        offset += 100
    return _category_cache


def resolve_category(category_name):
    if not category_name or not category_name.strip():
        return None
    cats = _fetch_all_categories()
    cat_id = cats.get(category_name.strip().upper())
    if cat_id:
        return cat_id
    r = api("POST", "/admin/product-categories", data={"name": category_name.strip()})
    if r.status_code == 200:
        new_id = r.json().get("product_category", {}).get("id")
        if new_id:
            cats[category_name.strip().upper()] = new_id
            print(f"    Categoría creada: {category_name} → {new_id}")
            return new_id
    print(f"    WARN: no se pudo crear categoría '{category_name}'")
    return None


# ---------------------------------------------------------------------------
# Inventory helpers (for both new and existing products)
# ---------------------------------------------------------------------------
_stock_location_id = None

def get_stock_location():
    global _stock_location_id
    if _stock_location_id:
        return _stock_location_id
    r = api("GET", "/admin/stock-locations", params={"limit": 10})
    if r.status_code == 200:
        locs = r.json().get("stock_locations", [])
        if locs:
            _stock_location_id = locs[0]["id"]
            return _stock_location_id
    return None


def set_inventory(variant_id, sku, quantity, product_id=None):
    """Set inventory level. Skips if quantity None/<=0 or stock already exists."""
    if quantity is None or quantity <= 0:
        return True

    # Search inventory item by SKU (Medusa v2 doesn't have GET /admin/variants/{id})
    r = api("GET", "/admin/inventory-items", params={"q": sku})
    inv_item_id = None
    if r.status_code == 200:
        for item in r.json().get("inventory_items", []):
            if item.get("sku") == sku:
                inv_item_id = item["id"]
                break

    if inv_item_id:
        loc_id = get_stock_location()
        if loc_id:
            r_check = api("GET", f"/admin/inventory-items/{inv_item_id}/location-levels")
            if r_check.status_code == 200:
                levels = r_check.json().get("inventory_levels", [])
                current_stock = sum(l.get("stocked_quantity", 0) for l in levels)
                if current_stock > 0:
                    return True
    else:
        r2 = api("POST", "/admin/inventory-items", data={"sku": sku})
        if r2.status_code != 200:
            print(f"    INV CREATE FAILED: {r2.status_code} {r2.text[:200]}")
            return False
        inv_item_id = r2.json().get("inventory_item", {}).get("id")
        if not inv_item_id:
            print(f"    INV CREATE NO ID: {r2.text[:200]}")
            return False
        if product_id:
            r3 = api("POST", f"/admin/products/{product_id}/variants/{variant_id}/inventory-items", data={"inventory_item_id": inv_item_id, "required_quantity": 1})
            if r3.status_code != 200:
                print(f"    INV LINK FAILED: {r3.status_code} {r3.text[:200]}")
                return False

    loc_id = get_stock_location()
    if not loc_id:
        return False

    r4 = api("POST", f"/admin/inventory-items/{inv_item_id}/location-levels", data={
        "stocked_quantity": quantity,
        "location_id": loc_id,
    })
    if r4.status_code != 200:
        r_levels = api("GET", f"/admin/inventory-items/{inv_item_id}/location-levels")
        if r_levels.status_code == 200:
            for lvl in r_levels.json().get("inventory_levels", []):
                if lvl.get("location_id") == loc_id:
                    api("DELETE", f"/admin/inventory-items/{inv_item_id}/location-levels/{lvl['id']}")
        r4 = api("POST", f"/admin/inventory-items/{inv_item_id}/location-levels", data={
            "stocked_quantity": quantity,
            "location_id": loc_id,
        })
    return r4.status_code == 200


# ---------------------------------------------------------------------------
# Sales channel helpers (only for NEW products)
# ---------------------------------------------------------------------------
def get_or_create_sales_channel(name="DankoShop"):
    r = api("GET", "/admin/sales-channels", params={"limit": 100})
    if r.status_code == 200:
        for ch in r.json().get("sales_channels", []):
            if ch.get("name", "").strip().lower() == name.strip().lower():
                return ch["id"]
    r2 = api("POST", "/admin/sales-channels", data={"name": name, "is_default": True})
    if r2.status_code == 200:
        return r2.json().get("sales_channel", {}).get("id")
    return None


def link_product_to_channels(product_id, channel_names):
    if not channel_names:
        return
    default_ch = get_or_create_sales_channel()
    ch_ids = set()
    if default_ch:
        ch_ids.add(default_ch)
    for name in [n.strip() for n in channel_names.split(",") if n.strip()]:
        ch_id = get_or_create_sales_channel(name)
        if ch_id:
            ch_ids.add(ch_id)
    if not ch_ids:
        return
    r = api("POST", f"/admin/products/{product_id}", data={
        "sales_channels": [{"id": cid} for cid in ch_ids]
    })
    if r.status_code != 200:
        print(f"    WARN: no se pudo vincular canales de venta")


def ensure_region():
    r = api("GET", "/admin/regions", params={"limit": 100})
    if r.status_code == 200:
        for reg in r.json().get("regions", []):
            if reg.get("currency_code") == "ars":
                return reg["id"]
    r = api("POST", "/admin/regions", data={
        "name": "Argentina", "currency_code": "ars",
        "countries": ["ar"], "payment_providers": [], "metadata": {},
    })
    if r.status_code == 200:
        return r.json()["region"]["id"]
    return None


def find_product(sku):
    r = api("GET", "/admin/products", params={"q": sku, "limit": 20})
    if r.status_code != 200:
        return None
    for p in r.json().get("products", []):
        for v in p.get("variants", []):
            if v.get("sku") == sku:
                return p
    return None


def remove_inventory_if_empty(sku):
    """Remove auto-created inventory item (Medusa v2 creates one with stock=0 by default)."""
    r = api("GET", "/admin/inventory-items", params={"q": sku})
    if r.status_code != 200:
        return
    for item in r.json().get("inventory_items", []):
        if item.get("sku") == sku:
            stock = sum(l.get("stocked_quantity", 0) for l in item.get("location_levels", []))
            if stock == 0:
                api("DELETE", f"/admin/inventory-items/{item['id']}")
                print(f"    Inventario: eliminado item vacío (Medusa lo creó automático)")
            break


def create_product(product, region_id):
    metadata = calc_metadata(product["precio_mayorista"])
    if product["envio_grande"]:
        metadata["envio_grande"] = True

    payload = {
        "title": product["name"],
        "description": product.get("descripcion", ""),
        "handle": slugify(product["sku"]),
        "status": "published",
        "options": [{"title": "Default", "values": ["Default"]}],
        "variants": [{
            "title": "Default",
            "sku": product["sku"],
            "options": {"Default": "Default"},
            "prices": [{"amount": product["precio_lista"], "currency_code": "ars", "region_id": region_id}] if product["precio_lista"] > 0 else [],
        }],
        "metadata": metadata,
    }

    cat_name = product.get("categoria", "")
    cat_id = resolve_category(cat_name)
    if cat_id:
        payload["categories"] = [{"id": cat_id}]

    ch_names = product.get("canales", "")

    if DRY_RUN:
        print(f"    DRY-RUN: crear producto '{product['name']}' con precio ${product['precio_lista']:,}")
        return "dry"

    r = api("POST", "/admin/products", data=payload)
    if r.status_code == 200:
        new_id = r.json()["product"]["id"]
        if ch_names:
            link_product_to_channels(new_id, ch_names)
        inv = product.get("inventario")
        created_variants = r.json().get("product", {}).get("variants", [])
        if inv is not None and created_variants:
            vid = created_variants[0]["id"]
            inv_result = set_inventory(vid, product["sku"], inv, product_id=new_id)
            if inv_result == "set":
                print(f"    Inventario: {inv} unidades")
        else:
            remove_inventory_if_empty(product["sku"])
        return new_id
    print(f"    CREATE FAILED: {r.status_code} {r.text[:200]}")
    return None


def update_product(product, existing, region_id):
    product_id = existing["id"]
    metadata = calc_metadata(product["precio_mayorista"])
    payload = metadata_payload(metadata, product["envio_grande"], existing.get("metadata"))

    actual = (existing.get("metadata") or {}).get("precio_mayorista")
    try:
        actual = int(round(float(actual)))
    except (TypeError, ValueError):
        actual = None
    nuevo = int(round(float(product["precio_mayorista"])))
    metadata_changed = any(
        (value == "" and key in (existing.get("metadata") or {}))
        or (value != "" and (existing.get("metadata") or {}).get(key) != value)
        for key, value in payload.items()
    )
    if actual == nuevo and not metadata_changed:
        inv = product.get("inventario")
        if inv is not None and existing.get("variants"):
            vid = existing["variants"][0]["id"]
            if not DRY_RUN:
                inv_result = set_inventory(vid, product["sku"], inv, product_id=product_id)
                if inv_result == "set":
                    print(f"    Inventario: {inv} unidades")
                elif inv_result == "skip" and inv and inv > 0:
                    print(f"    Inventario: ya tiene stock, sin cambios")
        elif (inv is None or (inv is not None and inv <= 0)) and not DRY_RUN:
            remove_inventory_if_empty(product["sku"])
        return "skip"

    if DRY_RUN:
        print(f"    DRY-RUN: actualizar precio ${actual or 0:,} → ${nuevo:,}")
        return "dry"

    r = api("POST", f"/admin/products/{product_id}", data={"metadata": payload})
    if r.status_code != 200:
        print(f"    UPDATE FAILED: {r.status_code} {r.text[:200]}")
        return False

    if existing.get("variants"):
        vid = existing["variants"][0]["id"]
        r2 = api("POST", f"/admin/products/{product_id}/variants/{vid}", data={
            "prices": [{"amount": product["precio_lista"], "currency_code": "ars", "region_id": region_id}],
        })
        if r2.status_code != 200:
            print(f"    PRICE UPDATE FAILED: {r2.status_code}")

    inv = product.get("inventario")
    if inv is not None and existing.get("variants"):
        vid = existing["variants"][0]["id"]
        inv_result = set_inventory(vid, product["sku"], inv, product_id=product_id)
        if inv_result == "set":
            print(f"    Inventario: {inv} unidades")
        elif inv_result == "skip" and inv and inv > 0:
            print(f"    Inventario: ya tiene stock, sin cambios")
    elif inv is None or (inv is not None and inv <= 0):
        remove_inventory_if_empty(product["sku"])

    return product_id


def main():
    print("=" * 60)
    print("  Control Catálogo → Medusa Sync")
    print(f"  Excel: {EXCEL_PATH}")
    if DRY_RUN:
        print("  *** MODO DRY-RUN ***")
    print("=" * 60)

    try:
        r = requests.get(f"{MEDUSA_URL}/health", timeout=10)
        if r.status_code != 200:
            print(f"Medusa not healthy: {r.status_code}")
            return
    except Exception as e:
        print(f"Cannot connect to Medusa: {e}")
        return

    if not get_token():
        print("Auth failed")
        return

    if not EXCEL_PATH.exists():
        print(f"Excel not found: {EXCEL_PATH}")
        return

    region_id = ensure_region()
    if not region_id:
        print("Could not ensure ARS region")
        return

    products = read_excel()
    print(f"Excel products: {len(products)}")
    print(f"Medusa URL: {MEDUSA_URL}\n")

    created = 0
    updated = 0
    skipped = 0
    failed = 0

    for i, p in enumerate(products, 1):
        print(f"[{i}/{len(products)}] {p['sku']}: {p['name'][:50]}")
        existing = find_product(p["sku"])

        if existing:
            pid = update_product(p, existing, region_id)
            if pid == "skip" or pid == "dry":
                skipped += 1
                print(f"    {'DRY-RUN sin cambios' if pid == 'dry' else 'Sin cambios'}")
            elif pid:
                updated += 1
                print(f"    Precios actualizados")
            else:
                failed += 1
        else:
            pid = create_product(p, region_id)
            if pid == "dry":
                created += 1
            elif pid:
                created += 1
                print(f"    Creado")
            else:
                failed += 1

    print(f"\n{'='*60}")
    print(f"  Creados: {created} | Actualizados: {updated} | Sin cambios: {skipped} | Errores: {failed}")
    print(f"{'='*60}")
    if not DRY_RUN and (created > 0 or updated > 0):
        print(f"\nDespués corré: python3 scripts/sync_medusa_to_excel.py para bajar el Maestro")


if __name__ == "__main__":
    main()
