#!/usr/bin/env python3
"""
procesar_chat_12_13.py - Genera Control_12_13_Agosto.xlsx

Analiza el chat de WhatsApp del 12 y 13 de agosto y arma un Excel
"inteligente" sincronizable con el maestro:

- Una fila por MENSAJE (109 con imagen).
- Asocia la imagen a cada mensaje por timestamp exacto
  (varios mensajes en el mismo segundo -> orden por sufijo del archivo).
- Extrae nombre, SKUs (ASCII y unicode 𝟎-𝟗), precios y fecha.
- Coteja con Productos_Maestro.xlsx usando la regla confirmada:
    mayorista_por_transferencia * 1.072  vs  col F (Precio Mayorista)
  (si no hay mayorista por transferencia, usa mayorista efectivo como fallback)
  - Para productos SIN mayorista (solo publican lista/efectivo minorista), la
    referencia confiable es el precio de la publicacion anterior (chat 5/8,
    guardado en Productos_Maestro_backup_10ago.xlsx): el maestro I quedo en la
    base vieja x1.10 (factor web anterior), no en la actual x1.15, y genera
    falsos BAJA. Si el precio del chat coincide con la publicacion anterior,
    se marca SIN CAMBIO.
  Estado -> AUMENTO / BAJA / SIN CAMBIO / NUEVO / SIN MAYORISTA / SIN SKU.

Uso:
  python3 scripts/procesar_chat_12_13.py
"""

import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import openpyxl

BASE = Path(__file__).resolve().parent.parent
CHAT_FILE = Path("/home/claudio/Descargas/Mayorista/Mensajes  12 y 13 agosto/chat.txt")
CHAT_PREVIO_FILE = Path("/home/claudio/Descargas/Mayorista/Mensajes desde el 5 de agosto/chat.txt")
IMAGES_DIR = Path("/home/claudio/Descargas/Mayorista/Imagenes 12 y13 Agosto")
MAESTRO_PATH = BASE / "excel" / "Productos_Maestro.xlsx"
BACKUP_PREVIO_PATH = BASE / "excel" / "Productos_Maestro_backup_10ago.xlsx"
OUT_XLSX = BASE / "excel" / "Control_12_13_Agosto.xlsx"

FACTOR = 1.072
TOLERANCIA = 0.01  # 1% -> SIN CAMBIO

UNICODE_DIGITS = {u: str(i) for i, u in enumerate("𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗")}

EMOJIS_PRODUCTO = ["🛒", "🛞", "📱", "📺", "🫕", "🎧", "🍺", "🏠", "🪑"]

MARKETING = [
    "nuevo ingreso", "nuevos ingresos", "nuevo producto", "ultimas", "últimas",
    "super reingreso", "llegó", "llegó el", "ultima unidad", "última unidad",
    "📢ultima", "últimas 6", "últimas 4", "últimas 3", "último en stock",
    "🚨", "🔥", "¡potencia", "hace tu pedido", "en stock", "última unid",
]


def normalize_digits(s):
    return "".join(UNICODE_DIGITS.get(ch, ch) for ch in s)


def parse_timestamp(ts_str):
    try:
        return datetime.strptime(ts_str.strip(), "%m/%d/%y, %I:%M:%S %p")
    except ValueError:
        return None


def ts_to_folder(dt):
    return dt.strftime("%Y-%m-%d at %H.%M.%S")


def split_by_timestamp(lines):
    messages = []
    cur = None
    for line in lines:
        m = re.match(r"\[(\d+/\d+/\d+,\s+\d+:\d+:\d+\s+[AP]M)\]", line)
        if m:
            if cur is not None:
                messages.append(cur)
            ts = parse_timestamp(m.group(1))
            cur = {"timestamp": ts, "lines": [line]}
        elif cur is not None:
            cur["lines"].append(line)
    if cur is not None:
        messages.append(cur)
    return messages


