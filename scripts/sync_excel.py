#!/usr/bin/env python3
"""
Sync products from excel/Productos_Maestro.xlsx to Medusa v2 backend via REST API.
Usage:
  MEDUSA_BACKEND_URL=https://... python3 sync_excel.py

Creates the Argentina (ARS) region if missing, creates missing categories,
and creates/updates products with minorista prices as metadata and ARS
calculated prices on the default variant.
"""

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
EXCEL_PATH = Path("/home/claudio/Descargas/dankoshop/excel/Productos_Maestro.xlsx")
IMAGE_URLS_FILE = Path("/home/claudio/Descargas/dankoshop/data/image_urls.json")
ADMIN_EMAIL = os.getenv("MEDUSA_ADMIN_EMAIL", "admin@dankoshop.com")
ADMIN_PASSWORD = os.getenv("MEDUSA_ADMIN_PASSWORD", "supersecret")

HEADERS = {"Content-Type": "application/json"}
if MEDUSA_API_TOKEN:
    HEADERS["Authorization"] = f"Bearer {MEDUSA_API_TOKEN}"


def read_products() -> List[Dict]:
    """Read products directly from excel/Productos_Maestro.xlsx"""
    if not EXCEL_PATH.exists():
        print(f"Excel maestro not found at {EXCEL_PATH}")
        return []

    import openpyxl
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active

    def parse_float(val):
        if val is None:
            return None
        try:
            return float(str(val).replace("$", "").replace(",", "").strip())
        except Exception:
            return None

    def parse_int(val):
        if val is None:
            return None
        try:
            return int(float(str(val).replace("$", "").replace(",", "").strip()))
        except Exception:
            return None

    products = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0] or not row[1]:
            continue
        products.append({
            "sku": str(row[0]).strip(),
            "name": str(row[1]).strip(),
            "category": str(row[2]).strip() if row[2] else "General",
            "precio_lista": parse_float(row[3]),
            "precio_efectivo": parse_float(row[4]),
            "precio_transferencia": parse_float(row[5]),
            "precio_mayorista": parse_float(row[6]),
            "precio_mayorista_transferencia": None,
            "cuotas": parse_int(row[7]),
            "cuota_valor": parse_float(row[8]),
            "description": str(row[9]).strip() if row[9] else "",
        })
    print(f"Loaded {len(products)} products from {EXCEL_PATH}")
    return products


def load_image_urls() -> Dict[str, List[str]]:
    """Load {sku: [url, ...]} mapping from data/image_urls.json"""
    if not IMAGE_URLS_FILE.exists():
        print(f"image_urls.json not found at {IMAGE_URLS_FILE}")
        return {}
    try:
        data = json.loads(IMAGE_URLS_FILE.read_text())
    except Exception as e:
        print(f"Could not parse image_urls.json: {e}")
        return {}
    if isinstance(data, dict):
        return {str(k): (v if isinstance(v, list) else [v]) for k, v in data.items()}
    return {}


