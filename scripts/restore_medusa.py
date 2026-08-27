#!/usr/bin/env python3
"""
Restaurar backup de Medusa vía Admin API.
Restaura: categorías, colecciones, canales de venta, productos, e inventario.

Uso:
  export MEDUSA_BACKEND_URL=https://dankoshop-api-production.up.railway.app
  export MEDUSA_ADMIN_EMAIL=admin@dankoshop.com
  export MEDUSA_ADMIN_PASSWORD=supersecret
  python3 scripts/restore_medusa.py data/backups/backup_20260823_211003.json
"""

import os
import sys
import json
import time
import requests

MEDUSA_URL = os.environ.get("MEDUSA_BACKEND_URL", "https://dankoshop-api-production.up.railway.app")
EMAIL = os.environ.get("MEDUSA_ADMIN_EMAIL", "admin@dankoshop.com")
PASSWORD = os.environ.get("MEDUSA_ADMIN_PASSWORD", "supersecret")

if len(sys.argv) < 2:
    print("Uso: python3 restore_medusa.py <backup_file.json> [--dry-run]")
    sys.exit(1)

BACKUP_FILE = sys.argv[1]
DRY_RUN = "--dry-run" in sys.argv

if DRY_RUN:
    print("*** MODO DRY-RUN: no se hará ningún cambio en Medusa ***\n")


