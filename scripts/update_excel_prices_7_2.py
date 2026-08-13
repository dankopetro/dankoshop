#!/usr/bin/env python3
"""
scripts/update_excel_prices_7_2.py
Aumenta un 7.2% la columna 'Precio Mayorista' en excel/Productos_Maestro.xlsx y excel/Productos_Local.xlsx.
Crea backups antes de modificar los archivos.
"""

import openpyxl
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
EXCEL_MAESTRO = ROOT_DIR / "excel" / "Productos_Maestro.xlsx"
EXCEL_LOCAL = ROOT_DIR / "excel" / "Productos_Local.xlsx"
FACTOR = 1.072

def update_file(path: Path):
    if not path.exists():
        print(f"Archivo no existe: {path}")
        return

    # Backup
    backup_path = path.parent / f"{path.stem}_backup_pre72{path.suffix}"
    shutil.copy2(path, backup_path)
    print(f"✅ Backup creado: {backup_path.name}")

    wb = openpyxl.load_workbook(path, data_only=False)
    ws = wb.active

    count = 0
    updated_items = []
    for row in ws.iter_rows(min_row=2):
        sku_cell = row[0]
        name_cell = row[1]
        precio_may_cell = row[5] # Columna F (0-indexed 5)

        sku = sku_cell.value
        name = name_cell.value
        precio_may = precio_may_cell.value

        if sku and name and precio_may is not None:
            try:
                val = float(str(precio_may).replace("$", "").replace(",", "").strip())
                new_val = int(round(val * FACTOR))
                precio_may_cell.value = new_val
                count += 1
                updated_items.append((sku, str(name)[:35], val, new_val))
            except Exception as e:
                print(f"  ⚠ Advertencia en SKU {sku}: {e}")

    wb.save(path)
    print(f"✅ Actualizados {count} productos en {path.name}\n")
    return updated_items

def main():
    print("=== Aumentando Precios en Excel (+7.2%) ===\n")
    items_m = update_file(EXCEL_MAESTRO)
    update_file(EXCEL_LOCAL)

    if items_m:
        print("Muestra de cambios realizados (Primeros 10 productos):")
        print("-" * 80)
        print(f"{'SKU':<25} | {'Nombre':<35} | {'Anterior':<10} | {'Nuevo (+7.2%)':<12}")
        print("-" * 80)
        for sku, name, old_p, new_p in items_m[:10]:
            print(f"{sku:<25} | {name:<35} | ${int(old_p):<9,} | ${new_p:<11,}")
        print("-" * 80)

if __name__ == "__main__":
    main()
