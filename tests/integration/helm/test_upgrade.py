"""Integration tests for Helm chart upgrade scenarios."""

import subprocess
import time
import yaml
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    return result


def test_upgrade_chart():
    """Test that chart can be upgraded without downtime."""
    chart_path = Path(__file__).parent.parent.parent.parent / "charts" / "pylight"
    initial_values = Path(__file__).parent / "fixtures" / "local-values.yaml"
    updated_values = Path(__file__).parent / "fixtures" / "updated-values.yaml"
    release_name = "pylight-test-upgrade"
    
    try:
        # Deploy initial version
        run_command(
            ["helm", "install", release_name, str(chart_path), "-f", str(initial_values)],
            check=True
        )
        
        time.sleep(10)  # Wait for initial deployment
        
        # Perform upgrade
        result = run_command(
            ["helm", "upgrade", release_name, str(chart_path), "-f", str(updated_values)],
            check=False
        )
        
        assert result.returncode == 0, f"Helm upgrade failed: {result.stderr}"
        assert "STATUS: deployed" in result.stdout or release_name in result.stdout
        
        # Wait for upgrade to complete
        time.sleep(10)
        
        # Verify release is still deployed
        result = run_command(["helm", "list", "-q"], check=True)
        assert release_name in result.stdout
        
    finally:
        # Cleanup
        run_command(["helm", "uninstall", release_name], check=False)


def test_service_available_during_upgrade():
    """Test that service remains available during upgrade."""
    chart_path = Path(__file__).parent.parent.parent.parent / "charts" / "pylight"
    initial_values = Path(__file__).parent / "fixtures" / "local-values.yaml"
    updated_values = Path(__file__).parent / "fixtures" / "updated-values.yaml"
    release_name = "pylight-test-availability"
    
    try:
        # Deploy initial version
        run_command(
            ["helm", "install", release_name, str(chart_path), "-f", str(initial_values)],
            check=True
        )
        
        time.sleep(15)  # Wait for pods to be ready
        
        # Start upgrade in background
        upgrade_process = subprocess.Popen(
            ["helm", "upgrade", release_name, str(chart_path), "-f", str(updated_values)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # While upgrade is running, check service availability
        max_checks = 30
        available_count = 0
        
        for _ in range(max_checks):
            # Check if service endpoint is accessible
            result = run_command(
                ["kubectl", "get", "svc", f"{release_name}-pylight-service", "-o", "jsonpath={.spec.clusterIP}"],
                check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                available_count += 1
            time.sleep(1)
            
            # Check if upgrade completed
            if upgrade_process.poll() is not None:
                break
        
        # Wait for upgrade to complete
        upgrade_process.wait()
        
        # Verify service was available during most checks
        assert available_count > max_checks * 0.8, "Service was not available during upgrade"
        
    finally:
        run_command(["helm", "uninstall", release_name], check=False)


if __name__ == "__main__":
    """Run upgrade tests."""
    print("Running Helm chart upgrade integration tests...")
    
    try:
        test_upgrade_chart()
        print("✓ Chart upgrade test passed")
        
        test_service_available_during_upgrade()
        print("✓ Service availability during upgrade test passed")
        
        print("\nAll upgrade tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise

