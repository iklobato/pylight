#!/usr/bin/env bash
# Test Helm chart upgrade scenarios

set -euo pipefail

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Default values
RELEASE_NAME="${DEFAULT_RELEASE_NAME}"
VALUES_FILE=""
NAMESPACE="${DEFAULT_NAMESPACE}"
TIMEOUT=300
ROLLBACK_ON_FAILURE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--release)
            RELEASE_NAME="$2"
            shift 2
            ;;
        -f|--values)
            VALUES_FILE="$2"
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
        --rollback-on-failure)
            ROLLBACK_ON_FAILURE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Test Helm chart upgrade scenarios"
            echo ""
            echo "Options:"
            echo "  -r, --release NAME        Helm release name (default: $DEFAULT_RELEASE_NAME)"
            echo "  -f, --values FILE         Path to updated values file (required)"
            echo "  -n, --namespace NAME      Kubernetes namespace (default: $DEFAULT_NAMESPACE)"
            echo "  --timeout SECONDS         Upgrade timeout in seconds (default: 300)"
            echo "  --rollback-on-failure     Rollback on upgrade failure"
            echo "  -h, --help                Show this help message"
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
if [[ -z "$VALUES_FILE" ]]; then
    log_error "Values file is required. Use -f or --values to specify."
    exit 1
fi

# Main upgrade function
main() {
    log_info "Testing Helm chart upgrade"
    log_info "Release name: $RELEASE_NAME"
    log_info "Namespace: $NAMESPACE"
    log_info "Updated values file: $VALUES_FILE"
    
    # Validate prerequisites
    if ! validate_prerequisites; then
        log_error "Prerequisites validation failed"
        exit 1
    fi
    
    # Validate values file
    if ! validate_yaml_file "$VALUES_FILE"; then
        log_error "Values file validation failed"
        exit 1
    fi
    
    # Check if release exists
    if ! helm list -n "$NAMESPACE" -q | grep -q "^${RELEASE_NAME}$"; then
        log_error "Release '$RELEASE_NAME' not found in namespace '$NAMESPACE'"
        log_error "Deploy the chart first using: ./scripts/helm-local-test/deploy.sh -r $RELEASE_NAME"
        exit 1
    fi
    
    # Get current revision
    local current_revision
    current_revision=$(helm list -n "$NAMESPACE" "$RELEASE_NAME" -o json | \
        grep -o '"revision":[0-9]*' | grep -o '[0-9]*' || echo "1")
    log_info "Current revision: $current_revision"
    
    # Check service availability before upgrade
    log_info "Checking service availability before upgrade..."
    local service_name="${RELEASE_NAME}-pylight-service"
    local service_available_before=false
    
    if kubectl get svc "$service_name" -n "$NAMESPACE" >/dev/null 2>&1; then
        service_available_before=true
        log_info "✓ Service exists before upgrade"
    fi
    
    # Perform upgrade
    log_info "Performing Helm upgrade..."
    if ! helm upgrade "$RELEASE_NAME" "$CHART_DIR" \
        -f "$VALUES_FILE" \
        -n "$NAMESPACE" \
        --wait \
        --timeout "${TIMEOUT}s"; then
        log_error "Helm chart upgrade failed"
        
        if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
            log_info "Rolling back to previous revision..."
            helm rollback "$RELEASE_NAME" -n "$NAMESPACE" --wait || true
        fi
        
        preserve_logs "$RELEASE_NAME" "$NAMESPACE"
        exit 1
    fi
    
    log_info "✓ Helm chart upgraded successfully"
    
    # Wait for rolling update to complete
    log_info "Waiting for rolling update to complete..."
    if ! wait_for_pods_ready "$RELEASE_NAME" "$NAMESPACE" "$TIMEOUT"; then
        log_error "Upgrade completed but pods are not ready"
        
        if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
            log_info "Rolling back to previous revision..."
            helm rollback "$RELEASE_NAME" -n "$NAMESPACE" --wait || true
        else
            preserve_logs "$RELEASE_NAME" "$NAMESPACE"
        fi
        
        exit 1
    fi
    
    # Verify service remains available
    log_info "Verifying service remains available..."
    if kubectl get svc "$service_name" -n "$NAMESPACE" >/dev/null 2>&1; then
        log_info "✓ Service remains available after upgrade"
    else
        log_error "✗ Service not available after upgrade"
        exit 1
    fi
    
    # Verify new configuration is applied
    log_info "Verifying new configuration is applied..."
    local new_revision
    new_revision=$(helm list -n "$NAMESPACE" "$RELEASE_NAME" -o json | \
        grep -o '"revision":[0-9]*' | grep -o '[0-9]*' || echo "1")
    
    if [[ "$new_revision" -gt "$current_revision" ]]; then
        log_info "✓ Configuration updated (revision: $current_revision → $new_revision)"
    else
        log_warn "⚠ Revision did not increase (may indicate no changes)"
    fi
    
    # Run full validation suite
    log_info "Running full validation suite..."
    if "${SCRIPT_DIR}/validate.sh" -r "$RELEASE_NAME" -n "$NAMESPACE"; then
        log_info "✓ All validations passed after upgrade"
        log_info "Upgrade completed successfully"
        return 0
    else
        log_error "Validation failed after upgrade"
        
        if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
            log_info "Rolling back to previous revision..."
            helm rollback "$RELEASE_NAME" -n "$NAMESPACE" --wait || true
        else
            preserve_logs "$RELEASE_NAME" "$NAMESPACE"
        fi
        
        exit 1
    fi
}

# Run main function
main "$@"