def strip_timestamp(line):
    """Quita '[fecha, hora] Nombre:' del inicio y emojis decorativos."""
    line = re.sub(r"^\[\d+/\d+/\d+,\s+\d+:\d+:\d+\s+[AP]M\]\s*\w.*?:\s*", "", line)
    line = re.sub(r"<imagen omitida>\s*", "", line)
    line = re.sub(r"<video omitido>\s*", "", line)
    line = re.sub(r"\[Reenviado[^\]]*\]\s*", "", line)
    return line


def es_marketing(line):
    low = line.lower()
    return any(m in low for m in MARKETING)


def clean_title(line):
    """Deja el título legible: quita emojis, SKUs al inicio y ruido."""
    t = strip_timestamp(line)
    t = re.sub(r"^(?:[\d]{3,5})[)]\s*", "", t)          # "(9347) Celular..."
    t = re.sub(r"^(?:[\d]{3,5})[)]?\s*", "", t)          # "8582) Celular..."
    t = re.sub(r"[\[(]N[°º]\s*[\d𝟎-𝟗]{3,5}[)\]]\s*", "", t)  # "(N°6324)"
    t = re.sub(r"[\[(]\s*[\d𝟎-𝟗]{3,5}[)\]]\s*", "", t)      # "(6232)" "[9643]"
    t = re.sub(r"[^\w\sáéíóúñÁÉÍÓÚÜü.°\"'-]", " ", t)          # emojis
    t = re.sub(r"\s+", " ", t).strip(" -–")
    return t


def find_title(body_lines):
    """Busca la línea de producto. Devuelve título legible o ''."""
    # 1) línea con emoji de producto y que no sea marketing
    for l in body_lines:
        t = l.strip()
        if not t:
            continue
        if any(e in t for e in EMOJIS_PRODUCTO) and not es_marketing(t):
            return clean_title(t)
    # 2) línea que contiene un SKU (N° / (xxxx) / [xxxx]) con nombre
    for l in body_lines:
        t = l.strip()
        if not t:
            continue
        if re.search(r"N[°º]\s*[\d𝟎-𝟗]{3,5}|\([\d𝟎-𝟗]{3,5}\)|\[[\d𝟎-𝟗]{3,5}\]", normalize_digits(t)):
            if len(t) > 8 and not es_marketing(t):
                return clean_title(t)
    # 3) primera línea no vacía
    for l in body_lines:
        t = l.strip()
        if t and not es_marketing(t):
            return clean_title(t)
    return ""


def extract_price_value(text):
    """Primer precio con $ en una línea -> int (soporta miles con . o ,)."""
    m = re.search(r"[$]\s*([\d]{1,3}(?:[.,][\d]{3})*(?:[.,][\d]{2})?)", text)
    if not m:
        m = re.search(r"(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{2})?)", text)
        if not m:
            return None
    return int(m.group(1).replace(".", "").replace(",", ""))


def extract_skus(lines):
    """Devuelve (main_sku, [skus...]).
    Solo captura N° con símbolo de grado (evita 'RZN356' o 'i3-N305').
    Soporta múltiples SKUs separados por '/' (ej. (6091/6093), N°7703/7705)."""
    skus = []
    for line in lines:
        ln = normalize_digits(line)
        # N° obligatorio con símbolo (N° / Nº) o (N°), puede llevar múltiples
        n_match = re.findall(r"[N𝐍][°º]\s*([\d𝟎-𝟗]{3,5}(?:\s*/\s*[\d𝟎-𝟗]{3,5})*)", ln)
        if n_match:
            for g in n_match:
                skus.extend([s.strip() for s in g.split("/") if s.strip()])
            continue
        br_match = re.findall(r"\[([\d𝟎-𝟗]{3,5}(?:\s*/\s*[\d𝟎-𝟗]{3,5})*)\]", ln)
        for g in br_match:
            skus.extend([s.strip() for s in g.split("/") if s.strip()])
        pa_match = re.findall(r"\(([\d𝟎-𝟗]{3,5}(?:\s*/\s*[\d𝟎-𝟗]{3,5})*)\)", ln)
        for g in pa_match:
            skus.extend([s.strip() for s in g.split("/") if s.strip()])
        ha_match = re.findall(r"#([\d𝟎-𝟗]{3,5}(?:\s*/\s*[\d𝟎-𝟗]{3,5})*)", ln)
        for g in ha_match:
            skus.extend([s.strip() for s in g.split("/") if s.strip()])
    skus = list(dict.fromkeys(skus))
    return (skus[0] if skus else None), skus


