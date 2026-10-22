#!/usr/bin/env python3
"""
rotar_password_admin_prod.py - Rota la password del admin de Medusa en PRODUCCIÓN.

No necesita la dashboard: usa el CLI de Railway (túnel SSH a Postgres).

Uso:
  railway login                              # solo la primera vez (la sesión caduca)
  python3 scripts/rotar_password_admin_prod.py

Qué hace:
  1. Lee las variables del servicio Postgres (PGUSER / PGPASSWORD / PGDATABASE)
  2. Abre un túnel SSH a la base (railway connect --tunnel-only)
  3. Actualiza el hash scrypt de la password en provider_identity
  4. Verifica: login con la nueva (200) y con la vieja (401)

La password nueva sale de .env.production (MEDUSA_LOCAL_ADMIN_PASSWORD) o de
--password. Después hay que actualizarla en Vercel (MEDUSA_ADMIN_PASSWORD).
"""

import argparse
import base64
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env.production"
PROD_URL = os.getenv("MEDUSA_PROD_URL", "https://dankoshop-api-production.up.railway.app")
LOCAL_PORT = int(os.getenv("RAILWAY_TUNNEL_PORT", "5433"))
SERVICE = os.getenv("RAILWAY_PG_SERVICE", "Postgres")


def run(cmd, timeout=60, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)


def env_file_values():
    values = {}
    try:
        for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            values[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return values


def target_password(arg_password):
    if arg_password:
        return arg_password
    env = env_file_values()
    for key in ("MEDUSA_NUEVA_ADMIN_PASSWORD", "MEDUSA_LOCAL_ADMIN_PASSWORD"):
        if env.get(key):
            return env[key]
    if os.getenv("MEDUSA_NUEVA_ADMIN_PASSWORD"):
        return os.getenv("MEDUSA_NUEVA_ADMIN_PASSWORD")
    print("❌ No se encontró la password nueva.")
    print("   Pasala con --password '...' o ponela en .env.production como MEDUSA_NUEVA_ADMIN_PASSWORD")
    sys.exit(1)


def scrypt_hash(password):
    """Genera el hash con el mismo formato que Medusa (scrypt-kdf, logN=15, r=8, p=1)."""
    pwd_file = ROOT / ".tmp_pwd.txt"
    hash_file = ROOT / ".tmp_hash.txt"
    code = (
        "const scrypt=require('scrypt-kdf');"
        "const fs=require('fs');"
        "const pwd=fs.readFileSync(" + repr(str(pwd_file)) + ",'utf8').trim();"
        "scrypt.kdf(pwd,{logN:15,r:8,p:1}).then(h=>{"
        "fs.writeFileSync(" + repr(str(hash_file)) + ",h.toString('base64'));});"
    )
    pwd_file.write_text(password, encoding="utf-8")
    pwd_file.chmod(0o600)
    try:
        r = run(["node", "-e", code], timeout=60, cwd=str(ROOT / "medusa-backend"))
        if r.returncode != 0 or not hash_file.exists():
            raise RuntimeError(r.stderr[:300] or "node no pudo generar el hash")
        return hash_file.read_text(encoding="utf-8").strip()
    finally:
        for f in (pwd_file, hash_file):
            if f.exists():
                f.unlink()


def pg_vars():
    r = run(["railway", "variables", "--service", SERVICE, "--json"], timeout=60)
    if r.returncode != 0:
        print("❌ No se pudieron leer las variables de Railway.")
        print(r.stderr.strip()[:300] or r.stdout.strip()[:300])
        print("\n¿Te logueaste? Ejecutá:  railway login")
        sys.exit(1)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        print("❌ No se pudo interpretar la salida de `railway variables`")
        print(r.stdout[:300])
        sys.exit(1)


def wait_for_port(port, timeout=45):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=2):
                return True
        except OSError:
            time.sleep(1)
    return False


def main():
    parser = argparse.ArgumentParser(description="Rota la password del admin de Medusa en producción")
    parser.add_argument("--password", help="Password nueva (si no, se toma del .env.production)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Rotación de password del admin (PRODUCCIÓN)")
    print("=" * 60)

    who = run(["railway", "whoami"], timeout=30)
    if who.returncode != 0:
        print("❌ El CLI de Railway no está logueado. Ejecutá primero:  railway login")
        sys.exit(1)
    print(f"  Sesión Railway: {who.stdout.strip()}")

    password = target_password(args.password)
    print(f"  Password nueva: {'*' * len(password)} ({len(password)} caracteres)")

    vars_ = pg_vars()
    user = vars_.get("PGUSER") or "dankoshop"
    pgpass = vars_.get("PGPASSWORD") or ""
    dbname = vars_.get("PGDATABASE") or vars_.get("DATABASE") or "postgres"
    if not pgpass:
        print("❌ No se encontró PGPASSWORD del servicio Postgres")
        sys.exit(1)
    print(f"  Postgres: user={user} db={dbname}")

    print("\n  Abriendo túnel a Postgres...")
    tunnel = subprocess.Popen(
        ["railway", "connect", SERVICE, "--tunnel-only", "--port", str(LOCAL_PORT)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        if not wait_for_port(LOCAL_PORT):
            print("❌ El túnel no levantó. Logs:")
            out, err = tunnel.communicate(timeout=5)
            print((out or "")[:400], (err or "")[:400])
            sys.exit(1)
        print(f"  ✅ Túnel en 127.0.0.1:{LOCAL_PORT}")

        import psycopg2

        print("\n  Generando hash y actualizando...")
        new_hash = scrypt_hash(password)
        conn = psycopg2.connect(
            host="127.0.0.1", port=LOCAL_PORT, user=user,
            password=pgpass, dbname=dbname, connect_timeout=15,
            sslmode="require",
        )
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE provider_identity "
                    "SET provider_metadata = jsonb_set(provider_metadata, '{password}', to_jsonb(%s::text), true), "
                    "    updated_at = now() "
                    "WHERE provider = 'emailpass'",
                    (new_hash,),
                )
                print(f"  Filas actualizadas: {cur.rowcount}")
        conn.close()

        print("\n  Verificando...")
        email = os.getenv("MEDUSA_ADMIN_EMAIL") or env_file_values().get("MEDUSA_ADMIN_EMAIL", "admin@dankoshop.com")
        ok_new = requests.post(
            f"{PROD_URL}/auth/user/emailpass",
            json={"email": email, "password": password}, timeout=20,
        ).status_code == 200
        print(f"  Login con la NUEVA password: {'✅ 200 OK' if ok_new else '❌ falló'}")

        old = env_file_values().get("MEDUSA_ADMIN_PASSWORD", "")
        if old and old != password:
            st = requests.post(
                f"{PROD_URL}/auth/user/emailpass",
                json={"email": email, "password": old}, timeout=20,
            ).status_code
            print(f"  Login con la VIEJA password: {'✅ 401 (rechazada)' if st == 401 else f'⚠️  HTTP {st}'}")

        if ok_new:
            print("\n" + "=" * 60)
            print("  ✅ Password rotada en PRODUCCIÓN")
            print("=" * 60)
            print("  Falta actualizar Vercel:  MEDUSA_ADMIN_PASSWORD")
            print("  (y .env.production: MEDUSA_ADMIN_PASSWORD = la nueva)")
        else:
            print("\n❌ La password no quedó activa. Revisá el error arriba.")
            sys.exit(1)
    finally:
        tunnel.terminate()
        try:
            tunnel.wait(timeout=10)
        except subprocess.TimeoutExpired:
            tunnel.kill()


if __name__ == "__main__":
    main()
