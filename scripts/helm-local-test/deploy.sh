#!/usr/bin/env bash
# Deploy Helm chart to minikube cluster

set -euo pipefail

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Default values
VALUES_FILE="${DEFAULT_VALUES_FILE}"
RELEASE_NAME="${DEFAULT_RELEASE_NAME}"
NAMESPACE="${DEFAULT_NAMESPACE}"
TIMEOUT=120  # 2 minutes for deployment
CLEANUP_ON_FAILURE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--values)
            VALUES_FILE="$2"
            shift 2
            ;;
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
        --cleanup-on-failure)
            CLEANUP_ON_FAILURE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Deploy Pylight Helm chart to minikube cluster"
            echo ""
            echo "Options:"
            echo "  -f, --values FILE      Path to values file (default: $DEFAULT_VALUES_FILE)"
            echo "  -r, --release NAME     Helm release name (default: $DEFAULT_RELEASE_NAME)"
            echo "  -n, --namespace NAME   Kubernetes namespace (default: $DEFAULT_NAMESPACE)"
            echo "  --timeout SECONDS      Deployment timeout in seconds (default: 120)"
            echo "  --cleanup-on-failure   Clean up on deployment failure"
            echo "  -h, --help             Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Main deployment function
main() {
    log_info "Deploying Helm chart to minikube"
    log_info "Release name: $RELEASE_NAME"
    log_info "Namespace: $NAMESPACE"
    log_info "Values file: $VALUES_FILE"
    
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
    
    # Check if release already exists
    if helm list -n "$NAMESPACE" -q | grep -q "^${RELEASE_NAME}$"; then
        log_warn "Release '$RELEASE_NAME' already exists"
        log_info "Use upgrade.sh to update an existing release, or cleanup.sh to remove it first"
        exit 1
    fi
    
    # Deploy chart
    log_info "Installing Helm chart..."
    log_debug "Chart directory: $CHART_DIR"
    log_debug "Values file: $VALUES_FILE"
    
    # Ensure values file path is absolute
    local abs_values_file
    if [[ "$VALUES_FILE" = /* ]]; then
        abs_values_file="$VALUES_FILE"
    else
        abs_values_file="$(cd "$(dirname "$VALUES_FILE")" && pwd)/$(basename "$VALUES_FILE")"
    fi
    
    # Use absolute path for chart directory
    if ! helm install "$RELEASE_NAME" "$CHART_DIR" \
        -f "$abs_values_file" \
        -n "$NAMESPACE" \
        --create-namespace \
        --wait \
        --timeout "${TIMEOUT}s"; then
        log_error "Helm chart deployment failed"
        
        if [[ "$CLEANUP_ON_FAILURE" == "true" ]]; then
            log_info "Cleaning up failed deployment..."
            helm uninstall "$RELEASE_NAME" -n "$NAMESPACE" 2>/dev/null || true
        fi
        exit 1
    fi
    
    log_info "✓ Helm chart deployed successfully"
    
    # Wait for pods to be ready
    if wait_for_pods_ready "$RELEASE_NAME" "$NAMESPACE" "$TIMEOUT"; then
        log_info "✓ Deployment completed successfully"
        log_info "Release name: $RELEASE_NAME"
        log_info "To validate deployment, run: ./scripts/helm-local-test/validate.sh -r $RELEASE_NAME"
        return 0
    else
        log_error "Deployment completed but pods are not ready"
        
        if [[ "$CLEANUP_ON_FAILURE" == "true" ]]; then
            log_info "Cleaning up failed deployment..."
            helm uninstall "$RELEASE_NAME" -n "$NAMESPACE" 2>/dev/null || true
        else
            preserve_logs "$RELEASE_NAME" "$NAMESPACE"
        fi
        
        exit 1
    fi
}

# Run main function
main "$@"

