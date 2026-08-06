#!/bin/sh
set -x
echo "=== Running migration ==="
pnpm exec medusa db:migrate 2>&1
echo "=== Migration done, ensuring admin build ==="
pnpm exec medusa build 2>&1
echo "=== Admin build done, starting server ==="
exec ./node_modules/.bin/medusa start