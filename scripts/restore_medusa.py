#!/usr/bin/env python3
"""
Restaurar backup de Medusa vía Admin API.
Actualiza productos existentes (por SKU) o crea nuevos.

Uso:
  export MEDUSA_BACKEND_URL=https://dankoshop-api-production.up.railway.app
  export MEDUSA_ADMIN_EMAIL=admin@dankoshop.com
  export MEDUSA_ADMIN_PASSWORD=supersecret
  python3 scripts/restore_medusa.py data/backups/backup_20260811_193821.json
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
    print("Uso: python3 restore_medusa.py <backup_file.json>")
    sys.exit(1)

BACKUP_FILE = sys.argv[1]


def login():
    r = requests.post(f"{MEDUSA_URL}/auth/user/emailpass", json={"email": EMAIL, "password": PASSWORD}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


def get_all(token, endpoint):
    headers = {"Authorization": f"Bearer {token}"}
    all_items = []
    offset = 0
    while True:
        r = requests.get(f"{MEDUSA_URL}{endpoint}", headers=headers, params={"limit": 100, "offset": offset}, timeout=15)
        r.raise_for_status()
        data = r.json()
        items = data.get("products", data.get("collections", data.get("product_categories", data.get("items", []))))
        if not items:
            break
        all_items.extend(items)
        if len(items) < 100:
            break
        offset += 100
        time.sleep(0.2)
    return all_items


def restore():
    print(f"Conectando a {MEDUSA_URL}...")
    token = login()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("OK, autenticado.\n")

    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        backup = json.load(f)

    print(f"Backup del: {backup.get('timestamp', 'desconocido')}")
    print(f"Productos en backup: {len(backup.get('products', []))}\n")

    print("Obteniendo productos actuales...")
    current = get_all(token, "/admin/products")
    sku_map = {}
    for p in current:
        for v in p.get("variants", []):
            if v.get("sku"):
                sku_map[v["sku"]] = {"product_id": p["id"], "variant_id": v["id"]}
                break
    print(f"  {len(sku_map)} productos actuales\n")

    created = 0
    updated = 0
    skipped = 0
    errors = 0

    for product in backup.get("products", []):
        title = product.get("title", "Sin título")
        variants = product.get("variants", [])
        sku = variants[0].get("sku") if variants else None

        if not sku:
            skipped += 1
            continue

        # Format images
        images = []
        for img in product.get("images", []):
            url = img.get("url") if isinstance(img, dict) else str(img)
            if url:
                images.append({"url": url})

        # Base payload for updating existing product
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

        # Price payload for variant
        v_prices = []
        if variants and variants[0].get("prices"):
            for pr in variants[0]["prices"]:
                if isinstance(pr, dict) and pr.get("amount") is not None:
                    v_prices.append({
                        "amount": pr["amount"],
                        "currency_code": pr.get("currency_code", "ars").lower()
                    })

        try:
            if sku in sku_map:
                # Update existing product
                pid = sku_map[sku]["product_id"]
                vid = sku_map[sku]["variant_id"]

                r = requests.post(f"{MEDUSA_URL}/admin/products/{pid}", headers=headers, json=update_payload, timeout=15)
                if r.status_code == 200:
                    if v_prices:
                        requests.post(f"{MEDUSA_URL}/admin/products/{pid}/variants/{vid}", headers=headers, json={"prices": v_prices}, timeout=15)
                    updated += 1
                    print(f"  UPD {sku}: {title[:45]}")
                else:
                    errors += 1
                    print(f"  ERR {sku}: {r.status_code} - {r.text[:100]}")
            else:
                # Create new product
                create_payload = dict(update_payload)
                create_payload["options"] = [{"title": "Default", "values": ["Default"]}]
                create_payload["variants"] = [{
                    "title": "Default",
                    "sku": sku,
                    "options": {"Default": "Default"},
                    "prices": v_prices
                }]
                r = requests.post(f"{MEDUSA_URL}/admin/products", headers=headers, json=create_payload, timeout=15)
                if r.status_code == 200:
                    created += 1
                    print(f"  NEW {sku}: {title[:45]}")
                else:
                    errors += 1
                    print(f"  ERR {sku}: {r.status_code} - {r.text[:100]}")
            time.sleep(0.15)
        except Exception as e:
            errors += 1
            print(f"  ERR {sku}: {e}")

    print(f"\nResumen:")
    print(f"  Actualizados: {updated}")
    print(f"  Creados:      {created}")
    print(f"  Omitidos:     {skipped}")
    print(f"  Errores:      {errors}")


if __name__ == "__main__":
    restore()
