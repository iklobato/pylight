"""Pytest configuration and shared fixtures for external database tests."""

import os
import pytest
from typing import Generator
import subprocess
import time


@pytest.fixture(scope="session")
def database_url() -> str:
    """Get database connection URL from environment or use default."""
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/pylight_test"
    )


@pytest.fixture(scope="session")
def pylight_base_url() -> str:
    """Get Pylight API base URL from environment or use default."""
    return os.getenv("PYLIGHT_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def test_data_seed() -> int:
    """Get test data seed value for reproducibility."""
    return int(os.getenv("TEST_DATA_SEED", "42"))


@pytest.fixture(scope="session")
def records_per_table() -> int:
    """Get number of records to generate per table."""
    return int(os.getenv("RECORDS_PER_TABLE", "1000"))


@pytest.fixture(scope="function")
def clean_database(database_url: str) -> Generator[None, None, None]:
    """Fixture to ensure clean database state before each test."""
    # This will be implemented to clean/reset database state
    yield
    # Cleanup after test if needed


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before all tests."""
    # Verify database is accessible
    # Verify Pylight is running
    yield
    # Cleanup after all tests


@pytest.fixture(scope="session")
def pylight_server(pylight_base_url: str, database_url: str):
    """Optional fixture to start/stop Pylight server for tests.
    
    Only starts Pylight if PYLIGHT_AUTO_START environment variable is set.
    Otherwise, assumes Pylight is already running.
    """
    import subprocess
    import os
    import time
    import signal
    from pathlib import Path
    
    auto_start = os.getenv("PYLIGHT_AUTO_START", "false").lower() == "true"
    
    if not auto_start:
        # Just verify Pylight is running
        import requests
        try:
            response = requests.get(f"{pylight_base_url}/health", timeout=2)
            if response.status_code == 200:
                yield None
                return
        except Exception:
            pass
        
        pytest.skip(
            "Pylight API is not running. "
            "Start it manually or set PYLIGHT_AUTO_START=true to auto-start."
        )
    
    # Auto-start Pylight
    project_root = Path(__file__).parent.parent.parent
    script_dir = project_root / "scripts" / "external_db_test"
    start_script = script_dir / "start_pylight.sh"
    config_file = project_root / "tests" / "external_db" / "fixtures" / "test_config.yaml"
    pid_file = project_root / "tests" / "external_db" / "reports" / "pylight.pid"
    
    if not start_script.exists():
        pytest.skip(f"Pylight startup script not found: {start_script}")
    
    # Start Pylight
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    env["PYLIGHT_CONFIG"] = str(config_file)
    
    try:
        result = subprocess.run(
            [str(start_script), "--config", str(config_file)],
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            pytest.fail(
                f"Failed to start Pylight: {result.stderr}\n"
                f"Check logs: {project_root / 'tests' / 'external_db' / 'reports' / 'pylight.stderr.log'}"
            )
        
        # Wait a bit for server to be fully ready
        time.sleep(2)
        
        yield None
        
    finally:
        # Cleanup: Stop Pylight
        if pid_file.exists():
            try:
                with open(pid_file) as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
                # Force kill if still running
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                pid_file.unlink(missing_ok=True)
            except (ValueError, ProcessLookupError, FileNotFoundError):
                pass


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "automated: mark test as automated (deselect with '-m \"not automated\"')"
    )
    config.addinivalue_line(
        "markers", "manual: mark test as requiring manual execution"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )

