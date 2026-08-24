#!/usr/bin/env python3
"""
Backup de Medusa vía Admin API.
Exporta productos, colecciones, categorías, inventario, ubicaciones y canales de venta.

Uso:
  export MEDUSA_BACKEND_URL=https://dankoshop-api-production.up.railway.app
  export MEDUSA_ADMIN_EMAIL=admin@dankoshop.com
  export MEDUSA_ADMIN_PASSWORD=tu-password
  python3 scripts/backup_medusa.py
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

MEDUSA_URL = os.environ.get("MEDUSA_BACKEND_URL", "https://dankoshop-api-production.up.railway.app")
EMAIL = os.environ.get("MEDUSA_ADMIN_EMAIL", "admin@dankoshop.com")
PASSWORD = os.environ.get("MEDUSA_ADMIN_PASSWORD", "")

if not PASSWORD:
    print("ERROR: Setear MEDUSA_ADMIN_PASSWORD")
    sys.exit(1)

BACKUP_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)


def login():
    r = requests.post(f"{MEDUSA_URL}/auth/user/emailpass", json={"email": EMAIL, "password": PASSWORD}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


def get_all(token, endpoint, params=None, key=None):
    headers = {"Authorization": f"Bearer {token}"}
    all_items = []
    offset = 0
    while True:
        p = {"limit": 100, "offset": offset}
        if params:
            p.update(params)
        r = requests.get(f"{MEDUSA_URL}{endpoint}", headers=headers, params=p, timeout=15)
        r.raise_for_status()
        data = r.json()
        if key:
            items = data.get(key, [])
        else:
            items = data.get("products", data.get("collections", data.get("product_categories", data.get("shipping_options", []))))
        if not items:
            break
        all_items.extend(items)
        if len(items) < 100:
            break
        offset += 100
        time.sleep(0.3)
    return all_items


def backup():
    print(f"Conectando a {MEDUSA_URL}...")
    token = login()
    print("OK, autenticado.\n")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_data = {"timestamp": ts, "source": MEDUSA_URL}

    print("Exportando productos...")
    products = get_all(token, "/admin/products")
    backup_data["products"] = products
    print(f"  {len(products)} productos")

    print("Exportando colecciones...")
    collections = get_all(token, "/admin/collections")
    backup_data["collections"] = collections
    print(f"  {len(collections)} colecciones")

    print("Exportando categorías...")
    categories = get_all(token, "/admin/product-categories")
    backup_data["categories"] = categories
    print(f"  {len(categories)} categorías")

    print("Exportando inventario...")
    inventory = get_all(token, "/admin/inventory-items", key="inventory_items")
    backup_data["inventory_items"] = inventory
    print(f"  {len(inventory)} items de inventario")

    print("Exportando ubicaciones de stock...")
    locations = get_all(token, "/admin/stock-locations", key="stock_locations")
    backup_data["stock_locations"] = locations
    print(f"  {len(locations)} ubicaciones")

    print("Exportando canales de venta...")
    channels = get_all(token, "/admin/sales-channels", key="sales_channels")
    backup_data["sales_channels"] = channels
    print(f"  {len(channels)} canales de venta")

    filename = f"backup_{ts}.json"
    filepath = os.path.join(BACKUP_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)

    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"\nBackup guardado: {filepath} ({size_mb:.1f} MB)")
    return filepath


if __name__ == "__main__":
    backup()
