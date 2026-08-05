#!/usr/bin/env python3
"""
Parse WhatsApp chat.txt and extract products with prices, SKUs, specs, and timestamps.
Match with images from 'imagenes ATTIAN' folder by timestamp.
Output: products.json, products.csv, organized_images/
"""

import re
import json
import csv
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

CHAT_FILE = "/home/claudio/Descargas/LUCIANA ATTAIN/chat.txt"
IMAGES_DIR = Path("/home/claudio/Descargas/LUCIANA ATTAIN/imagenes ATTIAN")
OUTPUT_DIR = Path("/home/claudio/Descargas/dankoshop/data")
ORGANIZED_IMAGES_DIR = OUTPUT_DIR / "organized_images"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ORGANIZED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse WhatsApp timestamp like '7/31/26, 11:12:39 AM'"""
    try:
        return datetime.strptime(ts_str.strip(), "%m/%d/%y, %I:%M:%S %p")
    except ValueError:
        try:
            return datetime.strptime(ts_str.strip(), "%m/%d/%y, %I:%M %p")
        except ValueError:
            return None


def timestamp_to_folder_name(dt: datetime) -> str:
    """Convert datetime to folder format: '2026-07-31 at 11.12.39'"""
    return dt.strftime("%Y-%m-%d at %H.%M.%S")


def extract_price(text: str) -> Optional[int]:
    """Extract price from various formats"""
    patterns = [
        r'[\$]\s*([\d]{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',
        r'[\$]([\d.,]+)',
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            val = match.group(1).replace(".", "").replace(",", "")
            try:
                return int(val)
            except ValueError:
                continue
    return None


def extract_all_prices(line: str) -> List[int]:
    """Extract all prices from a line"""
    prices = []
    matches = re.findall(r'[\$]\s*([\d]{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)', line)
    for m in matches:
        try:
            prices.append(int(m.replace(".", "").replace(",", "")))
        except ValueError:
            pass
    return prices


def categorize_product(name: str) -> str:
    """Categorize product based on name"""
    # Normalize unicode characters for matching
    name_normalized = name.lower()
    unicode_map = {
        '𝗦': 's', '𝗠': 'm', '𝗔': 'a', '𝗥': 'r', '𝗧': 't', '𝗩': 'v',
        '𝗛': 'h', '𝗬': 'y', '𝗨': 'u', '𝗡': 'n', '𝗗': 'd', '𝗔': 'a', '𝗜': 'i',
        '𝗤': 'q', '𝗟': 'l', '𝗘': 'e', '𝗗': 'd', '𝗚': 'g', '𝗢': 'o', '𝗚': 'g', '𝗟': 'l', '𝗘': 'e', '𝗧': 't', '𝗩': 'v',
        '✨': '', '🇦': '', '🇷': '', '🏆': '', '🔥': '', '💙': '', '📱': '', '💎': '', '🌟': '', '⚡': '', '🎁': '', '📦': '', '🛍️': '',
        '🛒': '', '🏠': '', '🪑': '', '🛞': '', '📺': '', '🌴': '', '🌀': '', '🏆': '', '✨': '',
        '𝐓': 't', '𝐚': 'a', '𝐛': 'b', '𝐥': 'l', '𝐞': 'e', '𝐭': 't', '𝐔': 'u', '𝐥': 'l', '𝐭': 't', '𝐫': 'r', '𝐨': 'o', '𝐦': 'm', '𝐀': 'a', '𝐥': 'l', '𝐩': 'p', '𝐡': 'h', '𝐚': 'a',
        '𝟏': '1', '𝟎': '0', '𝟐': '2', '𝟖': '8', '𝟔': '6', '𝟓': '5', '𝟕': '7', '𝟑': '3', '𝟒': '4', '𝟗': '9',
        '𝖢': 'c', '𝗈': 'o', '𝖽': 'd', '𝖾': 'e', '.': '.',
        '💸': '', '💲': '', '💵': '', '💳': '', '🏦': '', '💰': '', '🏷️': '', '📦': '', '🏛️': '',
    }
    for u, a in unicode_map.items():
        name_normalized = name_normalized.replace(u, a)
    
    if any(kw in name_normalized for kw in ['celular', 'motorola', 'samsung', 'smartphone', 'g06', 'g04', 'a07', 'e10', 'moto e']):
        return "Celulares"
    elif any(kw in name_normalized for kw in ['tablet', 'tableta', 'ultrom alpha']):
        return "Tablets"
    elif any(kw in name_normalized for kw in ['notebook', 'laptop']):
        return "Notebooks"
    elif any(kw in name_normalized for kw in ['tv', 'smart tv', 'televisor', 'hyundai', 'qled', 'google tv']):
        return "TVs"
    elif any(kw in name_normalized for kw in ['lavarropas', 'lavadora', 'secarropas', 'centrifugado', 'vitta semiautomatico', 'drean semiautomatico', 'enova carga']):
        return "Lavarropas/Secarropas"
    elif any(kw in name_normalized for kw in ['heladera', 'freezer', 'frigobar', 'cervecera', 'briket', 'telefunken', 'drean no frost', 'enova freezer', 'midea']):
        return "Heladeras/Freezers"
    elif any(kw in name_normalized for kw in ['cocina', 'anafe', 'horno', 'microondas', 'escorial', 'usman', 'irina', 'kanji', 'vitroceramico', 'vitta negra', 'vitta multigas', 'candor', 'termotanque', 'temotanque']):
        return "Cocinas/Hornos/Microondas"
    elif any(kw in name_normalized for kw in ['freidora', 'air fryer', 'tostadora', 'termo eléctrico', 'vajilla', 'vaso', 'plato', 'durax', 'microsonic', 'smartlife', 'vitta 6.5', 'vitta 8', 'vitta 11', 'futura', 'midow']):
        return "Pequeños Electrodomésticos"
    elif any(kw in name_normalized for kw in ['bicicleta', 'bici ', 'rodado ', 'nathor', 'fiat 500', 'anderson', 'corvo', 'playera', 'paseo', 'carrozada']):
        return "Bicicletas"
    elif any(kw in name_normalized for kw in ['silla gamer', 'mesa gamer', 'gamer', 'ultrom negro-verde', 'gt-2310']):
        return "Gaming"
    elif any(kw in name_normalized for kw in ['reposera', 'sillón playero', 'sillon playero', 'carrito de playa', 'cama elástica', 'cama elastica', 'tobogán', 'tobogan', 'hamaca', 'inflador', 'xplay', 'mor ', 'mor plegable']):
        return "Outdoor/Playa"
    elif any(kw in name_normalized for kw in ['taladro', 'amoladora', 'rotomartillo', 'lijadora', 'atornillador', 'compresor', 'hidrolavadora', 'bomba centrífuga', 'bomba centrifuga', 'minitorno', 'termofusora', 'kit taladro', 'konan tools', 'kanji tools', 'midow ', 'atornillador']):
        return "Herramientas"
    elif any(kw in name_normalized for kw in ['colchón', 'colchon', 'almohada', 'chifonier', 'bajomesada', 'mesa de luz', 'cajonera', 'grifería', 'griferia', 'monocomando', 'termo eléctrico', 'sirena', 'termotanque', 'ducha']):
        return "Hogar/Baño"
    elif any(kw in name_normalized for kw in ['auriculares', 'auricular', 'guantes', 'bolsa de box', 'oreja de gato', 'suono']):
        return "Accesorios"
    elif any(kw in name_normalized for kw in ['paleta de pádel', 'paleta de padel', 'cigio']):
        return "Deportes"
    elif any(kw in name_normalized for kw in ['combo argentino', 'combo taladro']):
        return "Combos"
    else:
        return "Varios"


def scan_images() -> Dict[str, List[Path]]:
    """Scan images folder and group by timestamp (up to seconds)"""
    groups = defaultdict(list)
    for img_path in IMAGES_DIR.iterdir():
        if img_path.is_file() and img_path.suffix.lower() in ['.jpeg', '.jpg', '.png', '.webp', '.mp4']:
            match = re.search(r'(\d{4}-\d{2}-\d{2} at \d{2}\.\d{2}\.\d{2})', img_path.name)
            if match:
                ts_key = match.group(1)
                groups[ts_key].append(img_path)
    for key in groups:
        groups[key].sort(key=lambda p: p.name)
    return dict(groups)


def split_by_timestamp(lines: List[str]) -> List[Dict]:
    """Split chat lines into messages grouped by timestamp"""
    messages = []
    current_msg = None
    
    for i, line in enumerate(lines):
        ts_match = re.match(r'\[(\d+/\d+/\d+,\s+\d+:\d+:\d+\s+[AP]M)\]', line)
        if ts_match:
            if current_msg is not None:
                messages.append(current_msg)
            timestamp = parse_timestamp(ts_match.group(1))
            current_msg = {
                "timestamp": timestamp,
                "timestamp_str": ts_match.group(1),
                "timestamp_folder": timestamp_to_folder_name(timestamp) if timestamp else None,
                "start_line": i,
                "lines": [line]
            }
        elif current_msg is not None:
            current_msg["lines"].append(line)
    
    if current_msg is not None:
        messages.append(current_msg)
    
    return messages


def parse_product_from_line(line: str, timestamp: datetime, timestamp_folder: str, line_idx: int, msg_lines: List[str], msg_start_idx: int) -> Optional[Dict]:
    """Parse a single product from a line that contains a product emoji"""
    # Clean the line
    clean_line = line
    clean_line = re.sub(r'^\[\d+/\d+/\d+,\s+\d+:\d+:\d+\s+[AP]M\]\s*\w+.*?:\s*', '', clean_line)
    clean_line = re.sub(r'\[Reenviado[^\]]*\]\s*', '', clean_line)
    clean_line = re.sub(r'<imagen omitida>\s*', '', clean_line)
    clean_line = re.sub(r'<video omitido>\s*', '', clean_line)
    
    # Extract name after emoji
    name_match = re.search(r'[🛒📱🏠🪑🏆📦🌴🛞📺🇦🇷🌀✨]\s*(.+?)(?:\s*[💵💳🏦💰🏷️📦🏛️💸💲🪑💸💲]|$)', clean_line)
    if name_match:
        name = name_match.group(1).strip()
    else:
        name = clean_line.strip()[:100]
    
    # Clean up name
    name = re.sub(r'\s+', ' ', name).strip()
    name = re.sub(r'^[^\w\d]+|[^\w\d]+$', '', name).strip()
    
    # Skip if name is too short or looks like a header
    if len(name) < 5:
        return None
    if any(h in name.lower() for h in [
        'muy buenos días', 'arrancamos', 'te esperamos', 'vamos por',
        'llegó el', 'cerramos', 'energía para', 'crecer', 'vendiendo',
        'último en stock', 'última unidad', 'últimas unidades', 'ultimas unidades',
        'últimas 3 unidades', 'ultimas 3', 'única unidad', 'unica unidad',
        'lo pedis', 'lo tenes', 'por pedido', 'reingreso', 'nuevo ingreso',
        'novedad en stock', 'super reingreso', 'combo hogar',
        'ya disponibles', 'disponibles en sucursal', 'incluye:', '✨╔', 'esencial para',
        'nuevo ingreso', 'últimas unidades', 'ultimas unidades', 'última unidad', 'unica unidad'
    ]):
        return None
    
    # Extract SKU(s) from this line and next few lines (local indices)
    local_idx = line_idx - msg_start_idx
    skus = []
    for look_i in range(local_idx, min(local_idx + 10, len(msg_lines))):
        # Match both ASCII and unicode digits
        sku_matches = re.findall(r'(?:N[°º]\s*|Cod\.\s*|[\(#]\s*)([\d𝟎-𝟗]{3,5})', msg_lines[look_i])
        # Convert unicode digits to ASCII
        sku_matches = [re.sub(r'[𝟎-𝟗]', lambda m: str(ord(m.group()) - ord('𝟎')), s) for s in sku_matches]
        skus.extend(sku_matches)
    skus = list(dict.fromkeys(skus))
    main_sku = skus[0] if skus else f"AUTO-{timestamp.strftime('%Y%m%d%H%M%S')}-{line_idx}"
    
    # Parse prices from the message block
    prices = {
        "precio_lista": None,
        "precio_efectivo": None,
        "precio_transferencia": None,
        "precio_mayorista": None,
        "precio_mayorista_transferencia": None,
        "cuotas": None,
        "cuota_valor": None
    }
    
    description_lines = []
    specs = []
    
    for msg_line in msg_lines:
        line_clean = msg_line.strip()
        if not line_clean:
            continue
        line_lower = line_clean.lower()
        
        all_prices = extract_all_prices(line_clean)
        
        if "precio lista" in line_lower or "💸" in line_clean or "💲" in line_clean:
            if all_prices:
                prices["precio_lista"] = max(all_prices)
        elif "15% off" in line_lower and "minorista" in line_lower:
            if all_prices:
                prices["precio_efectivo"] = min(all_prices)
        elif "15% off" in line_lower and "mayorista" not in line_lower and "minorista" not in line_lower:
            if all_prices:
                prices["precio_efectivo"] = min(all_prices)
        elif "10% off" in line_lower and "minorista" in line_lower:
            if all_prices:
                prices["precio_transferencia"] = min(all_prices)
        elif "10%off" in line_lower or "10% off" in line_lower:
            if all_prices and prices["precio_transferencia"] is None:
                prices["precio_transferencia"] = min(all_prices)
        elif "17% off" in line_lower and "mayorista" in line_lower:
            if all_prices:
                prices["precio_mayorista"] = min(all_prices)
        elif "mayorista" in line_lower and "transferencia" in line_lower:
            if all_prices:
                prices["precio_mayorista_transferencia"] = min(all_prices)
        elif "mayorista" in line_lower and "3 unidades" in line_lower:
            if all_prices:
                prices["precio_mayorista"] = min(all_prices)
        elif "3 cuotas" in line_lower and "sin interés" in line_lower:
            prices["cuotas"] = 3
            if all_prices:
                prices["cuota_valor"] = min(all_prices)
        
        # Specs
        if any(c in line_clean for c in ['✅', '✔️', '✔', '᯾', '•', '✓', '* ✅']) and not any(p in line_lower for p in ['off', 'lista', 'cuotas', 'precio']):
            specs.append(line_clean)
        # Description
        elif line_clean and not line_clean.startswith('[') and len(line_clean) > 5:
            if not any(kw in line_lower for kw in ['off', 'lista', 'cuotas', 'transferencia', 'efectivo', 'mayorista', 'precio', 'reingreso', 'nuevo ingreso', 'últimas', 'ultimas', 'única', 'unica', 'stock', 'pedido', 'muy buenos', 'arrancamos', 'te esperamos', 'vamos por', 'llegó el', 'cerramos', 'energía', 'crecer', 'vendiendo', 'hace tu pedido', 'asistente', 'carla', '24 hs', '365 días']):
                description_lines.append(line_clean)
    
    description = "\n".join(description_lines[:8]) if description_lines else ""
    specs_text = "\n".join(specs[:20]) if specs else ""
    category = categorize_product(name)
    
    # Calculate missing prices
    if prices["precio_lista"] is None:
        if prices["precio_efectivo"] is not None:
            prices["precio_lista"] = round(prices["precio_efectivo"] / 0.85)
        elif prices["precio_transferencia"] is not None:
            prices["precio_lista"] = round(prices["precio_transferencia"] / 0.90)
        elif prices["precio_mayorista"] is not None:
            prices["precio_lista"] = round(prices["precio_mayorista"] / 0.83)
        elif prices["precio_mayorista_transferencia"] is not None:
            prices["precio_lista"] = round(prices["precio_mayorista_transferencia"] / 0.90)
    
    if prices["precio_lista"] is not None:
        if prices["precio_efectivo"] is None:
            prices["precio_efectivo"] = round(prices["precio_lista"] * 0.85)
        if prices["precio_transferencia"] is None:
            prices["precio_transferencia"] = round(prices["precio_lista"] * 0.90)
        if prices["precio_mayorista"] is None:
            prices["precio_mayorista"] = round(prices["precio_lista"] * 0.83)
    
    return {
        "sku": main_sku,
        "skus": skus,
        "name": name,
        "description": description,
        "specs": specs_text,
        "category": category,
        "prices": prices,
        "timestamp": timestamp.isoformat() if timestamp else "",
        "timestamp_folder": timestamp_folder,
        "images": []
    }


def parse_all_products(lines: List[str]) -> List[Dict]:
    """Parse all products by first splitting by timestamp, then finding all product lines in each message"""
    messages = split_by_timestamp(lines)
    products = []
    
    for msg in messages:
        if not msg["timestamp"]:
            continue
        
        # Find all lines with product emojis in this message
        product_emojis = ['🛒', '📱', '🏠', '🪑', '🏆', '📦', '🌴', '🛞', '📺', '🇦🇷', '🌀', '✨']
        
        for local_idx, line in enumerate(msg["lines"]):
            global_idx = msg["start_line"] + local_idx
            if any(emoji in line for emoji in product_emojis):
                # Check if it's a header/marketing line
                is_header = any(h in line.lower() for h in [
                    'muy buenos días', 'arrancamos', 'te esperamos', 'vamos por',
                    'llegó el', 'cerramos', 'energía para', 'crecer', 'vendiendo',
                    'último en stock', 'última unidad', 'últimas unidades', 'ultimas unidades',
                    'últimas 3 unidades', 'ultimas 3', 'única unidad', 'unica unidad',
                    'lo pedis', 'lo tenes', 'por pedido', 'reingreso', 'nuevo ingreso',
                    'novedad en stock', 'super reingreso', 'combo hogar',
                    'ya disponibles', 'disponibles en sucursal', 'incluye:', '✨╔', 'esencial para',
                    'pantalla', 'sistema de lavado', 'precio por escala'
                ])
                
                is_price_line = any(p in line.lower() for p in [
                    'off mayorista', 'off minorista', 'precio lista', 'precio por unidad',
                    'mayorista 3 unidades', 'mayorista por transferencia', 'cuotas sin interés',
                    '3 cuotas', 'transferencia 10%', 'efectivo 15%', 'minorista $',
                    'mayorista $', 'lista $', 'precio:', 'cuota de',
                    'precio por escala', 'mayorista *$', '15%off efectivo'
                ])
                
                # Also skip lines that are clearly specs (start with unicode bold or common spec patterns)
                is_spec_line = (
                    line.strip().startswith(('𝐏', '𝐒', '𝐂', '𝐀', '𝐁', '𝐃', '𝐄', '𝐅', '𝐆', '𝐇', '𝐈', '𝐉', '𝐊', '𝐋', '𝐌', '𝐍', '𝐎', '𝐏', '𝐐', '𝐑', '𝐒', '𝐓', '𝐔', '𝐕', '𝐖', '𝐗', '𝐘', '𝐙')) or
                    line.strip().startswith(('✅', '✔️', '✔', '⚡', '🎙️', '📡', '🎮', '🎬', '🌀', '⚙️', '🧺', '🔒', '᯾', '•', '* ✅', '✓'))
                )
                
                if not is_header and not is_price_line and not is_spec_line:
                    has_image = '<imagen omitida>' in line or '<video omitido>' in line
                    product = parse_product_from_line(
                        line, msg["timestamp"], msg["timestamp_folder"], 
                        global_idx, msg["lines"], msg["start_line"]
                    )
                    if product and product["name"]:
                        product["has_image_ref"] = has_image
                        products.append(product)
    
    return products


def distribute_images(products: List[Dict], image_groups: Dict[str, List[Path]]) -> List[Dict]:
    """Distribute images to products"""
    assigned_count = defaultdict(int)
    
    for product in products:
        ts_folder = product["timestamp_folder"]
        if ts_folder in image_groups:
            available = image_groups[ts_folder]
            idx = assigned_count[ts_folder]
            if idx < len(available):
                product["images"] = [str(available[idx])]
                assigned_count[ts_folder] += 1
            elif available:
                product["images"] = [str(available[-1])]
    
    return products


def copy_images_to_organized(products: List[Dict]):
    """Copy images to organized folder structure"""
    for product in products:
        if not product["images"]:
            continue
        sku = product["sku"]
        name_slug = re.sub(r'[^\w\s-]', '', product["name"]).strip().replace(' ', '_')[:50]
        dest_dir = ORGANIZED_IMAGES_DIR / f"{sku}_{name_slug}"
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        for idx, src_path in enumerate(product["images"]):
            src = Path(src_path)
            ext = src.suffix
            dest_name = f"{sku}_{idx+1}{ext}"
            dest = dest_dir / dest_name
            try:
                shutil.copy2(src, dest)
                product["images"][idx] = str(dest.relative_to(OUTPUT_DIR))
            except Exception as e:
                print(f"Error copying {src}: {e}")


def deduplicate_products(products: List[Dict]) -> List[Dict]:
    """Deduplicate by SKU - keep the most complete entry"""
    by_sku = defaultdict(list)
    for p in products:
        by_sku[p["sku"]].append(p)
    
    result = []
    for sku, entries in by_sku.items():
        if len(entries) == 1:
            result.append(entries[0])
        else:
            best = max(entries, key=lambda p: (
                (p["prices"]["precio_lista"] is not None) +
                (p["prices"]["precio_efectivo"] is not None) +
                (p["prices"]["precio_transferencia"] is not None) +
                (p["prices"]["precio_mayorista"] is not None) +
                len(p["description"]) +
                len(p["specs"]) +
                len(p["images"])
            ))
            all_images = []
            for e in entries:
                all_images.extend(e["images"])
            best["images"] = list(dict.fromkeys(all_images))
            result.append(best)
    return result


def main():
    print("Reading chat file...")
    with open(CHAT_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("Parsing products...")
    products = parse_all_products(lines)
    print(f"Found {len(products)} product messages")
    
    print("Scanning images...")
    image_groups = scan_images()
    print(f"Found {len(image_groups)} image timestamp groups")
    total_imgs = sum(len(v) for v in image_groups.values())
    print(f"Total images: {total_imgs}")
    
    print("Distributing images to products...")
    products = distribute_images(products, image_groups)
    
    print("Deduplicating products by SKU...")
    products = deduplicate_products(products)
    print(f"After deduplication: {len(products)} products")
    
    print("Copying images to organized folder...")
    copy_images_to_organized(products)
    
    # Remove internal fields
    for p in products:
        p.pop("timestamp_folder", None)
        p.pop("has_image_ref", None)
    
    # Save JSON
    json_path = OUTPUT_DIR / "products.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"Saved {json_path}")
    
    # Save CSV
    csv_path = OUTPUT_DIR / "products.csv"
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "sku", "name", "category", "description", "specs",
            "precio_lista", "precio_efectivo", "precio_transferencia",
            "precio_mayorista", "precio_mayorista_transferencia",
            "cuotas", "cuota_valor", "timestamp", "images"
        ])
        for p in products:
            writer.writerow([
                p["sku"], p["name"], p["category"], p["description"], p["specs"],
                p["prices"]["precio_lista"], p["prices"]["precio_efectivo"],
                p["prices"]["precio_transferencia"], p["prices"]["precio_mayorista"],
                p["prices"]["precio_mayorista_transferencia"],
                p["prices"]["cuotas"], p["prices"]["cuota_valor"],
                p["timestamp"], "|".join(p["images"])
            ])
    print(f"Saved {csv_path}")
    
    # Summary
    with_images = sum(1 for p in products if p["images"])
    total_images = sum(len(p["images"]) for p in products)
    with_lista = sum(1 for p in products if p["prices"]["precio_lista"])
    with_eff = sum(1 for p in products if p["prices"]["precio_efectivo"])
    with_trans = sum(1 for p in products if p["prices"]["precio_transferencia"])
    with_may = sum(1 for p in products if p["prices"]["precio_mayorista"])
    
    print(f"\nSummary:")
    print(f"  Products: {len(products)}")
    print(f"  With images: {with_images} ({total_images} total)")
    print(f"  With precio_lista: {with_lista}")
    print(f"  With precio_efectivo: {with_eff}")
    print(f"  With precio_transferencia: {with_trans}")
    print(f"  With precio_mayorista: {with_may}")
    
    cats = {}
    for p in products:
        cats[p['category']] = cats.get(p['category'], 0) + 1
    print(f"\nCategories:")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {c}: {n}")
    
    print(f"\nSample products:")
    for p in products[:8]:
        print(f"  {p['sku']}: {p['name'][:55]} - Lista: {p['prices']['precio_lista']}, Eff: {p['prices']['precio_efectivo']}, Imgs: {len(p['images'])}")


if __name__ == "__main__":
    main()