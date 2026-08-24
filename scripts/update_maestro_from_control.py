#!/usr/bin/env python3
"""
scripts/update_maestro_from_control.py

Actualiza el Excel maestro (columna I "Precio Ingresado") con los precios del
Excel de control de Luciana (columna D), emparejando por SKU.

Reglas por SKU:
  - Un solo valor -> se usa ese valor.
  - Varios valores iguales -> se usa ese valor.
  - Varios valores DISTINTOS -> se toma el MÁS ALTO (actualización más reciente).

También genera un Excel "Nuevos_Para_Medusa.xlsx" con los artículos que están en
el control pero NO en el maestro, para cargarlos manualmente en Medusa.
Crea backup del maestro antes de modificar.
"""

import openpyxl
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTROL_PATH = ROOT / "excel" / "Control_Precios_Luciana_Desde_8_Agosto.xlsx"
MAESTRO_PATH = ROOT / "excel" / "Productos_Maestro.xlsx"
NUEVOS_PATH = ROOT / "excel" / "Nuevos_Para_Medusa.xlsx"


def leer_control():
    wb = openpyxl.load_workbook(CONTROL_PATH, data_only=True)
    ws = wb.active
    skus = defaultdict(lambda: {"d": [], "art": None, "fecha": None})
    for r in range(2, ws.max_row + 1):
        sku = ws.cell(r, 1).value
        d = ws.cell(r, 4).value
        art = ws.cell(r, 2).value
        fecha = ws.cell(r, 8).value
        if not sku:
            continue
        s = str(sku).strip()
        if d is not None:
            skus[s]["d"].append(d)
        if skus[s]["art"] is None:
            skus[s]["art"] = art
        if skus[s]["fecha"] is None:
            skus[s]["fecha"] = fecha
    return skus


def leer_maestro_skus():
    wb = openpyxl.load_workbook(MAESTRO_PATH, data_only=False)
    ws = wb.active
    filas = {}
    for r in range(2, ws.max_row + 1):
        sku = ws.cell(r, 1).value
        if sku:
            filas[str(sku).strip()] = r
    return filas, ws


def actualizar_maestro(skus_control, filas_maestro):
    wb = openpyxl.load_workbook(MAESTRO_PATH, data_only=False)
    ws = wb.active

    actualizados = 0
    for sku, datos in skus_control.items():
        if sku in filas_maestro and datos["d"]:
            fila = filas_maestro[sku]
            valor = max(datos["d"])
            ws.cell(row=fila, column=11, value=valor)
            actualizados += 1

    wb.save(MAESTRO_PATH)
    return actualizados


def generar_nuevos(skus_control, filas_maestro):
    nuevos = []
    for sku, datos in skus_control.items():
        if sku not in filas_maestro and datos["d"]:
            nuevos.append({
                "sku": sku,
                "articulo": datos["art"] or "",
                "precio": max(datos["d"]),
                "fecha": datos["fecha"] or "",
            })

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Nuevos Para Medusa"
    ws.append(["SKU", "Artículo", "Precio Ingresado", "Fecha Actualización"])

    for item in sorted(nuevos, key=lambda x: x["sku"]):
        ws.append([item["sku"], item["articulo"], item["precio"], item["fecha"]])

    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 55
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 22
    wb.save(NUEVOS_PATH)
    return len(nuevos)


def main():
    if not CONTROL_PATH.exists():
        print(f"Control no existe: {CONTROL_PATH}")
        return

    backup = MAESTRO_PATH.parent / (
        f"{MAESTRO_PATH.stem}_backup_{datetime.now().strftime('%d%m%y_%H%M%S')}.xlsx"
    )
    shutil.copy2(MAESTRO_PATH, backup)
    print(f"Backup maestro: {backup.name}")

    skus = leer_control()
    print(f"SKU únicos en control: {len(skus)}")

    filas_maestro, _ = leer_maestro_skus()
    actualizados = actualizar_maestro(skus, filas_maestro)
    print(f"Columna I actualizada en maestro: {actualizados} SKU")

    nuevos = generar_nuevos(skus, filas_maestro)
    print(f"Artículos nuevos para Medusa: {nuevos} -> {NUEVOS_PATH.name}")


if __name__ == "__main__":
    main()