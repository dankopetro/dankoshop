#!/usr/bin/env python3
"""
medusa_auth.py - Credenciales del admin de Medusa, sin hardcodear secretos.

Busca MEDUSA_ADMIN_EMAIL / MEDUSA_ADMIN_PASSWORD en:
  1) Variables de entorno
  2) El archivo .env.production de la raíz del repo (está en .gitignore)

Uso:
  from medusa_auth import get_admin_credentials
  email, password = get_admin_credentials()

Para cambiar la contraseña del admin (la de producción), ver GUIA-ADMINISTRADORA-DANKOSHOP.md.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env.production"

DEFAULT_EMAIL = "admin@dankoshop.com"


def _parse_env_file(path):
    values = {}
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                val = val.strip().strip('"').strip("'")
                values[key.strip()] = val
    except OSError:
        return values
    return values


def load_env_file():
    """Carga .env.production en os.environ sin pisar variables ya definidas."""
    for key, val in _parse_env_file(ENV_FILE).items():
        os.environ.setdefault(key, val)


def get_admin_credentials(local=False):
    """Devuelve (email, password) del admin de Medusa.

    Para la instancia local (local=True) se puede usar un admin distinto:
    MEDUSA_LOCAL_ADMIN_EMAIL / MEDUSA_LOCAL_ADMIN_PASSWORD.

    Lanza SystemExit con un mensaje claro si falta la contraseña.
    """
    file_vals = _parse_env_file(ENV_FILE)
    load_env_file()
    if local:
        email = os.getenv("MEDUSA_LOCAL_ADMIN_EMAIL", "").strip() or os.getenv(
            "MEDUSA_ADMIN_EMAIL", DEFAULT_EMAIL).strip()
        password = os.getenv("MEDUSA_LOCAL_ADMIN_PASSWORD", "").strip() or os.getenv(
            "MEDUSA_ADMIN_PASSWORD", "").strip()
        env_key = "MEDUSA_LOCAL_ADMIN_PASSWORD"
    else:
        email = os.getenv("MEDUSA_ADMIN_EMAIL", DEFAULT_EMAIL).strip()
        password = os.getenv("MEDUSA_ADMIN_PASSWORD", "").strip()
        env_key = "MEDUSA_ADMIN_PASSWORD"
    # Avisa si la password del entorno difiere de la del archivo (casi siempre
    # una variable vieja exportada a mano que pisa .env.production y causa 401).
    file_pw = file_vals.get(env_key, "").strip()
    if file_pw and password and password != file_pw:
        print(
            f"⚠️  {env_key} del entorno difiere de {ENV_FILE.name}.\n"
            f"   Si el login falla con 401, es casi seguro la password vieja.\n"
            f"   Solución: unset {env_key} y volvé a correr.",
            file=sys.stderr,
        )
    if not password:
        print(
            "❌ Falta MEDUSA_ADMIN_PASSWORD.\n"
            "   Opciones:\n"
            f"   a) Exportarla: export MEDUSA_ADMIN_PASSWORD='tu-password'\n"
            f"   b) Agregarla a {ENV_FILE} (ese archivo NO se sube a GitHub)\n"
            "   Ver GUIA-ADMINISTRADORA-DANKOSHOP.md → 'Cambiar la clave del admin'.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return email, password


if __name__ == "__main__":
    email, password = get_admin_credentials()
    print(f"email: {email}")
    print(f"password: {'*' * len(password)} ({len(password)} caracteres)")
