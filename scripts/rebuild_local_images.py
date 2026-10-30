#!/usr/bin/env python3
"""
rebuild_local_images.py - Deja las imágenes de Medusa local 100% espejo de producción.

Compara el thumbnail de cada producto local contra producción (match por SKU) y
reemplaza los que difieren. NO toca producción. NO borra imágenes huérfanas de
Cloudinary (solo re-apunta los productos locales a las URLs correctas).

Uso:
  python3 scripts/rebuild_local_images.py --dry-run   # preview de qué cambiaría
  python3 scripts/rebuild_local_images.py             # aplicar cambios

Credenciales: .env.production vía medusa_auth.py.
URLs: MEDUSA_LOCAL_URL (default http://localhost:9100) y MEDUSA_PROD_URL.
"""

import os
import sys
import time
import argparse
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from medusa_auth import get_admin_credentials  # noqa: E402

LOCAL_URL = os.environ.get("MEDUSA_LOCAL_URL", "http://localhost:9100")
PROD_URL = os.environ.get("MEDUSA_PROD_URL", "https://dankoshop-api-production.up.railway.app")


def login(base_url, email, password):
    r = requests.post(
        f"{base_url}/auth/user/emailpass",
        json={"email": email, "password": password}, timeout=15,
    )
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['token']}"}


def get_all_products(base_url, headers):
    out, offset = [], 0
    while True:
        rr = requests.get(
            f"{base_url}/admin/products", headers=headers,
            params={"limit": 100, "offset": offset}, timeout=30,
        )
        rr.raise_for_status()
        data = rr.json()
        batch = data.get("products", [])
        out.extend(batch)
        offset += 100
        if not batch or offset >= data.get("count", 0):
            break
    return out


def sku_map(products):
    m = {}
    for p in products:
        for v in p.get("variants", []):
            if v.get("sku"):
                m[v["sku"]] = p
    return m


def image_urls_of(product):
    """Todas las URLs de imagen de un producto (thumbnail primero)."""
    urls = []
    thumb = product.get("thumbnail")
    if thumb:
        urls.append(thumb)
    for img in product.get("images", []):
        u = img.get("url")
        if u and u not in urls:
            urls.append(u)
    return urls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("=" * 60)
    print("  Rebuild imágenes de local → espejo de producción")
    print("=" * 60)

    email, password = get_admin_credentials()
    ph = login(PROD_URL, email, password)
    lh = login(LOCAL_URL, email, password)
    print("  ✅ Autenticado en producción y local\n")

    print("🔎 Comparando thumbnails...")
    prod = sku_map(get_all_products(PROD_URL, ph))
    local = sku_map(get_all_products(LOCAL_URL, lh))
    print(f"   Producción: {len(prod)} SKUs | Local: {len(local)} SKUs")

    to_fix = []
    for sku, pp in prod.items():
        lp = local.get(sku)
        if not lp:
            continue
        if (pp.get("thumbnail") or "") != (lp.get("thumbnail") or ""):
            to_fix.append((sku, pp, lp))

    same = sum(
        1 for sku, pp in prod.items()
        if sku in local and (pp.get("thumbnail") or "") == (local[sku].get("thumbnail") or "")
    )
    print(f"   Idénticos: {same} | A corregir: {len(to_fix)}")

    if not to_fix:
        print("\n✅ Local ya es espejo exacto de producción. Nada que hacer.")
        return

    if args.dry_run:
        print("\n🔍 DRY-RUN — se reemplazarían:")
        for sku, pp, lp in to_fix:
            print(f"   {sku}: {lp.get('thumbnail','').split('/')[-1]} → {pp.get('thumbnail','').split('/')[-1]}")
        print(f"\n   ({len(to_fix)} productos se actualizarían)")
        return

    print("\n🛠️  Reemplazando imágenes divergentes...")
    ok = fail = 0
    for sku, pp, lp in to_fix:
        urls = image_urls_of(pp)
        payload = {"images": [{"url": u} for u in urls]}
        if urls:
            payload["thumbnail"] = urls[0]
        r = requests.post(
            f"{LOCAL_URL}/admin/products/{lp['id']}", headers=lh, json=payload, timeout=30,
        )
        if r.status_code == 200:
            ok += 1
            print(f"   ✅ {sku}: {pp.get('title','')[:40]}")
        else:
            fail += 1
            print(f"   ❌ {sku}: {r.status_code} {r.text[:100]}")
        time.sleep(0.1)

    print(f"\n{'=' * 60}")
    print(f"  📊 RESUMEN: actualizados={ok} | errores={fail}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
