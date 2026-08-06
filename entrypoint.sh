#!/bin/sh
set -e

echo "=== Waiting for DB ==="
sleep 5

echo "=== Running migration ==="
pnpm exec medusa db:migrate 2>&1

echo "=== Checking/Creating admin user ==="
# Try to create admin user (will fail silently if exists)
pnpm exec medusa user --email admin@dankoshop.com --password supersecret 2>&1 || true

echo "=== Seeding products if empty ==="
# Run custom seed script
node /app/seed-products.js 2>&1 || true

echo "=== Starting server on 0.0.0.0:9000 ==="
exec ./node_modules/.bin/medusa start