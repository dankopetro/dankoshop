#!/bin/bash
# sync-a-local.sh - Bajar cambios de Producción a Local
# Uso: ./scripts/sync-a-local.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "  PRODUCCIÓN → LOCAL"
echo "========================================"
echo ""

# Verificar conexión a producción
echo "Verificando conexión a producción..."
if ! curl -s -o /dev/null -w "%{http_code}" https://dankoshop-api-production.up.railway.app/health | grep -q "200"; then
    echo "❌ No se puede conectar a producción."
    echo "   Verificá tu conexión a internet."
    exit 1
fi
echo "✓ Producción disponible"

# Verificar que Medusa local esté corriendo
if ! ss -tln 2>/dev/null | grep -q ":9100 "; then
    echo ""
    echo "⚠️  Medusa local no está corriendo. Arrancándolo..."
    bash "$SCRIPT_DIR/medusa-local.sh" start
    if [ $? -ne 0 ]; then
        echo "❌ No se pudo arrancar Medusa local."
        exit 1
    fi
fi
echo "✓ Local disponible"
echo ""

# Ejecutar sync
python3 "$SCRIPT_DIR/sync_inteligente_prod_a_local.py"