def get_auth_token() -> Optional[str]:
    """Get API token from Medusa v2 admin login"""
    global MEDUSA_API_TOKEN
    if MEDUSA_API_TOKEN:
        return MEDUSA_API_TOKEN

    try:
        resp = requests.post(
            f"{MEDUSA_URL}/auth/user/emailpass",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if resp.status_code == 200:
            token = resp.json().get("token")
            if token:
                MEDUSA_API_TOKEN = token
                HEADERS["Authorization"] = f"Bearer {token}"
                return token
        else:
            print(f"Login failed ({resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"Login failed: {e}")
    return None


def medusa_request(method: str, endpoint: str, data: dict = None, params: dict = None) -> requests.Response:
    """Make authenticated request to Medusa v2 API"""
    token = get_auth_token()
    if not token:
        raise Exception("No auth token available")

    url = f"{MEDUSA_URL}{endpoint}"
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"

    return requests.request(method, url, headers=headers, json=data, params=params, timeout=30)


def ensure_argentina_region() -> Optional[str]:
    """Return existing ARS region id or create it."""
    resp = medusa_request("GET", "/admin/regions", params={"limit": 100})
    if resp.status_code == 200:
        for r in resp.json().get("regions", []):
            if r.get("currency_code") == "ars":
                return r.get("id")
    resp = medusa_request("POST", "/admin/regions", data={
        "name": "Argentina",
        "currency_code": "ars",
        "countries": ["ar"],
        "payment_providers": [],
        "metadata": {},
    })
    if resp.status_code == 200:
        return resp.json()["region"]["id"]
    print(f"Failed to create Argentina region: {resp.status_code} {resp.text}")
    return None


def get_or_create_category(category_name: str) -> Optional[str]:
    """Get existing category by exact name or create it."""
    try:
        resp = medusa_request("GET", "/admin/product-categories", params={"limit": 100})
        if resp.status_code == 200:
            for cat in resp.json().get("product_categories", []):
                if cat.get("name", "").lower() == category_name.lower():
                    return cat.get("id")
        resp = medusa_request("POST", "/admin/product-categories", data={"name": category_name})
        if resp.status_code == 200:
            return resp.json()["product_category"]["id"]
        print(f"Failed to create category {category_name}: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Error with category {category_name}: {e}")
    return None


def find_product_by_sku(sku: str) -> Optional[Dict]:
    """Find existing product by matching variant SKU."""
    resp = medusa_request("GET", "/admin/products", params={"q": sku, "limit": 10})
    if resp.status_code != 200:
        return None
    for p in resp.json().get("products", []):
        for v in p.get("variants", []):
            if v.get("sku") == sku:
                return p
    return None


def build_metadata(product: Dict) -> Dict:
    precio_mayorista = product.get("precio_mayorista")

    if not precio_mayorista:
        return {}

    m = float(precio_mayorista)
    precio_lista = int(round(m * 1.25))
    precio_efectivo = int(round(m * 1.10))
    precio_transferencia = int(round(m * 1.15))

    cuota_3 = int(round(precio_lista / 3))
    cuota_6 = int(round(precio_lista / 6))
    tasa_ml = 0.12
    factor_12 = ((1 + tasa_ml) ** 12 - 1) / (tasa_ml * (1 + tasa_ml) ** 12)
    cuota_12 = int(round(precio_lista / factor_12))

    return {
        "precio_lista": precio_lista,
        "precio_efectivo": precio_efectivo,
        "precio_transferencia": precio_transferencia,
        "precio_mayorista": int(round(m)),
        "cuota_valor_3": cuota_3,
        "cuota_valor_6": cuota_6,
        "cuota_valor_12": cuota_12,
    }


def slugify(value: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFD", value)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = "".join(c if c.isalnum() else "-" for c in s)
    return s.strip("-")[:200] or "producto"


def update_variant_price(product_id: str, variant_id: str, price: float, region_id: str) -> bool:
    """Set ARS price on the variant (region-scoped)."""
    resp = medusa_request("POST", f"/admin/products/{product_id}/variants/{variant_id}", data={
        "prices": [{"amount": int(round(price)), "currency_code": "ars", "region_id": region_id}],
    })
    return resp.status_code == 200


def create_or_update_product(product: Dict, region_id: str, category_id: Optional[str], image_urls: Dict[str, List[str]]) -> bool:
    """Create or update product in Medusa v2."""
    sku = product["sku"]
    precio_mayorista = product.get("precio_mayorista")
    list_price = int(round(float(precio_mayorista) * 1.25)) if precio_mayorista else 0
    images = [{"url": u} for u in (image_urls.get(sku) or [])[:10]]

    metadata = build_metadata(product)
    handle = slugify(sku)

    existing = find_product_by_sku(sku)

    if existing:
        product_id = existing["id"]
        variant_id = None
        for v in existing.get("variants", []):
            if v.get("sku") == sku:
                variant_id = v.get("id")
                break

        update_payload = {"metadata": metadata}
        if images:
            update_payload["images"] = images
            update_payload["thumbnail"] = images[0]["url"]
        resp = medusa_request("POST", f"/admin/products/{product_id}", data=update_payload)
        if resp.status_code != 200:
            print(f"  Failed to update {sku}: {resp.status_code} {resp.text}")
            return False

        if variant_id and list_price > 0:
            if not update_variant_price(product_id, variant_id, list_price, region_id):
                print(f"  Failed to update price for {sku}")
                return False

        print(f"  Updated: {sku}")
        return True

    # Create new product
    variant = {
        "title": "Default",
        "sku": sku,
        "options": {"Default": "Default"},
        "prices": [{"amount": list_price, "currency_code": "ars", "region_id": region_id}] if list_price > 0 else [],
    }
    product_data = {
        "title": product["name"],
        "description": product["description"] or "",
        "handle": handle,
        "status": "published",
        "thumbnail": images[0]["url"] if images else None,
        "images": images,
        "options": [{"title": "Default", "values": ["Default"]}],
        "variants": [variant],
        "categories": [{"id": category_id}] if category_id else [],
        "metadata": metadata,
    }
    resp = medusa_request("POST", "/admin/products", data=product_data)
    if resp.status_code == 200:
        print(f"  Created: {sku}")
        return True
    print(f"  Failed to create {sku}: {resp.status_code} {resp.text}")
    return False


def main():
    print("=" * 60)
    print("DankoShop - Sync Products to Medusa v2")
    print("=" * 60)

    try:
        resp = requests.get(f"{MEDUSA_URL}/health", timeout=10)
        if resp.status_code != 200:
            print(f"Medusa not healthy at {MEDUSA_URL}")
            return
    except Exception as e:
        print(f"Cannot connect to Medusa at {MEDUSA_URL}: {e}")
        return

    if not get_auth_token():
        print("Could not authenticate with Medusa admin. Check MEDUSA_ADMIN_EMAIL/PASSWORD.")
        return

    products = read_products()
    if not products:
        print("No products to sync")
        return
    image_urls = load_image_urls()

    region_id = ensure_argentina_region()
    if not region_id:
        print("Could not ensure Argentina (ARS) region. Aborting.")
        return
    print(f"Argentina region: {region_id}")

    print(f"Found {len(products)} products | images mapped: {len(image_urls)}")
    print(f"Medusa URL: {MEDUSA_URL}")
    print("-" * 60)

    success = 0
    failed = 0
    for i, product in enumerate(products, 1):
        print(f"[{i}/{len(products)}] {product['sku']}: {product['name'][:50]}")
        category_id = get_or_create_category(product["category"])
        if create_or_update_product(product, region_id, category_id, image_urls):
            success += 1
        else:
            failed += 1
        time.sleep(0.1)

    print("-" * 60)
    print(f"Done! Success: {success}, Failed: {failed}")


if __name__ == "__main__":
    main()
