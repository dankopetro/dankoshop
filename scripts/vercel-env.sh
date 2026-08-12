#!/bin/bash
# Configura las variables de entorno de Vercel para el storefront.
# Uso: primero instalar la CLI y loguearse:
#   npm i -g vercel && vercel login
# Luego ejecutar:
#   ./scripts/vercel-env.sh
set -e

PROJECT="dankoshop-storefront"

VARS=(
  "NEXT_PUBLIC_MEDUSA_BACKEND_URL|https://dankoshop-api-production.up.railway.app"
  "NEXT_PUBLIC_MEDUSA_PUBLISHABLE_KEY|pk_fc06e44a06bc2556affab5c23313b32a8bf5213371a09a482c9479f3ec82fc17"
  "NEXT_PUBLIC_BASE_URL|https://dankoshop.com.ar"
  "MERCADOPAGO_ACCESS_TOKEN|APP_USR-1119114696926126-080718-8f8ab2d591ceb590c45b0ced8198b318-511502931"
  "MERCADOPAGO_PUBLIC_KEY|APP_USR-2943d8a1-ea0e-4a80-9d6f-0089d8cd6f75"
  "GITHUB_TOKEN|"
  "CONTENT_ADMIN_PASSWORD|"
)

for entry in "${VARS[@]}"; do
  name="${entry%%|*}"
  value="${entry#*|}"
  if [ -z "$value" ]; then
    read -sp "Valor para $name (secreto): " value
    echo ""
  fi
  echo "Setting $name..."
  echo "$value" | vercel env add "$name" production --token "$VERCEL_TOKEN" --yes 2>/dev/null || \
    echo "$value" | vercel env add "$name" production --yes
done

echo "✅ Variables configuradas. Hacé redeploy del proyecto en Vercel."
