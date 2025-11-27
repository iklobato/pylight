"""Integration tests for Helm chart deployment validation."""

import subprocess
import time
import yaml
from pathlib import Path
from typing import Dict, Any


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    return result


def test_deploy_chart_to_minikube():
    """Test that chart can be deployed to minikube."""
    chart_path = Path(__file__).parent.parent.parent.parent / "charts" / "pylight"
    values_file = Path(__file__).parent / "fixtures" / "local-values.yaml"
    release_name = "pylight-test-deploy"
    
    # Cleanup any existing release
    try:
        run_command(["helm", "uninstall", release_name], check=False)
    except:
        pass
    
    try:
        # Deploy chart
        result = run_command(
            ["helm", "install", release_name, str(chart_path), "-f", str(values_file)],
            check=False
        )
        
        assert result.returncode == 0, f"Helm install failed: {result.stderr}"
        assert "STATUS: deployed" in result.stdout or release_name in result.stdout
        
        # Wait for deployment
        time.sleep(5)
        
        # Verify release exists
        result = run_command(["helm", "list", "-q"], check=True)
        assert release_name in result.stdout
        
    finally:
        # Cleanup
        run_command(["helm", "uninstall", release_name], check=False)


def test_validate_resources_created():
    """Test that all required Kubernetes resources are created."""
    chart_path = Path(__file__).parent.parent.parent.parent / "charts" / "pylight"
    values_file = Path(__file__).parent / "fixtures" / "local-values.yaml"
    release_name = "pylight-test-resources"
    
    try:
        # Deploy chart
        run_command(
            ["helm", "install", release_name, str(chart_path), "-f", str(values_file)],
            check=True
        )
        
        time.sleep(3)
        
        # Check for Deployment
        result = run_command(
            ["kubectl", "get", "deployment", "-l", f"app.kubernetes.io/instance={release_name}", "-o", "name"],
            check=True
        )
        assert "deployment" in result.stdout.lower()
        
        # Check for Service
        result = run_command(
            ["kubectl", "get", "service", "-l", f"app.kubernetes.io/instance={release_name}", "-o", "name"],
            check=True
        )
        assert "service" in result.stdout.lower()
        
    finally:
        run_command(["helm", "uninstall", release_name], check=False)


def test_pods_become_ready():
    """Test that pods become ready after deployment."""
    chart_path = Path(__file__).parent.parent.parent.parent / "charts" / "pylight"
    values_file = Path(__file__).parent / "fixtures" / "local-values.yaml"
    release_name = "pylight-test-pods"
    
    try:
        # Deploy chart
        run_command(
            ["helm", "install", release_name, str(chart_path), "-f", str(values_file)],
            check=True
        )
        
        # Wait for pods with timeout
        max_wait = 300  # 5 minutes
        elapsed = 0
        interval = 5
        
        while elapsed < max_wait:
            result = run_command(
                ["kubectl", "get", "pods", "-l", f"app.kubernetes.io/instance={release_name}", 
                 "-o", "jsonpath={.items[*].status.phase}"],
                check=False
            )
            
            if "Running" in result.stdout:
                # Check if ready
                ready_result = run_command(
                    ["kubectl", "get", "pods", "-l", f"app.kubernetes.io/instance={release_name}",
                     "-o", "jsonpath={.items[*].status.conditions[?(@.type==\"Ready\")].status}"],
                    check=False
                )
                if "True" in ready_result.stdout:
                    return  # Success
            
            time.sleep(interval)
            elapsed += interval
        
        assert False, f"Pods did not become ready within {max_wait} seconds"
        
    finally:
        run_command(["helm", "uninstall", release_name], check=False)


if __name__ == "__main__":
    """Run deployment tests."""
    print("Running Helm chart deployment integration tests...")
    
    try:
        test_deploy_chart_to_minikube()
        print("✓ Chart deployment test passed")
        
        test_validate_resources_created()
        print("✓ Resource validation test passed")
        
        test_pods_become_ready()
        print("✓ Pod readiness test passed")
        
        print("\nAll deployment tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise

