#!/usr/bin/env python3
"""
sync_both.py - Excel → Medusa sync (local + producción)

Sincroniza precios, metadata, categorías, inventario y canales de venta
a AMBOS Medusa (local y Railway) en un solo comando.

Health check automático: si uno está caído, avisa y sincroniza al disponible.

Usage:
  python3 scripts/sync_both.py [archivo.xlsx]
  python3 scripts/sync_both.py --prod-only [archivo.xlsx]
  python3 scripts/sync_both.py --local-only [archivo.xlsx]

Env vars:
  MEDUSA_LOCAL_URL     (default: http://localhost:9100)
  MEDUSA_PROD_URL      (default: https://dankoshop-api-production.up.railway.app)
  MEDUSA_ADMIN_EMAIL   (default: admin@dankoshop.com)
  MEDUSA_ADMIN_PASSWORD (default: ***PASSWORD_ROTADA***)
"""

import os
import sys
import json
import math
import argparse
import subprocess
import requests
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEFAULT_LOCAL_URL = "http://localhost:9100"
DEFAULT_PROD_URL = "https://dankoshop-api-production.up.railway.app"
DEFAULT_EMAIL = "admin@dankoshop.com"
DEFAULT_PASSWORD = "***PASSWORD_ROTADA***"

ALLOWED_METADATA_KEYS = {
    "precio_lista", "precio_efectivo", "precio_mayorista",
    "cuota_valor_3", "cuota_valor_6", "cuota_valor_12", "envio_grande",
}


# ---------------------------------------------------------------------------
# Shared utility functions (Medusa-agnostic)
# ---------------------------------------------------------------------------
def parse_price(val):
    if val is None:
        return None
    try:
        return float(str(val).replace("$", "").replace(",", "").strip())
    except Exception:
        return None


def calc_metadata(mayorista):
    if mayorista is None:
        return {}
    m = float(mayorista)
    lista = int(round(m * 1.25))
    efectivo = int(round(m * 1.15))
    cuota_3 = int(round(lista / 3))
    cuota_6 = int(round(lista / 6))
    tasa = 0.12
    factor = ((1 + tasa) ** 12 - 1) / (tasa * (1 + tasa) ** 12)
    cuota_12 = int(round(lista / factor))
    return {
        "precio_lista": lista,
        "precio_efectivo": efectivo,
        "precio_mayorista": int(round(m)),
        "cuota_valor_3": cuota_3,
        "cuota_valor_6": cuota_6,
        "cuota_valor_12": cuota_12,
    }


def metadata_payload(metadata, envio_grande, existing_metadata):
    payload = dict(metadata)
    if envio_grande:
        payload["envio_grande"] = True
    for key in (existing_metadata or {}):
        if key not in ALLOWED_METADATA_KEYS or (key == "envio_grande" and not envio_grande):
            payload[key] = ""
    return payload


def slugify(value):
    import unicodedata
    s = unicodedata.normalize("NFD", value)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = "".join(c if c.isalnum() else "-" for c in s)
    return s.strip("-")[:200] or "producto"


def read_excel(excel_path):
    import openpyxl
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb["Nuevos Sync"] if "Nuevos Sync" in wb.sheetnames else wb.active
    is_sync_sheet = ws.title == "Nuevos Sync"
    products = []
    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        sku = str(row[0]).strip() if row[0] else None
        name = str(row[1]).strip() if row[1] else None
        if not sku or not name:
            continue
        if len(row) <= 5:
            print(f"  WARN row {idx}: fila incompleta ({len(row)} columnas), se saltea")
            continue
        # Nuevos Sync: col C (index 2) = Precio Compra Mayorista
        # Maestro: col F (index 5) = Precio Venta Bruto (formula =K*1.072)
        #          col K (index 10) = Precio Ingresado (source of truth)
        # If F is empty (uncalculated formula), fall back to K
        if is_sync_sheet:
            precio_mayorista_raw = row[2]
        else:
            precio_mayorista_raw = row[5]
            if precio_mayorista_raw is None and len(row) > 10:
                precio_mayorista_raw = row[10]  # col K: Precio Ingresado
        envio_grande_raw = row[6] if len(row) > 6 else None

        inventario_raw = row[7] if len(row) > 7 else None
        canales_raw = row[8] if len(row) > 8 else None
        if is_sync_sheet:
            categoria_raw = row[7] if len(row) > 7 else None
            inventario_raw = row[8] if len(row) > 8 else None
            canales_raw = row[9] if len(row) > 9 else None
        else:
            categoria_raw = ""

        mayorista = parse_price(precio_mayorista_raw)
        if mayorista is None:
            print(f"  WARN row {idx}: SKU {sku} no tiene precio mayorista, se saltea")
            continue
        precio_lista = int(round(mayorista * 1.25))

        inventario = None
        if inventario_raw is not None:
            try:
                inventario = int(float(str(inventario_raw)))
            except (TypeError, ValueError):
                inventario = None

        products.append({
            "row": idx,
            "sku": sku,
            "name": name,
            "precio_lista": precio_lista,
            "precio_mayorista": mayorista,
            "envio_grande": str(envio_grande_raw).strip().lower() in ("true", "1", "sí", "si", "yes") if envio_grande_raw else False,
            "categoria": str(categoria_raw).strip() if categoria_raw else "",
            "inventario": inventario,
            "canales": str(canales_raw).strip() if canales_raw else "",
        })
    return products


