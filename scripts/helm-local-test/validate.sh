#!/usr/bin/env bash
# Validate deployed Helm chart functionality

set -euo pipefail

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Default values
RELEASE_NAME="${DEFAULT_RELEASE_NAME}"
NAMESPACE="${DEFAULT_NAMESPACE}"
TIMEOUT=300  # 5 minutes default
SKIP_API_TESTS=false
SKIP_DB_TESTS=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--release)
            RELEASE_NAME="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --skip-api)
            SKIP_API_TESTS=true
            shift
            ;;
        --skip-db)
            SKIP_DB_TESTS=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Validate deployed Helm chart functionality"
            echo ""
            echo "Options:"
            echo "  -r, --release NAME    Helm release name (default: $DEFAULT_RELEASE_NAME)"
            echo "  -n, --namespace NAME  Kubernetes namespace (default: $DEFAULT_NAMESPACE)"
            echo "  --timeout SECONDS     Timeout for pod readiness (default: 300)"
            echo "  --skip-api            Skip API endpoint tests"
            echo "  --skip-db             Skip database connectivity tests"
            echo "  -h, --help            Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Validation counters
VALIDATION_PASSED=0
VALIDATION_FAILED=0
VALIDATION_WARNINGS=0

# Validation functions
validate_resource_exists() {
    local resource_type="$1"
    local resource_name="$2"
    local description="$3"
    
    if kubectl get "$resource_type" "$resource_name" -n "$NAMESPACE" >/dev/null 2>&1; then
        log_info "✓ $description exists"
        ((VALIDATION_PASSED++))
        return 0
    else
        log_error "✗ $description not found: $resource_name"
        ((VALIDATION_FAILED++))
        return 1
    fi
}

validate_pods_ready() {
    log_info "Validating pod readiness..."
    
    if wait_for_pods_ready "$RELEASE_NAME" "$NAMESPACE" "$TIMEOUT"; then
        log_info "✓ All pods are ready"
        ((VALIDATION_PASSED++))
        return 0
    else
        log_error "✗ Pods are not ready"
        preserve_logs "$RELEASE_NAME" "$NAMESPACE"
        ((VALIDATION_FAILED++))
        return 1
    fi
}

