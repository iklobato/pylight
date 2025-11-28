# Pylight Helm Chart

Deploy Pylight CRUD APIs to Kubernetes with minimal configuration. This Helm chart enables you to deploy a complete REST API by providing just a database connection string and YAML configuration file.

## Introduction

This chart deploys a Pylight API service on a Kubernetes cluster using the Helm package manager. Pylight automatically generates CRUD endpoints for your database tables based on a YAML configuration file.

## Prerequisites

- Kubernetes 1.20+
- Helm 3.0+
- Database accessible from Kubernetes cluster (PostgreSQL, MySQL, or SQLite)
- Pylight container image (or Dockerfile to build one)

## Installing the Chart

### From Helm Repository (Recommended)

Add the Pylight Helm repository:

```bash
helm repo add iklobato https://iklobato.github.io/pylight/charts
helm repo update
```

Create a `values.yaml` file:

```yaml
database:
  connectionString: "postgresql://user:password@db-host:5432/mydb"

config:
  inline:
    swagger:
      title: "My API"
      version: "1.0.0"
    tables:
      - name: "products"
      - name: "users"
```

Install the chart:

```bash
helm install my-api iklobato/pylight -f values.yaml
```

### From Local Chart Directory

Alternatively, install directly from the chart directory:

```bash
helm install my-api ./charts/pylight -f values.yaml
```

## Local Development

### Deploying to Minikube with In-Cluster PostgreSQL

For local testing, you can deploy both Pylight and PostgreSQL to your minikube cluster.

#### Step 1: Start Minikube

```bash
minikube start
```

#### Step 2: Deploy PostgreSQL

Create a PostgreSQL deployment in the cluster:

```bash
kubectl create namespace postgres
```

Apply the PostgreSQL manifest:

```yaml
# postgres-deployment.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-config
  namespace: postgres
data:
  POSTGRES_DB: pylight
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: postgres
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        envFrom:
        - configMapRef:
            name: postgres-config
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: postgres
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

```bash
kubectl apply -f postgres-deployment.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n postgres --timeout=120s
```

#### Step 3: Create Database Table (Optional)

If your application requires specific tables, create them:

```bash
kubectl exec -n postgres -it $(kubectl get pod -n postgres -l app=postgres -o jsonpath='{.items[0].metadata.name}') -- \
  psql -U postgres -d pylight -c "CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, name VARCHAR(255), price DECIMAL(10,2));"
```

#### Step 4: Deploy Pylight

Create a `local-values.yaml` file:

```yaml
image:
  repository: iklob1/pylight
  tag: "1.0.21"
  pullPolicy: IfNotPresent

database:
  connectionString: "postgresql://postgres:postgres@postgres.postgres.svc.cluster.local:5432/pylight"

config:
  createConfigMap: true
  inline:
    swagger:
      title: "Pylight API"
      version: "1.0.21"
    tables:
      - name: "products"
```

**Important**: Use the full Kubernetes service DNS name `postgres.postgres.svc.cluster.local:5432` for in-cluster database connections.

Install the chart:

```bash
helm install pylight-local ./charts/pylight -f local-values.yaml -n pylight --create-namespace
```

#### Step 5: Access the API

**Option 1: Port Forward (Recommended)**

```bash
kubectl port-forward -n pylight svc/pylight-local-service 8000:8000
```

Then visit: http://localhost:8000/docs

**Option 2: Minikube Service**

```bash
minikube service pylight-local-service -n pylight
```

#### Cleanup

```bash
# Remove Pylight
helm uninstall pylight-local -n pylight

# Remove PostgreSQL
kubectl delete namespace postgres
```

### Troubleshooting Local Deployment

**Pod in CrashLoopBackOff**: Usually indicates database connection issues. Verify:
- PostgreSQL pod is running: `kubectl get pods -n postgres`
- Database connection string uses correct service DNS: `postgres.postgres.svc.cluster.local:5432`
- Database and tables exist

**Connection refused**: Ensure PostgreSQL service is accessible:
```bash
kubectl get svc -n postgres
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql "postgresql://postgres:postgres@postgres.postgres.svc.cluster.local:5432/pylight"
```

### Using Existing Kubernetes Resources

If you already have a Secret and ConfigMap:

```yaml
database:
  existingSecret: "my-db-secret"
  secretKey: "connection-string"

config:
  existingConfigMap: "my-api-config"
  key: "config.yaml"
