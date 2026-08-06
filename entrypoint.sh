#!/bin/sh
set -x
echo "=== Running migration ==="
pnpm exec medusa db:migrate 2>&1
echo "=== Migration done, starting server ==="
exec ./node_modules/.bin/medusa start