def login():
    r = requests.post(f"{MEDUSA_URL}/auth/user/emailpass", json={"email": EMAIL, "password": PASSWORD}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


def get_all(token, endpoint, key=None):
    headers = {"Authorization": f"Bearer {token}"}
    all_items = []
    offset = 0
    while True:
        r = requests.get(f"{MEDUSA_URL}{endpoint}", headers=headers, params={"limit": 100, "offset": offset}, timeout=15)
        r.raise_for_status()
        data = r.json()
        if key:
            items = data.get(key, [])
        else:
            items = data.get("products", data.get("collections", data.get("product_categories", data.get("items", []))))
        if not items:
            break
        all_items.extend(items)
        if len(items) < 100:
            break
        offset += 100
        time.sleep(0.2)
    return all_items


def restore_categories(token, backup_categories, headers):
    print("Restaurando categorías...")
    existing = get_all(token, "/admin/product-categories", key="product_categories")
    existing_map = {c["name"]: c["id"] for c in existing}

    id_map = {}
    created = 0
    skipped = 0

    for cat in backup_categories:
        name = cat.get("name", "")
        if not name:
            skipped += 1
            continue

        if name in existing_map:
            id_map[cat["id"]] = existing_map[name]
            skipped += 1
            continue

        if DRY_RUN:
            print(f"  DRY-RUN: crear categoría '{name}'")
            id_map[cat["id"]] = f"dry_cat_{name}"
            created += 1
            continue

        payload = {
            "name": name,
            "description": cat.get("description", name),
            "is_active": cat.get("is_active", True),
            "is_internal": cat.get("is_internal", False),
        }
        r = requests.post(f"{MEDUSA_URL}/admin/product-categories", headers=headers, json=payload, timeout=15)
        if r.status_code == 200:
            new_id = r.json()["product_category"]["id"]
            id_map[cat["id"]] = new_id
            existing_map[name] = new_id
            created += 1
            print(f"  NEW: {name}")
        else:
            print(f"  ERR: {name} - {r.status_code}")
        time.sleep(0.15)

    print(f"  Creadas: {created}, Ya existían: {skipped}")
    return id_map


def restore_sales_channels(token, backup_channels, headers):
    print("Restaurando canales de venta...")
    existing = get_all(token, "/admin/sales-channels", key="sales_channels")
    existing_map = {s["name"]: s["id"] for s in existing}

    id_map = {}
    created = 0
    skipped = 0

    for ch in backup_channels:
        name = ch.get("name", "")
        if not name:
            skipped += 1
            continue

        if name in existing_map:
            id_map[ch["id"]] = existing_map[name]
            skipped += 1
            continue

        if DRY_RUN:
            print(f"  DRY-RUN: crear canal '{name}'")
            id_map[ch["id"]] = f"dry_sc_{name}"
            created += 1
            continue

        payload = {
            "name": name,
            "description": ch.get("description", ""),
            "is_disabled": ch.get("is_disabled", False),
        }
        r = requests.post(f"{MEDUSA_URL}/admin/sales-channels", headers=headers, json=payload, timeout=15)
        if r.status_code == 200:
            new_id = r.json()["sales_channel"]["id"]
            id_map[ch["id"]] = new_id
            existing_map[name] = new_id
            created += 1
            print(f"  NEW: {name}")
        else:
            print(f"  ERR: {name} - {r.status_code}")
        time.sleep(0.15)

    print(f"  Creados: {created}, Ya existían: {skipped}")
    return id_map


def restore_products(token, backup_products, sc_id_map, headers):
    print("Restaurando productos...")
    current = get_all(token, "/admin/products")
    sku_map = {}
    for p in current:
        for v in p.get("variants", []):
            if v.get("sku"):
                sku_map[v["sku"]] = {"product_id": p["id"], "variant_id": v["id"]}
                break

    created = 0
    updated = 0
    skipped = 0
    errors = 0
    variant_sku_map = {}

    for product in backup_products:
        title = product.get("title", "Sin título")
        variants = product.get("variants", [])
        sku = variants[0].get("sku") if variants else None

        if not sku:
            skipped += 1
            continue

        images = []
        for img in product.get("images", []):
            url = img.get("url") if isinstance(img, dict) else str(img)
            if url:
                images.append({"url": url})

        update_payload = {
            "title": product.get("title"),
            "description": product.get("description"),
            "status": product.get("status", "published"),
            "images": images,
        }
        if product.get("thumbnail"):
            update_payload["thumbnail"] = product["thumbnail"]
        if product.get("metadata"):
            update_payload["metadata"] = product["metadata"]

        v_prices = []
        if variants and variants[0].get("prices"):
            for pr in variants[0]["prices"]:
                if isinstance(pr, dict) and pr.get("amount") is not None:
                    v_prices.append({
                        "amount": pr["amount"],
                        "currency_code": pr.get("currency_code", "ars").lower()
                    })

        sc_ids = []
        for sc in product.get("sales_channels", []):
            old_id = sc.get("id")
            if old_id in sc_id_map:
                sc_ids.append(sc_id_map[old_id])

        try:
            if sku in sku_map:
                pid = sku_map[sku]["product_id"]
                vid = sku_map[sku]["variant_id"]
                if DRY_RUN:
                    variant_sku_map[sku] = {"product_id": pid, "variant_id": vid}
                    updated += 1
                    print(f"  DRY-RUPD {sku}: {title[:45]}")
                    continue
                if sc_ids:
                    update_payload["sales_channels"] = [{"id": sid} for sid in sc_ids]
                r = requests.post(f"{MEDUSA_URL}/admin/products/{pid}", headers=headers, json=update_payload, timeout=15)
                if r.status_code == 200:
                    if v_prices:
                        requests.post(f"{MEDUSA_URL}/admin/products/{pid}/variants/{vid}", headers=headers, json={"prices": v_prices}, timeout=15)
                    updated += 1
                    variant_sku_map[sku] = {"product_id": pid, "variant_id": vid}
                    print(f"  UPD {sku}: {title[:45]}")
                else:
                    errors += 1
                    print(f"  ERR {sku}: {r.status_code} - {r.text[:100]}")
            else:
                if DRY_RUN:
                    created += 1
                    print(f"  DRY-RNEW {sku}: {title[:45]}")
                    continue
                create_payload = dict(update_payload)
                create_payload["options"] = [{"title": "Default", "values": ["Default"]}]
                create_payload["variants"] = [{
                    "title": "Default",
                    "sku": sku,
                    "options": {"Default": "Default"},
                    "prices": v_prices
                }]
                if sc_ids:
                    create_payload["sales_channels"] = [{"id": sid} for sid in sc_ids]
                r = requests.post(f"{MEDUSA_URL}/admin/products", headers=headers, json=create_payload, timeout=15)
                if r.status_code == 200:
                    created += 1
                    new_p = r.json()["product"]
                    new_vid = new_p["variants"][0]["id"] if new_p.get("variants") else None
                    variant_sku_map[sku] = {"product_id": new_p["id"], "variant_id": new_vid}
                    print(f"  NEW {sku}: {title[:45]}")
                else:
                    errors += 1
                    print(f"  ERR {sku}: {r.status_code} - {r.text[:100]}")
            time.sleep(0.15)
        except Exception as e:
            errors += 1
            print(f"  ERR {sku}: {e}")

    print(f"\n  Actualizados: {updated}")
    print(f"  Creados:      {created}")
    print(f"  Omitidos:     {skipped}")
    print(f"  Errores:      {errors}")
    return variant_sku_map


def restore_inventory(token, backup_inventory, variant_sku_map, headers):
    print("\nRestaurando inventario...")

    # Get first available stock location dynamically
    r = requests.get(f"{MEDUSA_URL}/admin/stock-locations", headers=headers, params={"limit": 10}, timeout=15)
    locations = r.json().get("stock_locations", []) if r.status_code == 200 else []
    location_id = locations[0]["id"] if locations else None
    if not location_id:
        print("  ERR: no stock location found")
        return
    print(f"  Location: {locations[0]['name']} ({location_id})")

    restored = 0
    skipped = 0
    errors = 0

    for item in backup_inventory:
        sku = item.get("sku")
        stocked = item.get("stocked_quantity", 0)

        if not sku or sku not in variant_sku_map:
            skipped += 1
            continue

        vid = variant_sku_map[sku]["variant_id"]
        if not vid:
            skipped += 1
            continue

        try:
            if DRY_RUN:
                if stocked > 0:
                    restored += 1
                    print(f"  DRY-RUN {sku}: {stocked} unidades")
                else:
                    skipped += 1
                continue

            # Check current stock — don't overwrite if already > 0
            r_check = requests.get(
                f"{MEDUSA_URL}/admin/inventory-items/{item['id']}/location-levels",
                headers=headers, timeout=15,
            )
            if r_check.status_code == 200:
                levels = r_check.json().get("inventory_levels", [])
                current = sum(l.get("stocked_quantity", 0) for l in levels)
                if current > 0:
                    skipped += 1
                    continue

            r = requests.post(
                f"{MEDUSA_URL}/admin/products/{variant_sku_map[sku]['product_id']}/variants/{vid}/inventory-items",
                headers=headers,
                json={"inventory_item_id": item["id"], "required_quantity": 1},
                timeout=15,
            )
            if r.status_code not in (200, 409):
                print(f"  WARN link {sku}: {r.status_code}")

            if stocked > 0:
                r = requests.post(
                    f"{MEDUSA_URL}/admin/inventory-items/{item['id']}/location-levels",
                    headers=headers,
                    json={
                        "location_id": location_id,
                        "stocked_quantity": stocked,
                    },
                    timeout=15,
                )
                if r.status_code == 200:
                    restored += 1
                    print(f"  OK {sku}: {stocked} unidades")
                else:
                    errors += 1
                    print(f"  ERR {sku}: {r.status_code} - {r.text[:100]}")
            else:
                skipped += 1
            time.sleep(0.1)
        except Exception as e:
            errors += 1
            print(f"  ERR {sku}: {e}")

    print(f"\n  Stock restaurado: {restored}")
    print(f"  Sin stock/omitidos: {skipped}")
    print(f"  Errores: {errors}")


def restore():
    print(f"Conectando a {MEDUSA_URL}...")
    token = login()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("OK, autenticado.\n")

    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        backup = json.load(f)

    print(f"Backup del: {backup.get('timestamp', 'desconocido')}")
    print(f"  Productos:  {len(backup.get('products', []))}")
    print(f"  Categorías: {len(backup.get('categories', []))}")
    print(f"  Colecciones: {len(backup.get('collections', []))}")
    print(f"  Canales:    {len(backup.get('sales_channels', []))}")
    print(f"  Inventario: {len(backup.get('inventory_items', []))}")
    print()

    cat_id_map = restore_categories(token, backup.get("categories", []), headers)
    print()

    sc_id_map = restore_sales_channels(token, backup.get("sales_channels", []), headers)
    print()

    variant_sku_map = restore_products(token, backup.get("products", []), sc_id_map, headers)

    restore_inventory(token, backup.get("inventory_items", []), variant_sku_map, headers)


if __name__ == "__main__":
    restore()