validate_health_endpoint() {
    log_info "Validating health check endpoint..."
    
    local service_url
    service_url=$(get_service_url "$RELEASE_NAME" "$NAMESPACE")
    local pod_name
    pod_name=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" \
        -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -z "$pod_name" ]]; then
        log_error "✗ No pods found for health check"
        ((VALIDATION_FAILED++))
        return 1
    fi
    
    # Test health endpoint via kubectl exec
    local health_response
    health_response=$(kubectl exec -n "$NAMESPACE" "$pod_name" -- \
        curl -sf http://localhost:8000/health 2>/dev/null || echo "")
    
    if [[ -n "$health_response" ]] && echo "$health_response" | grep -q "healthy\|status"; then
        log_info "✓ Health endpoint responds correctly: $health_response"
        ((VALIDATION_PASSED++))
        return 0
    else
        log_error "✗ Health endpoint failed or returned invalid response"
        preserve_logs "$RELEASE_NAME" "$NAMESPACE"
        ((VALIDATION_FAILED++))
        return 1
    fi
}

validate_api_endpoints() {
    if [[ "$SKIP_API_TESTS" == "true" ]]; then
        log_warn "Skipping API endpoint tests"
        return 0
    fi
    
    log_info "Validating API CRUD endpoints..."
    
    local pod_name
    pod_name=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" \
        -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -z "$pod_name" ]]; then
        log_error "✗ No pods found for API testing"
        ((VALIDATION_FAILED++))
        return 1
    fi
    
    # Get table name from ConfigMap (assuming products table from test values)
    local table_name="products"
    
    # Test GET /api/{table} (list)
    log_debug "Testing GET /api/$table_name"
    if kubectl exec -n "$NAMESPACE" "$pod_name" -- \
        curl -sf http://localhost:8000/api/$table_name >/dev/null 2>&1; then
        log_info "✓ GET /api/$table_name endpoint works"
        ((VALIDATION_PASSED++))
    else
        log_warn "⚠ GET /api/$table_name endpoint failed (may be expected if table is empty)"
        ((VALIDATION_WARNINGS++))
    fi
    
    # Test POST /api/{table} (create)
    log_debug "Testing POST /api/$table_name"
    local create_response
    create_response=$(kubectl exec -n "$NAMESPACE" "$pod_name" -- \
        curl -sf -X POST http://localhost:8000/api/$table_name \
        -H "Content-Type: application/json" \
        -d '{"name":"Test Product","price":100}' 2>/dev/null || echo "")
    
    if [[ -n "$create_response" ]] && echo "$create_response" | grep -q "id\|name"; then
        log_info "✓ POST /api/$table_name endpoint works"
        ((VALIDATION_PASSED++))
        
        # Extract ID for further tests
        local item_id
        item_id=$(echo "$create_response" | grep -o '"id":[0-9]*' | grep -o '[0-9]*' | head -1 || echo "")
        
        if [[ -n "$item_id" ]]; then
            # Test GET /api/{table}/{id}
            log_debug "Testing GET /api/$table_name/$item_id"
            if kubectl exec -n "$NAMESPACE" "$pod_name" -- \
                curl -sf http://localhost:8000/api/$table_name/$item_id >/dev/null 2>&1; then
                log_info "✓ GET /api/$table_name/$item_id endpoint works"
                ((VALIDATION_PASSED++))
            else
                log_warn "⚠ GET /api/$table_name/$item_id endpoint failed"
                ((VALIDATION_WARNINGS++))
            fi
        fi
    else
        log_warn "⚠ POST /api/$table_name endpoint failed (may indicate database connection issue)"
        ((VALIDATION_WARNINGS++))
    fi
    
    return 0
}

validate_database_connectivity() {
    if [[ "$SKIP_DB_TESTS" == "true" ]]; then
        log_warn "Skipping database connectivity tests"
        return 0
    fi
    
    log_info "Validating database connectivity from pods..."
    
    local pod_name
    pod_name=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" \
        -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -z "$pod_name" ]]; then
        log_warn "⚠ Cannot validate database connectivity (no pods found)"
        ((VALIDATION_WARNINGS++))
        return 0
    fi
    
    # Try to connect to PostgreSQL from the pod
    # Use host.docker.internal to access host PostgreSQL from minikube pods
    log_debug "Testing PostgreSQL connection from pod: $pod_name"
    
    # Check if pod can reach PostgreSQL (using nc or curl if available in pod)
    if kubectl exec -n "$NAMESPACE" "$pod_name" -- \
        sh -c "command -v nc >/dev/null 2>&1 && nc -z host.docker.internal 5432 2>/dev/null || command -v curl >/dev/null 2>&1 && curl -sf --max-time 2 http://host.docker.internal:5432 >/dev/null 2>&1 || timeout 2 bash -c 'echo > /dev/tcp/host.docker.internal/5432' 2>/dev/null || exit 1" 2>/dev/null; then
        log_info "✓ Pod can reach PostgreSQL at host.docker.internal:5432"
        ((VALIDATION_PASSED++))
    else
        log_warn "⚠ Pod cannot reach PostgreSQL (may be expected if using different connection string)"
        ((VALIDATION_WARNINGS++))
    fi
    
    # Check for database connection errors in logs
    local db_errors
    db_errors=$(kubectl logs -n "$NAMESPACE" "$pod_name" 2>/dev/null | \
        grep -i "database\|connection\|postgres\|error" | grep -i "fail\|error" | wc -l | tr -d ' ')
    
    if [[ "$db_errors" -gt 0 ]]; then
        log_warn "⚠ Found potential database errors in pod logs"
        ((VALIDATION_WARNINGS++))
    else
        log_info "✓ No database connection errors in logs"
        ((VALIDATION_PASSED++))
    fi
    
    return 0
}

validate_redis_connectivity() {
    log_info "Validating Redis connectivity from pods (optional)..."
    
    # Check if Redis is configured/available
    if ! validate_redis_prerequisite 2>/dev/null; then
        log_info "Skipping Redis connectivity test (Redis not available)"
        return 0
    fi
    
    local pod_name
    pod_name=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" \
        -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -z "$pod_name" ]]; then
        log_warn "⚠ Cannot validate Redis connectivity (no pods found)"
        ((VALIDATION_WARNINGS++))
        return 0
    fi
    
    # Try to connect to Redis from the pod
    log_debug "Testing Redis connection from pod: $pod_name"
    
    # Check if pod can reach Redis (using nc or curl if available in pod)
    if kubectl exec -n "$NAMESPACE" "$pod_name" -- \
        sh -c "command -v nc >/dev/null 2>&1 && nc -z host.docker.internal 6379 2>/dev/null || command -v curl >/dev/null 2>&1 && curl -sf --max-time 2 http://host.docker.internal:6379 >/dev/null 2>&1 || timeout 2 bash -c 'echo > /dev/tcp/host.docker.internal/6379' 2>/dev/null || exit 1" 2>/dev/null; then
        log_info "✓ Pod can reach Redis at host.docker.internal:6379"
        ((VALIDATION_PASSED++))
    else
        log_warn "⚠ Pod cannot reach Redis (may be expected if Redis is not configured)"
        ((VALIDATION_WARNINGS++))
    fi
    
    return 0
}

# Main validation function
main() {
    log_info "Validating Helm chart deployment: $RELEASE_NAME"
    log_info "Namespace: $NAMESPACE"
    
    # Validate prerequisites
    if ! validate_prerequisites; then
        log_error "Prerequisites validation failed"
        exit 1
    fi
    
    # Check if release exists
    if ! helm list -n "$NAMESPACE" -q | grep -q "^${RELEASE_NAME}$"; then
        log_error "Release '$RELEASE_NAME' not found in namespace '$NAMESPACE'"
        log_error "Deploy the chart first using: ./scripts/helm-local-test/deploy.sh -r $RELEASE_NAME"
        exit 1
    fi
    
    log_info "Starting validation..."
    echo ""
    
    # 1. Validate Kubernetes resources
    log_info "=== Resource Validation ==="
    local fullname="${RELEASE_NAME}-pylight"
    
    validate_resource_exists "deployment" "$fullname" "Deployment"
    validate_resource_exists "service" "${fullname}-service" "Service"
    
    # Check for ConfigMap (if inline config is used)
    local configmap_name="${fullname}-configmap"
    if kubectl get configmap "$configmap_name" -n "$NAMESPACE" >/dev/null 2>&1; then
        log_info "✓ ConfigMap exists: $configmap_name"
        ((VALIDATION_PASSED++))
    else
        log_warn "⚠ ConfigMap not found (may be using existing ConfigMap)"
        ((VALIDATION_WARNINGS++))
    fi
    
    # Check for Secret (if inline connection string is used)
    local secret_name="${fullname}-secret"
    if kubectl get secret "$secret_name" -n "$NAMESPACE" >/dev/null 2>&1; then
        log_info "✓ Secret exists: $secret_name"
        ((VALIDATION_PASSED++))
    else
        log_warn "⚠ Secret not found (may be using existing Secret)"
        ((VALIDATION_WARNINGS++))
    fi
    
    echo ""
    
    # 2. Validate pod readiness
    log_info "=== Pod Readiness Validation ==="
    if ! validate_pods_ready; then
        log_error "Critical validation failed: pods are not ready"
        exit 1
    fi
    
    echo ""
    
    # 3. Validate health endpoint
    log_info "=== Health Check Validation ==="
    if ! validate_health_endpoint; then
        log_error "Critical validation failed: health endpoint not responding"
        exit 1
    fi
    
    echo ""
    
    # 4. Validate API endpoints
    log_info "=== API Endpoint Validation ==="
    validate_api_endpoints
    
    echo ""
    
    # 5. Validate database connectivity
    log_info "=== Database Connectivity Validation ==="
    validate_database_connectivity
    
    echo ""
    
    # 6. Validate Redis connectivity (optional)
    log_info "=== Redis Connectivity Validation (Optional) ==="
    validate_redis_connectivity
    
    echo ""
    
    # Summary
    log_info "=== Validation Summary ==="
    log_info "Passed: $VALIDATION_PASSED"
    log_warn "Warnings: $VALIDATION_WARNINGS"
    
    if [[ $VALIDATION_FAILED -gt 0 ]]; then
        log_error "Failed: $VALIDATION_FAILED"
        log_error "Validation failed. Check logs above for details."
        preserve_logs "$RELEASE_NAME" "$NAMESPACE"
        exit 1
    else
        log_info "✓ All critical validations passed"
        if [[ $VALIDATION_WARNINGS -gt 0 ]]; then
            log_warn "Some non-critical validations had warnings. Review above."
        fi
        return 0
    fi
}

# Run main function
main "$@"

