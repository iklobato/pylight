#!/usr/bin/env bash
# Common helper functions for Helm local test scripts
# 
# This script provides common functions used by all Helm local test scripts:
# - Prerequisite validation
# - Logging functions
# - YAML validation
# - Pod readiness checking
# - Log preservation

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHART_DIR="$(cd "${SCRIPT_DIR}/../../charts/pylight" && pwd)"

# Default values
DEFAULT_RELEASE_NAME="pylight-test"
DEFAULT_NAMESPACE="default"
DEFAULT_VALUES_FILE="${SCRIPT_DIR}/test-values.yaml"
DEFAULT_TIMEOUT=300

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_debug() {
    if [[ "${DEBUG:-}" == "1" ]]; then
        echo -e "[DEBUG] $*"
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Validate PostgreSQL prerequisite
validate_postgres_prerequisite() {
    log_info "Validating PostgreSQL availability..."
    
    if ! command_exists psql; then
        log_warn "psql not found, attempting connection test with nc/curl..."
    fi
    
    # Try to connect to PostgreSQL on localhost:5432
    if command_exists psql; then
        if PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d postgres -c "SELECT 1;" >/dev/null 2>&1; then
            log_info "✓ PostgreSQL is accessible at localhost:5432"
            return 0
        fi
    elif command_exists nc; then
        if nc -z localhost 5432 >/dev/null 2>&1; then
            log_info "✓ PostgreSQL port 5432 is open on localhost"
            return 0
        fi
    elif command_exists curl; then
        # PostgreSQL doesn't respond to HTTP, but we can check if port is open
        if timeout 1 bash -c "echo > /dev/tcp/localhost/5432" 2>/dev/null; then
            log_info "✓ PostgreSQL port 5432 is open on localhost"
            return 0
        fi
    fi
    
    log_error "PostgreSQL is not accessible at localhost:5432"
    log_error "Please ensure PostgreSQL is running:"
    log_error "  docker run -d --name psql -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:latest"
    log_error "  Or start your existing PostgreSQL container"
    return 1
}

# Validate Redis prerequisite (optional)
validate_redis_prerequisite() {
    log_info "Validating Redis availability (optional)..."
    
    # Try to connect to Redis on localhost:6379
    if command_exists redis-cli; then
        if redis-cli -h localhost -p 6379 ping >/dev/null 2>&1; then
            log_info "✓ Redis is accessible at localhost:6379"
            return 0
        fi
    elif command_exists nc; then
        if nc -z localhost 6379 >/dev/null 2>&1; then
            log_info "✓ Redis port 6379 is open on localhost"
            return 0
        fi
    elif command_exists curl; then
        if timeout 1 bash -c "echo > /dev/tcp/localhost/6379" 2>/dev/null; then
            log_info "✓ Redis port 6379 is open on localhost"
            return 0
        fi
    fi
    
    log_warn "Redis is not accessible at localhost:6379 (optional - tests will skip Redis checks)"
    log_warn "To enable Redis testing:"
    log_warn "  docker run -d --name redis -p 6379:6379 redis:latest"
    return 0  # Don't fail, Redis is optional
}

# Validate minikube prerequisite
validate_minikube_prerequisite() {
    log_info "Validating minikube status..."
    
    if ! command_exists minikube; then
        log_error "minikube is not installed"
        log_error "Please install minikube:"
        log_error "  macOS: brew install minikube"
        log_error "  Linux: https://minikube.sigs.k8s.io/docs/start/"
        return 1
    fi
    
    if ! minikube status >/dev/null 2>&1; then
        log_error "minikube is not running"
        log_error "Please start minikube:"
        log_error "  minikube start --driver=docker"
        return 1
    fi
    
    log_info "✓ minikube is running"
    return 0
}

# Validate prerequisites
validate_prerequisites() {
    log_info "Validating prerequisites..."
    
    local missing_tools=()
    
    # Check minikube
    if ! validate_minikube_prerequisite; then
        log_error ""
        log_error "To fix:"
        log_error "  1. Install minikube: https://minikube.sigs.k8s.io/docs/start/"
        log_error "  2. Start minikube: minikube start --driver=docker"
        return 1
    fi
    
    # Check kubectl
    if ! command_exists kubectl; then
        missing_tools+=("kubectl")
    else
        # Verify kubectl context is minikube
        local current_context
        current_context=$(kubectl config current-context 2>/dev/null || echo "")
        if [[ "$current_context" != "minikube" ]]; then
            log_warn "kubectl context is '$current_context', expected 'minikube'"
            log_warn "Some operations may fail. Consider running: kubectl config use-context minikube"
        else
            log_debug "✓ kubectl is configured for minikube"
        fi
    fi
    
    # Check helm
    if ! command_exists helm; then
        missing_tools+=("helm")
    else
        log_debug "✓ helm is installed"
    fi
    
    # Check curl (for API testing)
    if ! command_exists curl; then
        missing_tools+=("curl")
    else
        log_debug "✓ curl is installed"
    fi
    
    # Report missing tools
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error ""
        log_error "To fix:"
        for tool in "${missing_tools[@]}"; do
            case "$tool" in
                kubectl)
                    log_error "  - Install kubectl: https://kubernetes.io/docs/tasks/tools/"
                    ;;
                helm)
                    log_error "  - Install Helm: https://helm.sh/docs/intro/install/"
                    ;;
                curl)
                    log_error "  - Install curl: Usually pre-installed, or use package manager"
                    ;;
            esac
        done
        return 1
    fi
    
    # Verify Helm chart exists
    if [[ ! -d "$CHART_DIR" ]]; then
        log_error "Helm chart not found at: $CHART_DIR"
        return 1
    fi
    log_debug "✓ Helm chart found at $CHART_DIR"
    
    log_info "All prerequisites validated successfully"
    return 0
}

