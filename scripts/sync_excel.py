#!/usr/bin/env python3
"""
Sync products from CSV/JSON to Medusa backend via REST API.
Run after editing excel/Productos_Maestro.xlsx and exporting to CSV.
"""

import csv
import json
import os
import sys
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional

# Config
MEDUSA_URL = os.getenv("MEDUSA_BACKEND_URL", "http://localhost:9000")
MEDUSA_API_TOKEN = os.getenv("MEDUSA_API_TOKEN", "")
CSV_PATH = Path("/home/claudio/Descargas/dankoshop/data/products.csv")
JSON_PATH = Path("/home/claudio/Descargas/dankoshop/data/products.json")
IMAGES_BASE = Path("/home/claudio/Descargas/dankoshop/data/organized_images")

HEADERS = {
    "Content-Type": "application/json",
}
if MEDUSA_API_TOKEN:
    HEADERS["Authorization"] = f"Bearer {MEDUSA_API_TOKEN}"


EXCEL_PATH = Path("/home/claudio/Descargas/dankoshop/excel/Productos_Maestro.xlsx")

def read_products() -> List[Dict]:
    """Read products directly from excel/Productos_Maestro.xlsx"""
    if not EXCEL_PATH.exists():
        print(f"Excel maestro not found at {EXCEL_PATH}")
        return []
    
    import openpyxl
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active
    
    products = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0] or not row[1]:
            continue
        sku = str(row[0]).strip()
        name = str(row[1]).strip()
        category = str(row[2]).strip() if row[2] else "General"
        def parse_float(val):
            if val is None:
                return None
            try:
                return float(str(val).replace("$", "").replace(",", "").strip())
            except:
                return None
        def parse_int(val):
            if val is None:
                return None
            try:
                return int(float(str(val).replace("$", "").replace(",", "").strip()))
            except:
                return None

        precio_lista = parse_float(row[3])
        precio_efectivo = parse_float(row[4])
        precio_transferencia = parse_float(row[5])
        precio_mayorista = parse_float(row[6])
        cuotas = parse_int(row[7])
        cuota_valor = parse_float(row[8])
        description = str(row[9]).strip() if row[9] else ""
        imgs_str = str(row[10]).strip() if row[10] else ""
        images = [i.strip() for i in imgs_str.split("|") if i.strip()]
        
        products.append({
            "sku": sku,
            "name": name,
            "category": category,
            "description": description,
            "specs": "",
            "precio_lista": precio_lista,
            "precio_efectivo": precio_efectivo,
            "precio_transferencia": precio_transferencia,
            "precio_mayorista": precio_mayorista,
            "cuotas": cuotas,
            "cuota_valor": cuota_valor,
            "images": images,
        })
    print(f"Loaded {len(products)} products from {EXCEL_PATH}")
    return products


