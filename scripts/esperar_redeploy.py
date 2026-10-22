#!/usr/bin/env python3
"""
esperar_redeploy.py - Vigila y aplica el redeploy del backend hasta que Railway lo permita.

Contexto (21/10/2026): Railway tuvo un incidente de seguridad que pausó todos los
deploys. El backend quedó corriendo con el JWT_SECRET por defecto (público en el
repo), lo que permite forjar tokens de admin. Las variables correctas ya están en
Railway, pero un deployment activo congela sus variables: hace falta un redeploy.

Este script reintenta el redeploy (probando varias vías) y, cuando lo logra,
verifica que el token forjado ya no sirva y avisa por Telegram.

No necesita instalar nada: solo Python 3.8+ (stdlib) y el CLI de Railway.

Uso:
  python3 esperar_redeploy.py                    # reintenta cada 60s
  python3 esperar_redeploy.py --cada 30          # más seguido
  python3 esperar_redeploy.py --una-vez          # un intento y salir
  python3 esperar_redeploy.py --sin-telegram     # sin avisos

Variables de entorno (opcionales):
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID  -> para avisar cuando se aplique
  JWT_SECRET_NUEVO                     -> secret nuevo (para la verificación)
  RAILWAY_BIN                          -> ruta al CLI (default: railway)
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = os.environ.get("MEDUSA_PROD_URL", "https://dankoshop-api-production.up.railway.app")
DEPLOYMENT_ID = os.environ.get("RAILWAY_DEPLOYMENT_ID", "44e88348-ca6a-40e9-b996-8cec151e0943")
ENVIRONMENT_ID = os.environ.get("RAILWAY_ENVIRONMENT_ID", "00edf817-87ee-4988-9b15-1a75a12a9432")
SERVICE_ID = os.environ.get("RAILWAY_SERVICE_ID", "e26fbbdb-e502-44c6-acee-a91a273dfa59")
ACTOR_ID = os.environ.get("MEDUSA_ADMIN_USER_ID", "user_01M5GHJZ58R2X0D58EPXR5X32Z")
SECRET_DEFAULT = "super-secret-jwt"   # el que quedó en el contenedor (público en el repo)
RAILWAY_BIN = os.environ.get("RAILWAY_BIN", "railway")
LOG_PATH = Path(os.environ.get("REDEPLOY_LOG", Path(__file__).resolve().parent / "redeploy.log"))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
AVISOS_UMBRAL = int(os.environ.get("AVISOS_UMBRAL", "30"))


# --------------------------------------------------------------------------- utils
def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def telegram(text):
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT):
        return False
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=json.dumps({"chat_id": TELEGRAM_CHAT, "text": text, "parse_mode": "HTML"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=20).read()
        return True
    except Exception as e:
        log(f"  (no se pudo avisar por Telegram: {e})")
        return False


def b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def forge_token(secret: str, actor_id: str, ttl: int = 300) -> str:
    """Forja un JWT HS256 (mismo formato que usa Medusa)."""
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"actor_id": actor_id, "actor_type": "user", "auth_provider": "emailpass",
               "app_metadata": {"user_id": actor_id}, "user_metadata": {},
               "iat": now, "exp": now + ttl}

    def enc(d):
        return b64(json.dumps(d, separators=(",", ":")).encode())

    signing_input = f"{enc(header)}.{enc(payload)}"
    sig = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{b64(sig)}"


def http_status(url, token=None, timeout=20):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        req = urllib.request.Request(url, headers=headers)
        return urllib.request.urlopen(req, timeout=timeout).status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


# --------------------------------------------------------------------------- railway
def railway_api(query, timeout=90):
    try:
        r = subprocess.run([RAILWAY_BIN, "api", query], capture_output=True, text=True, timeout=timeout)
        return r.stdout or ""
    except Exception as e:
        return json.dumps({"errors": [{"message": str(e)}]})


VIAS = [
    ("deploymentRedeploy (imagen previa, sin build)",
     f'mutation {{ deploymentRedeploy(id: "{DEPLOYMENT_ID}", usePreviousImageTag: true) {{ id status }} }}', 120),
    ("serviceInstanceDeploy (build del ultimo commit)",
     f'mutation {{ serviceInstanceDeploy(environmentId: "{ENVIRONMENT_ID}", serviceId: "{SERVICE_ID}", latestCommit: true) }}', 120),
    ("serviceInstanceRedeploy",
     f'mutation {{ serviceInstanceRedeploy(environmentId: "{ENVIRONMENT_ID}", serviceId: "{SERVICE_ID}") }}', 120),
]


def intentar_deploy():
    """Prueba las vías de redeploy en orden. Devuelve (hecho, vía, mensaje)."""
    for nombre, query, timeout in VIAS:
        out = railway_api(query, timeout=timeout)
        if '"errors"' in out:
            try:
                msg = json.loads(out)["errors"][0]["message"]
            except Exception:
                msg = out[:100]
            log(f"  · {nombre}: {msg}")
            continue
        log(f"  · {nombre}: OK")
        return True, nombre, "ok"
    return False, None, "todas pausadas"


# --------------------------------------------------------------------------- verificación
def verificar():
    """Devuelve (estado, detalle). estado: 'ok' | 'vulnerable' | 'indefinido'"""
    secret_nuevo = os.environ.get("JWT_SECRET_NUEVO", "").strip()

    st_default = http_status(f"{API}/admin/users", forge_token(SECRET_DEFAULT, ACTOR_ID))
    st_nuevo = http_status(f"{API}/admin/users", forge_token(secret_nuevo, ACTOR_ID)) if secret_nuevo else 0
    st_login = http_status(f"{API}/health")

    log(f"  verificación -> default={st_default} nuevo={st_nuevo} health={st_login}")
    if st_default == 200:
        return "vulnerable", "el secret por defecto TODAVIA sirve"
    if secret_nuevo and st_nuevo == 200:
        return "ok", "secret nuevo activo y el viejo rechazado"
    if st_default == 401 and st_login == 200:
        return "ok", "el secret por defecto fue rechazado y el backend responde"
    return "indefinido", f"default={st_default} nuevo={st_nuevo}"


def esperar_healthy(timeout_min=5):
    """Espera a que el backend responda. Devuelve True si levantó."""
    deadline = time.time() + timeout_min * 60
    while time.time() < deadline:
        if http_status(f"{API}/health") == 200:
            return True
        time.sleep(5)
    return False


def main():
    parser = argparse.ArgumentParser(description="Espera y aplica el redeploy del backend")
    parser.add_argument("--cada", type=int, default=300, help="Segundos entre intentos")
    parser.add_argument("--una-vez", action="store_true", help="Un solo intento y salir")
    parser.add_argument("--sin-telegram", action="store_true", help="No enviar avisos")
    parser.add_argument("--build-tras-fix", action="store_true", default=True,
                        help="Después del fix, pedir un build para aplicar el Dockerfile nuevo")
    args = parser.parse_args()

    global TELEGRAM_TOKEN, TELEGRAM_CHAT
    if args.sin_telegram:
        TELEGRAM_TOKEN = TELEGRAM_CHAT = ""

    log("=" * 62)
    log("  Vigilante de redeploy (backend DankoShop)")
    log("=" * 62)
    log(f"  API:          {API}")
    log(f"  Deployment:   {DEPLOYMENT_ID[:8]}...")
    log(f"  Intervalo:    {args.cada}s")
    log(f"  Telegram:     {'sí' if TELEGRAM_TOKEN else 'no'}")

    intento = 0
    avisado = False
    while True:
        intento += 1
        log(f"intento {intento}: intentando redeploy...")
        hecho, via, mensaje = intentar_deploy()
        if hecho:
            log(f"✅ redeploy disparado vía {via}. Esperando que el backend levante...")
            wait_min = 15 if "build" in via else 5
            if not esperar_healthy(wait_min):
                log("  el backend no volvió a tiempo; sigo esperando")
            else:
                time.sleep(10)
            estado, detalle = verificar()
            if estado == "ok":
                log(f"🎉 RESUELTO: {detalle}")
                telegram("🔐 <b>JWT secret rotado en producción</b>\n"
                         "El forjado de tokens de admin quedó cerrado.\n"
                         "Podés revisar el panel con normalidad.")
                if args.build_tras_fix:
                    log("  pidiendo build del último commit (para aplicar el Dockerfile nuevo)...")
                    out = railway_api(VIAS[1][1], timeout=120)
                    if '"errors"' in out:
                        log("  el build no se pudo pedir (se puede hacer a mano desde el dashboard)")
                    else:
                        log("  build solicitado. Subirá con el Dockerfile nuevo (admin con $MEDUSA_ADMIN_PASSWORD).")
            else:
                log(f"⚠️  redeploy aplicado pero la verificación da: {detalle}")
                telegram(f"⚠️ <b>Redeploy aplicado</b> pero la verificación dio: {detalle}")
            return
        if not avisado and intento >= AVISOS_UMBRAL:
            avisado = True
            log("avisando por Telegram que sigue pausado")
            telegram("⏳ <b>Railway sigue con los deploys pausados</b>\n"
                     "El fix del JWT secret todavía no se pudo aplicar.\n"
                     "Cuando puedas: Railway → <code>dankoshop-api</code> → <b>Redeploy</b>.")
        if args.una_vez:
            return
        time.sleep(args.cada)


if __name__ == "__main__":
    main()
