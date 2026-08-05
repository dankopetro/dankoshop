#!/usr/bin/env python3
"""
Seed script to import products from data/products.json into Medusa.
Run this after Medusa backend is running.
"""

import json
import os
import sys
import time
import requests
from pathlib import Path

MEDUSA_URL = os.getenv("MEDUSA_BACKEND_URL", "http://localhost:9000")
ADMIN_EMAIL = os.getenv("MEDUSA_ADMIN_EMAIL", "admin@dankoshop.com")
ADMIN_PASSWORD = os.getenv("MEDUSA_ADMIN_PASSWORD", "supersecret")
JSON_PATH = Path("/home/claudio/Descargas/dankoshop/data/products.json")
IMAGES_BASE = Path("/home/claudio/Descargas/dankoshop/data/organized_images")


def get_admin_token():
    """Login to Medusa admin and get token"""
    resp = requests.post(
        f"{MEDUSA_URL}/admin/auth",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=10
    )
    if resp.status_code == 200:
        return resp.json().get("access_token")
    print(f"Login failed: {resp.text}")
    return None


def create_admin_user():
    """Create admin user if it doesn't exist"""
    try:
        resp = requests.post(
            f"{MEDUSA_URL}/admin/users",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
            },
            timeout=10
        )
        if resp.status_code == 200:
            print(f"Admin user created: {ADMIN_EMAIL}")
            return True
    except Exception:
        pass
    return False


def seed_products():
    """Import all products from JSON"""
    if not JSON_PATH.exists():
        print(f"Products file not found: {JSON_PATH}")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        products = json.load(f)

    print(f"Found {len(products)} products to import")
    
    # Try to login
    token = get_admin_token()
    if not token:
        print("Failed to get admin token. Make sure Medusa is running and admin user exists.")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Get or create sales channels
    resp = requests.get(f"{MEDUSA_URL}/admin/sales-channels", headers=headers, timeout=10)
    sales_channels = resp.json().get("sales_channels", []) if resp.status_code == 200 else []
    sales_channel_id = sales_channels[0]["id"] if sales_channels else None

    # Get categories
    resp = requests.get(f"{MEDUSA_URL}/admin/product-categories?limit=100", headers=headers, timeout=10)
    existing_categories = resp.json().get("product_categories", []) if resp.status_code == 200 else []
    category_map = {c["name"].lower(): c["id"] for c in existing_categories}

    success = 0
    failed = 0

    for i, product in enumerate(products, 1):
        sku = product["sku"]
        category_name = product.get("category", "Varios")
        
        # Get or create category
        category_id = category_map.get(category_name.lower())
        if not category_id:
            try:
                resp = requests.post(
                    f"{MEDUSA_URL}/admin/product-categories",
                    json={"name": category_name, "handle": category_name.lower().replace(" ", "-").replace("/", "-")},
                    headers=headers,
                    timeout=10
                )
                if resp.status_code == 200:
                    category_id = resp.json()["product_category"]["id"]
                    category_map[category_name.lower()] = category_id
            except Exception as e:
                print(f"  Error creating category: {e}")

        # Prepare prices
        prices = product.get("prices", {})
        price_lista = prices.get("precio_lista") or prices.get("precio_efectivo") or product.get("precio_lista") or product.get("precio_efectivo") or 0
        
        # Prepare product data
        product_data = {
            "title": product["name"],
            "handle": sku.lower().replace(" ", "-").replace("°", "").replace("/", "-").replace(".", ""),
            "description": product.get("description", "") or product.get("specs", ""),
            "status": "published",
            "thumbnail": None,
            "images": [],
            "categories": [{"id": category_id}] if category_id else [],
            "variants": [{
                "title": product["name"],
                "sku": sku,
                "manage_inventory": True,
                "inventory_quantity": 100,
                "allow_backorder": False,
                "prices": [
                    {"amount": price_lista, "currency_code": "ars"},
                ],
                "options": [],
            }],
            "options": [],
            "metadata": {
                "precio_lista": prices.get("precio_lista") or product.get("precio_lista"),
                "precio_efectivo": prices.get("precio_efectivo") or product.get("precio_efectivo"),
                "precio_transferencia": prices.get("precio_transferencia") or product.get("precio_transferencia"),
                "precio_mayorista": prices.get("precio_mayorista") or product.get("precio_mayorista"),
                "precio_mayorista_transferencia": prices.get("precio_mayorista_transferencia") or product.get("precio_mayorista_transferencia"),
                "cuotas": prices.get("cuotas") or product.get("cuotas"),
                "cuota_valor": prices.get("cuota_valor") or product.get("cuota_valor"),
                "specs": product.get("specs", ""),
            },
        }

        if sales_channel_id:
            product_data["sales_channels"] = [{"id": sales_channel_id}]

        # Check if product exists
        try:
            resp = requests.get(
                f"{MEDUSA_URL}/admin/products",
                params={"q": sku, "limit": 1},
                headers=headers,
                timeout=10
            )
            existing = None
            if resp.status_code == 200:
                items = resp.json().get("products", [])
                if items and items[0].get("variants") and items[0]["variants"][0].get("sku") == sku:
                    existing = items[0]

            if existing:
                # Update
                resp = requests.post(
                    f"{MEDUSA_URL}/admin/products/{existing['id']}",
                    json=product_data,
                    headers=headers,
                    timeout=30
                )
                if resp.status_code == 200:
                    print(f"  [{i}/{len(products)}] Updated: {sku}")
                    success += 1
                else:
                    print(f"  [{i}/{len(products)}] Failed to update {sku}: {resp.status_code}")
                    failed += 1
            else:
                # Create
                resp = requests.post(
                    f"{MEDUSA_URL}/admin/products",
                    json=product_data,
                    headers=headers,
                    timeout=30
                )
                if resp.status_code == 200:
                    print(f"  [{i}/{len(products)}] Created: {sku}")
                    success += 1
                else:
                    print(f"  [{i}/{len(products)}] Failed to create {sku}: {resp.status_code}")
                    failed += 1

        except Exception as e:
            print(f"  [{i}/{len(products)}] Error {sku}: {e}")
            failed += 1

        time.sleep(0.05)

    print(f"\nDone! Created/Updated: {success}, Failed: {failed}")


if __name__ == "__main__":
    print("=" * 60)
    print("DankoShop - Seed Products")
    print("=" * 60)
    seed_products()