#!/usr/bin/env python3
"""
sync_excel_to_medusa.py - Excel → Medusa sync
Lee Productos_Maestro.xlsx o Nuevos_*_Sync.xlsx y sincroniza precios, metadata,
categorías, inventario y canales de venta.

- Productos que ya existen (mismo SKU): se actualizan precios/cuotas (metadata + precio variante)
  + inventario (si la columna Inventario tiene valor). NUNCA toca categoría ni canales en existentes.
- Productos nuevos (SKU que no existe en Medusa) se CREAN con precios, categoría, canales e inventario.
- La columna "Precio Lista" (col E) es SOLO de control en el Excel: no se usa ni se sube.

Excel columns (Nuevos Sync):
  0: SKU
  1: Artículo (product name)
  4: PRECIO LISTA (control) — fórmula =F*1.25, NO se sube
  5: Precio Mayorista / Precio Venta Bruto (source of truth)
  6: Envío Grande (TRUE/FALSE)
  7: Categoría (solo para nuevos)
  8: Inventario (nuevos y existentes)
  9: Canales de Venta (solo para nuevos)

Usage:
  python3 scripts/sync_excel_to_medusa.py [ruta_archivo.xlsx]
  (el archivo por defecto es excel/Productos_Maestro.xlsx.
   Para subir un Nuevos_Sync, pasarle la ruta:
   python3 scripts/sync_excel_to_medusa.py excel/Nuevos_14_15_Sync.xlsx)
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
EXCEL_PATH = Path(__file__).resolve().parent.parent / "excel" / "Productos_Maestro.xlsx"
if len(sys.argv) > 1:
    EXCEL_PATH = Path(sys.argv[1])

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


def read_excel():
    import openpyxl
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb["Nuevos Sync"] if "Nuevos Sync" in wb.sheetnames else wb.active
    is_sync_sheet = ws.title == "Nuevos Sync"
    products = []
    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        sku = str(row[0]).strip() if row[0] else None
        name = str(row[1]).strip() if row[1] else None
        if not sku or not name:
            continue
        if len(row) <= 5:
            print(f"  WARN row {idx}: fila incompleta ({len(row)} columnas), se saltea")
            continue
        precio_mayorista_raw = row[2] if is_sync_sheet else row[5]
        envio_grande_raw = row[6] if len(row) > 6 else None

        # Maestro: col 7=H Inventario, col 8=I Canales de Venta
        # Nuevos Sync: col 7=H Categoría, col 8=I Inventario, col 9=J Canales
        inventario_raw = row[7] if len(row) > 7 else None
        canales_raw = row[8] if len(row) > 8 else None
        if is_sync_sheet:
            categoria_raw = row[7] if len(row) > 7 else None
            inventario_raw = row[8] if len(row) > 8 else None
            canales_raw = row[9] if len(row) > 9 else None
        else:
            categoria_raw = ""

        mayorista = parse_price(precio_mayorista_raw)
        if mayorista is None:
            print(f"  WARN row {idx}: SKU {sku} no tiene precio mayorista, se saltea")
            continue
        precio_lista = int(round(mayorista * 1.25))

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
            "precio_lista": precio_lista,
            "precio_mayorista": mayorista,
            "envio_grande": str(envio_grande_raw).strip().lower() in ("true", "1", "sí", "si", "yes") if envio_grande_raw else False,
            "categoria": str(categoria_raw).strip() if categoria_raw else "",
            "inventario": inventario,
            "canales": str(canales_raw).strip() if canales_raw else "",
        })
    return products


def parse_price(val):
    if val is None:
        return None
    try:
        return float(str(val).replace("$", "").replace(",", "").strip())
    except Exception:
        return None


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
    """Actualiza el formato vigente y elimina las claves obsoletas de Medusa."""
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
    """Returns category_id for a name, or None."""
    if not category_name or not category_name.strip():
        return None
    cats = _fetch_all_categories()
    cat_id = cats.get(category_name.strip().upper())
    if cat_id:
        return cat_id
    # Create if not exists
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


def set_inventory(variant_id, sku, quantity):
    """Set inventory level for a variant's inventory item."""
    # Find inventory item for this variant
    r = api("GET", f"/admin/variants/{variant_id}", params={"expand": "inventory_items"})
    if r.status_code != 200:
        return False
    inv_items = r.json().get("variant", {}).get("inventory_items", [])
    if not inv_items:
        # Create inventory item and link to variant
        r2 = api("POST", "/admin/inventory-items", data={"sku": sku})
        if r2.status_code != 200:
            return False
        inv_item_id = r2.json().get("inventory_item", {}).get("id")
        if not inv_item_id:
            return False
        # Link to variant
        r3 = api("POST", f"/admin/products/variants/{variant_id}/inventory-items", data={"inventory_item_id": inv_item_id})
        if r3.status_code != 200:
            return False
        inv_items = [{"inventory_item_id": inv_item_id}]

    inv_item_id = inv_items[0]["inventory_item_id"]
    loc_id = get_stock_location()
    if not loc_id:
        return False

    # Set level
    r4 = api("POST", f"/admin/inventory-items/{inv_item_id}/location-levels", data={
        "stocked_quantity": quantity,
        "location_id": loc_id,
    })
    # If level exists, update it
    if r4.status_code != 200:
        r4 = api("DELETE", f"/admin/inventory-items/{inv_item_id}/location-levels/{loc_id}")
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
    """Link product to specified sales channels (by name)."""
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


