#!/usr/bin/env python3
"""
sync_inteligente.py - Sync inteligente Local ↔ Producción
Solo crea, actualiza o salta productos. NUNCA borra.

Uso:
  python3 scripts/sync_inteligente.py --to-prod    # Local → Producción
  python3 scripts/sync_inteligente.py --to-local   # Producción → Local
"""

import os
import sys
import json
import time
import argparse
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
        items = data.get("products", [])
        if not items:
            break
        all_items.extend(items)
        if len(items) < 100:
            break
        offset += 100
        time.sleep(0.3)
    return all_items


def get_sku(product):
    variants = product.get("variants", [])
    return variants[0].get("sku") if variants else None


def normalize_product(product):
    """Extrae los campos comparables de un producto"""
    return {
        "title": product.get("title", ""),
        "description": product.get("description", ""),
        "status": product.get("status", "published"),
        "images": sorted([img.get("url", "") for img in product.get("images", []) if img.get("url")]),
        "prices": sorted([
            (pr.get("amount"), pr.get("currency_code", ""))
            for v in product.get("variants", [])
            for pr in v.get("prices", [])
            if pr.get("amount")
        ]),
        "metadata": product.get("metadata", {}),
        "categories": sorted([c.get("id", "") for c in product.get("categories", []) if c.get("id")]),
    }


def build_payload(product):
    """Construye el payload para crear/actualizar un producto"""
    variants = product.get("variants", [])

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
        } for v in variants] if variants else [{"title": "Default", "sku": product.get("variants", [{}])[0].get("sku"), "options": {"Default": "Default"}, "prices": []}],
    }
    if product.get("metadata"):
        payload["metadata"] = {k: v for k, v in product["metadata"].items() if not k.startswith("_")}
    return payload


def find_product_by_sku(url, token, sku):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{url}/admin/products", headers=headers, params={"q": sku, "limit": 20}, timeout=15)
    if r.status_code == 200:
        for p in r.json().get("products", []):
            for v in p.get("variants", []):
                if v.get("sku") == sku:
                    return p
    return None


def create_product(url, token, payload):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(f"{url}/admin/products", headers=headers, json=payload, timeout=15)
    if r.status_code == 200:
        return r.json().get("product", {}).get("id")
    if "already exists" in r.text and "handle" in r.text:
        sku = payload.get("variants", [{}])[0].get("sku", "")
        if sku:
            payload["handle"] = f"{payload.get('title', '').lower().replace(' ', '-').replace('/', '-')}-{sku}"
            r = requests.post(f"{url}/admin/products", headers=headers, json=payload, timeout=15)
            if r.status_code == 200:
                return r.json().get("product", {}).get("id")
    return None


def update_product(url, token, product_id, payload):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(f"{url}/admin/products/{product_id}", headers=headers, json=payload, timeout=15)
    return r.status_code == 200


def sync(source_name, source_url, source_token, dest_name, dest_url, dest_token):
    print(f"\n{'='*60}")
    print(f"  Sync: {source_name} → {dest_name}")
    print(f"{'='*60}")

    # Descargar productos de ambos lados
    print(f"\nDescargando de {source_name}...")
    source_products = get_all(source_url, source_token, "/admin/products")
    print(f"  {len(source_products)} productos en origen")

    print(f"Descargando de {dest_name}...")
    dest_products = get_all(dest_url, dest_token, "/admin/products")
    print(f"  {len(dest_products)} productos en destino")

    # Indexar por SKU
    source_map = {}
    for p in source_products:
        sku = get_sku(p)
        if sku:
            source_map[sku] = p

    dest_map = {}
    for p in dest_products:
        sku = get_sku(p)
        if sku:
            dest_map[sku] = p

    # Pre-fetch inventory and sales channels from source
    print(f"\nLeyendo inventario y canales de venta de {source_name}...")
    src_inv = fetch_source_inventory(source_url, source_token)
    print(f"  Inventario: {len(src_inv)} SKUs")
    src_sc = fetch_source_sales_channels(source_url, source_token)
    print(f"  Canales: {len(src_sc)} productos con canales")

    # Comparar y sincronizar
    print(f"\nComparando productos...")
    created = 0
    updated = 0
    skipped = 0
    errors = 0

    for i, (sku, src_product) in enumerate(source_map.items(), 1):
        title = src_product.get("title", "?")[:40]
        src_norm = normalize_product(src_product)

        if sku in dest_map:
            dest_product = dest_map[sku]
            dest_norm = normalize_product(dest_product)

            if src_norm == dest_norm:
                print(f"  [{i}/{len(source_map)}] {sku}: {title} → SALTAR")
                skipped += 1
            else:
                payload = build_payload(src_product)
                if update_product(dest_url, dest_token, dest_product["id"], payload):
                    print(f"  [{i}/{len(source_map)}] {sku}: {title} → ACTUALIZAR")
                    updated += 1
                    qty = src_inv.get(sku)
                    if qty is not None and dest_product.get("variants"):
                        sync_inventory(dest_url, dest_token, dest_product["variants"][0]["id"], sku, qty)
                    ch = ", ".join(src_sc.get(src_product.get("id"), []))
                    if ch:
                        sync_sales_channels(dest_url, dest_token, dest_product["id"], ch)
                else:
                    print(f"  [{i}/{len(source_map)}] {sku}: {title} → ERROR")
                    errors += 1
        else:
            payload = build_payload(src_product)
            new_id = create_product(dest_url, dest_token, payload)
            if new_id:
                print(f"  [{i}/{len(source_map)}] {sku}: {title} → CREAR")
                created += 1
                qty = src_inv.get(sku)
                if qty:
                    r_prod = _api(dest_url, dest_token, "GET", f"/admin/products/{new_id}")
                    if r_prod.status_code == 200:
                        variants = r_prod.json().get("product", {}).get("variants", [])
                        if variants:
                            sync_inventory(dest_url, dest_token, variants[0]["id"], sku, qty)
                ch = ", ".join(src_sc.get(src_product.get("id"), []))
                if ch:
                    sync_sales_channels(dest_url, dest_token, new_id, ch)
            else:
                print(f"  [{i}/{len(source_map)}] {sku}: {title} → ERROR")
                errors += 1

        time.sleep(0.2)

    # Resumen
    print(f"\n{'='*60}")
    print(f"  Resumen:")
    print(f"    Creados:      {created}")
    print(f"    Actualizados: {updated}")
    print(f"    Sin cambios:  {skipped}")
    print(f"    Errores:      {errors}")
    print(f"{'='*60}")

    if source_name == "Local":
        print(f"\n  ⚠️  Para BORRAR productos, hacelo manualmente en {dest_name}")
        print(f"     (el sync NUNCA borra productos)")


def main():
    parser = argparse.ArgumentParser(description="Sync inteligente Local ↔ Producción")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--to-prod", action="store_true", help="Local → Producción")
    group.add_argument("--to-local", action="store_true", help="Producción → Local")
    args = parser.parse_args()

    # Test connections
    print("Verificando conexiones...")

    print(f"  Local: {LOCAL_URL}", end="")
    try:
        r = requests.get(f"{LOCAL_URL}/health", timeout=5)
        print(f" {'✓' if r.status_code == 200 else '✗'}")
        if r.status_code != 200:
            print("  Arrancá Medusa local: ./scripts/medusa-local.sh start")
            return
    except Exception as e:
        print(f" ✗ {e}")
        print("  Arrancá Medusa local: ./scripts/medusa-local.sh start")
        return

    print(f"  Producción: {PROD_URL}", end="")
    try:
        r = requests.get(f"{PROD_URL}/health", timeout=10)
        print(f" {'✓' if r.status_code == 200 else '✗'}")
        if r.status_code != 200:
            return
    except Exception as e:
        print(f" ✗ {e}")
        return

    # Login
    print("\nAutenticando...")
    local_token = login(LOCAL_URL)
    prod_token = login(PROD_URL)
    print("  OK")

    # Sync
    if args.to_prod:
        sync("Local", LOCAL_URL, local_token, "Producción", PROD_URL, prod_token)
    else:
        sync("Producción", PROD_URL, prod_token, "Local", LOCAL_URL, local_token)


if __name__ == "__main__":
    main()
