"""Integration tests for Helm chart scaling scenarios."""

import subprocess
import time
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    return result


def test_scale_up_replicas():
    """Test that chart can scale up by increasing replica count."""
    chart_path = Path(__file__).parent.parent.parent.parent / "charts" / "pylight"
    values_file = Path(__file__).parent / "fixtures" / "scaling-values.yaml"
    release_name = "pylight-test-scale"
    
    try:
        # Deploy with 1 replica
        run_command(
            ["helm", "install", release_name, str(chart_path), "-f", str(values_file)],
            check=True
        )
        
        time.sleep(10)  # Wait for initial deployment
        
        # Verify 1 pod exists
        result = run_command(
            ["kubectl", "get", "pods", "-l", f"app.kubernetes.io/instance={release_name}",
             "-o", "jsonpath={.items[*].metadata.name}"],
            check=True
        )
        initial_pods = len([p for p in result.stdout.split() if p])
        assert initial_pods == 1, f"Expected 1 pod, found {initial_pods}"
        
        # Scale to 3 replicas
        run_command(
            ["helm", "upgrade", release_name, str(chart_path), "-f", str(values_file),
             "--set", "replicaCount=3"],
            check=True
        )
        
        # Wait for scaling
        max_wait = 300
        elapsed = 0
        interval = 5
        
        while elapsed < max_wait:
            result = run_command(
                ["kubectl", "get", "pods", "-l", f"app.kubernetes.io/instance={release_name}",
                 "-o", "jsonpath={.items[*].metadata.name}"],
                check=True
            )
            pod_count = len([p for p in result.stdout.split() if p])
            
            if pod_count == 3:
                # Check all pods are ready
                ready_result = run_command(
                    ["kubectl", "get", "pods", "-l", f"app.kubernetes.io/instance={release_name}",
                     "-o", "jsonpath={.items[*].status.conditions[?(@.type==\"Ready\")].status}"],
                    check=True
                )
                ready_count = ready_result.stdout.count("True")
                if ready_count == 3:
                    return  # Success
            
            time.sleep(interval)
            elapsed += interval
        
        assert False, f"Scaling did not complete within {max_wait} seconds"
        
    finally:
        run_command(["helm", "uninstall", release_name], check=False)


def test_scale_down_replicas():
    """Test that chart can scale down by decreasing replica count."""
    chart_path = Path(__file__).parent.parent.parent.parent / "charts" / "pylight"
    values_file = Path(__file__).parent / "fixtures" / "scaling-values.yaml"
    release_name = "pylight-test-scale-down"
    
    try:
        # Deploy with 3 replicas
        run_command(
            ["helm", "install", release_name, str(chart_path), "-f", str(values_file),
             "--set", "replicaCount=3"],
            check=True
        )
        
        time.sleep(15)  # Wait for initial deployment
        
        # Scale down to 1 replica
        run_command(
            ["helm", "upgrade", release_name, str(chart_path), "-f", str(values_file),
             "--set", "replicaCount=1"],
            check=True
        )
        
        # Wait for scaling
        max_wait = 300
        elapsed = 0
        interval = 5
        
        while elapsed < max_wait:
            result = run_command(
                ["kubectl", "get", "pods", "-l", f"app.kubernetes.io/instance={release_name}",
                 "-o", "jsonpath={.items[*].metadata.name}"],
                check=True
            )
            pod_count = len([p for p in result.stdout.split() if p])
            
            if pod_count == 1:
                # Check pod is ready
                ready_result = run_command(
                    ["kubectl", "get", "pods", "-l", f"app.kubernetes.io/instance={release_name}",
                     "-o", "jsonpath={.items[*].status.conditions[?(@.type==\"Ready\")].status}"],
                    check=True
                )
                if "True" in ready_result.stdout:
                    return  # Success
            
            time.sleep(interval)
            elapsed += interval
        
        assert False, f"Scaling down did not complete within {max_wait} seconds"
        
    finally:
        run_command(["helm", "uninstall", release_name], check=False)


if __name__ == "__main__":
    """Run scaling tests."""
    print("Running Helm chart scaling integration tests...")
    
    try:
        test_scale_up_replicas()
        print("✓ Scale up test passed")
        
        test_scale_down_replicas()
        print("✓ Scale down test passed")
        
        print("\nAll scaling tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise

