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
pnpm exec medusa user --email admin@dankoshop.com --password supersecret 2>&1 || true

echo "=== Starting server on 0.0.0.0:9000 ==="
exec ./node_modules/.bin/medusa start