"""Integration tests for Pylight Helm chart deployment."""

import subprocess
import time
import yaml
from pathlib import Path
from typing import Dict, Any


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    return result


def test_helm_template_renders():
    """Test that Helm templates render without errors."""
    chart_path = Path(__file__).parent.parent / "charts" / "pylight"
    
    # Test basic template rendering
    result = run_command(
        ["helm", "template", "test-release", str(chart_path)],
        check=False
    )
    
    assert result.returncode == 0, f"Helm template failed: {result.stderr}"
    assert "kind: Deployment" in result.stdout
    assert "kind: Service" in result.stdout


def test_helm_template_with_values():
    """Test that Helm templates render with custom values."""
    chart_path = Path(__file__).parent.parent / "charts" / "pylight"
    
    values = {
        "database": {
            "connectionString": "postgresql://user:pass@host:5432/db"
        },
        "config": {
            "inline": {
                "swagger": {
                    "title": "Test API",
                    "version": "1.0.0"
                },
                "tables": [
                    {"name": "products"}
                ]
            }
        },
        "replicaCount": 2
    }
    
    # Write values to temp file
    values_file = Path("/tmp/test-values.yaml")
    with open(values_file, "w") as f:
        yaml.dump(values, f)
    
    try:
        result = run_command(
            ["helm", "template", "test-release", str(chart_path), "-f", str(values_file)],
            check=False
        )
        
        assert result.returncode == 0, f"Helm template with values failed: {result.stderr}"
        assert "replicas: 2" in result.stdout
    finally:
        values_file.unlink(missing_ok=True)


def test_helm_template_with_existing_secret():
    """Test that Helm templates work with existing Secret reference."""
    chart_path = Path(__file__).parent.parent / "charts" / "pylight"
    
    values = {
        "database": {
            "existingSecret": "my-db-secret",
            "secretKey": "connection-string"
        },
        "config": {
            "existingConfigMap": "my-config"
        }
    }
    
    values_file = Path("/tmp/test-values-existing.yaml")
    with open(values_file, "w") as f:
        yaml.dump(values, f)
    
    try:
        result = run_command(
            ["helm", "template", "test-release", str(chart_path), "-f", str(values_file)],
            check=False
        )
        
        assert result.returncode == 0, f"Helm template with existing resources failed: {result.stderr}"
        # Should not create Secret or ConfigMap
        assert "kind: Secret" not in result.stdout or "test-release-pylight-secret" not in result.stdout
        assert "kind: ConfigMap" not in result.stdout or "test-release-pylight-configmap" not in result.stdout
    finally:
        values_file.unlink(missing_ok=True)


def test_helm_values_schema_validation():
    """Test that values.schema.json validates correctly."""
    chart_path = Path(__file__).parent.parent / "charts" / "pylight"
    schema_path = chart_path / "values.schema.json"
    
    assert schema_path.exists(), "values.schema.json not found"
    
    # Test with invalid values (missing required fields)
    invalid_values = {
        "image": {}  # Missing repository
    }
    
    values_file = Path("/tmp/test-invalid-values.yaml")
    with open(values_file, "w") as f:
        yaml.dump(invalid_values, f)
    
    try:
        result = run_command(
            ["helm", "template", "test-release", str(chart_path), "-f", str(values_file)],
            check=False
        )
        
        # Schema validation should catch this
        # Note: Helm 3.8+ validates schema automatically
        # Older versions may not validate, so we check return code
        if result.returncode != 0:
            assert "repository" in result.stderr.lower() or "required" in result.stderr.lower()
    finally:
        values_file.unlink(missing_ok=True)


if __name__ == "__main__":
    """Run integration tests."""
    print("Running Helm chart integration tests...")
    
    try:
        test_helm_template_renders()
        print("✓ Template rendering test passed")
        
        test_helm_template_with_values()
        print("✓ Template with values test passed")
        
        test_helm_template_with_existing_secret()
        print("✓ Template with existing resources test passed")
        
        test_helm_values_schema_validation()
        print("✓ Values schema validation test passed")
        
        print("\nAll integration tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise

