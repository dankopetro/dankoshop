#!/usr/bin/env python3
"""Genera lista de precios (Excel + PDF) desde Productos_Maestro.xlsx.

Uso:
  python3 scripts/generar_lista_precios.py                          # ambos
  python3 scripts/generar_lista_precios.py --solo-excel              # solo Excel
  python3 scripts/generar_lista_precios.py --solo-pdf                # solo PDF
  python3 scripts/generar_lista_precios.py --categoria Gaming        # filtrar
  python3 scripts/generar_lista_precios.py --mayorista               # precios mayoristas
"""

import sys
import os
import re
import argparse
import math
from pathlib import Path
from datetime import datetime

from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile

import requests
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# DejaVu Sans for Unicode support in PDF
FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONT_REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

def strip_emoji(text):
    """Remove emojis and non-latin chars that break PDF fonts."""
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0000FE00-\U0000FE0F"
        "\U0000200D\U00002764\U00002600-\U000026FF\U00002700-\U000027BF"
        "\U0000231A-\U0000231B\U00002328\U000023CF\U000023E9-\U000023F3"
        "\U000023F8-\U000023FA\U000025AA-\U000025AB\U000025B6\U000025C0"
        "\U000025FB-\U000025FE\U00002614-\U00002615\U00002648-\U00002653"
        "\U0000267F\U00002693\U000026A1\U000026AA-\U000026AB"
        "\U000026BD-\U000026BE\U000026C4-\U000026C5\U000026CE-\U000026CF"
        "\U000026D4\U000026EA\U000026F2-\U000026F3\U000026F5\U000026FA"
        "\U000026FD\U00002702\U00002705\U00002708-\U0000270D\U0000270F"
        "\U00002712\U00002714\U00002716\U0000271D\U00002721\U00002728"
        "\U00002733-\U00002734\U00002744\U00002747\U0000274C\U0000274E"
        "\U00002753-\U00002755\U00002757\U00002763-\U00002764"
        "\U00002795-\U00002797\U000027A1\U000027B0\U000027BF"
        "\U00002934-\U00002935\U00002B05-\U00002B07\U00002B1B-\U00002B1C"
        "\U00002B50\U00002B55\U00003030\U0000303D\U00003297\U00003299"
        "\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U0000200D"
        "\U00002640\U00002642\U00002695-\U00002696\U00002708\U0000269B"
        "\U0001F9B0-\U0001F9B3\U0001F9B8-\U0001F9B9]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub("", text).strip()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
EXCEL_PATH = ROOT / "excel" / "Productos_Maestro.xlsx"
OUTPUT_DIR = ROOT / "outputs"

MEDUSA_URL = os.environ.get("MEDUSA_BACKEND_URL", "https://dankoshop-api-production.up.railway.app")
ADMIN_EMAIL = "admin@dankoshop.com"
ADMIN_PASSWORD = "supersecret"

# Category colors (RGB tuples for Excel, hex for PDF)
CAT_COLORS = {
    "Accesorios":                    ((76, 175, 80),   "#4CAF50"),
    "Audio":                         ((156, 39, 176),  "#9C27B0"),
    "Bicicletas":                    ((33, 150, 243),  "#2196F3"),
    "Celulares":                     ((0, 150, 136),   "#009688"),
    "Cocinas":                       ((255, 87, 34),   "#FF5722"),
    "Combos":                        ((255, 152, 0),   "#FF9800"),
    "Deportes":                      ((139, 195, 74),  "#8BC34A"),
    "Gaming":                        ((63, 81, 181),   "#3F51B5"),
    "Heladeras":                     ((0, 188, 212),   "#00BCD4"),
    "Herramientas":                  ((121, 85, 72),   "#795548"),
    "Hogar":                         ((233, 30, 99),   "#E91E63"),
    "Jugueteria":                    ((255, 235, 59),  "#FFEB3B"),
    "Lavarropas":                    ((3, 169, 244),   "#03A9F4"),
    "Notebooks y Tablets":           ((103, 58, 183),  "#673AB7"),
    "Outdoor":                       ((76, 175, 80),   "#4CAF50"),
    "Pequeños Electrodomésticos":    ((255, 193, 7),   "#FFC107"),
    "TVs":                           ((244, 67, 54),   "#F44336"),
}

DEFAULT_COLOR = ((158, 158, 158), "#9E9E9E")

# Excel header colors
HEADER_FILL = PatternFill(start_color="1A237E", end_color="1A237E", fill_type="solid")
HEADER_FONT = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
BODY_FONT = Font(name="Calibri", size=10)
MONEY_FORMAT = '#,##0'


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
_token = None

