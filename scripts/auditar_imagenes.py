#!/usr/bin/env python3
"""
auditar_imagenes.py - Auditoria de imagenes de Medusa produccion (SOLO LECTURA).

Descarga los thumbnails de todos los productos y detecta problemas:
  1. Filename del thumbnail NO contiene el SKU del producto (sospechoso)
  2. Misma URL de imagen compartida entre productos distintos (contaminacion)
  3. Thumbnail faltante
  4. Filename con formato UUID (ilegible, no identifica SKU)

NO escribe nada en Medusa. Solo genera:
  - /tmp/audit_thumbs/{sku}_thumb.{ext}   (thumbnails descargados)
  - data/auditoria_imagenes.json           (reporte estructural)

Uso:
  python3 scripts/auditar_imagenes.py
  python3 scripts/auditar_imagenes.py --categoria Celulares
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from medusa_auth import get_admin_credentials  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MEDUSA_PROD_URL = os.environ.get(
    "MEDUSA_BACKEND_URL", "https://dankoshop-api-production.up.railway.app"
)
THUMBS_DIR = Path("/tmp/audit_thumbs")
REPORT_PATH = ROOT / "data" / "auditoria_imagenes.json"


def login():
    email, password = get_admin_credentials()
    r = requests.post(
        f"{MEDUSA_PROD_URL}/auth/user/emailpass",
        json={"email": email, "password": password}, timeout=15,
    )
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['token']}"}


def get_all_products(headers):
    products = []
    offset = 0
    while True:
        rr = requests.get(
            f"{MEDUSA_PROD_URL}/admin/products",
            headers=headers, params={"limit": 100, "offset": offset}, timeout=30,
        )
        rr.raise_for_status()
        data = rr.json()
        batch = data.get("products", [])
        products.extend(batch)
        offset += 100
        if not batch or offset >= data.get("count", 0):
            break
    return products


def get_categories(headers):
    """Mapa product_id -> nombre de categoría.

    Nota: /admin/product-categories NO devuelve los products asociados
    (expand=products da 400). La forma que funciona es listar productos
    con ?category_id=... por cada categoría.
    """
    rr = requests.get(
        f"{MEDUSA_PROD_URL}/admin/product-categories",
        headers=headers, params={"limit": 100}, timeout=30,
    )
    rr.raise_for_status()
    cats = {}
    for c in rr.json().get("product_categories", []):
        offset = 0
        while True:
            rp = requests.get(
                f"{MEDUSA_PROD_URL}/admin/products", headers=headers,
                params={"limit": 100, "offset": offset, "category_id": c["id"]},
                timeout=30,
            )
            rp.raise_for_status()
            data = rp.json()
            batch = data.get("products", [])
            for p in batch:
                cats.setdefault(p.get("id"), c.get("name"))
            offset += 100
            if not batch or offset >= data.get("count", 0):
                break
    return cats


def filename_of(url):
    if not url:
        return ""
    return url.split("?")[0].split("/")[-1]


def looks_uuid(name):
    base = name.rsplit(".", 1)[0]
    return len(base) >= 32 and "-" in base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--categoria", help="Filtrar por nombre de categoría")
    ap.add_argument("--no-descargar", action="store_true", help="Solo análisis estructural")
    args = ap.parse_args()

    print("=" * 60)
    print("  Auditoría de imágenes — Medusa producción (SOLO LECTURA)")
    print("=" * 60)

    headers = login()
    print("\n🔎 Descargando productos...")
    products = get_all_products(headers)
    print(f"   {len(products)} productos")

    cat_map = get_categories(headers)

    # Filtrar por categoría si se pidió
    if args.categoria:
        wanted = set()
        for c_id, c_name in cat_map.items():
            if c_name and c_name.strip().lower() == args.categoria.strip().lower():
                wanted.add(c_id)
        products = [p for p in products if p.get("id") in wanted]
        print(f"   Filtrado '{args.categoria}': {len(products)} productos")

    # Indexar uso de URLs entre productos
    url_to_products = defaultdict(set)
    records = []
    for p in products:
        skus = [v.get("sku") for v in p.get("variants", []) if v.get("sku")]
        sku = skus[0] if skus else p.get("handle", "?")
        imgs = [i.get("url") for i in p.get("images", []) if i.get("url")]
        thumb = p.get("thumbnail")
        for u in set(imgs + ([thumb] if thumb else [])):
            url_to_products[u].add(sku)
        records.append({
            "sku": sku,
            "title": p.get("title", ""),
            "product_id": p.get("id"),
            "category": cat_map.get(p.get("id"), "(sin cat)"),
            "thumbnail": thumb,
            "images": imgs,
        })

    # Descargar thumbnails
    if not args.no_descargar:
        THUMBS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"\n⬇️  Descargando thumbnails a {THUMBS_DIR}...")
        ok = fail = 0
        for rec in records:
            if not rec["thumbnail"]:
                continue
            ext = os.path.splitext(filename_of(rec["thumbnail"]))[1] or ".jpg"
            dest = THUMBS_DIR / f"{rec['sku']}_thumb{ext}"
            if dest.exists():
                ok += 1
                continue
            try:
                r = requests.get(rec["thumbnail"], timeout=30, stream=True)
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                ok += 1
            except Exception as e:
                fail += 1
                rec["download_error"] = str(e)
        print(f"   ✅ {ok} descargados | ❌ {fail} errores")

    # Análisis estructural
    print("\n🧪 Analizando estructura...")
    issues = []
    for rec in records:
        flags = []
        thumb = rec["thumbnail"]
        if not thumb:
            flags.append("SIN_THUMBNAIL")
        else:
            fname = filename_of(thumb)
            if looks_uuid(fname):
                flags.append("FILENAME_UUID")
            # El filename debería contener el SKU
            sku_compact = rec["sku"].replace("-", "").lower()
            fname_compact = fname.replace("-", "").replace("_", "").lower()
            if sku_compact and sku_compact not in fname_compact:
                flags.append("FILENAME_NO_SKU")
        # URLs compartidas entre productos distintos
        shared = set()
        for u in set(rec["images"] + ([thumb] if thumb else [])):
            others = url_to_products[u] - {rec["sku"]}
            if others:
                shared.update(others)
        if shared:
            flags.append(f"URL_COMPARTIDA_CON:{','.join(sorted(shared)[:5])}")
        rec["flags"] = flags
        if flags:
            issues.append(rec)

    # Resumen
    print(f"\n{'=' * 60}")
    print(f"  📊 RESULTADO ESTRUCTURAL")
    print(f"{'=' * 60}")
    print(f"  Productos auditados:  {len(records)}")
    print(f"  Con señales de alerta: {len(issues)}")

    by_flag = defaultdict(int)
    for rec in issues:
        for f in rec["flags"]:
            by_flag[f.split(":")[0]] += 1
    print()
    for flag, n in sorted(by_flag.items(), key=lambda x: -x[1]):
        print(f"    {flag:22s} {n}")

    # Guardar reporte
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(records),
            "with_issues": len(issues),
            "records": records,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  Reporte: {REPORT_PATH}")
    print(f"  Thumbnails: {THUMBS_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
