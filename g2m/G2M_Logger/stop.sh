#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/mqtt_logger.pid"

stop_pid() {
    local pid="$1"

    if ! kill -0 "$pid" 2>/dev/null; then
        return 0
    fi

    echo "Deteniendo mqtt_logger.py con PID $pid"
    kill "$pid" 2>/dev/null || true

    for _ in {1..5}; do
        if ! kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
        sleep 1
    done

    echo "El proceso sigue activo; forzando cierre con kill -9"
    kill -9 "$pid" 2>/dev/null || true
}

if [[ -f "$PID_FILE" ]]; then
    PID="$(cat "$PID_FILE")"
    if [[ -n "$PID" ]]; then
        stop_pid "$PID"
    fi
    rm -f "$PID_FILE"
else
    PIDS="$(pgrep -f "python3 mqtt_logger.py" || true)"
    if [[ -z "$PIDS" ]]; then
        echo "No se encontro mqtt_logger.py corriendo."
        exit 0
    fi

    for PID in $PIDS; do
        stop_pid "$PID"
    done
fi

echo "mqtt_logger.py detenido."
