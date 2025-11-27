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
TEST_SEQUENCE=false  # If true, test scaling from 1 to 5 replicas sequentially

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
        --test-sequence)
            TEST_SEQUENCE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Test horizontal scaling scenarios"
            echo ""
            echo "Options:"
            echo "  -r, --release NAME    Helm release name (default: $DEFAULT_RELEASE_NAME)"
            echo "  --replicas COUNT      Target replica count (required, unless --test-sequence)"
            echo "  -n, --namespace NAME Kubernetes namespace (default: $DEFAULT_NAMESPACE)"
            echo "  --timeout SECONDS    Scaling timeout in seconds (default: 300)"
            echo "  --test-sequence       Test scaling from 1 to 5 replicas sequentially"
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
if [[ "$TEST_SEQUENCE" == "false" ]] && [[ -z "$REPLICAS" ]]; then
    log_error "Replica count is required. Use --replicas to specify, or --test-sequence to test 1-5."
    exit 1
fi

# Validate replica count is a positive integer (if provided)
if [[ -n "$REPLICAS" ]] && ! [[ "$REPLICAS" =~ ^[1-9][0-9]*$ ]]; then
    log_error "Replica count must be a positive integer: $REPLICAS"
    exit 1
fi

# If test sequence, validate replica count is within range
if [[ "$TEST_SEQUENCE" == "true" ]] && [[ -n "$REPLICAS" ]]; then
    if [[ "$REPLICAS" -lt 1 ]] || [[ "$REPLICAS" -gt 5 ]]; then
        log_error "For test sequence, replica count must be between 1 and 5: $REPLICAS"
        exit 1
    fi
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

# Test scaling sequence from 1 to 5 replicas
test_scaling_sequence() {
    log_info "Testing scaling sequence from 1 to 5 replicas..."
    
    local max_replicas=5
    local test_replicas=1
    
    # Start from 1 replica
    log_info "=== Starting scaling sequence test ==="
    
    while [[ $test_replicas -le $max_replicas ]]; do
        log_info ""
        log_info "=== Testing with $test_replicas replica(s) ==="
        
        # Scale to current test replica count
        REPLICAS=$test_replicas
        
        # Perform scaling (reuse main logic but don't exit on error, continue sequence)
        local current_replicas
        current_replicas=$(kubectl get deployment -n "$NAMESPACE" \
            -l "app.kubernetes.io/instance=$RELEASE_NAME" \
            -o jsonpath='{.items[0].spec.replicas}' 2>/dev/null || echo "1")
        
        if [[ "$current_replicas" != "$test_replicas" ]]; then
            log_info "Scaling from $current_replicas to $test_replicas replicas..."
            if ! helm upgrade "$RELEASE_NAME" "$CHART_DIR" \
                -n "$NAMESPACE" \
                --reuse-values \
                --set "replicaCount=$test_replicas" \
                --wait \
                --timeout "${TIMEOUT}s"; then
                log_error "Failed to scale to $test_replicas replicas"
                preserve_logs "$RELEASE_NAME" "$NAMESPACE"
                return 1
            fi
            
            # Wait for pods to be ready
            if ! wait_for_pods_ready "$RELEASE_NAME" "$NAMESPACE" "$TIMEOUT"; then
                log_error "Pods not ready at $test_replicas replicas"
                preserve_logs "$RELEASE_NAME" "$NAMESPACE"
                return 1
            fi
        else
            log_info "Already at $test_replicas replicas, validating..."
        fi
        
        # Validate pod count
        local pod_count
        pod_count=$(kubectl get pods -n "$NAMESPACE" \
            -l "app.kubernetes.io/instance=$RELEASE_NAME" \
            -o jsonpath='{.items[*].metadata.name}' 2>/dev/null | \
            wc -w | tr -d ' ')
        
        if [[ "$pod_count" -eq "$test_replicas" ]]; then
            log_info "✓ Correct pod count: $pod_count"
        else
            log_error "✗ Incorrect pod count: expected $test_replicas, found $pod_count"
            preserve_logs "$RELEASE_NAME" "$NAMESPACE"
            return 1
        fi
        
        # Verify all pods are healthy
        local ready_count
        ready_count=$(kubectl get pods -n "$NAMESPACE" \
            -l "app.kubernetes.io/instance=$RELEASE_NAME" \
            -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null | \
            grep -o "True" | wc -l | tr -d ' ')
        
        if [[ "$ready_count" -eq "$test_replicas" ]]; then
            log_info "✓ All $ready_count pod(s) are ready"
        else
            log_error "✗ Not all pods ready: $ready_count/$test_replicas"
            preserve_logs "$RELEASE_NAME" "$NAMESPACE"
            return 1
        fi
        
        # Test health endpoint on all pods
        local pods
        pods=$(kubectl get pods -n "$NAMESPACE" \
            -l "app.kubernetes.io/instance=$RELEASE_NAME" \
            -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
        
        local healthy_pods=0
        for pod in $pods; do
            if kubectl exec -n "$NAMESPACE" "$pod" -- \
                curl -sf http://localhost:8000/health >/dev/null 2>&1; then
                healthy_pods=$((healthy_pods + 1))
            fi
        done
        
        if [[ $healthy_pods -eq $test_replicas ]]; then
            log_info "✓ All $test_replicas pod(s) can handle requests"
        else
            log_warn "⚠ Only $healthy_pods/$test_replicas pod(s) can handle requests"
        fi
        
        log_info "✓ Validation complete for $test_replicas replica(s)"
        
        # Increment for next iteration
        test_replicas=$((test_replicas + 1))
    done
    
    log_info ""
    log_info "=== Scaling sequence test completed successfully ==="
    log_info "Tested scaling from 1 to $max_replicas replicas"
    return 0
}

# Run main function
main() {
    if [[ "$TEST_SEQUENCE" == "true" ]]; then
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
        
        test_scaling_sequence
    else
        # Original main logic for single replica scaling
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
    fi
}

# Run main function
main "$@"