def get_token():
    global _token
    if _token:
        return _token
    try:
        r = requests.post(f"{MEDUSA_URL}/auth/user/emailpass",
                          json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                          timeout=10)
        if r.status_code == 200:
            _token = r.json().get("token")
            return _token
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Read products from Maestro Excel
# ---------------------------------------------------------------------------
def read_products(categoria_filter=None):
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active
    products = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        sku = str(row[0]).strip() if row[0] else None
        name = str(row[1]).strip() if row[1] else None
        if not sku or not name:
            continue
        cat_raw = str(row[2]).strip() if row[2] else ""
        top_cat = cat_raw.split("/")[0].strip() if cat_raw else "Sin categoría"

        if categoria_filter and top_cat.lower() != categoria_filter.lower():
            continue

        precio_lista = row[4] if row[4] else 0
        precio_mayorista = row[5] if row[5] else 0
        envio_grande = str(row[6]).strip().lower() in ("true", "1", "sí", "si", "yes") if row[6] else False

        try:
            precio_lista = int(round(float(precio_lista)))
        except (TypeError, ValueError):
            precio_lista = 0
        try:
            precio_mayorista = int(round(float(precio_mayorista)))
        except (TypeError, ValueError):
            precio_mayorista = 0

        precio_efectivo = int(round(precio_lista * 0.85)) if precio_lista else 0

        products.append({
            "sku": sku,
            "name": name,
            "category": top_cat,
            "precio_lista": precio_lista,
            "precio_efectivo": precio_efectivo,
            "precio_mayorista": precio_mayorista,
            "envio_grande": envio_grande,
        })
    wb.close()
    return products


# ---------------------------------------------------------------------------
# Fetch thumbnails from Medusa
# ---------------------------------------------------------------------------
def fetch_thumbnails(products):
    token = get_token()
    if not token:
        print("  WARN: No se pudo autenticar con Medusa, PDF sin imágenes")
        return {}
    headers = {"Authorization": f"Bearer {token}"}
    thumbnails = {}
    skus = [p["sku"] for p in products]

    # Fetch all products at once (Medusa supports limit up to 100)
    offset = 0
    all_products = []
    while True:
        try:
            r = requests.get(f"{MEDUSA_URL}/admin/products", headers=headers,
                             params={"limit": 100, "offset": offset}, timeout=20)
            if r.status_code != 200:
                break
            batch = r.json().get("products", [])
            all_products.extend(batch)
            if len(batch) < 100:
                break
            offset += 100
        except Exception:
            break

    # Build thumbnail map
    sku_set = set(skus)
    for p in all_products:
        for v in p.get("variants", []):
            sku = v.get("sku")
            if sku in sku_set and p.get("thumbnail"):
                thumbnails[sku] = p["thumbnail"]

    return thumbnails


# ---------------------------------------------------------------------------
# Generate Excel
# ---------------------------------------------------------------------------
def generate_excel(products, output_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Lista de Precios"

    # Title row
    ws.merge_cells("A1:G1")
    title_cell = ws["A1"]
    title_cell.value = f"LISTA DE PRECIOS - DankoShop"
    title_cell.font = Font(name="Calibri", bold=True, size=16, color="1A237E")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 35

    # Date row
    ws.merge_cells("A2:G2")
    date_cell = ws["A2"]
    date_cell.value = f"Generada: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    date_cell.font = Font(name="Calibri", size=10, italic=True, color="666666")
    date_cell.alignment = Alignment(horizontal="center")
    ws.row_dimensions[2].height = 20

    # Header row
    headers = ["SKU", "Artículo", "Categoría", "Precio Lista", "Precio Efectivo", "Precio Mayorista", "Envío Grande"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[4].height = 25

    # Data rows grouped by category
    current_cat = None
    row_num = 5
    for p in sorted(products, key=lambda x: (x["category"], x["name"])):
        # Category separator
        if p["category"] != current_cat:
            current_cat = p["category"]
            ws.merge_cells(f"A{row_num}:G{row_num}")
            cat_cell = ws.cell(row=row_num, column=1, value=f"  {current_cat}")
            rgb = CAT_COLORS.get(current_cat, DEFAULT_COLOR)[0]
            cat_fill = PatternFill(start_color=f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}",
                                   end_color=f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}",
                                   fill_type="solid")
            cat_cell.fill = cat_fill
            cat_cell.font = Font(name="Calibri", bold=True, size=11, color="FFFFFF")
            ws.row_dimensions[row_num].height = 22
            row_num += 1

        # Data row
        row_data = [
            p["sku"], p["name"], p["category"],
            p["precio_lista"], p["precio_efectivo"], p["precio_mayorista"],
            "Sí" if p["envio_grande"] else ""
        ]
        for col, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col, value=val)
            cell.font = BODY_FONT
            cell.border = Border(
                bottom=Side(style="thin", color="CCCCCC"),
            )
            if col in (4, 5, 6) and isinstance(val, (int, float)):
                cell.number_format = MONEY_FORMAT
                cell.alignment = Alignment(horizontal="right")
            if col == 7:
                cell.alignment = Alignment(horizontal="center")
        row_num += 1

    # Column widths
    widths = [18, 45, 25, 15, 16, 18, 14]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    wb.save(output_path)
    print(f"  Excel: {output_path}")


