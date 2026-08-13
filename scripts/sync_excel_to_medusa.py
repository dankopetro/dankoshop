#!/usr/bin/env python3
"""
sync_excel_to_medusa.py - Excel → Medusa sync (SOLO PRECIOS)
Lee excel/Productos_Maestro.xlsx y actualiza SOLO precios y cuotas en Medusa.

- Productos que ya existen (mismo SKU): se actualizan SOLO precios/cuotas
  (metadata + precio del variante). Si el precio mayorista no cambió, se salta.
- NUNCA toca título, descripción, categoría ni imágenes.
- Productos nuevos (SKU que no existe en Medusa) se CREAN con sus precios.
- La columna "Precio Lista" (col E) es SOLO de control en el Excel: no se usa ni se sube.

Excel columns:
  0: SKU
  1: Artículo (product name)
  4: PRECIO LISTA (control) — fórmula =F*1.25, NO se sube
  5: Precio Mayorista (source of truth)
  6: Envío Grande (TRUE/FALSE)

Usage:
  python3 scripts/sync_excel_to_medusa.py [ruta_archivo.xlsx]
  (el archivo por defecto es excel/Productos_Maestro.xlsx.
   Para subir el Excel local a producción, pasarle la ruta:
   python3 scripts/sync_excel_to_medusa.py excel/Productos_Local.xlsx)
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
    ws = wb.active
    products = []
    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        sku = str(row[0]).strip() if row[0] else None
        name = str(row[1]).strip() if row[1] else None
        if not sku or not name:
            continue
        # Col E (Precio Lista) es SOLO de control en el Excel. No se usa ni se sube.
        precio_mayorista_raw = row[5]
        envio_grande_raw = row[6] if len(row) > 6 else None

        mayorista = parse_price(precio_mayorista_raw)
        if mayorista is None:
            print(f"  WARN row {idx}: SKU {sku} no tiene precio mayorista, se saltea")
            continue
        precio_lista = int(round(mayorista * 1.25))

        products.append({
            "row": idx,
            "sku": sku,
            "name": name,
            "precio_lista": precio_lista,
            "precio_mayorista": mayorista,
            "envio_grande": str(envio_grande_raw).strip().lower() in ("true", "1", "sí", "si", "yes") if envio_grande_raw else False,
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


def slugify(value):
    import unicodedata
    s = unicodedata.normalize("NFD", value)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = "".join(c if c.isalnum() else "-" for c in s)
    return s.strip("-")[:200] or "producto"


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
    r = api("POST", "/admin/products", data=payload)
    if r.status_code == 200:
        return r.json()["product"]["id"]
    print(f"    CREATE FAILED: {r.status_code} {r.text[:200]}")
    return None


def update_product(product, existing, region_id):
    product_id = existing["id"]
    metadata = calc_metadata(product["precio_mayorista"])
    if product["envio_grande"]:
        metadata["envio_grande"] = True

    # Comparar precio mayorista actual vs el del Excel
    actual = (existing.get("metadata") or {}).get("precio_mayorista")
    try:
        actual = int(round(float(actual)))
    except (TypeError, ValueError):
        actual = None
    nuevo = int(round(float(product["precio_mayorista"])))
    if actual == nuevo:
        return "skip"

    # Actualizar solo metadata de precios/cuotas
    payload = {"metadata": metadata}
    r = api("POST", f"/admin/products/{product_id}", data=payload)
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

    return product_id


def write_medusa_ids_to_excel(products, id_map):
    import openpyxl
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb.active
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