def parse_prices(lines):
    """Extrae precios por línea/reglas. Devuelve dict con None si faltan."""
    precio_lista = None
    precio_unidad = None     # efectivo minorista por unidad
    mayorista_efectivo = None
    mayorista_transfer = None
    precio_trans_minorista = None

    en_transferencia = False
    en_efectivo = False

    for l in lines:
        low = l.lower()
        v = extract_price_value(l)

        # sección transferencia (también captura su precio si está en la misma línea)
        if "por transferencia" in low and ("pagando" in low or "10%" in low or "10%off" in low or "🏦" in l):
            en_transferencia = True
            en_efectivo = False
            continue
        if ("pagando en efectivo" in low or "💰 pagando efectivo" in low or
                "efectivo 15% off" in low or "pagando efectivo" in low or "💰efectivo 15% off" in low):
            en_transferencia = False
            en_efectivo = True
            # la línea puede traer el precio del efectivo minorista
            if v is not None and "$" in l and "mayorista" not in low:
                if precio_unidad is None:
                    precio_unidad = v
            continue

        # Precio Lista
        if "precio lista" in low or "precio list" in low:
            if v is not None:
                precio_lista = v
            continue

        # Mayorista por transferencia (explícito) o mayorista en sección transferencia
        if "mayorista por transferencia" in low:
            if v is not None:
                mayorista_transfer = v
            continue
        if en_transferencia and "mayorista" in low:
            if v is not None and "por unidad" not in low:
                mayorista_transfer = v
            continue
        # 'Mayorista 3 unidades $X' bajo 'Pagando por transferencia'
        if en_transferencia and ("mayorista 3" in low or "mayorista $" in low or "📦" in l):
            if v is not None and "por unidad" not in low and "efectivo" not in low:
                mayorista_transfer = v
            continue

        # Mayorista efectivo (sección efectivo o línea con 'Mayorista llevando 3')
        if "mayorista" in low and (en_efectivo or "llevando 3" in low):
            if v is not None and "por unidad" not in low and "transferencia" not in low:
                if mayorista_efectivo is None:
                    mayorista_efectivo = v
            continue

        # Precio por unidad
        if "precio por unidad" in low:
            # En la sección transferencia hay OTRO 'Precio por unidad'
            # (el precio unitario al pagar por transferencia), no lo pisamos.
            if en_transferencia:
                continue
            if v is not None:
                precio_unidad = v
            continue

        # 15% OFF minorista / efectivo por unidad
        if "15% off minorista" in low or "15%off minorista" in low:
            if v is not None and precio_unidad is None:
                precio_unidad = v
            continue
        if ("15% off" in low or "15%off" in low) and "$" in l and "mayorista" not in low:
            if v is not None and precio_unidad is None:
                precio_unidad = v
            continue

        # 'Minorista $X' en sección efectivo
        if "minorista $" in low and en_efectivo:
            if v is not None and precio_unidad is None:
                precio_unidad = v
            continue

        # 10% off transferencia (minorista, NO mayorista)
        if "10% off transferencia" in low or "10%off transferencia" in low:
            if v is not None:
                precio_trans_minorista = v
            continue

        # formato '1️⃣ X $x' (auriculares)
        if "1️⃣" in l or re.search(r"1\s*X", l):
            if v is not None and precio_unidad is None:
                precio_unidad = v
            continue
        if "6️⃣" in l and "transferencia" in low:
            if v is not None and mayorista_transfer is None:
                mayorista_transfer = v
            continue
        if "6️⃣" in l and "efectivo" in low:
            if v is not None and mayorista_efectivo is None:
                mayorista_efectivo = v
            continue

    return {
        "precio_lista": precio_lista,
        "precio_unidad": precio_unidad,
        "mayorista_efectivo": mayorista_efectivo,
        "mayorista_transfer": mayorista_transfer,
        "precio_trans_minorista": precio_trans_minorista,
    }