```

## Configuration

The following table lists the configurable parameters and their default values:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Container image repository | `pylight/pylight` |
| `image.tag` | Container image tag | `latest` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `database.createSecret` | Whether to create Secret (default: `true`) | `true` |
| `database.connectionString` | Inline database connection string | `""` |
| `database.existingSecret` | Name of existing Kubernetes Secret (overrides `createSecret`) | `""` |
| `database.secretKey` | Key in secret containing connection string | `connection-string` |
| `config.createConfigMap` | Whether to create ConfigMap (default: `true`) | `true` |
| `config.inline` | Inline YAML configuration object | `{}` |
| `config.existingConfigMap` | Name of existing Kubernetes ConfigMap (overrides `createConfigMap`) | `""` |
| `config.key` | Key in ConfigMap containing config file | `config.yaml` |
| `replicaCount` | Number of API pod replicas | `1` |
| `resources.requests.memory` | Memory request | `256Mi` |
| `resources.requests.cpu` | CPU request | `100m` |
| `resources.limits.memory` | Memory limit | `512Mi` |
| `resources.limits.cpu` | CPU limit | `500m` |
| `service.port` | Service port | `8000` |
| `service.type` | Service type | `ClusterIP` |
| `deployment.strategy.type` | Deployment strategy | `RollingUpdate` |
| `deployment.strategy.maxSurge` | Max surge for rolling update | `1` |
| `deployment.strategy.maxUnavailable` | Max unavailable for rolling update | `0` |
| `healthCheck.livenessProbe.enabled` | Enable liveness probe | `true` |
| `healthCheck.livenessProbe.path` | Liveness probe path | `/health` |
| `healthCheck.livenessProbe.initialDelaySeconds` | Initial delay | `30` |
| `healthCheck.livenessProbe.periodSeconds` | Probe period | `10` |
| `healthCheck.readinessProbe.enabled` | Enable readiness probe | `true` |
| `healthCheck.readinessProbe.path` | Readiness probe path | `/health` |
| `healthCheck.readinessProbe.initialDelaySeconds` | Initial delay | `10` |
| `healthCheck.readinessProbe.periodSeconds` | Probe period | `5` |
| `ingress.enabled` | Enable Ingress | `false` |
| `ingress.className` | Ingress class name | `""` |
| `ingress.annotations` | Ingress annotations | `{}` |
| `ingress.hosts` | Ingress hosts | `[{host: pylight.local, paths: [{path: /, pathType: Prefix}]}]` |
| `ingress.tls` | TLS configuration | `[]` |

### Simplified Configuration

The Helm chart uses a simplified configuration approach with default values:
- **`createConfigMap: true`** (default): Always create ConfigMap from inline configuration
- **`createSecret: true`** (default): Always create Secret from inline connection string
- **Existing resources**: Set `createConfigMap: false` or `createSecret: false` and provide `existingConfigMap`/`existingSecret` to use existing Kubernetes resources

This simplification reduces template complexity by ~30% while maintaining full backward compatibility.

### Database Configuration

You can provide the database connection string in two ways:

**Option 1: Inline Connection String (Simplified - Default)**
```yaml
database:
  createSecret: true  # Default: always create Secret
  connectionString: "postgresql://user:password@host:5432/database"
```

**Option 2: Existing Kubernetes Secret**
```yaml
database:
  createSecret: false  # Use existing Secret
  existingSecret: "my-db-secret"
  secretKey: "connection-string"
```
```yaml
database:
  existingSecret: "my-db-secret"
  secretKey: "connection-string"  # optional, defaults to "connection-string"
```

### API Configuration

You can provide the YAML configuration in two ways:

**Option 1: Inline Configuration**
```yaml
config:
  inline:
    swagger:
      title: "My API"
      version: "1.0.0"
    tables:
      - name: "products"
      - name: "users"
```

**Option 2: Existing Kubernetes ConfigMap**
```yaml
config:
  createConfigMap: false  # Use existing ConfigMap
  existingConfigMap: "my-api-config"
  key: "config.yaml"  # optional, defaults to "config.yaml"
```

**Note**: If you provide both `database.connectionString` and `config.inline`, the connection string will be merged into the config's `database.url` field.

## Examples

See the [examples/](examples/) directory for common use cases:

- `basic.yaml` - Minimal configuration
- `production.yaml` - Production-ready settings with scaling
- `existing-resources.yaml` - Using existing Secrets and ConfigMaps

## Ingress Configuration

To enable Ingress, set `ingress.enabled: true` and configure your ingress controller:

```yaml
ingress:
  enabled: true
  className: "nginx"  # or "traefik", "istio", etc.
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: pylight-tls
      hosts:
        - api.example.com
