#!/usr/bin/env bash
# Test horizontal scaling scenarios

set -euo pipefail

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Default values
RELEASE_NAME="${DEFAULT_RELEASE_NAME}"
REPLICAS=""
NAMESPACE="${DEFAULT_NAMESPACE}"
TIMEOUT=300

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--release)
            RELEASE_NAME="$2"
            shift 2
            ;;
        --replicas)
            REPLICAS="$2"
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
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Test horizontal scaling scenarios"
            echo ""
            echo "Options:"
            echo "  -r, --release NAME    Helm release name (default: $DEFAULT_RELEASE_NAME)"
            echo "  --replicas COUNT      Target replica count (required)"
            echo "  -n, --namespace NAME Kubernetes namespace (default: $DEFAULT_NAMESPACE)"
            echo "  --timeout SECONDS    Scaling timeout in seconds (default: 300)"
            echo "  -h, --help           Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$REPLICAS" ]]; then
    log_error "Replica count is required. Use --replicas to specify."
    exit 1
fi

# Validate replica count is a positive integer
if ! [[ "$REPLICAS" =~ ^[1-9][0-9]*$ ]]; then
    log_error "Replica count must be a positive integer: $REPLICAS"
    exit 1
fi

# Main scaling function
main() {
    log_info "Testing horizontal scaling"
    log_info "Release name: $RELEASE_NAME"
    log_info "Target replicas: $REPLICAS"
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
    
    # Get current replica count
    local current_replicas
    current_replicas=$(kubectl get deployment -n "$NAMESPACE" \
        -l "app.kubernetes.io/instance=$RELEASE_NAME" \
        -o jsonpath='{.items[0].spec.replicas}' 2>/dev/null || echo "1")
    
    log_info "Current replicas: $current_replicas"
    log_info "Target replicas: $REPLICAS"
    
    if [[ "$current_replicas" == "$REPLICAS" ]]; then
        log_warn "Release already has $REPLICAS replicas"
        log_info "No scaling needed"
        return 0
    fi
    
    # Update replica count via helm upgrade
    log_info "Scaling to $REPLICAS replicas..."
    if ! helm upgrade "$RELEASE_NAME" "$CHART_DIR" \
        -n "$NAMESPACE" \
        --reuse-values \
        --set "replicaCount=$REPLICAS" \
        --wait \
        --timeout "${TIMEOUT}s"; then
        log_error "Helm upgrade failed during scaling"
        preserve_logs "$RELEASE_NAME" "$NAMESPACE"
        exit 1
    fi
    
    log_info "✓ Helm upgrade completed"
    
    # Wait for scaling to complete
    log_info "Waiting for scaling to complete..."
    if ! wait_for_pods_ready "$RELEASE_NAME" "$NAMESPACE" "$TIMEOUT"; then
        log_error "Scaling completed but pods are not ready"
        preserve_logs "$RELEASE_NAME" "$NAMESPACE"
        exit 1
    fi
    
    # Verify correct number of pods
    log_info "Verifying pod count..."
    local pod_count
    pod_count=$(kubectl get pods -n "$NAMESPACE" \
        -l "app.kubernetes.io/instance=$RELEASE_NAME" \
        -o jsonpath='{.items[*].metadata.name}' 2>/dev/null | \
        wc -w | tr -d ' ')
    
    if [[ "$pod_count" -eq "$REPLICAS" ]]; then
        log_info "✓ Correct number of pods: $pod_count"
    else
        log_error "✗ Incorrect pod count: expected $REPLICAS, found $pod_count"
        preserve_logs "$RELEASE_NAME" "$NAMESPACE"
        exit 1
    fi
    
    # Verify all pods are healthy
    log_info "Verifying all pods are healthy..."
    local ready_count
    ready_count=$(kubectl get pods -n "$NAMESPACE" \
        -l "app.kubernetes.io/instance=$RELEASE_NAME" \
        -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null | \
        grep -o "True" | wc -l | tr -d ' ')
    
    if [[ "$ready_count" -eq "$REPLICAS" ]]; then
        log_info "✓ All $ready_count pod(s) are ready"
    else
        log_error "✗ Not all pods are ready: $ready_count/$REPLICAS"
        preserve_logs "$RELEASE_NAME" "$NAMESPACE"
        exit 1
    fi
    
    # Test load distribution (basic check - verify all pods can handle requests)
    log_info "Testing load distribution..."
    local pods
    pods=$(kubectl get pods -n "$NAMESPACE" \
        -l "app.kubernetes.io/instance=$RELEASE_NAME" \
        -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    
    local successful_requests=0
    local total_requests=0
    
    for pod in $pods; do
        total_requests=$((total_requests + 1))
        if kubectl exec -n "$NAMESPACE" "$pod" -- \
            curl -sf http://localhost:8000/health >/dev/null 2>&1; then
            successful_requests=$((successful_requests + 1))
            log_debug "✓ Pod $pod can handle requests"
        else
            log_warn "⚠ Pod $pod cannot handle requests"
        fi
    done
    
    if [[ $successful_requests -eq $total_requests ]] && [[ $total_requests -gt 0 ]]; then
        log_info "✓ All $total_requests pod(s) can handle requests"
    else
        log_warn "⚠ Only $successful_requests/$total_requests pod(s) can handle requests"
    fi
    
    log_info "✓ Scaling completed successfully"
    log_info "Current replicas: $REPLICAS"
    return 0
}

# Run main function
main "$@"

