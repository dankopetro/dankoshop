#!/usr/bin/env python3
"""
extraer_imagenes_categoria.py - Extrae las imágenes de una categoría a una carpeta destino.

Fuentes de imagen (en orden de prioridad):
  1. Imágenes ASIGNADAS en Medusa producción (fuente de verdad = lo que ve el cliente)
  2. URLs de Cloudinary en data/image_urls.json
  3. Imágenes locales data/products_images/{SKU}/ (SOLO con --fuente local)

⚠️ La carpeta local data/products_images/ está CONTAMINADA (archivos renombrados
   y productos ajenos mezclados). Por eso Medusa producción es la fuente por defecto,
   nunca la carpeta local. Usa --fuente local solo si sabés lo que hacés.

Uso:
  python3 scripts/extraer_imagenes_categoria.py --categoria "Celulares" --destino /ruta/carpeta
  python3 scripts/extraer_imagenes_categoria.py --categoria Celulares --destino ./salida --fuente cloudinary
  python3 scripts/extraer_imagenes_categoria.py --categoria Celulares --destino ./salida --dry-run

Flags:
  --categoria   Nombre exacto de la categoría (case-insensitive). Ej: Celulares, TVs.
  --destino     Carpeta de salida (se crea si no existe).
  --fuente      auto (default, usa las 3 fuentes) | local | cloudinary | medusa
  --por-sku     Subcarpeta por SKU dentro del destino (default: archivos planos).
  --dry-run     Solo lista lo que se extraería, no escribe nada.

Credenciales: lee .env.production vía medusa_auth.py (para la fuente Medusa).
"""

import os
import sys
import json
import argparse
import shutil
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from medusa_auth import get_admin_credentials  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_IMAGES_DIR = ROOT / "data" / "products_images"
IMAGE_URLS_JSON = ROOT / "data" / "image_urls.json"
MEDUSA_PROD_URL = os.environ.get(
    "MEDUSA_PROD_URL", "https://dankoshop-api-production.up.railway.app"
)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".JPG", ".JPEG", ".PNG", ".WEBP"}


def get_category_skus_prod(category_name):
    """Devuelve [(sku, title)] de los productos publicados de una categoría en Medusa producción."""
    email, password = get_admin_credentials()
    r = requests.post(
        f"{MEDUSA_PROD_URL}/auth/user/emailpass",
        json={"email": email, "password": password},
        timeout=15,
    )
    r.raise_for_status()
    headers = {"Authorization": f"Bearer {r.json()['token']}"}

    # Buscar la categoría por nombre (case-insensitive)
    rr = requests.get(
        f"{MEDUSA_PROD_URL}/admin/product-categories",
        headers=headers, params={"limit": 100}, timeout=30,
    )
    rr.raise_for_status()
    cat_id = None
    for c in rr.json().get("product_categories", []):
        if c.get("name", "").strip().lower() == category_name.strip().lower():
            cat_id = c["id"]
            break
    if not cat_id:
        available = sorted(
            c.get("name") for c in rr.json().get("product_categories", [])
        )
        raise SystemExit(
            f"❌ Categoría '{category_name}' no encontrada en producción.\n"
            f"   Disponibles: {', '.join(available)}"
        )

    # Listar productos de esa categoría
    products = []
    offset = 0
    while True:
        rr = requests.get(
            f"{MEDUSA_PROD_URL}/admin/products",
            headers=headers,
            params={"limit": 100, "offset": offset, "category_id": cat_id},
            timeout=30,
        )
        rr.raise_for_status()
        data = rr.json()
        batch = data.get("products", [])
        products.extend(batch)
        offset += 100
        if not batch or offset >= data.get("count", 0):
            break

    result = []
    for p in products:
        skus = [v.get("sku") for v in p.get("variants", []) if v.get("sku")]
        if skus:
            result.append((skus[0], p.get("title", "")))
    return result, headers


def local_images(sku):
    """Rutas de imágenes locales para un SKU."""
    folder = PRODUCTS_IMAGES_DIR / sku
    if not folder.is_dir():
        return []
    return [f for f in sorted(folder.iterdir()) if f.suffix in IMAGE_EXTS]


def medusa_product_images(sku, headers):
    """URLs de imagen ASIGNADAS en Medusa producción (fuente de verdad = lo que ve el cliente)."""
    urls = []
    try:
        rr = requests.get(
            f"{MEDUSA_PROD_URL}/admin/products",
            headers=headers, params={"q": sku, "limit": 100}, timeout=30,
        )
        for p in rr.json().get("products", []):
            if any(v.get("sku") == sku for v in p.get("variants", [])):
                if p.get("thumbnail"):
                    urls.append(p["thumbnail"])
                for img in p.get("images", []):
                    if img.get("url"):
                        urls.append(img["url"])
                break
    except Exception:
        pass
    return _dedupe(urls)