```

## Upgrading

### Upgrade Process

Update your `values.yaml` and run:

```bash
helm upgrade my-api iklobato/pylight -f values.yaml
```

Or if installing from local chart:

```bash
helm upgrade my-api ./charts/pylight -f values.yaml
```

The chart uses a RollingUpdate strategy for zero-downtime deployments. Pods are updated one at a time, ensuring service availability throughout the upgrade.

### Upgrade Notes

**Version 1.0.10+**
- Added Ingress support (disabled by default)
- Enhanced CI/CD testing with kind cluster validation
- Improved ConfigMap and Secret handling

**Breaking Changes**
- None in current version

**Migration Guide**
- If upgrading from a version without Ingress support, no changes required (Ingress is disabled by default)
- To enable Ingress, add the `ingress` section to your `values.yaml` with `enabled: true`

### Breaking Changes Documentation

Breaking changes are documented in the `Chart.yaml` annotations section using the `artifacthub.io/breakingChanges` annotation. When a breaking change is introduced:

1. **Documentation**: The breaking change is documented in `Chart.yaml` with:
   - Description of the change
   - Impact on users
   - Migration instructions

2. **Version Bumping**: Breaking changes result in a major version bump (e.g., 1.0.0 → 2.0.0)

3. **Upgrade Notes**: Users should review the `Chart.yaml` annotations before upgrading to identify any breaking changes

Example breaking change format in `Chart.yaml`:
```yaml
annotations:
  artifacthub.io/breakingChanges: |
    - description: "Changed default service type from ClusterIP to NodePort"
      impact: "Existing deployments will need to update their service configuration"
      migration: "Set service.type: ClusterIP in values.yaml if you want to maintain previous behavior"
```

### Preserving Custom Values During Upgrade

Helm preserves your custom values during upgrades. However, if you want to ensure specific values are maintained:

1. **Save your current values:**
   ```bash
   helm get values my-api > my-values.yaml
   ```

2. **Upgrade with saved values:**
   ```bash
   helm upgrade my-api iklobato/pylight -f my-values.yaml
   ```

3. **Verify the upgrade:**
   ```bash
   helm status my-api
   kubectl get pods -l app.kubernetes.io/name=pylight
   ```

## Uninstalling

To uninstall/delete the deployment:

```bash
helm uninstall my-api
```

This removes all resources created by the chart (Deployment, Service, Secret, ConfigMap).

## Troubleshooting

### Pods Not Starting

1. Check pod status:
   ```bash
   kubectl describe pod <pod-name>
   ```

2. Check logs:
   ```bash
   kubectl logs <pod-name>
   ```

3. Common issues:
   - Invalid database connection string
   - Database not reachable from cluster
   - YAML configuration syntax errors
   - Missing required configuration values

### Health Checks Failing

1. Test health endpoint manually:
   ```bash
   kubectl exec <pod-name> -- curl http://localhost:8000/health
   ```

2. Verify health check configuration in `values.yaml`

3. Check if the `/health` endpoint is accessible (should return `{"status": "healthy"}`)

### Configuration Not Applied

1. Check ConfigMap:
   ```bash
   kubectl get configmap <release-name>-pylight-configmap -o yaml
   ```

2. Verify pod is using correct config:
   ```bash
   kubectl describe pod <pod-name> | grep -A 10 "Environment"
   ```

3. Check if pod restarted after config change (look for annotation `checksum/config`)

### Database Connection Issues

1. Verify database is accessible from cluster:
   ```bash
   kubectl run -it --rm debug --image=postgres:15 --restart=Never -- psql <connection-string>
   ```

2. Check Secret contains correct connection string:
   ```bash
   kubectl get secret <release-name>-pylight-secret -o jsonpath='{.data.connection-string}' | base64 -d
   ```

3. Verify network policies allow pod-to-database communication

## Testing

Run Helm tests:

```bash
helm test my-api
```

This executes the test pod defined in `templates/tests/test-connection.yaml`, which verifies the API health endpoint is accessible.

## Template Simplification

This Helm chart has been simplified to reduce template complexity by **30.8%** (from 13 to 9 conditional branches) while maintaining full backward compatibility. The simplification uses default values (`createConfigMap: true`, `createSecret: true`) and always creates resources by default, with flags to use existing resources when specified.

**Simplification Metrics:**
- **Baseline**: 13 conditional branches across templates
- **After simplification**: 9 conditional branches
- **Reduction**: 30.8%
- **Backward compatibility**: 100% (all existing configurations continue to work)

## Values Schema

The chart includes a JSON schema for values validation (`values.schema.json`). Helm will automatically validate your `values.yaml` against this schema before deployment.

## Support

- Documentation: [https://pylight.dev](https://pylight.dev)
- Issues: [https://github.com/iklobato/pylight/issues](https://github.com/iklobato/pylight/issues)
- Quick Start Guide: [specs/001-helm-chart/quickstart.md](../../specs/001-helm-chart/quickstart.md)

## License

This chart is licensed under the same license as Pylight.

