# Helm Local Testing Scripts

This directory contains scripts for deploying and testing the Pylight Helm chart in a local minikube environment.

## Prerequisites

- minikube installed and running
- kubectl configured for minikube
- Helm 3.0+ installed
- PostgreSQL running in Docker at localhost:5432 (credentials: postgres:postgres)
- curl installed (for API testing)

## Scripts

### `deploy.sh`

Deploy the Helm chart to minikube cluster.

```bash
# Basic usage
./scripts/helm-local-test/deploy.sh

# Custom values file and release name
./scripts/helm-local-test/deploy.sh -f custom-values.yaml -r my-release

# With cleanup on failure
./scripts/helm-local-test/deploy.sh --cleanup-on-failure
```

**Options:**
- `-f, --values FILE`: Path to values file (default: `test-values.yaml`)
- `-r, --release NAME`: Helm release name (default: `pylight-test`)
- `-n, --namespace NAME`: Kubernetes namespace (default: `default`)
- `--timeout SECONDS`: Deployment timeout (default: 120)
- `--cleanup-on-failure`: Clean up on deployment failure
- `-h, --help`: Show help message

### `validate.sh`

Validate deployed Helm chart functionality.

```bash
# Basic usage
./scripts/helm-local-test/validate.sh -r pylight-test

# Custom namespace and timeout
./scripts/helm-local-test/validate.sh -r pylight-test -n test-namespace --timeout 600

# Skip API or database tests
./scripts/helm-local-test/validate.sh -r pylight-test --skip-api --skip-db
```

**Options:**
- `-r, --release NAME`: Helm release name (required)
- `-n, --namespace NAME`: Kubernetes namespace (default: `default`)
- `--timeout SECONDS`: Timeout for pod readiness (default: 300)
- `--skip-api`: Skip API endpoint tests
- `--skip-db`: Skip database connectivity tests
- `-h, --help`: Show help message

**Validation Steps:**
1. Verify Kubernetes resources exist (Deployment, Service, ConfigMap, Secret)
2. Wait for pods to become ready
3. Test `/health` endpoint
4. Test API CRUD endpoints
5. Verify database connectivity
6. Verify data persistence

### `upgrade.sh`

Test Helm chart upgrade scenarios.

```bash
# Basic usage
./scripts/helm-local-test/upgrade.sh -r pylight-test -f updated-values.yaml

# With rollback on failure
./scripts/helm-local-test/upgrade.sh -r pylight-test -f updated-values.yaml --rollback-on-failure
```

**Options:**
- `-r, --release NAME`: Helm release name (required)
- `-f, --values FILE`: Path to updated values file (required)
- `-n, --namespace NAME`: Kubernetes namespace (default: `default`)
- `--timeout SECONDS`: Upgrade timeout (default: 300)
- `--rollback-on-failure`: Rollback on upgrade failure
- `-h, --help`: Show help message

**Upgrade Steps:**
1. Verify release exists
2. Perform `helm upgrade`
3. Wait for rolling update to complete
4. Validate service remains available during upgrade
5. Validate new configuration is applied
6. Run full validation suite

### `scale.sh`

Test horizontal scaling scenarios.

```bash
# Scale to 3 replicas
./scripts/helm-local-test/scale.sh -r pylight-test --replicas 3

# Scale to 5 replicas in custom namespace
./scripts/helm-local-test/scale.sh -r pylight-test --replicas 5 -n test-namespace
```

**Options:**
- `-r, --release NAME`: Helm release name (required)
- `--replicas COUNT`: Target replica count (required)
- `-n, --namespace NAME`: Kubernetes namespace (default: `default`)
- `--timeout SECONDS`: Scaling timeout (default: 300)
- `-h, --help`: Show help message

**Scaling Steps:**
1. Verify release exists
2. Update replica count via `helm upgrade`
3. Wait for scaling to complete
4. Verify correct number of pods
5. Test load distribution across pods
6. Validate all pods are healthy

### `cleanup.sh`

Remove test resources and validate cleanup.

```bash
# Basic usage
./scripts/helm-local-test/cleanup.sh -r pylight-test

# Force cleanup even if resources don't exist
./scripts/helm-local-test/cleanup.sh -r pylight-test --force
```

**Options:**
- `-r, --release NAME`: Helm release name (required)
- `-n, --namespace NAME`: Kubernetes namespace (default: `default`)
- `--force`: Force cleanup even if resources don't exist
- `-h, --help`: Show help message

**Cleanup Steps:**
1. Uninstall Helm release
2. Verify resources are removed
3. Report cleanup status

## Common Functions

The `common.sh` script provides shared functions used by all scripts:

- `validate_prerequisites()`: Check for required tools (minikube, kubectl, helm, curl)
- `validate_yaml_file()`: Validate YAML file syntax
- `wait_for_pods_ready()`: Wait for pods to become ready with timeout
- `get_service_url()`: Get service URL for testing
- `preserve_logs()`: Save pod logs for debugging

## Test Values File

The `test-values.yaml` file contains default configuration for local testing:

- Database connection: `postgresql://postgres:postgres@host.docker.internal:5432/testdb`
- Minimal API configuration with test tables
- Single replica for initial testing
- Minimal resource limits

**Note:** The connection string uses `host.docker.internal` to access localhost PostgreSQL from within minikube pods.

## Example Workflow

```bash
# 1. Deploy chart
./scripts/helm-local-test/deploy.sh -r pylight-test

# 2. Validate deployment
./scripts/helm-local-test/validate.sh -r pylight-test

# 3. Test upgrade
./scripts/helm-local-test/upgrade.sh -r pylight-test -f updated-values.yaml

# 4. Test scaling
./scripts/helm-local-test/scale.sh -r pylight-test --replicas 3

# 5. Cleanup
./scripts/helm-local-test/cleanup.sh -r pylight-test
```

## Debugging

All scripts preserve pod logs on failure in `scripts/helm-local-test/logs/` directory.

Enable debug mode by setting the `DEBUG` environment variable:

```bash
DEBUG=1 ./scripts/helm-local-test/deploy.sh
```

## Error Handling

All scripts use `set -euo pipefail` for strict error handling:
- `set -e`: Exit on error
- `set -u`: Exit on undefined variable
- `set -o pipefail`: Exit on pipe failure

Scripts provide clear error messages and preserve logs for debugging.

## Integration Tests

Python-based integration tests are available in `tests/integration/helm/`:

- `test_deployment.py`: Deployment validation tests
- `test_upgrade.py`: Upgrade scenario tests
- `test_scaling.py`: Scaling scenario tests

Run tests with pytest:

```bash
pytest tests/integration/helm/
```

## Troubleshooting

### minikube not running
```bash
minikube start
```

### kubectl not configured for minikube
```bash
kubectl config use-context minikube
```

### PostgreSQL not accessible
Ensure PostgreSQL is running in Docker and accessible at localhost:5432. The connection string uses `host.docker.internal` to access host services from minikube.

### Pods not becoming ready
Check pod logs:
```bash
kubectl logs -n default -l app.kubernetes.io/instance=pylight-test
```

Check pod status:
```bash
kubectl describe pod -n default -l app.kubernetes.io/instance=pylight-test
```

### Health endpoint not responding
Verify the health endpoint is enabled in the Helm chart and the API is running:
```bash
kubectl exec -n default <pod-name> -- curl http://localhost:8000/health
```

## See Also

- [Helm Chart Documentation](../../charts/pylight/README.md)
- [Local Testing Quickstart](../../specs/002-helm-local-testing/quickstart.md)
- [Feature Specification](../../specs/002-helm-local-testing/spec.md)

