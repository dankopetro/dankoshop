#!/usr/bin/env bash
set -uo pipefail

# Control de la instancia local de Medusa + contenedores Docker de apoyo.
# Garantiza que nunca haya más de una instancia ni procesos colgados.
#
# Uso: ./scripts/medusa-local.sh {start|stop|restart|status}

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$ROOT/medusa-backend/apps/backend"
MEDUSA_BIN="$APP_DIR/node_modules/.bin/../@medusajs/cli/cli.js"
PIDFILE="/tmp/medusa-local.pid"
LOGFILE="/tmp/medusa-local.log"
PORT="${PORT:-9100}"
CONTAINERS=(dankoshop-postgres dankoshop-redis)

is_port_listening() { ss -tln 2>/dev/null | grep -q ":$PORT "; }

pid_alive() {
  [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null
}

find_port_pid() {
  ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP 'pid=\K[0-9]+' | head -1
}

ensure_docker() {
  if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker no está corriendo. Arrancalo (sudo systemctl start docker) e intentá de nuevo."
    exit 1
  fi
}

ensure_containers() {
  ensure_docker
  for c in "${CONTAINERS[@]}"; do
    if ! docker ps --format '{{.Names}}' | grep -qx "$c"; then
      echo ">> Arrancando contenedor $c"
      docker start "$c" >/dev/null
    fi
  done
  echo -n ">> Esperando a PostgreSQL... "
  for _ in $(seq 1 30); do
    if docker exec dankoshop-postgres pg_isready -U dankoshop -d dankoshop >/dev/null 2>&1; then
      echo "listo."
      return 0
    fi
    sleep 1
  done
  echo "ERROR: PostgreSQL no respondió a tiempo."
  exit 1
}

start() {
  if is_port_listening; then
    echo "El puerto $PORT ya está en uso (PID $(find_port_pid)). No se inicia otra instancia."
    echo "Si es una instancia colgada, ejecutá: $0 stop"
    exit 1
  fi
  ensure_containers
  cd "$APP_DIR" || exit 1
  echo ">> Iniciando Medusa en :$PORT (log: $LOGFILE)"
  PORT="$PORT" nohup "$MEDUSA_BIN" start >"$LOGFILE" 2>&1 &
  echo $! >"$PIDFILE"
  echo ">> Esperando a que levante el server..."
  for _ in $(seq 1 90); do
    if is_port_listening; then
      echo "✔ Listo."
      echo "   Store API:  http://localhost:$PORT/store"
      echo "   Admin:      http://localhost:$PORT/app"
      return 0
    fi
    sleep 2
  done
  echo "ERROR: no levantó a tiempo. Revisá $LOGFILE"
  exit 1
}

stop() {
  local pid
  pid=$(find_port_pid)
  if [ -z "$pid" ] && pid_alive; then
    pid=$(cat "$PIDFILE")
  fi
  if [ -n "$pid" ]; then
    echo ">> Deteniendo Medusa (PID $pid)"
    kill "$pid" 2>/dev/null
    sleep 3
    kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null
  else
    echo "No hay instancia corriendo."
  fi
  rm -f "$PIDFILE"
}

status() {
  ensure_docker
  echo "Contenedores:"
  docker ps --filter "name=dankoshop" --format "  {{.Names}}: {{.Status}}"
  echo "Medusa:"
  if is_port_listening; then
    echo "  ✔ Corriendo en :$PORT (PID $(find_port_pid))"
  else
    echo "  ✗ Puerto $PORT libre (no hay instancia)"
  fi
  echo "Memoria:"
  free -h | head -2 | sed 's/^/  /'
}

case "${1:-start}" in
  start) start ;;
  stop) stop ;;
  restart) stop; sleep 2; start ;;
  status) status ;;
  *) echo "Uso: $0 {start|stop|restart|status}"; exit 1 ;;
esac
