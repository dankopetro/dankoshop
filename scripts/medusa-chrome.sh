#!/bin/bash
# medusa-chrome.sh - Arranca Medusa, abre Chrome, para Medusa al cerrar Chrome

URL=$1
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Arrancar Medusa si no está corriendo
if ! ss -tln 2>/dev/null | grep -q ":9100 "; then
    bash "$SCRIPT_DIR/medusa-local.sh" start > /dev/null 2>&1
    sleep 5
fi

# Verificar que Medusa esté corriendo
if ! ss -tln 2>/dev/null | grep -q ":9100 "; then
    notify-send "Error" "Medusa no pudo arrancar. Revisá: /tmp/medusa-local.log"
    exit 1
fi

# Abrir Chrome
/usr/bin/google-chrome "$URL" &
CHROME_PID=$!

# Esperar a que cierre Chrome
wait $CHROME_PID 2>/dev/null

# Detener Medusa
bash "$SCRIPT_DIR/medusa-local.sh" stop > /dev/null 2>&1
