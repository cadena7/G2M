#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/mqtt_logger.pid"
LOG_FILE="$SCRIPT_DIR/nohup.out"

cd "$SCRIPT_DIR"

if [[ -f "$PID_FILE" ]]; then
    PID="$(cat "$PID_FILE")"
    if [[ -n "$PID" ]] && kill -0 "$PID" 2>/dev/null; then
        echo "mqtt_logger.py ya esta corriendo con PID $PID"
        exit 0
    fi
    rm -f "$PID_FILE"
fi

nohup python3 mqtt_logger.py >> "$LOG_FILE" 2>&1 &
PID="$!"
echo "$PID" > "$PID_FILE"

echo "mqtt_logger.py iniciado con PID $PID"
echo "Log: $LOG_FILE"