def parse_message(msg):
    lines = msg["lines"]
    if not any("<imagen omitida>" in l or "<video omitido>" in l for l in lines):
        return None

    body_lines = [strip_timestamp(lines[0])] + [l.strip() for l in lines[1:] if l.strip()]

    main_sku, skus = extract_skus(lines)
    prices = parse_prices(lines)
    title = find_title(body_lines)

    return {
        "fecha": msg["timestamp"].strftime("%d/%m/%Y") if msg["timestamp"] else "",
        "hora": msg["timestamp"].strftime("%H:%M") if msg["timestamp"] else "",
        "folder": ts_to_folder(msg["timestamp"]) if msg["timestamp"] else None,
        "title": title,
        "sku": main_sku,
        "skus": skus,
        **prices,
    }


def scan_image_groups():
    """{folder: [(sufijo_int, nombre, path), ...]} base primero."""
    groups = defaultdict(list)
    for p in IMAGES_DIR.iterdir():
        if p.suffix.lower() not in [".jpeg", ".jpg", ".png", ".webp"]:
            continue
        m = re.search(r"(\d{4}-\d{2}-\d{2} at \d{2}\.\d{2}\.\d{2})", p.name)
        if not m:
            continue
        suf = re.search(r"\((\d+)\)", p.name)
        groups[m.group(1)].append((int(suf.group(1)) if suf else 0, p.name))
    out = {}
    for k, v in groups.items():
        v.sort(key=lambda x: x[0])
        out[k] = v
    return out


def load_maestro():
    """{sku: (titulo, F_mayorista, I_ingresado)}"""
    wb = openpyxl.load_workbook(MAESTRO_PATH, data_only=True)
    ws = wb.active
    d = {}
    for r in range(2, ws.max_row + 1):
        sku = ws.cell(r, 1).value
        if sku:
            d[str(sku).strip()] = (ws.cell(r, 2).value, ws.cell(r, 6).value, ws.cell(r, 9).value)
    return d


def load_precio_anterior():
    """
    Precios de la publicacion anterior. Fuente primaria: chat desde el 5 de
    agosto, parseado con el mismo parser (ultima aparicion por SKU). Fallback
    para SKUs ausentes: backup del maestro del 10/8 (mismo periodo 5-10 ago),
    que trae el mayorista (mTransf) y el efectivo minorista (unidad).
    """
    d = {}
    if CHAT_PREVIO_FILE.exists():
        with open(CHAT_PREVIO_FILE, encoding="utf-8") as f:
            lines = f.readlines()
        messages = split_by_timestamp(lines)
        for msg in messages:
            p = parse_message(msg)
            if p is None or p["sku"] is None:
                continue
            d[p["sku"]] = {
                "unidad": p["precio_unidad"],
                "mEfectivo": p["mayorista_efectivo"],
                "mTransf": p["mayorista_transfer"],
                "lista": p["precio_lista"],
                "fecha": p["fecha"],
            }
    if BACKUP_PREVIO_PATH.exists():
        wb = openpyxl.load_workbook(BACKUP_PREVIO_PATH, data_only=True)
        ws = wb.active
        for r in range(2, ws.max_row + 1):
            sku = ws.cell(r, 1).value
            if not sku:
                continue
            s = str(sku).strip()
            if s in d:
                continue
            d[s] = {
                "unidad": ws.cell(r, 5).value,
                "mEfectivo": None,
                "mTransf": ws.cell(r, 7).value,
                "lista": ws.cell(r, 4).value,
                "fecha": "backup 10/8",
            }
    return d


