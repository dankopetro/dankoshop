#!/bin/sh
# ⚠️  ESTE ARCHIVO NO ES USADO POR EL DOCKERFILE ACTUAL.
# El CMD del Dockerfile corre: db:migrate → medusa user → medusa start
# Este archivo quedó de una versión anterior y NO debe ser ejecutado en producción.
# No ejecutar manualmente salvo para testing local.
set -e

echo "=== Waiting for DB ==="
sleep 5

echo "=== Running migration ==="
pnpm exec medusa db:migrate 2>&1

echo "=== Checking/Creating admin user ==="
# Try to create admin user (will fail silently if exists)
# La password NUNCA se hardcodea: se toma de la env var MEDUSA_ADMIN_PASSWORD.
if [ -n "$MEDUSA_ADMIN_PASSWORD" ]; then
  pnpm exec medusa user --email "${MEDUSA_ADMIN_EMAIL:-admin@dankoshop.com}" --password "$MEDUSA_ADMIN_PASSWORD" 2>&1 || true
else
  echo "MEDUSA_ADMIN_PASSWORD no seteado: se omite la creacion del admin"
fi

echo "=== Starting server on 0.0.0.0:9000 ==="
exec ./node_modules/.bin/medusa start