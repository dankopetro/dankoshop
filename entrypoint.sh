#!/bin/sh
set -x
echo "=== Running migration ==="
pnpm exec medusa db:migrate 2>&1
echo "=== Migration done, building admin with increased memory ==="
NODE_OPTIONS="--max-old-space-size=2048" pnpm exec medusa build 2>&1
echo "=== Admin build done, starting server ==="
exec ./node_modules/.bin/medusa start