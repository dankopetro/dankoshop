#!/usr/bin/env python3
"""Limpia inventario en Medusa: borra todos los inventory items,
crea location 'Local Warehouse' y setea stock para SKUs específicos.

Usage:
  MEDUSA_ADMIN_PASSWORD=supersecret python3 scripts/clean_inventory.py
  MEDUSA_ADMIN_PASSWORD=supersecret python3 scripts/clean_inventory.py --dry-run
"""

import os
import sys
import time
import requests

MEDUSA_URL = os.getenv("MEDUSA_BACKEND_URL", "https://dankoshop-api-production.up.railway.app")
EMAIL = os.getenv("MEDUSA_ADMIN_EMAIL", "admin@dankoshop.com")
PASSWORD = os.getenv("MEDUSA_ADMIN_PASSWORD", "supersecret")
DRY_RUN = "--dry-run" in sys.argv

STOCK_OVERRIDES = {
    "6983": 5,
    "SIN026": 1,
}

_token = None


def get_token():
    global _token
    if _token:
        return _token
    r = requests.post(f"{MEDUSA_URL}/auth/user/emailpass",
                      json={"email": EMAIL, "password": PASSWORD}, timeout=10)
    if r.status_code == 200:
        _token = r.json().get("token")
        return _token
    print(f"AUTH FAILED: {r.status_code}")
    return None


def api(method, endpoint, data=None, params=None):
    token = get_token()
    if not token:
        raise RuntimeError("No auth")
    return requests.request(
        method, f"{MEDUSA_URL}{endpoint}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=data, params=params, timeout=30,
    )


def delete_all_inventory_items():
    print("\n1. Borrando inventory items...")
    offset = 0
    total = 0
    while True:
        r = api("GET", "/admin/inventory-items", params={"limit": 100, "offset": offset})
        if r.status_code != 200:
            print(f"  Error fetching items: {r.status_code}")
            break
        items = r.json().get("inventory_items", [])
        if not items:
            break
        for item in items:
            item_id = item["id"]
            sku = item.get("sku", "?")
            if DRY_RUN:
                print(f"  DRY-RUN: borrar {sku} ({item_id})")
            else:
                r2 = api("DELETE", f"/admin/inventory-items/{item_id}")
                if r2.status_code in (200, 204):
                    total += 1
                else:
                    print(f"  ERR borrar {sku}: {r2.status_code}")
        if len(items) < 100:
            break
        offset += 100
    print(f"  {'Would delete' if DRY_RUN else 'Eliminados'}: {total}")


def ensure_location():
    print("\n2. Configurando stock location...")
    r = api("GET", "/admin/stock-locations", params={"limit": 100})
    locations = r.json().get("stock_locations", []) if r.status_code == 200 else []

    existing = next((l for l in locations if l["name"] == "Local Warehouse"), None)
    if existing:
        print(f"  Local Warehouse ya existe: {existing['id']}")
        return existing["id"]

    european = next((l for l in locations if l["name"] == "European Warehouse"), None)
    if european:
        if DRY_RUN:
            print(f"  DRY-RUN: renombrar European → Local Warehouse")
            return european["id"]
        r2 = api("POST", f"/admin/stock-locations/{european['id']}", data={"name": "Local Warehouse"})
        if r2.status_code == 200:
            print(f"  Renombrado a Local Warehouse: {european['id']}")
            return european["id"]
        print(f"  WARN: no se pudo renombrar, usando European")

    if DRY_RUN:
        print("  DRY-RUN: crear Local Warehouse")
        return "dry-run"
    r3 = api("POST", "/admin/stock-locations", data={"name": "Local Warehouse"})
    if r3.status_code == 200:
        loc_id = r3.json().get("stock_location", {}).get("id")
        print(f"  Local Warehouse creado: {loc_id}")
        return loc_id
    print("  ERR: no se pudo crear location")
    return None


def create_inventory_for_skus(location_id):
    print("\n3. Creando inventory items para SKUs con stock...")
    created = 0
    for sku, qty in STOCK_OVERRIDES.items():
        print(f"  {sku}: {qty} unidades")
        if DRY_RUN:
            continue

        r = api("GET", "/admin/products", params={"q": sku, "limit": 5})
        if r.status_code != 200:
            print(f"    ERR buscar producto")
            continue
        products = r.json().get("products", [])
        variant_id = None
        product_id = None
        for p in products:
            for v in p.get("variants", []):
                if v.get("sku") == sku:
                    variant_id = v["id"]
                    product_id = p["id"]
                    break
            if variant_id:
                break
        if not variant_id:
            print(f"    WARN: variante no encontrada")
            continue

        r2 = api("POST", "/admin/inventory-items", data={"sku": sku})
        if r2.status_code != 200:
            print(f"    ERR crear inventory item: {r2.status_code}")
            continue
        inv_id = r2.json().get("inventory_item", {}).get("id")
        if not inv_id:
            continue

        r3 = api("POST", f"/admin/products/{product_id}/variants/{variant_id}/inventory-items",
                 data={"inventory_item_id": inv_id})
        if r3.status_code not in (200, 409):
            print(f"    WARN vincular: {r3.status_code}")

        r4 = api("POST", f"/admin/inventory-items/{inv_id}/location-levels",
                 data={"stocked_quantity": qty, "location_id": location_id})
        if r4.status_code == 200:
            created += 1
            print(f"    OK: {qty} unidades en Local Warehouse")
        else:
            print(f"    ERR setear stock: {r4.status_code}")
        time.sleep(0.1)

    print(f"\n  {'Would create' if DRY_RUN else 'Creados'}: {created}")


def main():
    print("=" * 60)
    print("  Medusa Inventory Cleanup")
    print(f"  URL: {MEDUSA_URL}")
    if DRY_RUN:
        print("  *** DRY-RUN ***")
    print("=" * 60)

    if not get_token():
        print("Auth failed")
        return

    delete_all_inventory_items()
    location_id = ensure_location()
    if location_id and location_id != "dry-run":
        create_inventory_for_skus(location_id)

    print(f"\n{'='*60}")
    print("  Listo! Ahora corré sync_medusa_to_excel.py para bajar el Maestro")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
