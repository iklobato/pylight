#!/bin/bash
# Stop Pylight API server started by start_pylight.sh
# Usage: ./stop_pylight.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PID_FILE="$PROJECT_ROOT/tests/external_db/reports/pylight.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "Pylight PID file not found: $PID_FILE"
    echo "Pylight may not be running or was not started by start_pylight.sh"
    exit 1
fi

PYLIGHT_PID=$(cat "$PID_FILE")

if ! ps -p "$PYLIGHT_PID" > /dev/null 2>&1; then
    echo "Pylight process (PID: $PYLIGHT_PID) is not running"
    rm -f "$PID_FILE"
    exit 1
fi

echo "Stopping Pylight (PID: $PYLIGHT_PID)..."
kill "$PYLIGHT_PID" 2>/dev/null || true

# Wait for process to stop
for i in {1..10}; do
    if ! ps -p "$PYLIGHT_PID" > /dev/null 2>&1; then
        echo "✓ Pylight stopped successfully"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# Force kill if still running
if ps -p "$PYLIGHT_PID" > /dev/null 2>&1; then
    echo "Force killing Pylight..."
    kill -9 "$PYLIGHT_PID" 2>/dev/null || true
    sleep 1
    rm -f "$PID_FILE"
    echo "✓ Pylight force stopped"
else
    echo "✓ Pylight stopped successfully"
    rm -f "$PID_FILE"
fi