# ---------------------------------------------------------------------------
# Generate PDF
# ---------------------------------------------------------------------------
def download_thumb(url):
    """Download a single thumbnail, return bytes or None."""
    try:
        turl = url.replace("/upload/", "/upload/w_60,h_60,c_fill/")
        r = requests.get(turl, timeout=8)
        if r.status_code == 200:
            return r.content
    except Exception:
        pass
    return None


def generate_pdf(products, thumbnails, output_path):
    from fpdf import FPDF

    class PriceListPDF(FPDF):
        def header(self):
            pass

        def footer(self):
            self.set_y(-15)
            self.set_font(f"{FONT}", "", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f"www.dankoshop.com.ar | WhatsApp: 221 621 9596 | Pagina {self.page_no()}/{{nb}}", align="C")

    pdf = PriceListPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Register Unicode fonts
    if os.path.exists(FONT_REGULAR):
        pdf.add_font("DejaVu", "", FONT_REGULAR)
        pdf.add_font("DejaVu", "B", FONT_BOLD)
        FONT = "DejaVu"
    else:
        FONT = "Helvetica"

    # Pre-download all thumbnails in parallel
    print("  Descargando imágenes...")
    thumb_urls = {p["sku"]: thumbnails[p["sku"]] for p in products if p["sku"] in thumbnails}
    thumb_data = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(download_thumb, url): sku for sku, url in thumb_urls.items()}
        done = 0
        for future in as_completed(futures):
            sku = futures[future]
            data = future.result()
            if data:
                thumb_data[sku] = data
            done += 1
            if done % 50 == 0:
                print(f"    {done}/{len(thumb_urls)} imágenes descargadas...")
    print(f"    {len(thumb_data)}/{len(thumb_urls)} imágenes listas")

    # --- Cover page ---
    pdf.add_page()
    pdf.set_fill_color(26, 35, 126)  # Indigo
    pdf.rect(0, 0, 210, 297, "F")

    # White box
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(20, 40, 170, 180, "F")

    # Title
    pdf.set_xy(20, 60)
    pdf.set_font(f"{FONT}", "B", 36)
    pdf.set_text_color(26, 35, 126)
    pdf.cell(170, 20, "DANKO", align="C")
    pdf.set_xy(20, 80)
    pdf.set_font(f"{FONT}", "B", 36)
    pdf.set_text_color(244, 67, 54)
    pdf.cell(170, 20, "SHOP", align="C")

    # Subtitle
    pdf.set_xy(20, 115)
    pdf.set_font(f"{FONT}", "", 18)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(170, 10, "LISTA DE PRECIOS", align="C")

    # Date
    pdf.set_xy(20, 135)
    pdf.set_font(f"{FONT}", "", 12)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(170, 10, datetime.now().strftime("%d/%m/%Y"), align="C")

    # Stats
    total = len(products)
    cats = len(set(p["category"] for p in products))
    pdf.set_xy(20, 160)
    pdf.set_font(f"{FONT}", "", 12)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(170, 8, f"{total} productos en {cats} categorías", align="C")

    # Contact
    pdf.set_xy(20, 190)
    pdf.set_font(f"{FONT}", "", 11)
    pdf.set_text_color(26, 35, 126)
    pdf.cell(170, 8, "www.dankoshop.com.ar", align="C")
    pdf.set_xy(20, 200)
    pdf.cell(170, 8, "WhatsApp: 221 621 9596", align="C")

    # --- Product pages ---
    grouped = {}
    for p in products:
        grouped.setdefault(p["category"], []).append(p)

    for cat_name in sorted(grouped.keys()):
        cat_products = grouped[cat_name]
        rgb = CAT_COLORS.get(cat_name, DEFAULT_COLOR)[0]
        hex_color = CAT_COLORS.get(cat_name, DEFAULT_COLOR)[1]

        pdf.add_page()

        # Category header bar
        pdf.set_fill_color(rgb[0], rgb[1], rgb[2])
        pdf.rect(0, 10, 210, 18, "F")
        pdf.set_xy(10, 12)
        pdf.set_font(f"{FONT}", "B", 16)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(190, 14, f"  {cat_name} ({len(cat_products)})", align="L")

        y = 32

        for p in cat_products:
            # Check if we need a new page
            if y > 260:
                pdf.add_page()
                # Category header on continuation
                pdf.set_fill_color(rgb[0], rgb[1], rgb[2])
                pdf.rect(0, 10, 210, 14, "F")
                pdf.set_xy(10, 11)
                pdf.set_font(f"{FONT}", "B", 12)
                pdf.set_text_color(255, 255, 255)
                pdf.cell(190, 12, f"  {cat_name} (continuación)")
                y = 28

            # Product card background
            pdf.set_fill_color(245, 245, 245)
            pdf.rect(10, y, 190, 28, "F")

            # Left color accent
            pdf.set_fill_color(rgb[0], rgb[1], rgb[2])
            pdf.rect(10, y, 3, 28, "F")

            # Thumbnail
            img_bytes = thumb_data.get(p["sku"])
            if img_bytes:
                try:
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                        tmp.write(img_bytes)
                        tmp_path = tmp.name
                    pdf.image(tmp_path, x=16, y=y+4, w=20, h=20)
                    os.unlink(tmp_path)
                except Exception:
                    pass

            # Product name
            has_img = p["sku"] in thumb_data
            text_x = 42 if has_img else 16
            pdf.set_xy(text_x, y + 2)
            pdf.set_font(f"{FONT}", "B", 10)
            pdf.set_text_color(33, 33, 33)
            name = strip_emoji(p["name"])[:55] + ("..." if len(p["name"]) > 55 else "")
            pdf.cell(100, 5, name)

            # SKU
            pdf.set_xy(text_x, y + 8)
            pdf.set_font(f"{FONT}", "", 7)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(60, 4, f"SKU: {p['sku']}")

            # Prices on the right
            price_x = 135

            # Precio Lista (credito)
            pdf.set_xy(price_x, y + 2)
            pdf.set_font(f"{FONT}", "", 7)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(55, 4, "Precio Lista (Credito)")
            pdf.set_xy(price_x, y + 6)
            pdf.set_font(f"{FONT}", "B", 11)
            pdf.set_text_color(33, 33, 33)
            pdf.cell(55, 6, f"${p['precio_lista']:,}")

            # Precio Efectivo
            pdf.set_xy(price_x, y + 13)
            pdf.set_font(f"{FONT}", "", 7)
            pdf.set_text_color(76, 175, 80)
            pdf.cell(55, 4, "Precio Efectivo/Transferencia")
            pdf.set_xy(price_x, y + 17)
            pdf.set_font(f"{FONT}", "B", 12)
            pdf.set_text_color(76, 175, 80)
            pdf.cell(55, 6, f"${p['precio_efectivo']:,}")

            # Envio Grande badge
            if p["envio_grande"]:
                pdf.set_xy(text_x, y + 14)
                pdf.set_fill_color(255, 193, 7)
                pdf.set_font(f"{FONT}", "B", 6)
                pdf.set_text_color(33, 33, 33)
                pdf.cell(25, 5, " ENVIO GRANDE ", fill=True, align="C")

            # Separator line
            pdf.set_draw_color(220, 220, 220)
            pdf.line(10, y + 29, 200, y + 29)

            y += 30

    pdf.output(output_path)
    print(f"  PDF:   {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Genera lista de precios (Excel + PDF)")
    parser.add_argument("--solo-excel", action="store_true", help="Solo generar Excel")
    parser.add_argument("--solo-pdf", action="store_true", help="Solo generar PDF")
    parser.add_argument("--categoria", type=str, help="Filtrar por categoría")
    parser.add_argument("--mayorista", action="store_true", help="Usar precios mayoristas")
    args = parser.parse_args()

    print("=" * 50)
    print("  Generador de Lista de Precios - DankoShop")
    print("=" * 50)

    products = read_products(args.categoria)
    if not products:
        print("  No se encontraron productos.")
        return

    print(f"  Productos: {len(products)}")
    if args.categoria:
        print(f"  Categoría: {args.categoria}")
    if args.mayorista:
        print("  Modo: Precios Mayoristas")

    OUTPUT_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    excel_path = OUTPUT_DIR / f"lista_precios_{today}.xlsx"
    pdf_path = OUTPUT_DIR / f"lista_precios_{today}.pdf"

    if not args.solo_pdf:
        print("\nGenerando Excel...")
        generate_excel(products, excel_path)

    if not args.solo_excel:
        print("\nBuscando imágenes de productos en Medusa...")
        thumbnails = fetch_thumbnails(products)
        print(f"  Imágenes encontradas: {len(thumbnails)}/{len(products)}")
        print("\nGenerando PDF...")
        generate_pdf(products, thumbnails, pdf_path)

    print("\n" + "=" * 50)
    print("  ¡Listo!")
    print("=" * 50)


if __name__ == "__main__":
    main()
