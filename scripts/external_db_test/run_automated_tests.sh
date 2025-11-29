#!/bin/bash
# Run automated test suite for external database integration
# Usage: ./run_automated_tests.sh [--base-url URL] [--database-url URL] [--verbose] [--auto-start] [--no-cleanup]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

BASE_URL="${PYLIGHT_BASE_URL:-http://localhost:8000}"
DATABASE_URL="${TEST_DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/pylight_test}"
VERBOSE=""
AUTO_START=false
NO_CLEANUP=false
PYLIGHT_STARTED_BY_SCRIPT=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --base-url)
            BASE_URL="$2"
            shift 2
            ;;
        --database-url)
            DATABASE_URL="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE="-v"
            shift
            ;;
        --auto-start)
            AUTO_START=true
            shift
            ;;
        --no-cleanup)
            NO_CLEANUP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=== Running Automated Test Suite ==="
echo "Pylight Base URL: $BASE_URL"
echo "Database URL: $DATABASE_URL"
echo ""

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Pre-flight checks
echo "=== Pre-flight Checks ==="

# Check database connectivity
echo -n "Checking database connection... "
if python3 -c "
import psycopg2
import sys
try:
    conn = psycopg2.connect('$DATABASE_URL', connect_timeout=2)
    conn.close()
    print('✓')
    sys.exit(0)
except Exception as e:
    print(f'✗ Error: {e}')
    sys.exit(1)
" 2>&1; then
    echo "✓ Database is accessible"
else
    echo "✗ Database is not accessible"
    echo "  Please ensure PostgreSQL is running and accessible at: $DATABASE_URL"
    exit 1
fi

# Check Pylight API
echo -n "Checking Pylight API... "
if curl -s -f "$BASE_URL/health" > /dev/null 2>&1; then
    echo "✓ Pylight API is running"
else
    echo "✗ Pylight API is not running"
    
    if [ "$AUTO_START" = true ]; then
        echo ""
        echo "Auto-starting Pylight..."
        CONFIG_FILE="$PROJECT_ROOT/tests/external_db/fixtures/test_config.yaml"
        if "$SCRIPT_DIR/start_pylight.sh" --config "$CONFIG_FILE"; then
            PYLIGHT_STARTED_BY_SCRIPT=true
            echo "✓ Pylight started successfully"
        else
            echo "✗ Failed to start Pylight"
            echo "  Check logs: tail -50 tests/external_db/reports/pylight.stderr.log"
            exit 1
        fi
    else
        echo ""
        echo "To start Pylight automatically, use --auto-start flag:"
        echo "  ./scripts/external_db_test/run_automated_tests.sh --auto-start"
        echo ""
        echo "Or start Pylight manually:"
        echo "  ./scripts/external_db_test/start_pylight.sh"
        exit 1
    fi
fi

echo ""

# Export environment variables for tests
export PYLIGHT_BASE_URL="$BASE_URL"
export TEST_DATABASE_URL="$DATABASE_URL"

# Run pytest
cd "$PROJECT_ROOT"

echo "=== Running Tests ==="
TEST_LOG="$PROJECT_ROOT/tests/external_db/reports/test-execution.log"

# Run tests and capture output
if pytest tests/external_db/automated/ \
    $VERBOSE \
    --html=tests/external_db/reports/test-report.html \
    --self-contained-html \
    --json-report \
    --json-report-file=tests/external_db/reports/test-report.json \
    --junitxml=tests/external_db/reports/test-report.xml \
    -m "automated" \
    2>&1 | tee "$TEST_LOG"; then
    TEST_EXIT_CODE=0
else
    TEST_EXIT_CODE=${PIPESTATUS[0]}
fi

echo ""
echo "=== Test Execution Summary ==="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ All tests passed"
else
    echo "✗ Some tests failed (exit code: $TEST_EXIT_CODE)"
    echo ""
    echo "Check test logs:"
    echo "  tail -50 $TEST_LOG"
    echo ""
    echo "Check Pylight logs (if issues with API):"
    echo "  tail -50 tests/external_db/reports/pylight.stderr.log"
fi

echo ""
echo "Reports available in tests/external_db/reports/:"
echo "  - test-report.html (HTML report)"
echo "  - test-report.json (JSON report)"
echo "  - test-report.xml (JUnit XML)"
echo "  - test-execution.log (Full test output)"

# Cleanup: Stop Pylight if we started it
if [ "$PYLIGHT_STARTED_BY_SCRIPT" = true ] && [ "$NO_CLEANUP" = false ]; then
    echo ""
    echo "=== Cleanup ==="
    PID_FILE="$PROJECT_ROOT/tests/external_db/reports/pylight.pid"
    if [ -f "$PID_FILE" ]; then
        PYLIGHT_PID=$(cat "$PID_FILE")
        if ps -p "$PYLIGHT_PID" > /dev/null 2>&1; then
            echo "Stopping Pylight (PID: $PYLIGHT_PID)..."
            kill "$PYLIGHT_PID" 2>/dev/null || true
            rm -f "$PID_FILE"
            echo "✓ Pylight stopped"
        fi
    fi
fi

exit $TEST_EXIT_CODE

