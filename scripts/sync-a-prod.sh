#!/bin/bash
# sync-a-prod.sh - Subir cambios de Local a Producción
# Uso: ./scripts/sync-a-prod.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "  LOCAL → PRODUCCIÓN"
echo "========================================"
echo ""

# Verificar que Medusa local esté corriendo
if ! ss -tln 2>/dev/null | grep -q ":9100 "; then
    echo "❌ Medusa local no está corriendo."
    echo ""
    echo "Arrancalo primero:"
    echo "  ./scripts/medusa-local.sh start"
    echo ""
    exit 1
fi

# Verificar conexión a producción
echo "Verificando conexión a producción..."
if ! curl -s -o /dev/null -w "%{http_code}" https://dankoshop-api-production.up.railway.app/health | grep -q "200"; then
    echo "❌ No se puede conectar a producción."
    echo "   Verificá tu conexión a internet."
    exit 1
fi
echo "✓ Producción disponible"
echo ""

# Ejecutar sync
python3 "$SCRIPT_DIR/sync_inteligente_local_a_prod.py"