# Validate YAML file
validate_yaml_file() {
    local yaml_file="$1"
    
    if [[ ! -f "$yaml_file" ]]; then
        log_error "YAML file not found: $yaml_file"
        return 1
    fi
    
    # Try to parse YAML (requires yq or python)
    if command_exists yq; then
        if ! yq eval '.' "$yaml_file" >/dev/null 2>&1; then
            log_error "Invalid YAML syntax in: $yaml_file"
            return 1
        fi
    elif command_exists python3; then
        if ! python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
            log_error "Invalid YAML syntax in: $yaml_file"
            return 1
        fi
    else
        log_warn "Cannot validate YAML syntax (yq or python3 not found)"
    fi
    
    log_debug "✓ YAML file is valid: $yaml_file"
    return 0
}

# Wait for pods to be ready
wait_for_pods_ready() {
    local release_name="$1"
    local namespace="${2:-$DEFAULT_NAMESPACE}"
    local timeout="${3:-$DEFAULT_TIMEOUT}"
    
    log_info "Waiting for pods to be ready (timeout: ${timeout}s)..."
    
    local start_time
    start_time=$(date +%s)
    local elapsed=0
    
    while [[ $elapsed -lt $timeout ]]; do
        local ready_count
        local total_count
        
        ready_count=$(kubectl get pods -n "$namespace" -l "app.kubernetes.io/instance=$release_name" \
            --field-selector=status.phase=Running \
            -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null | \
            grep -o "True" | wc -l | tr -d ' ')
        
        total_count=$(kubectl get pods -n "$namespace" -l "app.kubernetes.io/instance=$release_name" \
            -o jsonpath='{.items[*].metadata.name}' 2>/dev/null | wc -w | tr -d ' ')
        
        if [[ "$ready_count" -gt 0 ]] && [[ "$ready_count" -eq "$total_count" ]]; then
            log_info "✓ All $ready_count pod(s) are ready"
            return 0
        fi
        
        log_debug "Pods ready: $ready_count/$total_count (elapsed: ${elapsed}s)"
        sleep 2
        
        elapsed=$(($(date +%s) - start_time))
    done
    
    log_error "Timeout waiting for pods to be ready after ${timeout}s"
    return 1
}

# Get service URL
get_service_url() {
    local release_name="$1"
    local namespace="${2:-$DEFAULT_NAMESPACE}"
    local service_name="${release_name}-pylight-service"
    
    echo "${service_name}.${namespace}.svc.cluster.local"
}

# Preserve pod logs, descriptions, and resource state on failure
preserve_logs() {
    local release_name="$1"
    local namespace="${2:-$DEFAULT_NAMESPACE}"
    local log_dir="${SCRIPT_DIR}/logs"
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local session_dir="${log_dir}/${release_name}_${timestamp}"
    
    mkdir -p "$session_dir"
    
    log_info "Preserving diagnostic information to $session_dir..."
    
    # Save pod logs and descriptions
    local pods
    pods=$(kubectl get pods -n "$namespace" -l "app.kubernetes.io/instance=$release_name" \
        -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -z "$pods" ]]; then
        log_warn "No pods found for release: $release_name"
    else
        for pod in $pods; do
            log_debug "Saving logs for pod: $pod"
            kubectl logs -n "$namespace" "$pod" > "${session_dir}/${pod}.log" 2>&1 || true
            kubectl describe pod -n "$namespace" "$pod" > "${session_dir}/${pod}.describe.txt" 2>&1 || true
        done
    fi
    
    # Save resource state
    log_debug "Saving resource state..."
    kubectl get all -n "$namespace" -l "app.kubernetes.io/instance=$release_name" \
        -o yaml > "${session_dir}/resources.yaml" 2>&1 || true
    kubectl get configmap,secret -n "$namespace" -l "app.kubernetes.io/instance=$release_name" \
        -o yaml > "${session_dir}/config-resources.yaml" 2>&1 || true
    kubectl get events -n "$namespace" --sort-by='.lastTimestamp' \
        > "${session_dir}/events.txt" 2>&1 || true
    
    # Save Helm release status
    log_debug "Saving Helm release status..."
    helm status "$release_name" -n "$namespace" > "${session_dir}/helm-status.txt" 2>&1 || true
    helm get values "$release_name" -n "$namespace" > "${session_dir}/helm-values.yaml" 2>&1 || true
    
    log_info "Diagnostic information preserved in $session_dir"
    log_info "Review logs, resource state, and events for troubleshooting"
}