def cloudinary_json_urls(sku):
    """URLs del data/image_urls.json (puede estar contaminado — SOLO como fallback)."""
    if not IMAGE_URLS_JSON.exists():
        return []
    with open(IMAGE_URLS_JSON, encoding="utf-8") as f:
        db = json.load(f)
    return _dedupe(db.get(sku, []))


def _dedupe(urls):
    seen = set()
    uniq = []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def download(url, dest_path, timeout=30):
    r = requests.get(url, timeout=timeout, stream=True)
    r.raise_for_status()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(r.raw, f)
    return dest_path.stat().st_size


def ext_from_url(url, default=".jpg"):
    path = url.split("?")[0]
    ext = os.path.splitext(path)[1]
    return ext if ext in IMAGE_EXTS else default


def main():
    ap = argparse.ArgumentParser(description="Extrae imágenes de una categoría a una carpeta.")
    ap.add_argument("--categoria", required=True, help="Nombre de la categoría (ej: Celulares)")
    ap.add_argument("--destino", required=True, help="Carpeta de salida")
    ap.add_argument("--fuente", default="auto", choices=["auto", "medusa", "cloudinary", "local"],
                    help="auto/medusa=asignadas en Medusa (correcto). cloudinary=agrega JSON (riesgo). local=carpeta contaminada.")
    ap.add_argument("--por-sku", action="store_true", help="Crear subcarpeta por SKU")
    ap.add_argument("--dry-run", action="store_true", help="Solo listar, no escribir")
    args = ap.parse_args()

    destino = Path(args.destino).expanduser().resolve()
    print("=" * 60)
    print(f"  Extraer imágenes — categoría: {args.categoria}")
    print(f"  Destino: {destino}")
    print(f"  Fuente:  {args.fuente}")
    print("=" * 60)

    # Resolver SKUs de la categoría (desde Medusa producción)
    print("\n🔎 Resolviendo productos de la categoría en Medusa producción...")
    skus_titles, headers = get_category_skus_prod(args.categoria)
    print(f"   {len(skus_titles)} productos encontrados")

    if not args.dry_run:
        destino.mkdir(parents=True, exist_ok=True)

    total_files = 0
    total_bytes = 0
    report = []

    for sku, title in skus_titles:
        out_dir = destino / sku if args.por_sku else destino
        saved = []

        # Determinar URLs según la fuente
        if args.fuente == "local":
            # ⚠️ Carpeta local CONTAMINADA — solo bajo pedido explícito
            for i, src in enumerate(local_images(sku), 1):
                dest = out_dir / f"{sku}_{i}{src.suffix}"
                if not args.dry_run:
                    shutil.copy2(src, dest)
                saved.append(f"[local] {dest.name}")
        else:
            # Fuente de verdad: imágenes asignadas en Medusa producción
            urls = medusa_product_images(sku, headers)
            if args.fuente == "cloudinary":
                # Agregar las del JSON (puede traer contaminación)
                urls = _dedupe(cloudinary_json_urls(sku) + urls)
            for i, url in enumerate(urls, 1):
                dest = out_dir / f"{sku}_{i}{ext_from_url(url)}"
                if args.dry_run:
                    saved.append(f"[medusa] {dest.name}")
                else:
                    try:
                        sz = download(url, dest)
                        total_bytes += sz
                        saved.append(f"[medusa] {dest.name}")
                    except Exception as e:
                        saved.append(f"[ERROR] {url[:50]}: {e}")

        total_files += len([s for s in saved if not s.startswith("[ERROR]")])
        report.append((sku, title, saved))
        print(f"  {sku}: {len(saved)} imágenes → {title[:45]}")

    # Resumen
    print(f"\n{'=' * 60}")
    print(f"  📊 RESUMEN")
    print(f"{'=' * 60}")
    ok = sum(1 for r in report for s in r[2] if not s.startswith("[ERROR]"))
    err = sum(1 for r in report for s in r[2] if s.startswith("[ERROR]"))
    print(f"  Productos: {len(skus_titles)}")
    print(f"  Imágenes:  {ok} extraídas" + (f" ({err} errores)" if err else ""))
    if not args.dry_run:
        print(f"  Tamaño:    {total_bytes / (1024*1024):.1f} MB")
        print(f"  Destino:   {destino}")
    else:
        print(f"  (dry-run: no se escribió nada)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
