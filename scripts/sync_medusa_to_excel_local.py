#!/usr/bin/env python3
"""
sync_medusa_to_excel_local.py - Medusa (LOCAL) to Excel sync
Reads all products from LOCAL Medusa backend and writes them to excel/Productos_Local.xlsx.

New products (in Medusa but not in Excel) are ADDED.
Existing products (matched by Medusa ID hidden in col 8) are UPDATED.
Products in Excel but not in Medusa are DELETED (ghost rows).

Excel columns (centered, colored headers):
  0: SKU
  1: Artículo
  2: Categoría
  3: Descripción
  4: Precio Lista
  5: Precio Mayorista
  6: Envío Grande
  7: Inventario
  8: Canales de Venta
  9: (hidden) Medusa Product ID
  10: Precio Ingresado

Prices are derived from Precio Mayorista stored in product metadata.

Usage:
  python3 scripts/sync_medusa_to_excel_local.py [ruta_archivo.xlsx]
  (el archivo por defecto es excel/Productos_Local.xlsx)
"""

import os
import sys
import json
import shutil
from datetime import datetime
import requests
from pathlib import Path

MEDUSA_URL = os.getenv("MEDUSA_BACKEND_URL", "http://localhost:9100")
ADMIN_EMAIL = os.getenv("MEDUSA_ADMIN_EMAIL", "admin@dankoshop.com")
ADMIN_PASSWORD = os.getenv("MEDUSA_ADMIN_PASSWORD", "supersecret")
EXCEL_PATH = Path(__file__).resolve().parent.parent / "excel" / "Productos_Local.xlsx"
if len(sys.argv) > 1:
    EXCEL_PATH = Path(sys.argv[1])

_token = None

# Header colors (hex without #)
HEADER_COLORS = {
    "SKU": "D35230",           # rojo
    "Artículo": "E8A838",      # naranja/dorado
    "Categoría": "4CAF50",     # verde
    "Inventario": "795548",    # marrón
    "Canales de Venta": "607D8B", # gris azulado
    "Descripción": "2196F3",   # azul
    "Precio Lista": "9C27B0",  # púrpura
    "Precio Mayorista": "FF9800", # naranja
    "Envío Grande": "00BCD4",  # cyan
    "Precio Ingresado": "78909C", # gris azulado oscuro
}


