#!/usr/bin/env python3
"""
sync_imagenes_a_medusa_local.py - Vincula imágenes de Cloudinary a productos de Medusa local.

Lee las URLs de imagen de Cloudinary (de image_urls.json y de Medusa producción)
y las asigna a los productos de Medusa local que les faltan imágenes, haciendo match por SKU.

Uso:
  python3 scripts/sync_imagenes_a_medusa_local.py
  python3 scripts/sync_imagenes_a_medusa_local.py --dry-run

Credenciales: lee de .env.production vía medusa_auth.py (MEDUSA_ADMIN_EMAIL / PASSWORD).
URLs: usa MEDUSA_LOCAL_URL (default http://localhost:9100) y MEDUSA_PROD_URL
      (default https://dankoshop-api-production.up.railway.app).
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from medusa_auth import get_admin_credentials

LOCAL_URL = os.environ.get("MEDUSA_LOCAL_URL", "http://localhost:9100")
PROD_URL = os.environ.get("MEDUSA_PROD_URL", "https://dankoshop-api-production.up.railway.app")
IMAGE_URLS_PATH = Path(__file__).resolve().parent.parent / "data" / "image_urls.json"

DELAY_BETWEEN_CALLS = 0.1  # segundos, para no saturar la API local


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def login(base_url, email, password):
    r = requests.post(
        f"{base_url}/auth/user/emailpass",
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if r.status_code == 200:
        return r.json().get("token")
    print(f"  AUTH FAILED ({r.status_code}) contra {base_url}: {r.text[:200]}")
    return None


def api_request(base_url, token, method, endpoint, data=None, params=None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.request(
        method,
        f"{base_url}{endpoint}",
        headers=headers,
        json=data,
        params=params,
        timeout=30,
    )
    time.sleep(DELAY_BETWEEN_CALLS)
    return r


def get_all_products(base_url, token):
    """Devuelve lista completa de productos con paginación."""
    all_products = []
    offset = 0
    while True:
        r = api_request(base_url, token, "GET", "/admin/products",
                        params={"limit": 100, "offset": offset})
        if r.status_code != 200:
            print(f"  Error obteniendo productos offset={offset}: {r.status_code}")
            break
        batch = r.json().get("products", [])
        all_products.extend(batch)
        if len(batch) < 100:
            break
        offset += 100
    return all_products


def product_sku_list(product):
    """Extrae SKUs de los variants de un producto."""
    skus = []
    for v in product.get("variants", []):
        if v.get("sku"):
            skus.append(v["sku"])
    return skus


def product_has_thumbnail(product):
    """True si el producto tiene el campo thumbnail seteado."""
    return bool(product.get("thumbnail"))


def product_has_images(product):
    """True si el producto tiene array de images (aunque no tenga thumbnail)."""
    images = product.get("images") or []
    return len(images) > 0


def product_first_image_url(product):
    """Devuelve la URL de la primera imagen del array images, o None."""
    images = product.get("images") or []
    if images:
        return images[0].get("url")
    return None


# ---------------------------------------------------------------------------
# Obtener mapas de URLs de imagen
# ---------------------------------------------------------------------------
def load_image_urls_json():
    """Carga image_urls.json si existe."""
    if not IMAGE_URLS_PATH.exists():
        print(f"  WARN: {IMAGE_URLS_PATH} no existe, se omite.")
        return {}
    with open(IMAGE_URLS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    print(f"  image_urls.json: {len(data)} SKUs con URLs de Cloudinary")
    return data


def fetch_production_thumbnails(token):
    """Obtiene {sku: thumbnail_url} de todos los productos de Medusa producción."""
    print("  Conectando a Medusa producción para obtener URLs de imagen...")
    all_products = get_all_products(PROD_URL, token)
    sku_to_url = {}
    for p in all_products:
        thumb = p.get("thumbnail")
        if thumb:
            for sku in product_sku_list(p):
                sku_to_url[sku] = thumb
    print(f"  Producción: {len(all_products)} productos, {len(sku_to_url)} SKUs con thumbnail")
    return sku_to_url


def build_url_map():
    """Combina image_urls.json + producción. Producción tiene prioridad."""
    url_map = {}
    json_map = load_image_urls_json()
    for sku, urls in json_map.items():
        if urls:
            url_map[sku] = urls[0]  # tomar la primera URL

    prod_token = login(PROD_URL, *get_admin_credentials())
    if prod_token:
        prod_map = fetch_production_thumbnails(prod_token)
        # Producción sobrescribe para tener la URL más reciente/completa
        url_map.update(prod_map)
    else:
        print("  WARN: No se pudo autenticar en producción, se usa solo image_urls.json")

    print(f"  Total URLs de imagen disponibles: {len(url_map)}")
    return url_map


# ---------------------------------------------------------------------------
# Sincronización a Medusa local
# ---------------------------------------------------------------------------
def sync_images_to_local(local_token, url_map, dry_run=False):
    """Vincula imágenes de Cloudinary a productos de Medusa local que les faltan."""
    local_products = get_all_products(LOCAL_URL, local_token)
    print(f"  Medusa local: {len(local_products)} productos totales")

    helped = 0
    already_had = 0
    fixed_thumbnail = 0
    no_cloudinary_url = 0
    failed = 0
    details = []

    for p in local_products:
        product_id = p["id"]
        title = p.get("title", "")[:60]
        skus = product_sku_list(p)
        has_thumb = product_has_thumbnail(p)
        has_images = product_has_images(p)

        # Caso 1: Ya tiene thumbnail → todo bien
        if has_thumb:
            already_had += 1
            continue

        # Caso 2: Tiene images pero no thumbnail → setear thumbnail desde images[0]
        if has_images and not has_thumb:
            first_url = product_first_image_url(p)
            if not first_url:
                no_cloudinary_url += 1
                continue
            if dry_run:
                print(f"  [DRY-RUN] Setearía thumbnail para {skus[0] if skus else '?sku'}: {title}")
                fixed_thumbnail += 1
                continue
            r = api_request(
                LOCAL_URL, local_token, "POST",
                f"/admin/products/{product_id}",
                data={"thumbnail": first_url},
            )
            if r.status_code == 200:
                fixed_thumbnail += 1
                details.append((skus[0] if skus else "?", title, first_url, "thumbnail-fixed"))
                print(f"  OK-thumb {skus[0] if skus else '?'}: {title}")
            else:
                failed += 1
                details.append((skus[0] if skus else "?", title, first_url, f"error {r.status_code}"))
                print(f"  ERROR-thumb {skus[0] if skus else '?'}: {r.status_code} {r.text[:100]}")
            continue

        # Caso 3: No tiene ni thumbnail ni images → buscar URL en Cloudinary y agregar
        if not skus:
            no_cloudinary_url += 1
            continue

        image_url = None
        matched_sku = None
        for sku in skus:
            if sku in url_map:
                image_url = url_map[sku]
                matched_sku = sku
                break

        if not image_url:
            no_cloudinary_url += 1
            continue

        if dry_run:
            print(f"  [DRY-RUN] Se agregaría imagen a {matched_sku}: {title}")
            helped += 1
            details.append((matched_sku, title, image_url, "dry-run"))
            continue

        # Agregar imagen y setear como thumbnail
        r = api_request(
            LOCAL_URL, local_token, "POST",
            f"/admin/products/{product_id}",
            data={"images": [{"url": image_url}], "thumbnail": image_url},
        )

        if r.status_code == 200:
            helped += 1
            details.append((matched_sku, title, image_url, "ok"))
            print(f"  OK {matched_sku}: {title}")
        else:
            failed += 1
            details.append((matched_sku, title, image_url, f"error {r.status_code}"))
            print(f"  ERROR {matched_sku}: {r.status_code} {r.text[:100]}")

    return {
        "total_local": len(local_products),
        "already_had_image": already_had,
        "fixed_thumbnail": fixed_thumbnail,
        "helped": helped,
        "no_cloudinary_url": no_cloudinary_url,
        "failed": failed,
        "details": details,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("  Sync Imágenes Cloudinary → Medusa Local")
    print("=" * 60)

    # Credenciales locales
    email, password = get_admin_credentials(local=True)

    # Login a local
    local_token = login(LOCAL_URL, email, password)
    if not local_token:
        print("❌ No se pudo autenticar en Medusa local. Abortando.")
        sys.exit(1)
    print("  ✅ Autenticado en Medusa local\n")

    # Construir mapa de URLs de imagen
    print("\n🔗 Construyendo mapa de URLs de imagen...")
    url_map = build_url_map()

    # Sincronizar
    print("\n🖼️  Vinculando imágenes a productos de Medusa local...")
    if dry_run:
        print("  🔍 MODO DRY-RUN: no se escribirá nada\n")

    result = sync_images_to_local(local_token, url_map, dry_run=dry_run)

    # Resumen
    print("\n" + "=" * 60)
    print("  📊 RESUMEN")
    print("=" * 60)
    print(f"  Productos totales en local:     {result['total_local']}")
    print(f"  Ya tenían thumbnail:            {result['already_had_image']}")
    print(f"  Thumbnail fixado:               {result['fixed_thumbnail']}")
    print(f"  Imágenes agregadas:             {result['helped']}")
    print(f"  Sin URL en Cloudinary:          {result['no_cloudinary_url']}")
    print(f"  Errores:                        {result['failed']}")

    if result["no_cloudinary_url"] > 0:
        print(f"\n  ⚠️  {result['no_cloudinary_url']} productos no tienen URL en Cloudinary.")
        print("     Para cubrirlos, subir las imágenes faltantes a Cloudinary y actualizar")
        print("     image_urls.json, luego volver a ejecutar este script.")

    if not dry_run and (result["helped"] > 0 or result["fixed_thumbnail"] > 0):
        total_fixed = result["helped"] + result["fixed_thumbnail"]
        print(f"\n  ✅ {total_fixed} productos recibieron imagen/thumbnail de Cloudinary.")

    print("=" * 60)


if __name__ == "__main__":
    main()