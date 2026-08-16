#!/usr/bin/env python3
"""
preparar_sync_14_15.py - Genera el Excel de sync para productos NUEVO + SIN SKU
del chat del 14 y 15 de agosto (los que van a Medusa).

Lee excel/Control_14_15_Agosto.xlsx (hoja "Control") y genera
excel/Nuevos_14_15_Sync.xlsx con la estructura que espera
sync_excel_to_medusa.py:

  A (0): SKU
  B (1): Artículo
  C (2): Precio Compra Mayorista     (referencia = Mayorista Efectivo col H del control)
  D (3): Fecha Actualización         (referencia)
  E (4): Imágenes JPG                (referencia manual, NO se sube a Medusa)
  F (5): Precio Venta Bruto          = round(Compra Mayorista * 1.072)
  G (6): Envío Grande                (vacío)

Reglas:
- Solo filas con Estado NUEVO o SIN SKU.
- Se excluyen las SIN SKU sin precio mayorista (col H).
- Se agrupa por Artículo (mismo nombre exacto), juntando todas las imágenes
  separadas por coma.
- Los que tienen SKU real (agregado a mano por el dueño) lo conservan; los que
  no, reciben provisorio SIN001...SIN0NN por orden de aparición.

Regla de precios (recordatorio):
- Precio Compra Mayorista = precio del mensaje que diga "precio por transferencia
  10% descuento (o OFF) por 3 unidades" / "Mayorista xxx$ llevando 3 unidades" /
  "$xxx Transferencia" / "solo un único precio" / "x1 de x6 x12" → × 1.0606.
- Precio Venta Bruto = Precio Compra Mayorista × 1.072 → va a Medusa
  (que aplica el 15% y el 25%).

Uso:
  python3 scripts/preparar_sync_14_15.py
"""

from pathlib import Path

import openpyxl

BASE = Path(__file__).resolve().parent.parent
CONTROL_PATH = BASE / "excel" / "Control_14_15_Agosto.xlsx"
SYNC_PATH = BASE / "excel" / "Nuevos_14_15_Sync.xlsx"
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
        mayorista = ws.cell(r, 8).value
        if not articulo:
            continue
        filas.append({
            "row": r,
            "estado": estado,
            "sku": str(ws.cell(r, 3).value or "").strip(),
            "articulo": articulo,
            "imagen": str(ws.cell(r, 6).value or "").strip(),
            "mayorista": mayorista,
            "fecha": ws.cell(r, 1).value,
        })
    return filas


def main():
    filas = leer_control()
    print(f"Filas NUEVO+SIN SKU: {len(filas)}")

    sin_precio = [f for f in filas if not f["mayorista"]]
    if sin_precio:
        print(f"Excluidos sin precio mayorista ({len(sin_precio)}):")
        for f in sin_precio:
            print(f"  row{f['row']}: {f['articulo']}")
    filas = [f for f in filas if f["mayorista"]]

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
        if f["sku"]:
            sku = f["sku"]
        else:
            sin_sku_idx += 1
            sku = f"SIN{sin_sku_idx:03d}"
        try:
            compra = int(round(float(f["mayorista"])))
            venta = int(round(float(f["mayorista"]) * FACTOR))
        except (TypeError, ValueError):
            compra = ""
            venta = ""
        productos.append({
            "sku": sku,
            "articulo": f["articulo"],
            "compra": compra,
            "fecha": f["fecha"],
            "imagenes": ", ".join(imgs),
            "venta": venta,
            "envio_grande": "",
        })

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Nuevos Sync"
    ws.append(["SKU", "Artículo", "Precio Compra Mayorista", "Fecha Actualización",
               "Imágenes JPG", "Precio Venta Bruto", "Envío Grande"])
    for p in productos:
        ws.append([p["sku"], p["articulo"], p["compra"], p["fecha"],
                   p["imagenes"], p["venta"], p["envio_grande"]])

    wb.save(SYNC_PATH)
    print(f"\nGuardado: {SYNC_PATH.name} ({len(productos)} productos)")


if __name__ == "__main__":
    main()