def get_token():
    global _token
    if _token:
        return _token
    r = requests.post(
        f"{MEDUSA_URL}/auth/user/emailpass",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if r.status_code == 200:
        _token = r.json().get("token")
        return _token
    print(f"AUTH FAILED ({r.status_code}): {r.text[:200]}")
    return None


def api(method, endpoint, data=None, params=None):
    token = get_token()
    if not token:
        raise RuntimeError("No auth token")
    return requests.request(
        method,
        f"{MEDUSA_URL}{endpoint}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=data,
        params=params,
        timeout=30,
    )


def fetch_all_products():
    products = []
    offset = 0
    while True:
        r = api("GET", "/admin/products", params={"limit": 100, "offset": offset})
        if r.status_code != 200:
            print(f"Error fetching products: {r.status_code}")
            break
        batch = r.json().get("products", [])
        products.extend(batch)
        if len(batch) < 100:
            break
        offset += 100
    return products


def fetch_category_map():
    """Build {product_id: category_name} by querying each category."""
    cat_map = {}
    cats = []
    offset = 0
    while True:
        r = api("GET", "/admin/product-categories", params={"limit": 100, "offset": offset})
        if r.status_code != 200:
            break
        batch = r.json().get("product_categories", [])
        cats.extend(batch)
        if len(batch) < 100:
            break
        offset += 100

    for cat in cats:
        r = api("GET", "/admin/products", params={"limit": 100, "category_id": cat["id"]})
        if r.status_code == 200:
            for p in r.json().get("products", []):
                cat_map[p["id"]] = cat["name"]
    return cat_map


def fetch_inventory_map():
    """Build {sku: inventory_quantity} from inventory items."""
    inv_map = {}
    offset = 0
    while True:
        r = api("GET", "/admin/inventory-items", params={"limit": 100, "offset": offset})
        if r.status_code != 200:
            break
        items = r.json().get("inventory_items", [])
        for item in items:
            sku = item.get("sku")
            if not sku:
                continue
            levels = item.get("location_levels", []) or []
            total = sum(l.get("available_quantity", 0) or 0 for l in levels)
            inv_map[sku] = total
        if len(items) < 100:
            break
        offset += 100
    return inv_map


def fetch_sales_channel_map():
    """Build {product_id: channel_names} from sales channels."""
    sc_map = {}
    r = api("GET", "/admin/sales-channels", params={"limit": 100})
    if r.status_code != 200:
        return sc_map
    channels = r.json().get("sales_channels", [])
    for ch in channels:
        ch_id, ch_name = ch["id"], ch.get("name", "")
        offset = 0
        while True:
            r2 = api("GET", "/admin/products", params={"limit": 100, "offset": offset, "sales_channel_id": ch_id})
            if r2.status_code != 200:
                break
            prods = r2.json().get("products", [])
            for p in prods:
                existing = sc_map.get(p["id"], [])
                if ch_name not in existing:
                    existing.append(ch_name)
                sc_map[p["id"]] = existing
            if len(prods) < 100:
                break
            offset += 100
    return sc_map


def read_existing_excel():
    """Returns {medusa_id: {row, sku, ...}} from existing Excel"""
    import openpyxl
    existing = {}
    if not EXCEL_PATH.exists():
        return existing

    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active
    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        medusa_id = row[10] if len(row) > 10 else None
        sku = row[0] if row[0] else None
        precio_ingresado = row[11] if len(row) > 11 else None
        if medusa_id:
            existing[str(medusa_id).strip()] = {
                "row": idx,
                "sku": sku,
                "precio_ingresado": precio_ingresado,
            }
        elif sku:
            existing[f"sku:{sku}"] = {
                "row": idx,
                "sku": sku,
                "precio_ingresado": precio_ingresado,
            }
    return existing


def write_excel(products_data, existing):
    """
    products_data: list of dicts with keys:
      medusa_id, sku, title, category, description, precio_lista, precio_mayorista,
      envio_grande, inventory, sales_channels
    existing: dict from read_existing_excel()
    """
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Productos"

    headers = ["SKU", "Artículo", "Categoría", "Descripción", "PRECIO LISTA (control)",
               "Precio Mayorista", "Envío Grande", "Inventario", "Canales de Venta"]
    hidden_headers = ["ID Medusa"]  # col 10 (hidden)

    # Write headers with colors
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill_cache = {}
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = header_font
        cell.alignment = center
        color = HEADER_COLORS.get(h, "333333")
        cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
        cell.border = thin_border

    # Hidden column for Medusa ID
    cell = ws.cell(row=1, column=10, value="ID Medusa")
    cell.font = Font(color="999999", size=8)
    ws.column_dimensions["J"].hidden = True

    # Col K: Precio Ingresado (se preserva del Excel anterior)
    cell = ws.cell(row=1, column=11, value="Precio Ingresado")
    cell.font = Font(color="FFFFFF", bold=True, size=10)
    cell.alignment = center
    color = HEADER_COLORS.get("Precio Ingresado", "333333")
    cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
    cell.border = thin_border

    # Write data
    data_center = Alignment(horizontal="center", vertical="center")
    data_left = Alignment(horizontal="left", vertical="center", wrap_text=True)

    def existing_lookup(p):
        e = existing.get(str(p["medusa_id"])) if p["medusa_id"] else None
        if e is None and p["sku"]:
            e = existing.get(f"sku:{p['sku']}")
        return e

    for row_idx, p in enumerate(products_data, 2):
        ws.cell(row=row_idx, column=1, value=p["sku"]).alignment = data_center
        ws.cell(row=row_idx, column=2, value=p["title"]).alignment = data_left
        ws.cell(row=row_idx, column=3, value=p["category"]).alignment = data_center
        ws.cell(row=row_idx, column=4, value=p["description"]).alignment = data_left

        precio_mayorista = p.get("precio_mayorista")
        cell6 = ws.cell(row=row_idx, column=6, value=precio_mayorista)
        cell6.alignment = data_center
        cell6.number_format = '#,##0'

        envio = "TRUE" if p.get("envio_grande") else ""
        ws.cell(row=row_idx, column=7, value=envio).alignment = data_center

        inv = p.get("inventory")
        ws.cell(row=row_idx, column=8, value=inv if inv is not None else "").alignment = data_center

        ws.cell(row=row_idx, column=9, value=p.get("sales_channels", "")).alignment = data_center

        ws.cell(row=row_idx, column=10, value=p["medusa_id"])

        prev = existing_lookup(p)
        precio_ing = None
        if prev and prev.get("precio_ingresado") is not None:
            precio_ing = prev["precio_ingresado"]
        elif precio_mayorista:
            precio_ing = int(round(float(precio_mayorista) / 1.072))
        ws.cell(row=row_idx, column=11, value=precio_ing)

        for col in range(1, 12):
            ws.cell(row=row_idx, column=col).border = thin_border

    # Col E: control — fórmula en TODA la columna hasta fila 10000,
    # así las filas nuevas (agregadas a mano) ya tienen fórmula.
    # No se sube a Medusa.
    MAX_FILA = 10000
    for r in range(2, MAX_FILA + 1):
        c5 = ws.cell(row=r, column=5, value=f'=IF(F{r}="","",F{r}*1.25)')
        c5.alignment = data_center
        c5.number_format = '#,##0'
        c6 = ws.cell(row=r, column=6, value=f'=IF(K{r}="","",ROUND(K{r}*1.072,0))')
        c6.alignment = data_center
        c6.number_format = '#,##0'

    # Column widths
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 55
    ws.column_dimensions["C"].width = 28
    ws.column_dimensions["D"].width = 50
    ws.column_dimensions["E"].width = 16
    ws.column_dimensions["F"].width = 18
    ws.column_dimensions["G"].width = 14
    ws.column_dimensions["H"].width = 12
    ws.column_dimensions["I"].width = 22

    # Freeze header
    ws.freeze_panes = "A2"

    # Auto-filter
    ws.auto_filter.ref = f"A1:I{len(products_data) + 1}"

    wb.save(EXCEL_PATH)

    # Recalc con LibreOffice headless para cachear valores de las fórmulas
    # (necesario para que sync_excel_to_medusa_local.py lea F con data_only=True).
    import subprocess
    outdir = Path(EXCEL_PATH).parent / "_recalc_medusa"
    outdir.mkdir(exist_ok=True)
    try:
        res = subprocess.run(
            ["soffice", "--headless", "--convert-to", "xlsx",
             "--outdir", str(outdir), str(EXCEL_PATH)],
            capture_output=True, text=True, timeout=180,
        )
        if res.returncode == 0:
            converted = outdir / EXCEL_PATH.name
            if converted.exists():
                shutil.copy2(converted, EXCEL_PATH)
    except Exception as e:
        print(f"  WARN: recalc LibreOffice falló: {e}")
    finally:
        shutil.rmtree(outdir, ignore_errors=True)

    # Backup con fecha/hora en excel/Masters/
    try:
        masters = Path(EXCEL_PATH).parent / "Masters"
        masters.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = masters / f"{EXCEL_PATH.stem}_{ts}.xlsx"
        shutil.copy2(EXCEL_PATH, backup)
        print(f"  Backup guardado: {backup}")
    except Exception as e:
        print(f"  WARN: backup falló: {e}")


def main():
    print("=" * 60)
    print("  Medusa (LOCAL) → Excel Sync")
    print(f"  Excel: {EXCEL_PATH}")
    print("=" * 60)

    try:
        r = requests.get(f"{MEDUSA_URL}/health", timeout=10)
        if r.status_code != 200:
            print(f"Medusa not healthy: {r.status_code}")
            return
    except Exception as e:
        print(f"Cannot connect to Medusa: {e}")
        return

    if not get_token():
        print("Auth failed")
        return

    raw_products = fetch_all_products()
    print(f"Medusa products: {len(raw_products)}")

    cat_map = fetch_category_map()
    print(f"Category mappings: {len(cat_map)}")

    inv_map = fetch_inventory_map()
    print(f"Inventory mappings: {len(inv_map)}")

    sc_map = fetch_sales_channel_map()
    print(f"Sales channel mappings: {len(sc_map)}")

    existing = read_existing_excel()
    print(f"Existing Excel rows: {len(existing)}")

    products_data = []
    for p in raw_products:
        meta = p.get("metadata", {}) or {}
        sku = None
        for v in p.get("variants", []):
            sku = v.get("sku")
            if sku:
                break
        if not sku:
            continue

        category = cat_map.get(p["id"], "")

        precio_mayorista = meta.get("precio_mayorista")
        precio_lista = meta.get("precio_lista")
        if precio_mayorista and not precio_lista:
            precio_lista = int(round(float(precio_mayorista) * 1.25))
        elif not precio_lista and p.get("variants"):
            # Fallback: use variant price / 1.25
            for v in p["variants"]:
                for pr in v.get("prices", []):
                    if pr.get("amount"):
                        precio_lista = pr["amount"]
                        precio_mayorista = int(round(pr["amount"] / 1.25))
                        break

        products_data.append({
            "medusa_id": p["id"],
            "sku": sku,
            "title": p.get("title", ""),
            "category": category,
            "description": p.get("description", "") or "",
            "precio_lista": precio_lista,
            "precio_mayorista": precio_mayorista,
            "envio_grande": bool(meta.get("envio_grande")),
            "inventory": inv_map.get(sku),
            "sales_channels": ", ".join(sc_map.get(p["id"], [])),
        })

    write_excel(products_data, existing)
    print(f"Excel written: {EXCEL_PATH}")
    print(f"  Products: {len(products_data)}")
    print(f"  Columns: SKU, Artículo, Categoría, Inventario, Canales de Venta, Descripción, Precios, Envío Grande")
    print(f"  Headers: centered + colored")
    print(f"\n{'='*60}")
    print(f"  Done!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