# ---------------------------------------------------------------------------
# MedusaClient - encapsula toda la lógica de conexión/sync por instancia
# ---------------------------------------------------------------------------
class MedusaClient:
    def __init__(self, name, url, email, password):
        self.name = name
        self.url = url
        self.email = email
        self.password = password
        self._token = None
        self._category_cache = {}
        self._stock_location_id = None
        self.online = False

    def health_check(self):
        try:
            r = requests.get(f"{self.url}/health", timeout=10)
            self.online = r.status_code == 200
        except Exception:
            self.online = False
        return self.online

    def login(self):
        try:
            r = requests.post(
                f"{self.url}/auth/user/emailpass",
                json={"email": self.email, "password": self.password},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            if r.status_code == 200:
                self._token = r.json().get("token")
                return True
            print(f"  AUTH FAILED ({r.status_code}): {r.text[:200]}")
        except Exception as e:
            print(f"  AUTH ERROR: {e}")
        return False

    def api(self, method, endpoint, data=None, params=None):
        if not self._token:
            raise RuntimeError("No auth token")
        r = requests.request(
            method,
            f"{self.url}{endpoint}",
            headers={"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"},
            json=data,
            params=params,
            timeout=30,
        )
        return r

    # -- Region --
    def ensure_region(self):
        r = self.api("GET", "/admin/regions", params={"limit": 100})
        if r.status_code == 200:
            for reg in r.json().get("regions", []):
                if reg.get("currency_code") == "ars":
                    return reg["id"]
        r = self.api("POST", "/admin/regions", data={
            "name": "Argentina", "currency_code": "ars",
            "countries": ["ar"], "payment_providers": [], "metadata": {},
        })
        if r.status_code == 200:
            return r.json()["region"]["id"]
        return None

    # -- Categories --
    def _fetch_all_categories(self):
        if self._category_cache:
            return self._category_cache
        offset = 0
        while True:
            r = self.api("GET", "/admin/product-categories", params={"limit": 100, "offset": offset})
            if r.status_code != 200:
                break
            for cat in r.json().get("product_categories", []):
                self._category_cache[cat["name"].strip().upper()] = cat["id"]
            if len(r.json().get("product_categories", [])) < 100:
                break
            offset += 100
        return self._category_cache

    def resolve_category(self, category_name):
        if not category_name or not category_name.strip():
            return None
        cats = self._fetch_all_categories()
        cat_id = cats.get(category_name.strip().upper())
        if cat_id:
            return cat_id
        r = self.api("POST", "/admin/product-categories", data={"name": category_name.strip()})
        if r.status_code == 200:
            new_id = r.json().get("product_category", {}).get("id")
            if new_id:
                cats[category_name.strip().upper()] = new_id
                print(f"    Categoría creada: {category_name} → {new_id}")
                return new_id
        print(f"    WARN: no se pudo crear categoría '{category_name}'")
        return None

    # -- Stock location --
    def get_stock_location(self):
        if self._stock_location_id:
            return self._stock_location_id
        r = self.api("GET", "/admin/stock-locations", params={"limit": 10})
        if r.status_code == 200:
            locs = r.json().get("stock_locations", [])
            if locs:
                self._stock_location_id = locs[0]["id"]
                return self._stock_location_id
        return None

    # -- Inventory --
    def set_inventory(self, variant_id, sku, quantity, product_id=None):
        if quantity is None or quantity <= 0:
            return "skip"

        r = self.api("GET", "/admin/inventory-items", params={"q": sku})
        inv_item_id = None
        if r.status_code == 200:
            for item in r.json().get("inventory_items", []):
                if item.get("sku") == sku:
                    inv_item_id = item["id"]
                    break

        if inv_item_id:
            loc_id = self.get_stock_location()
            if loc_id:
                r_check = self.api("GET", f"/admin/inventory-items/{inv_item_id}/location-levels")
                if r_check.status_code == 200:
                    levels = r_check.json().get("inventory_levels", [])
                    current_stock = sum(l.get("stocked_quantity", 0) for l in levels)
                    if current_stock > 0:
                        return "skip"
        else:
            r2 = self.api("POST", "/admin/inventory-items", data={"sku": sku})
            if r2.status_code != 200:
                print(f"    INV CREATE FAILED: {r2.status_code} {r2.text[:200]}")
                return "error"
            inv_item_id = r2.json().get("inventory_item", {}).get("id")
            if not inv_item_id:
                print(f"    INV CREATE NO ID: {r2.text[:200]}")
                return "error"
            if product_id:
                r3 = self.api("POST", f"/admin/products/{product_id}/variants/{variant_id}/inventory-items",
                              data={"inventory_item_id": inv_item_id, "required_quantity": 1})
                if r3.status_code != 200:
                    print(f"    INV LINK FAILED: {r3.status_code} {r3.text[:200]}")
                    return "error"

        loc_id = self.get_stock_location()
        if not loc_id:
            return "error"

        r4 = self.api("POST", f"/admin/inventory-items/{inv_item_id}/location-levels", data={
            "stocked_quantity": quantity,
            "location_id": loc_id,
        })
        if r4.status_code != 200:
            r_levels = self.api("GET", f"/admin/inventory-items/{inv_item_id}/location-levels")
            if r_levels.status_code == 200:
                for lvl in r_levels.json().get("inventory_levels", []):
                    if lvl.get("location_id") == loc_id:
                        self.api("DELETE", f"/admin/inventory-items/{inv_item_id}/location-levels/{lvl['id']}")
            r4 = self.api("POST", f"/admin/inventory-items/{inv_item_id}/location-levels", data={
                "stocked_quantity": quantity,
                "location_id": loc_id,
            })
        return "set" if r4.status_code == 200 else "error"

    def remove_inventory_if_empty(self, sku):
        r = self.api("GET", "/admin/inventory-items", params={"q": sku})
        if r.status_code != 200:
            return
        for item in r.json().get("inventory_items", []):
            if item.get("sku") == sku:
                stock = sum(l.get("stocked_quantity", 0) for l in item.get("location_levels", []))
                if stock == 0:
                    self.api("DELETE", f"/admin/inventory-items/{item['id']}")
                    print(f"    Inventario: eliminado item vacío (Medusa lo creó automático)")
                break

    # -- Sales channels --
    def get_or_create_sales_channel(self, name="DankoShop"):
        r = self.api("GET", "/admin/sales-channels", params={"limit": 100})
        if r.status_code == 200:
            for ch in r.json().get("sales_channels", []):
                if ch.get("name", "").strip().lower() == name.strip().lower():
                    return ch["id"]
        r2 = self.api("POST", "/admin/sales-channels", data={"name": name, "is_default": True})
        if r2.status_code == 200:
            return r2.json().get("sales_channel", {}).get("id")
        return None

    def link_product_to_channels(self, product_id, channel_names):
        if not channel_names:
            return
        default_ch = self.get_or_create_sales_channel()
        ch_ids = set()
        if default_ch:
            ch_ids.add(default_ch)
        for name in [n.strip() for n in channel_names.split(",") if n.strip()]:
            ch_id = self.get_or_create_sales_channel(name)
            if ch_id:
                ch_ids.add(ch_id)
        if not ch_ids:
            return
        r = self.api("POST", f"/admin/products/{product_id}", data={
            "sales_channels": [{"id": cid} for cid in ch_ids]
        })
        if r.status_code != 200:
            print(f"    WARN: no se pudo vincular canales de venta")

    # -- Products --
    def find_product(self, sku):
        r = self.api("GET", "/admin/products", params={"q": sku, "limit": 500})
        if r.status_code != 200:
            return None
        for p in r.json().get("products", []):
            for v in p.get("variants", []):
                if v.get("sku") == sku:
                    return p
        return None

    def create_product(self, product, region_id):
        metadata = calc_metadata(product["precio_mayorista"])
        if product["envio_grande"]:
            metadata["envio_grande"] = True

        payload = {
            "title": product["name"],
            "handle": slugify(product["sku"]),
            "status": "published",
            "options": [{"title": "Default", "values": ["Default"]}],
            "variants": [{
                "title": "Default",
                "sku": product["sku"],
                "options": {"Default": "Default"},
                "prices": [{"amount": product["precio_lista"], "currency_code": "ars", "region_id": region_id}] if product["precio_lista"] > 0 else [],
            }],
            "metadata": metadata,
        }

        cat_name = product.get("categoria", "")
        cat_id = self.resolve_category(cat_name)
        if cat_id:
            payload["categories"] = [{"id": cat_id}]

        ch_names = product.get("canales", "")

        r = self.api("POST", "/admin/products", data=payload)
        if r.status_code == 200:
            new_id = r.json()["product"]["id"]
            if ch_names:
                self.link_product_to_channels(new_id, ch_names)
            inv = product.get("inventario")
            created_variants = r.json().get("product", {}).get("variants", [])
            if inv is not None and created_variants:
                vid = created_variants[0]["id"]
                inv_result = self.set_inventory(vid, product["sku"], inv, product_id=new_id)
                if inv_result == "set":
                    print(f"    Inventario: {inv} unidades")
            else:
                self.remove_inventory_if_empty(product["sku"])
            return new_id
        print(f"    CREATE FAILED: {r.status_code} {r.text[:200]}")
        return None

    def update_product(self, product, existing, region_id):
        product_id = existing["id"]
        metadata = calc_metadata(product["precio_mayorista"])
        payload = metadata_payload(metadata, product["envio_grande"], existing.get("metadata"))

        actual = (existing.get("metadata") or {}).get("precio_mayorista")
        try:
            actual = int(round(float(actual)))
        except (TypeError, ValueError):
            actual = None
        nuevo = int(round(float(product["precio_mayorista"])))
        metadata_changed = any(
            (value == "" and key in (existing.get("metadata") or {}))
            or (value != "" and (existing.get("metadata") or {}).get(key) != value)
            for key, value in payload.items()
        )
        if actual == nuevo and not metadata_changed:
            inv = product.get("inventario")
            if inv is not None and existing.get("variants"):
                vid = existing["variants"][0]["id"]
                inv_result = self.set_inventory(vid, product["sku"], inv, product_id=product_id)
                if inv_result == "set":
                    print(f"    Inventario: {inv} unidades")
                elif inv_result == "skip" and inv and inv > 0:
                    print(f"    Inventario: ya tiene stock, sin cambios")
            elif inv is None or (inv is not None and inv <= 0):
                self.remove_inventory_if_empty(product["sku"])
            return "skip"

        r = self.api("POST", f"/admin/products/{product_id}", data={"metadata": payload})
        if r.status_code != 200:
            print(f"    UPDATE FAILED: {r.status_code} {r.text[:200]}")
            return False

        if existing.get("variants"):
            vid = existing["variants"][0]["id"]
            r2 = self.api("POST", f"/admin/products/{product_id}/variants/{vid}", data={
                "prices": [{"amount": product["precio_lista"], "currency_code": "ars", "region_id": region_id}],
            })
            if r2.status_code != 200:
                print(f"    PRICE UPDATE FAILED: {r2.status_code}")

        inv = product.get("inventario")
        if inv is not None and existing.get("variants"):
            vid = existing["variants"][0]["id"]
            inv_result = self.set_inventory(vid, product["sku"], inv, product_id=product_id)
            if inv_result == "set":
                print(f"    Inventario: {inv} unidades")
            elif inv_result == "skip" and inv and inv > 0:
                print(f"    Inventario: ya tiene stock, sin cambios")
        elif inv is None or (inv is not None and inv <= 0):
            self.remove_inventory_if_empty(product["sku"])

        return product_id

    # -- Sync orchestrator --
    def sync(self, products):
        region_id = self.ensure_region()
        if not region_id:
            print(f"  ❌ No se pudo asegurar región ARS en {self.name}")
            return {"created": 0, "updated": 0, "skipped": 0, "failed": 0}

        created = updated = skipped = failed = 0

        for i, p in enumerate(products, 1):
            print(f"  [{i}/{len(products)}] {p['sku']}: {p['name'][:50]}")
            existing = self.find_product(p["sku"])

            if existing:
                pid = self.update_product(p, existing, region_id)
                if pid == "skip":
                    skipped += 1
                    print(f"    Sin cambios")
                elif pid:
                    updated += 1
                    print(f"    Precios actualizados")
                else:
                    failed += 1
            else:
                pid = self.create_product(p, region_id)
                if pid:
                    created += 1
                    print(f"    Creado")
                else:
                    failed += 1

        return {"created": created, "updated": updated, "skipped": skipped, "failed": failed}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Excel → Medusa sync (local + producción)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python3 scripts/sync_both.py
  python3 scripts/sync_both.py excel/Productos_Maestro.xlsx
  python3 scripts/sync_both.py --prod-only
  python3 scripts/sync_both.py --local-only excel/Nuevos_14_15_Sync.xlsx
        """,
    )
    parser.add_argument("excel", nargs="?", default=None, help="Archivo Excel (default: Productos_Maestro.xlsx)")
    parser.add_argument("--prod-only", action="store_true", help="Solo sincronizar a producción (Railway)")
    parser.add_argument("--local-only", action="store_true", help="Solo sincronizar a local (localhost:9100)")
    return parser.parse_args()


def main():
    args = parse_args()

    # Resolve Excel path
    default_excel = Path(__file__).resolve().parent.parent / "excel" / "Productos_Maestro.xlsx"
    excel_path = Path(args.excel) if args.excel else default_excel

    if not excel_path.exists():
        print(f"❌ Excel no encontrado: {excel_path}")
        sys.exit(1)

    # Resolve URLs
    local_url = os.getenv("MEDUSA_LOCAL_URL", DEFAULT_LOCAL_URL)
    prod_url = os.getenv("MEDUSA_PROD_URL", DEFAULT_PROD_URL)
    email = os.getenv("MEDUSA_ADMIN_EMAIL", DEFAULT_EMAIL)
    password = os.getenv("MEDUSA_ADMIN_PASSWORD", DEFAULT_PASSWORD)

    # Create clients
    prod_client = MedusaClient("PRODUCCIÓN", prod_url, email, password)
    local_client = MedusaClient("LOCAL", local_url, email, password)

    # Auto-start local Medusa if needed
    local_was_running = False
    local_started_by_us = False
    medusa_local_sh = Path(__file__).resolve().parent / "medusa-local.sh"

    if not args.prod_only and medusa_local_sh.exists():
        # Check if local is already running
        try:
            r = requests.get(f"{local_url}/health", timeout=5)
            local_was_running = r.status_code == 200
        except Exception:
            local_was_running = False

        if not local_was_running:
            print("\n🚀 Levantando Medusa local...")
            try:
                result = subprocess.run(
                    [str(medusa_local_sh), "start"],
                    capture_output=True, text=True, timeout=60,
                )
                if result.returncode == 0:
                    local_started_by_us = True
                    print("   ✅ Local levantado")
                else:
                    print(f"   ⚠️  No se pudo levantar local: {result.stderr[:200]}")
            except Exception as e:
                print(f"   ⚠️  Error levantando local: {e}")

    # Health check both
    print("=" * 60)
    print("  Excel → Medusa Sync (local + producción)")
    print(f"  Excel: {excel_path}")
    print("=" * 60)

    print("\n🔍 Health check...")
    prod_ok = prod_client.health_check()
    local_ok = local_client.health_check()

    if not args.local_only:
        status = "✅ Online" if prod_ok else "❌ OFFLINE"
        print(f"  PRODUCCIÓN ({prod_url}): {status}")

    if not args.prod_only:
        status = "✅ Online" if local_ok else "❌ OFFLINE"
        print(f"  LOCAL ({local_url}): {status}")

    # Determine which to sync
    do_prod = prod_ok and not args.local_only
    do_local = local_ok and not args.prod_only

    if not do_prod and not do_local:
        print("\n❌ Ninguna Medusa disponible. No se puede sincronizar.")
        if not prod_ok and not args.local_only:
            print(f"  → Producción caída: {prod_url}")
        if not local_ok and not args.prod_only:
            print(f"  → Local caído: {local_url}")
        sys.exit(1)

    if not prod_ok and not args.local_only:
        print(f"\n⚠️  PRODUCCIÓN OFFLINE — sync pendiente cuando se levante")
    if not local_ok and not args.prod_only:
        print(f"\n⚠️  LOCAL OFFLINE — sync pendiente cuando se levante")

    # Read Excel once
    print(f"\n📖 Leyendo Excel...")
    products = read_excel(excel_path)
    print(f"   {len(products)} productos encontrados")

    # Login to available clients
    if do_prod:
        if not prod_client.login():
            print("\n❌ Login a producción falló")
            do_prod = False
    if do_local:
        if not local_client.login():
            print("\n❌ Login a local falló")
            do_local = False

    if not do_prod and not do_local:
        print("\n❌ No se pudo autenticar en ninguna Medusa")
        sys.exit(1)

    # Sync production first
    results_prod = None
    if do_prod:
        print(f"\n{'═'*60}")
        print(f"  📦 PRODUCCIÓN (Railway)")
        print(f"{'═'*60}")
        results_prod = prod_client.sync(products)

    # Sync local
    results_local = None
    if do_local:
        print(f"\n{'═'*60}")
        print(f"  🏠 LOCAL (localhost:9100)")
        print(f"{'═'*60}")
        results_local = local_client.sync(products)

    # Summary
    print(f"\n{'═'*60}")
    print(f"  📊 RESUMEN")
    print(f"{'═'*60}")
    print(f"  Archivo: {excel_path.name} ({len(products)} productos)")
    print()

    if results_prod:
        r = results_prod
        print(f"  PRODUCCIÓN:")
        print(f"    Creados: {r['created']} | Actualizados: {r['updated']} | Sin cambios: {r['skipped']} | Errores: {r['failed']}")
    elif not args.local_only:
        print(f"  PRODUCCIÓN: ⚠️ OFFLINE (pendiente)")

    if results_local:
        r = results_local
        print(f"  LOCAL:")
        print(f"    Creados: {r['created']} | Actualizados: {r['updated']} | Sin cambios: {r['skipped']} | Errores: {r['failed']}")
    elif not args.prod_only:
        print(f"  LOCAL: ⚠️ OFFLINE (pendiente)")

    print(f"{'═'*60}")

    # Auto-stop local Medusa if we started it
    if local_started_by_us and not local_was_running:
        print("\n🛑 Deteniendo Medusa local (lo había levantado yo)...")
        try:
            subprocess.run(
                [str(medusa_local_sh), "stop"],
                capture_output=True, text=True, timeout=30,
            )
            print("   ✅ Local detenido")
        except Exception as e:
            print(f"   ⚠️  Error deteniendo local: {e}")


if __name__ == "__main__":
    main()