def is_num(v):
    return isinstance(v, (int, float)) and v


def base_price(p, maestro_sku):
    """
    Precio base del chat que representa el 'Precio Ingresado' (I):
    - Si el maestro tiene I, se elige el campo del chat más cercano a I entre
      {mayorista_transfer, precio_unidad, precio_lista}: el maestro se guarda
      como I el 'precio por unidad' (efectivo minorista) que Luciana ingresa
      (verificado: I == precio_unidad en los casos testeados). Priorizar
      siempre 'mayorista por transferencia' genera falsos AUMENTO cuando
      unidad != mT (ej. 7815: I=194920=unidad, mT=202258 -> +3.76% falso).
    - Si no hay I, prioridad: mayorista_transfer (regla confirmada), luego
      precio_unidad, luego precio_lista.
    """
    cands = []
    if is_num(p["mayorista_transfer"]):
        cands.append(("transfer", p["mayorista_transfer"]))
    if is_num(p["precio_unidad"]):
        cands.append(("unidad", p["precio_unidad"]))
    if is_num(p["precio_lista"]):
        cands.append(("lista", p["precio_lista"]))
    if not cands:
        return None, None
    if maestro_sku and is_num(maestro_sku[2]):
        target = maestro_sku[2]
        cands.sort(key=lambda c: abs(c[1] - target))
    else:
        priority = {"transfer": 0, "unidad": 1, "lista": 2}
        cands.sort(key=lambda c: priority[c[0]])
    return cands[0][1], cands[0][0]


def estado_for(p, maestro, previo):
    sku = p["sku"]
    if sku is None:
        return "SIN SKU"
    m = maestro.get(sku)
    base, fuente = base_price(p, m)

    # Referencia primaria: la PUBLICACION ANTERIOR (chat 5/8 o backup 10/8),
    # campo a campo. El maestro I/F quedo desactualizado para varios productos
    # (base x1.10 vieja), asi que comparar contra el maestro genera falsos
    # AUMENTO/BAJA. Elegimos el campo del chat cuyo valor coincida mejor con
    # el mismo campo de la publicacion anterior.
    prev = previo.get(sku) if previo else None
    if prev is not None:
        field_map = {"transfer": "mTransf", "unidad": "unidad", "lista": "lista"}
        mejor = None
        for f in ("transfer", "unidad", "lista"):
            pv = prev.get(field_map[f])
            cur = p.get({"transfer": "mayorista_transfer",
                         "unidad": "precio_unidad",
                         "lista": "precio_lista"}[f])
            if is_num(pv) and is_num(cur):
                d = abs(cur - pv) / pv
                if mejor is None or d < mejor[0]:
                    mejor = (d, f, cur, pv)
        if mejor is not None and mejor[0] < 0.25:  # coincidencia plausible
            _, fuente, base, ref = mejor
            p["chat_F"] = round(base * FACTOR)
            p["fuente_base"] = fuente
            p["diff_pct"] = (base - ref) / ref * 100
            p["maestro_F"] = m[1] if m else None
            p["maestro_I"] = m[2] if m else None
            p["referencia"] = f"publicacion anterior ({prev.get('fecha','')})"
            if base > ref * (1 + TOLERANCIA):
                return "AUMENTO"
            if base < ref * (1 - TOLERANCIA):
                return "BAJA"
            return "SIN CAMBIO"

    if base is None:
        if m is None:
            return "NUEVO"
        return "SIN MAYORISTA"
    chat_f = round(base * FACTOR)
    p["chat_F"] = chat_f
    p["fuente_base"] = fuente
    if m is None:
        return "NUEVO"
    # Referencia: I si existe (F = I*1.072), si no F
    target = m[2] if is_num(m[2]) else m[1]
    if not is_num(target):
        return "SIN PRECIO MAESTRO"
    diff = (base - target) / target
    p["diff_pct"] = diff * 100
    p["maestro_F"] = m[1]
    p["maestro_I"] = m[2]
    if diff > TOLERANCIA:
        return "AUMENTO"
    if diff < -TOLERANCIA:
        return "BAJA"
    return "SIN CAMBIO"


def main():
    with open(CHAT_FILE, encoding="utf-8") as f:
        lines = f.readlines()
    messages = split_by_timestamp(lines)

    img_groups = scan_image_groups()
    used_count = defaultdict(int)
    missing_imgs = 0

    parsed = []
    for msg in messages:
        p = parse_message(msg)
        if p is None:
            continue
        imgs = []
        if p["folder"] in img_groups:
            available = img_groups[p["folder"]]
            while used_count[p["folder"]] < len(available):
                _, fname = available[used_count[p["folder"]]]
                imgs.append(fname)
                used_count[p["folder"]] += 1
                break
        if not imgs:
            missing_imgs += 1
        p["imagen"] = ", ".join(imgs)
        parsed.append(p)

    maestro = load_maestro()
    previo = load_precio_anterior()

    for p in parsed:
        p["estado"] = estado_for(p, maestro, previo)

    counts = defaultdict(int)
    for p in parsed:
        counts[p["estado"]] += 1
    print(f"Mensajes con imagen: {len(parsed)} | sin imagen: {missing_imgs}")
    for k in ["NUEVO", "AUMENTO", "BAJA", "SIN CAMBIO", "SIN MAYORISTA", "SIN SKU"]:
        if counts[k]:
            print(f"  {k}: {counts[k]}")

    # Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Control"
    headers = [
        "Fecha", "Hora", "SKU", "Otros SKUs", "Artículo", "Imagen",
        "Precio unidad (efectivo)", "Mayorista efectivo",
        "Mayorista transferencia", "Precio Lista",
        "Base (x1.072)", "Maestro F", "Diff %", "Estado", "Referencia",
    ]
    ws.append(headers)
    from openpyxl.styles import Font, PatternFill

    hf = Font(bold=True, color="FFFFFF")
    fills = {
        "AUMENTO": "C0392B",
        "BAJA": "2874A6",
        "NUEVO": "1E8449",
        "SIN CAMBIO": "7F8C8D",
        "SIN MAYORISTA": "B7950B",
        "SIN SKU": "6C3483",
    }
    for c in range(1, len(headers) + 1):
        cell = ws.cell(1, c)
        cell.font = hf
        cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")

    for p in parsed:
        ws.append([
            p["fecha"], p["hora"], p["sku"],
            ", ".join(p["skus"]) if p["skus"] else "",
            p["title"], p["imagen"],
            p["precio_unidad"], p["mayorista_efectivo"],
            p["mayorista_transfer"], p["precio_lista"],
            p.get("chat_F", ""), p.get("maestro_F", ""),
            round(p["diff_pct"], 2) if "diff_pct" in p else "",
            p["estado"],
            p.get("referencia", ""),
        ])
        row = ws.max_row
        if p["estado"] in fills:
            ws.cell(row, len(headers)).fill = PatternFill(
                start_color=fills[p["estado"]], end_color=fills[p["estado"]], fill_type="solid")

    widths = [12, 8, 10, 26, 45, 40, 16, 16, 18, 14, 12, 12, 9, 14, 20]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:O{ws.max_row}"

    all_used = set()
    for p in parsed:
        for fname in p["imagen"].split(", "):
            if fname:
                all_used.add(fname)
    ws2 = wb.create_sheet("Imagenes sin asignar")
    ws2.append(["Archivo"])
    for p in sorted(IMAGES_DIR.iterdir()):
        if p.name not in all_used:
            ws2.append([p.name])

    wb.save(OUT_XLSX)
    print(f"\nGuardado: {OUT_XLSX}")


if __name__ == "__main__":
    main()