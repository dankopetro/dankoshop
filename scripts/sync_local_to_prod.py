#!/usr/bin/env python3
"""
sync_local_to_prod.py - Sincronizar Local → Producción
Sube todos los productos de Medusa local (localhost:9100) a Railway (producción).

Uso:
  python3 scripts/sync_local_to_prod.py
"""

import os
import sys
import json
import time
import requests

sys.path.insert(0, os.path.dirname(__file__))
from sync_helpers import sync_inventory, fetch_source_inventory, sync_sales_channels, fetch_source_sales_channels, _api

LOCAL_URL = "http://localhost:9100"
PROD_URL = "https://dankoshop-api-production.up.railway.app"
EMAIL = os.environ.get("MEDUSA_ADMIN_EMAIL", "admin@dankoshop.com")
PASSWORD = os.environ.get("MEDUSA_ADMIN_PASSWORD", "supersecret")


def login(url):
    r = requests.post(f"{url}/auth/user/emailpass", json={"email": EMAIL, "password": PASSWORD}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


def get_all(url, token, endpoint):
    headers = {"Authorization": f"Bearer {token}"}
    all_items = []
    offset = 0
    while True:
        r = requests.get(f"{url}{endpoint}", headers=headers, params={"limit": 100, "offset": offset}, timeout=15)
        r.raise_for_status()
        data = r.json()
        items = data.get("products", data.get("collections", data.get("product_categories", [])))
        if not items:
            break
        all_items.extend(items)
        if len(items) < 100:
            break
        offset += 100
        time.sleep(0.3)
    return all_items


def restore_product(url, token, product):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    variants = product.get("variants", [])
    sku = variants[0].get("sku") if variants else None

    if not sku:
        return False

    # Build variant options as dict {option_title: value}
    variant_options = {"Default": "Default"}
    for v in variants:
        opts = v.get("options", [])
        if opts:
            variant_options = {}
            for opt in opts:
                if isinstance(opt, dict):
                    title = opt.get("option", {}).get("title", "Default") if isinstance(opt.get("option"), dict) else "Default"
                    value = opt.get("value", "Default")
                    variant_options[title] = value
            break
    if not variant_options:
        variant_options = {"Default": "Default"}

    payload = {
        "title": product.get("title"),
        "description": product.get("description"),
        "status": product.get("status", "published"),
        "images": [{"url": img["url"]} for img in product.get("images", []) if img.get("url")],
        "options": [{"title": k, "values": [v]} for k, v in variant_options.items()],
        "variants": [{
            "title": v.get("title", "Default"),
            "sku": v.get("sku"),
            "prices": [{"amount": pr["amount"], "currency_code": pr.get("currency_code", "ars")} for pr in v.get("prices", []) if pr.get("amount")],
            "options": variant_options,
        } for v in variants] if variants else [{"title": "Default", "sku": sku, "options": {"Default": "Default"}, "prices": []}],
    }

    if product.get("metadata"):
        payload["metadata"] = {k: v for k, v in product["metadata"].items() if not k.startswith("_")}

    # Buscar si existe por SKU
    r = requests.get(f"{url}/admin/products", headers=headers, params={"q": sku, "limit": 10}, timeout=15)
    existing = None
    if r.status_code == 200:
        for p in r.json().get("products", []):
            for v in p.get("variants", []):
                if v.get("sku") == sku:
                    existing = p
                    break

    if existing:
        r = requests.post(f"{url}/admin/products/{existing['id']}", headers=headers, json=payload, timeout=15)
        return existing["id"] if r.status_code == 200 else None
    else:
        r = requests.post(f"{url}/admin/products", headers=headers, json=payload, timeout=15)
        return r.json().get("product", {}).get("id") if r.status_code == 200 else None


def main():
    print("=" * 60)
    print("  Local → Producción (Railway)")
    print("=" * 60)

    # Test connections
    print(f"\nConectando a local: {LOCAL_URL}")
    try:
        r = requests.get(f"{LOCAL_URL}/health", timeout=5)
        if r.status_code != 200:
            print(f"  ERROR: Local no disponible ({r.status_code})")
            print("  Arrancá Medusa local: ./scripts/medusa-local.sh start")
            return
    except Exception as e:
        print(f"  ERROR: {e}")
        print("  Arrancá Medusa local: ./scripts/medusa-local.sh start")
        return

    print(f"Conectando a producción: {PROD_URL}")
    try:
        r = requests.get(f"{PROD_URL}/health", timeout=10)
        if r.status_code != 200:
            print(f"  ERROR: Producción no disponible ({r.status_code})")
            return
    except Exception as e:
        print(f"  ERROR: {e}")
        return

    # Login
    print("\nAutenticando...")
    local_token = login(LOCAL_URL)
    prod_token = login(PROD_URL)
    print("  OK")

    # Fetch from local
    print("\nDescargando productos de local...")
    products = get_all(LOCAL_URL, local_token, "/admin/products")
    print(f"  {len(products)} productos descargados")

    # Pre-fetch inventory and sales channels from source
    print("\nLeyendo inventario y canales de venta de Local...")
    src_inv = fetch_source_inventory(LOCAL_URL, local_token)
    print(f"  Inventario: {len(src_inv)} SKUs")
    src_sc = fetch_source_sales_channels(LOCAL_URL, local_token)
    print(f"  Canales: {len(src_sc)} productos con canales")

    # Restore to production
    print(f"\nRestaurando en producción...")
    created = 0
    updated = 0
    errors = 0

    for i, p in enumerate(products, 1):
        title = p.get("title", "?")[:40]
        sku = p.get("variants", [{}])[0].get("sku", "?")
        print(f"  [{i}/{len(products)}] {sku}: {title}", end="")

        try:
            new_id = restore_product(PROD_URL, prod_token, p)
            if new_id:
                print(" ✓")
                created += 1
                # Sync inventory
                qty = src_inv.get(sku)
                if qty is not None:
                    r_prod = _api(PROD_URL, prod_token, "GET", f"/admin/products/{new_id}")
                    if r_prod.status_code == 200:
                        variants = r_prod.json().get("product", {}).get("variants", [])
                        if variants:
                            sync_inventory(PROD_URL, prod_token, variants[0]["id"], sku, qty)
                # Sync sales channels
                ch = ", ".join(src_sc.get(p.get("id"), []))
                if ch:
                    sync_sales_channels(PROD_URL, prod_token, new_id, ch)
            else:
                print(" ✗")
                errors += 1
        except Exception as e:
            print(f" ✗ {e}")
            errors += 1

        time.sleep(0.2)

    print(f"\n{'='*60}")
    print(f"  Sincronizados: {created} | Errores: {errors}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
