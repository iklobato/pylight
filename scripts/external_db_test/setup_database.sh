#!/bin/bash
# Setup database for external database testing
# Usage: ./setup_database.sh [--docker|--kubernetes] [--namespace NAMESPACE]

set -euo pipefail

DEPLOYMENT_TYPE="docker"
NAMESPACE="test-db"

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
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=== Setting up database for external database testing ==="
echo "Deployment type: $DEPLOYMENT_TYPE"

if [ "$DEPLOYMENT_TYPE" == "docker" ]; then
    echo "Starting PostgreSQL in Docker..."
    python3 -c "
from tests.external_db.setup.database_docker import create_docker_database
db = create_docker_database(container_name='pylight-test-db')
print(f'Database connection string: {db.get_connection_string()}')
"
elif [ "$DEPLOYMENT_TYPE" == "kubernetes" ]; then
    echo "Deploying PostgreSQL to Kubernetes namespace: $NAMESPACE"
    python3 -c "
from tests.external_db.setup.database_kubernetes import create_kubernetes_database
db = create_kubernetes_database(namespace='$NAMESPACE')
print(f'Database connection string: {db.get_connection_string()}')
"
else
    echo "Invalid deployment type: $DEPLOYMENT_TYPE"
    exit 1
fi

echo "✓ Database setup complete"

