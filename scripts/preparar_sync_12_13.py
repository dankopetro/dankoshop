#!/usr/bin/env python3
"""
preparar_sync_12_13.py - Genera el Excel de sync para productos NUEVO + SIN SKU
del chat del 12 y 13 de agosto (los que van a Medusa).

Lee excel/Control_12_13_Agosto.xlsx (hoja "Control") y genera
excel/Nuevos_12_13_Sync.xlsx con la estructura que espera
sync_excel_to_medusa.py:

  A (0): SKU
  B (1): Artículo
  C (2): Precio Ingresado            (referencia = Precio unidad efectivo del chat)
  D (3): Fecha Actualización         (referencia)
  E (4): Imágenes JPG                (referencia manual, NO se sube a Medusa)
  F (5): Precio Mayorista            = round(Ingresado * 1.072)
  G (6): Envío Grande                (vacío)

Reglas:
- Solo filas con Estado NUEVO o SIN SKU.
- Se excluyen los SIN SKU sin precio (Tupper Gemplast, Los peluches que quedan).
- Se agrupa por Artículo (mismo nombre exacto), juntando todas las imágenes
  separadas por coma.
- Los NUEVO conservan su SKU real; los SIN SKU reciben provisorio SIN001...SIN015
  por orden de aparición.

Uso:
  python3 scripts/preparar_sync_12_13.py
"""

from pathlib import Path

import openpyxl

BASE = Path(__file__).resolve().parent.parent
CONTROL_PATH = BASE / "excel" / "Control_12_13_Agosto.xlsx"
SYNC_PATH = BASE / "excel" / "Nuevos_12_13_Sync.xlsx"
FACTOR = 1.072


def leer_control():
    wb = openpyxl.load_workbook(CONTROL_PATH, data_only=True)
    ws = wb["Control"]
    filas = []
    for r in range(2, ws.max_row + 1):
        estado = str(ws.cell(r, 14).value or "").strip()
        if estado not in ("NUEVO", "SIN SKU"):
            continue
        articulo = str(ws.cell(r, 5).value or "").strip()
        unid = ws.cell(r, 7).value
        if not articulo:
            continue
        filas.append({
            "row": r,
            "estado": estado,
            "sku": str(ws.cell(r, 3).value or "").strip(),
            "articulo": articulo,
            "imagen": str(ws.cell(r, 6).value or "").strip(),
            "unid": unid,
            "fecha": ws.cell(r, 1).value,
        })
    return filas


def main():
    filas = leer_control()
    print(f"Filas NUEVO+SIN SKU: {len(filas)}")

    sin_precio = [f for f in filas if not f["unid"]]
    if sin_precio:
        print(f"Excluidos sin precio ({len(sin_precio)}):")
        for f in sin_precio:
            print(f"  row{f['row']}: {f['articulo']}")
    filas = [f for f in filas if f["unid"]]

    agrupados = {}
    for f in filas:
        key = f["articulo"]
        if key not in agrupados:
            f = dict(f)
            f["imagenes"] = []
            agrupados[key] = f
        agrupados[key]["imagenes"].append(f["imagen"])

    productos = []
    sin_sku_idx = 0
    for f in agrupados.values():
        imgs = list(dict.fromkeys(x for x in f["imagenes"] if x))
        if f["estado"] == "NUEVO" and f["sku"]:
            sku = f["sku"]
        else:
            sin_sku_idx += 1
            sku = f"SIN{sin_sku_idx:03d}"
        try:
            ingresado = int(round(float(f["unid"])))
            mayorista = int(round(float(f["unid"]) * FACTOR))
        except (TypeError, ValueError):
            ingresado = ""
            mayorista = ""
        productos.append({
            "sku": sku,
            "articulo": f["articulo"],
            "ingresado": ingresado,
            "fecha": f["fecha"],
            "imagenes": ", ".join(imgs),
            "mayorista": mayorista,
            "envio_grande": "",
        })

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Nuevos Sync"
    ws.append(["SKU", "Artículo", "Precio Ingresado", "Fecha Actualización",
               "Imágenes JPG", "Precio Mayorista", "Envío Grande"])
    for p in productos:
        ws.append([p["sku"], p["articulo"], p["ingresado"], p["fecha"],
                   p["imagenes"], p["mayorista"], p["envio_grande"]])

    wb.save(SYNC_PATH)
    print(f"\nGuardado: {SYNC_PATH.name} ({len(productos)} productos)")


if __name__ == "__main__":
    main()
