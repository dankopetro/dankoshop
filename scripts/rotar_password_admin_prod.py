#!/usr/bin/env python3
"""
rotar_password_admin_prod.py - Rota la password del admin de Medusa en PRODUCCIÓN.

Hace todo por la API de Medusa, salvo un paso de SQL (no hay acceso a la base
desde afuera porque el proxy TCP de Railway está cerrado y los builds están
pausados por el incidente del 21/10/2026).

PASO ÚNICO (lo corrés vos en Railway → Postgres → Console):

  UPDATE auth_identity SET app_metadata = '{}'::jsonb
  WHERE id = (SELECT auth_identity_id FROM provider_identity
              WHERE entity_id='admin@dankoshop.com' AND provider='emailpass');

Eso deja la identidad "claimable" (sin actor). Con eso, este script:

  1. POST /auth/user/emailpass/register  -> aplica la password nueva (la vieja muere)
  2. POST /admin/invites + accept        -> crea el usuario y lo vincula
  3. Verificación                          -> login con la nueva (200) y con la vieja (401)
  4. Borra el admin temporal               -> queda un solo admin

Uso:
  python3 scripts/rotar_password_admin_prod.py
  python3 scripts/rotar_password_admin_prod.py --password 'mi-clave-nueva'
"""

import argparse
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env.production"
PROD_URL = os.getenv("MEDUSA_PROD_URL", "https://dankoshop-api-production.up.railway.app")
EMAIL_DEFAULT = "admin@dankoshop.com"
TEMP_EMAIL = "admin-temporal@dankoshop.com"


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


def api(method, path, token=None, data=None, params=None, timeout=30):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, PROD_URL + path, headers=headers, json=data,
                            params=params, timeout=timeout)


def target_password(arg):
    if arg:
        return arg
    env = env_file_values()
    for key in ("MEDUSA_NUEVA_ADMIN_PASSWORD", "MEDUSA_LOCAL_ADMIN_PASSWORD"):
        if env.get(key):
            return env[key]
    if os.getenv("MEDUSA_NUEVA_ADMIN_PASSWORD"):
        return os.getenv("MEDUSA_NUEVA_ADMIN_PASSWORD")
    print("❌ No se encontró la password nueva.")
    print("   Pasala con --password '...' o ponela en .env.production como MEDUSA_NUEVA_ADMIN_PASSWORD")
    sys.exit(1)


def clear_invites(token, email):
    r = api("GET", "/admin/invites", token=token, params={"email": email, "limit": 50})
    if r.status_code != 200:
        return
    for inv in r.json().get("invites", []):
        if inv.get("email") == email:
            api("DELETE", f"/admin/invites/{inv['id']}", token=token)


def user_id_for(token, email):
    users = api("GET", "/admin/users", token=token).json().get("users", [])
    u = next((x for x in users if x.get("email") == email), None)
    return u["id"] if u else None


def main():
    parser = argparse.ArgumentParser(description="Rota la password del admin de Medusa en producción")
    parser.add_argument("--password", help="Password nueva")
    args = parser.parse_args()

    env = env_file_values()
    email = env.get("MEDUSA_ADMIN_EMAIL") or EMAIL_DEFAULT
    old_password = env.get("MEDUSA_ADMIN_PASSWORD", "")
    new_password = target_password(args.password)

    print("=" * 62)
    print("  Rotación de password del admin (PRODUCCIÓN)")
    print("=" * 62)
    print(f"  Email:    {email}")
    print(f"  Password: {'*' * len(new_password)} ({len(new_password)} caracteres)")

    # 1) Aplicar la password nueva (la identidad debe estar "claimable")
    print("\n  1/4 Aplicando la password nueva...")
    r = api("POST", "/auth/user/emailpass/register",
            data={"email": email, "password": new_password})
    if r.status_code != 200:
        if "already exists" in r.text:
            print("❌ La identidad todavía tiene un actor asignado.")
            print("   Corré esto en Railway → Postgres → Console y volvé a correr el script:\n")
            print("   UPDATE auth_identity SET app_metadata = '{}'::jsonb")
            print("   WHERE id = (SELECT auth_identity_id FROM provider_identity")
            print("               WHERE entity_id='" + email + "' AND provider='emailpass');")
        else:
            print(f"❌ {r.status_code} {r.text[:250]}")
        sys.exit(1)
    identity_token = r.json()["token"]
    print("     ✅ password nueva aplicada (la vieja ya no autentica)")

    # 2) Recrear el usuario y vincularlo a la identidad
    print("\n  2/4 Recreando el usuario admin...")
    clear_invites(identity_token, email)
    r = api("POST", "/admin/invites", token=identity_token, data={"email": email})
    if r.status_code != 200:
        print(f"❌ No se pudo crear la invitación: {r.status_code} {r.text[:200]}")
        sys.exit(1)
    invite_token = (r.json().get("invite") or {}).get("token")
    if not invite_token:
        print(f"❌ La invitación no trae token: {r.text[:200]}")
        sys.exit(1)
    r = api("POST", "/admin/invites/accept", token=identity_token,
            params={"token": invite_token}, data={"email": email})
    if r.status_code != 200:
        print(f"❌ No se pudo aceptar la invitación: {r.status_code} {r.text[:250]}")
        sys.exit(1)
    print("     ✅ usuario creado y vinculado")

    # 3) Verificación
    print("\n  3/4 Verificando...")
    ok = api("POST", "/auth/user/emailpass", data={"email": email, "password": new_password})
    print(f"  Login con la NUEVA password: {'✅ 200 OK' if ok.status_code == 200 else '❌ ' + str(ok.status_code)}")
    token = ok.json().get("token") if ok.status_code == 200 else None
    if token:
        me = api("GET", "/admin/users/me", token=token)
        print(f"  Acceso al panel admin:      {'✅ OK' if me.status_code == 200 else '❌ ' + str(me.status_code)}")
    if old_password and old_password != new_password:
        st = api("POST", "/auth/user/emailpass", data={"email": email, "password": old_password})
        print(f"  Login con la VIEJA password: {'✅ 401 (rechazada)' if st.status_code == 401 else f'⚠️  HTTP {st.status_code}'}")

    # 4) Borrar el admin temporal
    print("\n  4/4 Eliminando el admin temporal...")
    if token:
        temp_token = api("POST", "/auth/user/emailpass",
                         data={"email": TEMP_EMAIL, "password": new_password})
        if temp_token.status_code == 200:
            temp_id = user_id_for(temp_token.json()["token"], TEMP_EMAIL)
            if temp_id:
                d = api("DELETE", f"/admin/users/{temp_id}", token=token)
                print(f"     {'✅ borrado' if d.status_code == 200 else '⚠️  no se pudo borrar (' + str(d.status_code) + ')'}")
        else:
            print("     (no estaba, nada que borrar)")

    if ok.status_code == 200:
        print("\n" + "=" * 62)
        print("  ✅ Password rotada en PRODUCCIÓN")
        print("=" * 62)
        print("  Falta actualizar en Vercel:  MEDUSA_ADMIN_PASSWORD")
        print("  (y en .env.production: MEDUSA_ADMIN_PASSWORD = la nueva)")
    else:
        print("\n❌ La password no quedó activa. Revisá el error de arriba.")
        sys.exit(1)


if __name__ == "__main__":
    main()
