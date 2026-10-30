#!/usr/bin/env python3
"""
contact_sheets.py - Genera hojas de contacto (montaje de miniaturas etiquetadas)
para revisión visual de las imágenes de producción.

Agrupa por categoría y arma una imagen con many thumbnails, cada uno etiquetado
con su SKU. Permite detectar visualmente contaminación de contenido (un producto
mostrando la foto de otro).

Uso:
  python3 scripts/contact_sheets.py                     # todas las categorías
  python3 scripts/contact_sheets.py --categoria Celulares
  python3 scripts/contact_sheets.py --por-hoja 20

Salida: /tmp/contact_sheets/{categoria}_NN.jpg
Requiere: ImageMagick (montage) + thumbnails en /tmp/audit_thumbs
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "data" / "auditoria_imagenes.json"
THUMBS = Path("/tmp/audit_thumbs")
OUT = Path("/tmp/contact_sheets")


def sanitize(name):
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:40]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--categoria", help="Solo una categoría")
    ap.add_argument("--por-hoja", type=int, default=24, help="Miniaturas por hoja")
    args = ap.parse_args()

    with open(REPORT, encoding="utf-8") as f:
        data = json.load(f)

    # Indexar thumbnails por sku
    thumb_by_sku = {}
    for f in THUMBS.iterdir():
        sku = f.name.rsplit("_thumb", 1)[0]
        thumb_by_sku[sku] = f

    # Agrupar por categoría
    by_cat = defaultdict(list)
    for rec in data["records"]:
        cat = rec.get("category", "(sin cat)") or "(sin cat)"
        if args.categoria and cat.strip().lower() != args.categoria.strip().lower():
            continue
        sku = rec["sku"]
        if sku in thumb_by_sku:
            by_cat[cat].append((sku, thumb_by_sku[sku]))

    OUT.mkdir(parents=True, exist_ok=True)
    total_sheets = 0
    for cat, items in sorted(by_cat.items()):
        cat_dir = OUT / sanitize(cat)
        cat_dir.mkdir(parents=True, exist_ok=True)
        for i in range(0, len(items), args.por_hoja):
            chunk = items[i:i + args.por_hoja]
            sheet_no = i // args.por_hoja + 1
            out_path = cat_dir / f"hoja_{sheet_no:02d}.jpg"
            # montage con etiqueta SKU debajo
            cmd = [
                "montage",
                "-label", "%t",          # %t = filename sin ext (sku_thumb)
                "-tile", "6x",           # 6 columnas
                "-geometry", "200x200+4+4",
                "-background", "white",
                "-pointsize", "14",
                "-title", f"{cat} — hoja {sheet_no}",
                *[str(p) for _, p in chunk],
                str(out_path),
            ]
            # El label %t muestra "SKU_thumb"; queremos solo SKU
            subprocess.run(cmd, check=True)
            total_sheets += 1
            skus = ", ".join(s for s, _ in chunk[:8])
            print(f"  {cat}/hoja_{sheet_no:02d}.jpg  ({len(chunk)} imgs)  [{skus}...]")

    print(f"\n✅ {total_sheets} hojas de contacto en {OUT}")


if __name__ == "__main__":
    main()
