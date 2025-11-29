#!/bin/bash
# Cleanup test resources
# Usage: ./cleanup.sh [--docker|--kubernetes] [--namespace NAMESPACE] [--force]

set -euo pipefail

DEPLOYMENT_TYPE="docker"
NAMESPACE="test-db"
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --docker)
            DEPLOYMENT_TYPE="docker"
            shift
            ;;
        --kubernetes)
            DEPLOYMENT_TYPE="kubernetes"
            shift
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=== Cleaning up test resources ==="
echo "Deployment type: $DEPLOYMENT_TYPE"

if [ "$DEPLOYMENT_TYPE" == "docker" ]; then
    echo "Stopping and removing Docker container..."
    python3 -c "
from tests.external_db.setup.database_docker import DockerDatabase
db = DockerDatabase(container_name='pylight-test-db')
db.cleanup()
"
elif [ "$DEPLOYMENT_TYPE" == "kubernetes" ]; then
    echo "Deleting Kubernetes namespace: $NAMESPACE"
    if [ "$FORCE" == "true" ]; then
        kubectl delete namespace "$NAMESPACE" --force --grace-period=0 || true
    else
        python3 -c "
from tests.external_db.setup.database_kubernetes import KubernetesDatabase
db = KubernetesDatabase(namespace='$NAMESPACE')
db.cleanup()
"
    fi
else
    echo "Invalid deployment type: $DEPLOYMENT_TYPE"
    exit 1
fi

echo "✓ Cleanup complete"

