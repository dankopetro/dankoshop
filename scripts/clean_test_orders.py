#!/usr/bin/env python3
"""
clean_test_orders.py - Borra pedidos de prueba de data/pedidos.json (GitHub).

Sin argumentos borra todos los pedidos cuyo id empiece con "TEST-".
Los pedidos reales no se tocan.

Usage:
  GITHUB_TOKEN=<token> python3 scripts/clean_test_orders.py
      Borra todos los pedidos TEST-*

  GITHUB_TOKEN=<token> python3 scripts/clean_test_orders.py --id DK-ABC123
      Borra solo ese pedido (compras de prueba hechas desde la web)

  GITHUB_TOKEN=<token> python3 scripts/clean_test_orders.py --email prueba@dankoshop.com.ar
      Borra todos los pedidos con ese email

  GITHUB_TOKEN=<token> python3 scripts/clean_test_orders.py --dry-run
      Muestra qué se borraría, sin subir nada

  GITHUB_TOKEN=<token> python3 scripts/clean_test_orders.py --list
      Lista todos los pedidos (sin borrar nada)

El token necesita permiso Contents: Read and Write sobre el repo.
(Es el mismo GITHUB_TOKEN que usa la app en Vercel.)
"""

import argparse
import base64
import json
import os
import sys

import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "dankopetro/dankoshop")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
ORDERS_PATH = "data/pedidos.json"


def get_current_file():
    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{ORDERS_PATH}?ref={GITHUB_BRANCH}",
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
        timeout=15,
    )
    if r.status_code == 404:
        return None
    r.raise_for_status()
    body = r.json()
    content = base64.b64decode(body["content"]).decode("utf-8")
    return {"sha": body["sha"], "data": json.loads(content or "[]")}


def is_test_order(order):
    return str(order.get("id", "")).startswith("TEST-")


def order_email(order):
    return str((order.get("cliente") or {}).get("email", "")).strip().lower()


def describe(order):
    cliente = order.get("cliente") or {}
    return (
        f"{order.get('id')} | {order.get('fecha', '?')} | "
        f"{cliente.get('nombre', '?')} | total={order.get('total', '?')}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Borra pedidos de prueba de data/pedidos.json en GitHub."
    )
    parser.add_argument("--id", action="append", default=[], metavar="ID",
                        help="Borrar pedido(s) con este id (repetible)")
    parser.add_argument("--email", metavar="EMAIL",
                        help="Borrar todos los pedidos con este email de cliente")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostrar qué se borraría, sin subir cambios")
    parser.add_argument("--list", action="store_true", dest="list_all",
                        help="Listar todos los pedidos y salir")
    args = parser.parse_args()

    if not GITHUB_TOKEN:
        print("❌ Falta GITHUB_TOKEN en el entorno.")
        print("   Ejemplo: GITHUB_TOKEN=<token> python3 scripts/clean_test_orders.py")
        sys.exit(1)

    current = get_current_file()
    if current is None:
        print("❌ No se encontró data/pedidos.json en GitHub.")
        sys.exit(1)

    orders = current["data"] if isinstance(current["data"], list) else []

    if args.list_all:
        print(f"Total pedidos: {len(orders)}")
        for o in orders:
            tag = "TEST" if is_test_order(o) else "REAL"
            print(f"  [{tag}] {describe(o)}")
        return

    wanted_ids = {i.strip() for i in args.id if i.strip()}

    if wanted_ids or args.email:
        selected = []
        for o in orders:
            if wanted_ids and str(o.get("id")) in wanted_ids:
                selected.append(o)
            elif args.email and order_email(o) == args.email.strip().lower():
                selected.append(o)
        if not selected:
            print("❌ No se encontró ningún pedido con ese criterio. No se subió nada.")
            sys.exit(1)
    else:
        selected = [o for o in orders if is_test_order(o)]

    selected_ids = {str(o.get("id")) for o in selected}
    remaining = [o for o in orders if str(o.get("id")) not in selected_ids]

    print(f"Total pedidos: {len(orders)} | A borrar: {len(selected)} | Quedan: {len(remaining)}")
    for o in selected:
        print(f"  🗑️  {describe(o)}")

    if not selected:
        print("✅ No hay pedidos de prueba. Nada que borrar.")
        return

    if args.dry_run:
        print("\n--dry-run: no se subió nada.")
        return

    content = json.dumps(remaining, ensure_ascii=False, indent=2) + "\n"
    put = requests.put(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{ORDERS_PATH}",
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Content-Type": "application/json"},
        json={
            "message": f"Limpiar {len(selected)} pedido(s) de prueba",
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "sha": current["sha"],
            "branch": GITHUB_BRANCH,
        },
        timeout=30,
    )
    if not put.ok:
        print(f"❌ Error al subir: {put.status_code} {put.text[:300]}")
        sys.exit(1)

    print(f"\n✅ Borrados {len(selected)} pedido(s). Quedan {len(remaining)}.")


if __name__ == "__main__":
    main()