def get_auth_token() -> Optional[str]:
    """Get API token from Medusa admin login"""
    global MEDUSA_API_TOKEN
    if MEDUSA_API_TOKEN:
        return MEDUSA_API_TOKEN
    
    # Try to login with default admin credentials
    email = os.getenv("MEDUSA_ADMIN_EMAIL", "admin@dankoshop.com")
    password = os.getenv("MEDUSA_ADMIN_PASSWORD", "supersecret")
    
    try:
        resp = requests.post(
            f"{MEDUSA_URL}/admin/auth",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            if token:
                MEDUSA_API_TOKEN = token
                HEADERS["Authorization"] = f"Bearer {token}"
                return token
    except Exception as e:
        print(f"Login failed: {e}")
    return None


def medusa_request(method: str, endpoint: str, data: dict = None, params: dict = None) -> requests.Response:
    """Make authenticated request to Medusa API"""
    token = get_auth_token()
    if not token:
        raise Exception("No auth token available")
    
    url = f"{MEDUSA_URL}{endpoint}"
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    
    return requests.request(method, url, headers=headers, json=data, params=params, timeout=30)


def get_or_create_category(category_name: str) -> Optional[str]:
    """Get existing category or create new one"""
    try:
        # Search for category
        resp = medusa_request("GET", "/admin/product-categories", params={"q": category_name, "limit": 10})
        if resp.status_code == 200:
            categories = resp.json().get("product_categories", [])
            for cat in categories:
                if cat["name"].lower() == category_name.lower():
                    return cat["id"]
        
        # Create new category
        resp = medusa_request("POST", "/admin/product-categories", data={"name": category_name})
        if resp.status_code == 200:
            return resp.json()["product_category"]["id"]
        else:
            print(f"Failed to create category {category_name}: {resp.text}")
    except Exception as e:
        print(f"Error with category {category_name}: {e}")
    return None


def upload_image(image_path: Path) -> Optional[str]:
    """Upload image to Medusa and return file ID"""
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/jpeg')}
            headers = {"Authorization": HEADERS.get("Authorization", "")}
            resp = requests.post(
                f"{MEDUSA_URL}/admin/uploads",
                headers=headers,
                files=files,
                timeout=30
            )
        if resp.status_code == 200:
            return resp.json()["file"]["id"]
        else:
            print(f"Failed to upload {image_path}: {resp.text}")
    except Exception as e:
        print(f"Error uploading {image_path}: {e}")
    return None


def create_or_update_product(product: Dict) -> bool:
    """Create or update product in Medusa"""
    sku = product["sku"]
    
    # Check if product exists by SKU
    try:
        resp = medusa_request("GET", "/admin/products", params={"q": sku, "limit": 1})
        existing = None
        if resp.status_code == 200:
            products = resp.json().get("products", [])
            for p in products:
                if p.get("variants") and p["variants"][0].get("sku") == sku:
                    existing = p
                    break
    except Exception as e:
        print(f"Error checking existing product {sku}: {e}")
        existing = None
    
    # Prepare product data
    prices = product.get("prices", {}) if "prices" in product else {}
    # If flat structure from CSV
    if "precio_lista" in product:
        prices = {
            "precio_lista": product["precio_lista"],
            "precio_efectivo": product["precio_efectivo"],
            "precio_transferencia": product["precio_transferencia"],
            "precio_mayorista": product["precio_mayorista"],
        }
    
    # Get category
    category_id = get_or_create_category(product["category"])
    
    # Prepare variant
    variant = {
        "sku": sku,
        "title": product["name"],
        "prices": [
            {"amount": prices.get("precio_lista", 0) or prices.get("precio_efectivo", 0), "currency_code": "ars", "region_id": "reg_01"},
        ],
        "options": [],
        "manage_inventory": True,
        "inventory_quantity": 100,
        "allow_backorder": False,
    }
    
    # Add metadata for different price types
    metadata = {
        "precio_lista": prices.get("precio_lista"),
        "precio_efectivo": prices.get("precio_efectivo"),
        "precio_transferencia": prices.get("precio_transferencia"),
        "precio_mayorista": prices.get("precio_mayorista"),
        "precio_mayorista_transferencia": prices.get("precio_mayorista_transferencia"),
        "cuotas": product.get("cuotas"),
        "cuota_valor": product.get("cuota_valor"),
    }
    
    product_data = {
        "title": product["name"],
        "subtitle": "",
        "description": product["description"] or product.get("specs", ""),
        "handle": sku.lower().replace(" ", "-").replace("°", "").replace("n°", "").replace("/", "-"),
        "status": "published",
        "thumbnail": None,
        "images": [],
        "options": [],
        "variants": [variant],
        "categories": [{"id": category_id}] if category_id else [],
        "tags": [],
        "metadata": {k: v for k, v in metadata.items() if v is not None},
        "sales_channels": [{"id": "sc_01"}] if False else [],  # Will need actual sales channel ID
    }
    
    if existing:
        # Update existing product
        product_id = existing["id"]
        try:
            resp = medusa_request("POST", f"/admin/products/{product_id}", data=product_data)
            if resp.status_code == 200:
                print(f"  Updated: {sku}")
                # Upload images
                upload_product_images(product_id, product["images"])
                return True
            else:
                print(f"  Failed to update {sku}: {resp.text}")
        except Exception as e:
            print(f"  Error updating {sku}: {e}")
    else:
        # Create new product
        try:
            resp = medusa_request("POST", "/admin/products", data=product_data)
            if resp.status_code == 200:
                new_product = resp.json()["product"]
                print(f"  Created: {sku}")
                # Upload images
                upload_product_images(new_product["id"], product["images"])
                return True
            else:
                print(f"  Failed to create {sku}: {resp.text}")
        except Exception as e:
            print(f"  Error creating {sku}: {e}")
    return False


def upload_product_images(product_id: str, image_paths: List[str]):
    """Upload images for a product"""
    for img_path in image_paths:
        full_path = Path("/home/claudio/Descargas/dankoshop") / img_path
        if full_path.exists():
            file_id = upload_image(full_path)
            if file_id:
                try:
                    medusa_request("POST", f"/admin/products/{product_id}/images", data={"file_id": file_id})
                    print(f"    + Image: {full_path.name}")
                except Exception as e:
                    print(f"    Error attaching image: {e}")


def main():
    print("=" * 60)
    print("DankoShop - Sync Products to Medusa")
    print("=" * 60)
    
    # Check Medusa connectivity
    try:
        resp = requests.get(f"{MEDUSA_URL}/health", timeout=5)
        if resp.status_code != 200:
            print(f"Medusa not healthy at {MEDUSA_URL}")
            return
    except Exception as e:
        print(f"Cannot connect to Medusa at {MEDUSA_URL}: {e}")
        print("Make sure Medusa backend is running: npm run dev:backend")
        return
    
    # Read products
    products = read_products()
    if not products:
        print("No products to sync")
        return
    
    print(f"Found {len(products)} products")
    print(f"Medusa URL: {MEDUSA_URL}")
    print("-" * 60)
    
    # Sync each product
    success = 0
    failed = 0
    for i, product in enumerate(products, 1):
        print(f"[{i}/{len(products)}] {product['sku']}: {product['name'][:50]}")
        if create_or_update_product(product):
            success += 1
        else:
            failed += 1
        time.sleep(0.1)  # Rate limiting
    
    print("-" * 60)
    print(f"Done! Success: {success}, Failed: {failed}")


if __name__ == "__main__":
    main()