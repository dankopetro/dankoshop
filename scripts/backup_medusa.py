#!/usr/bin/env python3
"""
Backup de Medusa vía Admin API.
Exporta productos, colecciones, categorías, inventario, ubicaciones y canales de venta.

Uso:
  python3 scripts/backup_medusa.py

Las credenciales salen de .env.production vía medusa_auth.py
(MEDUSA_ADMIN_EMAIL / MEDUSA_ADMIN_PASSWORD). MEDUSA_BACKEND_URL es
opcional: por defecto usa el backend de producción.
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from medusa_auth import get_admin_credentials
from datetime import datetime

MEDUSA_URL = os.environ.get("MEDUSA_BACKEND_URL", "https://dankoshop-api-production.up.railway.app")
EMAIL, PASSWORD = get_admin_credentials()

BACKUP_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)
def login():
    r = requests.post(f"{MEDUSA_URL}/auth/user/emailpass", json={"email": EMAIL, "password": PASSWORD}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]
def get_all(token, endpoint, params=None, key=None):
    headers = {"Authorization": f"Bearer {token}"}
    all_items = []
    offset = 0
    while True:
        p = {"limit": 100, "offset": offset}
        if params:
            p.update(params)
        r = requests.get(f"{MEDUSA_URL}{endpoint}", headers=headers, params=p, timeout=15)
        r.raise_for_status()
        data = r.json()
        if key:
            items = data.get(key, [])
        else:
            items = data.get("products", data.get("collections", data.get("product_categories", data.get("shipping_options", []))))
        if not items:
            break
        all_items.extend(items)
        if len(items) < 100:
            break
        offset += 100
        time.sleep(0.3)
    return all_items
def backup():
    print(f"Conectando a {MEDUSA_URL}...")
    token = login()
    print("OK, autenticado.\n")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_data = {"timestamp": ts, "source": MEDUSA_URL}

    print("Exportando productos...")
    products = get_all(token, "/admin/products")
    backup_data["products"] = products
    print(f"  {len(products)} productos")

    print("Exportando colecciones...")
    collections = get_all(token, "/admin/collections")
    backup_data["collections"] = collections
    print(f"  {len(collections)} colecciones")

    print("Exportando categorías...")
    categories = get_all(token, "/admin/product-categories")
    backup_data["categories"] = categories
    print(f"  {len(categories)} categorías")

    print("Exportando inventario...")
    inventory = get_all(token, "/admin/inventory-items", key="inventory_items")
    backup_data["inventory_items"] = inventory
    print(f"  {len(inventory)} items de inventario")

    print("Exportando ubicaciones de stock...")
    locations = get_all(token, "/admin/stock-locations", key="stock_locations")
    backup_data["stock_locations"] = locations
    print(f"  {len(locations)} ubicaciones")

    print("Exportando canales de venta...")
    channels = get_all(token, "/admin/sales-channels", key="sales_channels")
    backup_data["sales_channels"] = channels
    print(f"  {len(channels)} canales de venta")

    filename = f"backup_{ts}.json"
    filepath = os.path.join(BACKUP_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)

    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"\nBackup guardado: {filepath} ({size_mb:.1f} MB)")

    # Sincronizar imágenes de Cloudinary a Medusa local después del backup
    print("\n" + "=" * 60)
    print("  Sincronizando imágenes a Medusa local...")
    print("=" * 60)
    # Health check: verificar si Medusa local está arriba antes de sincronizar imágenes
    local_url = os.environ.get("MEDUSA_LOCAL_URL", "http://localhost:9100")
    local_was_running = False
    try:
        r = requests.get(f"{local_url}/health", timeout=5)
        local_was_running = r.status_code == 200
    except Exception:
        local_was_running = False

    # Si no está corriendo, levantarla
    local_started_by_us = False
    if not local_was_running:
        print(f"  🚀 Levantando Medusa local ({local_url})...")
        try:
            subprocess.run(
                [str(Path(__file__).resolve().parent / "medusa-local.sh"), "start"],
                capture_output=True, text=True, timeout=60,
                cwd=str(Path(__file__).resolve().parent.parent),
            )
            local_started_by_us = True
            print("  ✅ Medusa local levantada")
        except Exception as e:
            print(f"  ⚠️  No se pudo levantar Medusa local: {e}")
            return filepath

    # Verificar que esté arriba antes de continuar
    local_ok = False
    try:
        r = requests.get(f"{local_url}/health", timeout=5)
        local_ok = r.status_code == 200
    except Exception:
        local_ok = False

    if not local_ok:
        if local_started_by_us:
            print("\n🛑 Deteniendo Medusa local (falló el arranque)...")
            try:
                subprocess.run(
                    [str(Path(__file__).resolve().parent / "medusa-local.sh"), "stop"],
                    capture_output=True, text=True, timeout=30,
                    cwd=str(Path(__file__).resolve().parent.parent),
                )
            except Exception:
                pass
        print("  ⚠️  Medusa local no está disponible. Se omite sincronización de imágenes.")
        return filepath

    # Purgar productos locales huérfanos (en local pero no en producción)
    print("\n" + "=" * 60)
    print("  Purgando productos huérfanos de local...")
    print("=" * 60)
    try:
        lr = requests.post(f"{local_url}/auth/user/emailpass",
                           json={"email": EMAIL, "password": PASSWORD}, timeout=10)
        lr.raise_for_status()
        local_headers = {"Authorization": f"Bearer {lr.json()['token']}"}

        # Set de SKUs de producción (ya descargados para el backup)
        prod_skus = set()
        for p in backup_data.get("products", []):
            for v in p.get("variants", []):
                sku = (v.get("sku") or "").strip()
                if sku:
                    prod_skus.add(sku)
        prod_count = len(backup_data.get("products", []))

        # Todos los productos activos de local
        local_products = []
        offset = 0
        while True:
            rr = requests.get(f"{local_url}/admin/products", headers=local_headers,
                              params={"limit": 100, "offset": offset}, timeout=30)
            rr.raise_for_status()
            data = rr.json()
            batch = data.get("products", [])
            local_products.extend(batch)
            count = data.get("count", 0)
            offset += 100
            if not batch or offset >= count:
                break
        local_count = len(local_products)

        # Guardia de seguridad: si producción está muy vacía, no purgar
        if prod_count > 0 and prod_count < 0.8 * local_count:
            print(f"  ⚠️  Guardia: producción {prod_count} productos vs local {local_count}.")
            print(f"     Diferencia muy grande — se omite el purgado por seguridad.")
        else:
            orphans = []
            for p in local_products:
                local_skus = [(v.get("sku") or "").strip() for v in p.get("variants", [])]
                local_skus = [s for s in local_skus if s]
                # Si el producto tiene al menos un SKU presente en producción → conservar
                if local_skus and not any(s in prod_skus for s in local_skus):
                    orphans.append(p)
                # Productos sin ningún SKU se conservan por seguridad

            if not orphans:
                print(f"  ✅ Sin huérfanos. Local es espejo de producción ({local_count} productos).")
            else:
                deleted = 0
                for p in orphans:
                    pid = p.get("id")
                    title = (p.get("title") or "")[:50]
                    skus = ",".join((v.get("sku") or "") for v in p.get("variants", []))
                    dr = requests.delete(f"{local_url}/admin/products/{pid}",
                                         headers=local_headers, timeout=30)
                    if dr.status_code == 200:
                        print(f"    🗑️  Borrado {skus}: {title}")
                        deleted += 1
                    else:
                        print(f"    ❌ Error borrando {skus} ({dr.status_code})")
                print(f"  📊 Purgado: borrados={deleted} | conservados={local_count - len(orphans)}")
    except Exception as e:
        print(f"  ⚠️  Error en purgado de huérfanos: {e}")

    sync_script = Path(__file__).resolve().parent / "sync_imagenes_a_medusa_local.py"
    if sync_script.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(sync_script)],
                capture_output=True, text=True, timeout=300,
            )
            print(result.stdout)
            if result.returncode != 0:
                print(f"  WARN: sync de imágenes terminó con código {result.returncode}")
                print(result.stderr[:500])
            else:
                print("  ✅ Imágenes sincronizadas a Medusa local")
        except Exception as e:
            print(f"  ⚠️  Error ejecutando sync de imágenes: {e}")
    else:
        print(f"  WARN: {sync_script} no existe, se omite sincronización de imágenes")

    # Auto-stop: si levantamos local, lo cerramos al finalizar
    if local_started_by_us:
        print("\n🛑 Deteniendo Medusa local (lo levantó el backup)...")
        try:
            subprocess.run(
                [str(Path(__file__).resolve().parent / "medusa-local.sh"), "stop"],
                capture_output=True, text=True, timeout=30,
                cwd=str(Path(__file__).resolve().parent.parent),
            )
            print("   ✅ Medusa local detenida")
        except Exception as e:
            print(f"   ⚠️  Error deteniendo Medusa local: {e}")

    return filepath


if __name__ == "__main__":
    backup()
