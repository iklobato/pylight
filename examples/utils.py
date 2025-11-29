"""Shared utilities for integration examples."""

import subprocess
import time
import signal
import atexit
import sys
import requests
import psycopg2
import redis
from typing import Optional


def verify_postgres() -> bool:
    """Verify PostgreSQL is available.

    Returns:
        True if PostgreSQL is available, False otherwise
    """
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="postgres",
            connect_timeout=5,
        )
        conn.close()
        return True
    except Exception as e:
        print(f"ERROR: PostgreSQL not available: {e}")
        print("Please ensure PostgreSQL Docker container is running:")
        print("  docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres")
        return False


def verify_redis() -> bool:
    """Verify Redis is available.

    Returns:
        True if Redis is available, False otherwise
    """
    try:
        r = redis.Redis(host="localhost", port=6379, db=0, socket_connect_timeout=5)
        r.ping()
        return True
    except Exception as e:
        print(f"ERROR: Redis not available: {e}")
        print("Please ensure Redis is running:")
        print("  docker run -d -p 6379:6379 redis")
        return False


def start_server(
    app_module: str, host: str = "127.0.0.1", port: int = 8001
) -> Optional[subprocess.Popen]:
    """Start server in background process.

    Args:
        app_module: Python module path (e.g., "app:app")
        host: Host to bind to
        port: Port to bind to

    Returns:
        Server process or None if failed
    """
    try:
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", app_module, "--host", host, "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stderr with stdout
        )
        return process
    except Exception as e:
        print(f"ERROR: Failed to start server: {e}")
        return None


def wait_for_server(url: str = "http://127.0.0.1:8001/docs", max_attempts: int = 30) -> bool:
    """Wait for server to be ready.

    Args:
        url: URL to check
        max_attempts: Maximum number of attempts

    Returns:
        True if server is ready, False otherwise
    """
    for _ in range(max_attempts):
        try:
            response = requests.get(url, timeout=2)
            if response.status_code in [200, 404]:  # 404 is OK, means server is up
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    return False


def stop_server(process: Optional[subprocess.Popen]) -> None:
    """Stop server process with cleanup.

    Args:
        process: Server process to stop
    """
    if process is None:
        return

    try:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    except Exception as e:
        print(f"WARNING: Error stopping server: {e}")


def setup_server_cleanup(process: Optional[subprocess.Popen]) -> None:
    """Setup cleanup handlers for server process.

    Args:
        process: Server process to cleanup
    """
    if process is None:
        return

    def cleanup():
        stop_server(process)

    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda s, f: cleanup())
    signal.signal(signal.SIGTERM, lambda s, f: cleanup())

