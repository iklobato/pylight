# Helm Chart Deployment Test Procedures

This document provides step-by-step procedures for testing Pylight deployment via Helm charts with external databases in Kubernetes.

## Prerequisites

- Kubernetes cluster (minikube, kind, or cloud cluster)
- `kubectl` configured to access the cluster
- `helm` installed (v3.x)
- PostgreSQL database accessible from cluster (in-cluster or external)

## Step 1: Deploy PostgreSQL to Kubernetes

### Option A: In-Cluster PostgreSQL (Recommended for Testing)

1. Create namespace for PostgreSQL:
```bash
kubectl create namespace postgres
```

2. Deploy PostgreSQL using the provided manifest or Helm chart:
```bash
# Using the database_kubernetes.py script
python3 -c "
from tests.external_db.setup.database_kubernetes import create_kubernetes_database
db = create_kubernetes_database(namespace='postgres')
print(f'Database connection string: {db.get_connection_string()}')
"
```

3. Wait for PostgreSQL to be ready:
```bash
kubectl wait --for=condition=ready pod -l app=postgres -n postgres --timeout=300s
```

4. Verify PostgreSQL is running:
```bash
kubectl get pods -n postgres
kubectl get svc -n postgres
```

### Option B: External PostgreSQL

If using external PostgreSQL, ensure:
- Network connectivity from cluster to database
- Firewall rules allow connections
- Connection string format: `postgresql://user:password@host:port/database`

## Step 2: Create Database Schema and Test Data

1. Connect to PostgreSQL pod and create schema:
```bash
kubectl exec -it -n postgres $(kubectl get pod -n postgres -l app=postgres -o jsonpath='{.items[0].metadata.name}') -- \
  psql -U postgres -d pylight_test
```

2. Or use the schema generator:
```bash
export TEST_DATABASE_URL="postgresql://postgres:postgres@postgres.postgres.svc.cluster.local:5432/pylight_test"
python3 scripts/external-db-test/generate_test_data.py --skip-schema
```

## Step 3: Install Pylight Helm Chart

1. Add Helm repository (if using published chart):
```bash
helm repo add iklobato https://iklobato.github.io/pylight/charts
helm repo update
```

2. Create values file for deployment:
```yaml
# helm-values.yaml
image:
  repository: iklob1/pylight
  tag: "1.0.21"
  pullPolicy: IfNotPresent

database:
  connectionString: "postgresql://postgres:postgres@postgres.postgres.svc.cluster.local:5432/pylight_test"

config:
  createConfigMap: true
  inline:
    swagger:
      title: "Pylight Test API"
      version: "1.0.21"
    tables:
      - name: "products"
      - name: "users"
      - name: "orders"
```

3. Install Helm chart:
```bash
helm install pylight-test ./charts/pylight -f helm-values.yaml -n pylight --create-namespace
```

4. Wait for deployment to be ready:
```bash
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=pylight -n pylight --timeout=300s
```

## Step 4: Verify Deployment

1. Check pod status:
```bash
kubectl get pods -n pylight
kubectl logs -n pylight -l app.kubernetes.io/name=pylight
```

2. Check service:
```bash
kubectl get svc -n pylight
```

3. Check ConfigMap:
```bash
kubectl get configmap -n pylight
kubectl describe configmap -n pylight
```

## Step 5: Test REST Endpoints

1. Port forward to access API:
```bash
kubectl port-forward -n pylight svc/pylight-test-service 8000:8000
```

2. Test health endpoint:
```bash
curl http://localhost:8000/health
```

3. Test REST CRUD operations:
```bash
# List products
curl http://localhost:8000/api/products

# Get single product
curl http://localhost:8000/api/products/1

# Create product
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Product", "price": "99.99", "sku": "TEST-001"}'

# Update product
curl -X PUT http://localhost:8000/api/products/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Product"}'

# Delete product
curl -X DELETE http://localhost:8000/api/products/1
```

4. Test pagination, filtering, sorting:
```bash
# Pagination
curl "http://localhost:8000/api/products?page=1&limit=10"

# Filtering
curl "http://localhost:8000/api/products?price__gt=100"

# Sorting
curl "http://localhost:8000/api/products?sort=-price"
```

## Step 6: Test GraphQL Endpoints

1. Access GraphiQL interface:
```bash
# Port forward is already active from Step 5
open http://localhost:8000/graphiql
```

2. Test GraphQL queries:
```graphql
query {
  products {
    id
    name
    price
  }
}

query {
  product(id: 1) {
    id
    name
    price
  }
}
```

3. Test GraphQL mutations:
```graphql
mutation {
  createProduct(input: {
    name: "New Product"
    price: "149.99"
    sku: "NEW-001"
  }) {
    id
    name
  }
}
```

## Step 7: Test Helm Upgrade

1. Update values file with new configuration:
```yaml
# helm-values-upgrade.yaml
image:
  tag: "1.0.22"  # New version

replicaCount: 2  # Scale up
```

2. Upgrade Helm release:
```bash
helm upgrade pylight-test ./charts/pylight -f helm-values-upgrade.yaml -n pylight
```

3. Verify upgrade:
```bash
kubectl get pods -n pylight
kubectl rollout status deployment/pylight-test-pylight -n pylight
```

4. Test API still works after upgrade:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/products
```

## Step 8: Test Scaling

1. Scale deployment:
```bash
kubectl scale deployment pylight-test-pylight -n pylight --replicas=3
```

2. Verify all replicas are running:
```bash
kubectl get pods -n pylight
```

3. Verify all replicas connect to database:
```bash
# Check logs from each pod
kubectl logs -n pylight -l app.kubernetes.io/name=pylight --all-containers=true
```

4. Test load balancing (if service type is LoadBalancer or NodePort):
```bash
# Make multiple requests and verify they're distributed
for i in {1..10}; do
  curl http://localhost:8000/api/products
done
```

## Step 9: Cleanup

1. Uninstall Helm release:
```bash
helm uninstall pylight-test -n pylight
```

2. Delete namespace (if created):
```bash
kubectl delete namespace pylight
```

3. Cleanup PostgreSQL (if in-cluster):
```bash
kubectl delete namespace postgres
```

## Troubleshooting

### Pods in CrashLoopBackOff

- Check pod logs: `kubectl logs -n pylight -l app.kubernetes.io/name=pylight`
- Verify database connection string is correct
- Ensure database is accessible from cluster
- Check if database tables exist

### Service not accessible

- Verify service exists: `kubectl get svc -n pylight`
- Check service endpoints: `kubectl get endpoints -n pylight`
- Verify port forwarding: `kubectl port-forward -n pylight svc/pylight-test-service 8000:8000`

### Database connection errors

- Verify PostgreSQL pod is running: `kubectl get pods -n postgres`
- Test connection from pod: `kubectl run -it --rm debug --image=postgres:15 --restart=Never -- psql "postgresql://postgres:postgres@postgres.postgres.svc.cluster.local:5432/pylight_test"`
- Check network policies if using them

