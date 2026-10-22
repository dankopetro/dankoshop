#!/usr/bin/env python3
"""
esperar_redeploy.py - Reintenta el redeploy del backend hasta que Railway lo permita.

Contexto (21/10/2026): Railway tuvo un incidente que pausó todos los builds.
El backend quedó corriendo con el JWT_SECRET por defecto (público en el repo),
lo que permite forjar tokens de admin. Las variables correctas YA están en
Railway, pero un deployment activo congela sus propias variables: hace falta
un redeploy para que se apliquen.

Este script reintenta el redeploy (reutilizando la imagen actual, sin build) cada
N segundos. Cuando lo logra, verifica que el token forjado ya no sirva.

Uso:
  python3 scripts/esperar_redeploy.py            # reintenta cada 2 minutos
  python3 scripts/esperar_redeploy.py --cada 60  # reintenta cada 60 segundos
  python3 scripts/esperar_redeploy.py --una-vez  # un solo intento
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
LOG = Path("/tmp/opencode/redeploy.log")
API = "https://dankoshop-api-production.up.railway.app"
DEPLOYMENT_ID = "44e88348-ca6a-40e9-b996-8cec151e0943"
TOKEN_DEFAULT = "super-secret-jwt"   # el que quedó en el contenedor


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def railway_api(query):
    r = subprocess.run(["railway", "api", query], capture_output=True, text=True, timeout=120)
    return r.stdout


def try_redeploy():
    out = railway_api(
        f'mutation {{ deploymentRedeploy(id: "{DEPLOYMENT_ID}", usePreviousImageTag: true) {{ id status }} }}'
    )
    if '"errors"' in out:
        try:
            msg = json.loads(out)["errors"][0]["message"]
        except Exception:
            msg = out[:120]
        return False, msg
    return True, "ok"


def wait_healthy(timeout=240):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if requests.get(f"{API}/health", timeout=8).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(5)
    return False


def forged_token():
    """Token forjado con el secret por defecto (el que está en el contenedor)."""
    code = (
        "const jwt=require('jsonwebtoken');"
        "const fs=require('fs');"
        "const p={actor_id:'user_01ZZZZZZZZZZZZZZZZZZZZZZZZZ',actor_type:'user',auth_provider:'emailpass',"
        "app_metadata:{user_id:'user_01ZZZZZZZZZZZZZZZZZZZZZZZZZ'},user_metadata:{},"
        "iat:Math.floor(Date.now()/1000),exp:Math.floor(Date.now()/1000)+300};"
        f"fs.writeFileSync('/tmp/opencode/f_retry.txt', jwt.sign(p,{TOKEN_DEFAULT!r},{{algorithm:'HS256'}}));"
    )
    subprocess.run(["node", "-e", code], cwd=str(ROOT / "medusa-backend"),
                   capture_output=True, text=True, timeout=60)
    p = Path("/tmp/opencode/f_retry.txt")
    return p.read_text().strip() if p.exists() else None


def verify():
    tok = forged_token()
    if not tok:
        return None
    r = requests.get(f"{API}/admin/users", headers={"Authorization": f"Bearer {tok}"}, timeout=20)
    return r.status_code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cada", type=int, default=120, help="Segundos entre intentos")
    parser.add_argument("--una-vez", action="store_true", help="Un solo intento y salir")
    args = parser.parse_args()

    log("Iniciando espera de redeploy del backend (Railway paused builds)...")
    intento = 0
    while True:
        intento += 1
        ok, msg = try_redeploy()
        if ok:
            log(f"✅ Redeploy disparado (intento {intento}). Esperando que levante...")
            if wait_healthy():
                code = verify()
                if code == 401:
                    log("🎉 RESUELTO: el token forjado ahora es rechazado (401). El JWT_SECRET nuevo está aplicado.")
                else:
                    log(f"⚠️  El redeploy subió pero el token forjado sigue funcionando (HTTP {code}). Revisar.")
                log("Recordar: actualizar MEDUSA_ADMIN_* en Vercel si todavía apuntan al admin viejo.")
                return
            log("El backend no volvió a tiempo; vuelvo a intentar.")
        else:
            log(f"intento {intento}: todavía pausado ({msg})")
        if args.una_vez:
            return
        time.sleep(args.cada)


if __name__ == "__main__":
    main()
