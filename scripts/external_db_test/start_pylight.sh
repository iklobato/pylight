#!/bin/bash
# Start Pylight API server for external database testing
# Usage: ./start_pylight.sh [--config CONFIG_FILE] [--host HOST] [--port PORT] [--wait-timeout SECONDS]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_FILE="${PYLIGHT_CONFIG:-$PROJECT_ROOT/tests/external_db/fixtures/test_config.yaml}"
HOST="${PYLIGHT_HOST:-0.0.0.0}"
PORT="${PYLIGHT_PORT:-8000}"
WAIT_TIMEOUT="${PYLIGHT_WAIT_TIMEOUT:-60}"
LOG_DIR="$PROJECT_ROOT/tests/external_db/reports"
PID_FILE="$LOG_DIR/pylight.pid"
LOG_FILE="$LOG_DIR/pylight.log"
STDOUT_LOG="$LOG_DIR/pylight.stdout.log"
STDERR_LOG="$LOG_DIR/pylight.stderr.log"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --wait-timeout)
            WAIT_TIMEOUT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create log directory
mkdir -p "$LOG_DIR"

# Check if Pylight is already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Pylight is already running with PID $OLD_PID"
        echo "To stop it, run: kill $OLD_PID"
        exit 0
    else
        # Stale PID file
        rm -f "$PID_FILE"
    fi
fi

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Error: Port $PORT is already in use"
    echo "Either stop the existing service or use a different port with --port"
    exit 1
fi

# Verify config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

echo "=== Starting Pylight API Server ==="
echo "Config file: $CONFIG_FILE"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Log directory: $LOG_DIR"
echo ""

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Start Pylight in background
cd "$PROJECT_ROOT"
echo "Starting Pylight server..."
python3 -m cli start \
    --config "$CONFIG_FILE" \
    --host "$HOST" \
    --port "$PORT" \
    > "$STDOUT_LOG" 2> "$STDERR_LOG" &

PYLIGHT_PID=$!
echo "$PYLIGHT_PID" > "$PID_FILE"

echo "Pylight started with PID: $PYLIGHT_PID"
echo "Logs:"
echo "  stdout: $STDOUT_LOG"
echo "  stderr: $STDERR_LOG"
echo "  combined: $LOG_FILE"
echo ""

# Wait for server to be ready
echo "Waiting for Pylight to be ready (timeout: ${WAIT_TIMEOUT}s)..."
BASE_URL="http://${HOST}:${PORT}"
if [ "$HOST" = "0.0.0.0" ]; then
    BASE_URL="http://localhost:${PORT}"
fi

START_TIME=$(date +%s)
TIMEOUT_END=$((START_TIME + WAIT_TIMEOUT))
ATTEMPT=0

while [ $(date +%s) -lt $TIMEOUT_END ]; do
    ATTEMPT=$((ATTEMPT + 1))
    
    # Check if process is still running
    if ! ps -p "$PYLIGHT_PID" > /dev/null 2>&1; then
        echo "Error: Pylight process died unexpectedly"
        echo "Check logs for errors:"
        echo "  tail -50 $STDERR_LOG"
        rm -f "$PID_FILE"
        exit 1
    fi
    
    # Try health check
    if curl -s -f "$BASE_URL/health" > /dev/null 2>&1; then
        ELAPSED=$(( $(date +%s) - START_TIME ))
        echo "✓ Pylight is ready (took ${ELAPSED}s, ${ATTEMPT} attempts)"
        echo ""
        echo "API available at: $BASE_URL"
        echo "Health check: $BASE_URL/health"
        echo "Documentation: $BASE_URL/docs"
        echo ""
        echo "To stop Pylight: kill $PYLIGHT_PID"
        echo "Or use: ./scripts/external_db_test/stop_pylight.sh"
        exit 0
    fi
    
    sleep 2
done

# Timeout reached
echo "Error: Pylight did not become ready within ${WAIT_TIMEOUT}s"
echo "Check logs for errors:"
echo "  tail -50 $STDERR_LOG"
echo ""
echo "Last few lines of stderr:"
tail -20 "$STDERR_LOG" || true
echo ""
echo "Last few lines of stdout:"
tail -20 "$STDOUT_LOG" || true

# Don't exit with error - let user decide what to do
# The process is still running, they can check logs
exit 1