def create_product(product, region_id):
    metadata = calc_metadata(product["precio_mayorista"])
    if product["envio_grande"]:
        metadata["envio_grande"] = True

    payload = {
        "title": product["name"],
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

    # Category (only for new)
    cat_name = product.get("categoria", "")
    cat_id = resolve_category(cat_name)
    if cat_id:
        payload["categories"] = [{"id": cat_id}]

    # Sales channels (only for new)
    ch_names = product.get("canales", "")

    r = api("POST", "/admin/products", data=payload)
    if r.status_code == 200:
        new_id = r.json()["product"]["id"]
        # Link channels after creation
        if ch_names:
            link_product_to_channels(new_id, ch_names)
        # Set inventory if provided
        inv = product.get("inventario")
        if inv is not None and product["variants"]:
            vid = r.json()["product"]["variants"][0]["id"]
            set_inventory(vid, product["sku"], inv)
        return new_id
    print(f"    CREATE FAILED: {r.status_code} {r.text[:200]}")
    return None


def update_product(product, existing, region_id):
    product_id = existing["id"]
    metadata = calc_metadata(product["precio_mayorista"])
    payload = metadata_payload(metadata, product["envio_grande"], existing.get("metadata"))

    # Comparar precio mayorista actual vs el del Excel
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
        # Still update inventory if provided
        inv = product.get("inventario")
        if inv is not None and existing.get("variants"):
            vid = existing["variants"][0]["id"]
            set_inventory(vid, product["sku"], inv)
        return "skip"

    # Actualizar solo metadata de precios/cuotas
    r = api("POST", f"/admin/products/{product_id}", data={"metadata": payload})
    if r.status_code != 200:
        print(f"    UPDATE FAILED: {r.status_code} {r.text[:200]}")
        return False

    # Actualizar precio del variante
    if existing.get("variants"):
        vid = existing["variants"][0]["id"]
        r2 = api("POST", f"/admin/products/{product_id}/variants/{vid}", data={
            "prices": [{"amount": product["precio_lista"], "currency_code": "ars", "region_id": region_id}],
        })
        if r2.status_code != 200:
            print(f"    PRICE UPDATE FAILED: {r2.status_code}")

    # Update inventory if provided
    inv = product.get("inventario")
    if inv is not None and existing.get("variants"):
        vid = existing["variants"][0]["id"]
        set_inventory(vid, product["sku"], inv)

    return product_id


def write_medusa_ids_to_excel(products, id_map):
    import openpyxl
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb["Nuevos Sync"] if "Nuevos Sync" in wb.sheetnames else wb.active
    for p in products:
        sku = p["sku"]
        if sku in id_map:
            ws.cell(row=p["row"], column=8).value = id_map[sku]
    wb.save(EXCEL_PATH)


def main():
    print("=" * 60)
    print("  Excel → Medusa Sync")
    print(f"  Excel: {EXCEL_PATH}")
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
    print(f"Medusa URL: {MEDUSA_URL}")

    created = 0
    updated = 0
    skipped = 0
    failed = 0
    id_map = {}

    for i, p in enumerate(products, 1):
        print(f"[{i}/{len(products)}] {p['sku']}: {p['name'][:50]}")
        existing = find_product(p["sku"])

        if existing:
            pid = update_product(p, existing, region_id)
            if pid == "skip":
                skipped += 1
                print(f"    Sin cambios")
            elif pid:
                updated += 1
                id_map[p["sku"]] = pid
                print(f"    Precios actualizados")
            else:
                failed += 1
        else:
            pid = create_product(p, region_id)
            if pid:
                created += 1
                id_map[p["sku"]] = pid
                print(f"    Creado")
            else:
                failed += 1

    # Write medusa IDs back to Excel
    if id_map:
        try:
            write_medusa_ids_to_excel(products, id_map)
            print(f"\nWrote {len(id_map)} Medusa IDs to Excel")
        except Exception as e:
            print(f"\nCould not write IDs to Excel: {e}")

    print(f"\n{'='*60}")
    print(f"  Creados: {created} | Actualizados: {updated} | Sin cambios: {skipped} | Errores: {failed}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
