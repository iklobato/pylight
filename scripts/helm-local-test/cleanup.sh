#!/usr/bin/env bash
# Cleanup script for Helm chart test resources

set -euo pipefail

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Default values
RELEASE_NAME="${DEFAULT_RELEASE_NAME}"
NAMESPACE="${DEFAULT_NAMESPACE}"
FORCE=false

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
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -r, --release NAME    Helm release name (default: $DEFAULT_RELEASE_NAME)"
            echo "  -n, --namespace NAME Kubernetes namespace (default: $DEFAULT_NAMESPACE)"
            echo "  --force              Force cleanup even if resources don't exist"
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

# Main cleanup function
main() {
    log_info "Cleaning up Helm release: $RELEASE_NAME in namespace: $NAMESPACE"
    
    # Check if release exists
    if ! helm list -n "$NAMESPACE" -q | grep -q "^${RELEASE_NAME}$"; then
        if [[ "$FORCE" == "true" ]]; then
            log_warn "Release '$RELEASE_NAME' not found, but --force is set, continuing..."
        else
            log_warn "Release '$RELEASE_NAME' not found in namespace '$NAMESPACE'"
            log_info "Nothing to clean up"
            return 0
        fi
    fi
    
    # Uninstall Helm release
    log_info "Uninstalling Helm release: $RELEASE_NAME"
    if helm uninstall "$RELEASE_NAME" -n "$NAMESPACE" 2>/dev/null; then
        log_info "✓ Helm release uninstalled successfully"
    else
        if [[ "$FORCE" == "true" ]]; then
            log_warn "Failed to uninstall release (may not exist), continuing..."
        else
            log_error "Failed to uninstall Helm release"
            return 1
        fi
    fi
    
    # Wait a bit for resources to be deleted
    sleep 2
    
    # Verify resources are removed
    log_info "Verifying resources are removed..."
    
    local resources_remaining=0
    local failed_resources=()
    
    # Check for pods
    local pods
    pods=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" \
        -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    if [[ -n "$pods" ]]; then
        log_warn "Some pods still exist: $pods"
        failed_resources+=("pods: $pods")
        resources_remaining=$((resources_remaining + 1))
    fi
    
    # Check for services
    local services
    services=$(kubectl get svc -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" \
        -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    if [[ -n "$services" ]]; then
        log_warn "Some services still exist: $services"
        failed_resources+=("services: $services")
        resources_remaining=$((resources_remaining + 1))
    fi
    
    # Check for configmaps
    local configmaps
    configmaps=$(kubectl get configmap -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" \
        -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    if [[ -n "$configmaps" ]]; then
        log_warn "Some ConfigMaps still exist: $configmaps"
        failed_resources+=("configmaps: $configmaps")
        resources_remaining=$((resources_remaining + 1))
    fi
    
    # Check for secrets
    local secrets
    secrets=$(kubectl get secret -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" \
        -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    if [[ -n "$secrets" ]]; then
        log_warn "Some Secrets still exist: $secrets"
        failed_resources+=("secrets: $secrets")
        resources_remaining=$((resources_remaining + 1))
    fi
    
    # Check for deployments
    local deployments
    deployments=$(kubectl get deployment -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" \
        -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    if [[ -n "$deployments" ]]; then
        log_warn "Some Deployments still exist: $deployments"
        failed_resources+=("deployments: $deployments")
        resources_remaining=$((resources_remaining + 1))
    fi
    
    if [[ $resources_remaining -eq 0 ]]; then
        log_info "✓ All resources removed successfully"
    else
        log_warn "Some resources may still exist. They will be cleaned up by Kubernetes garbage collection."
        log_warn "Remaining resources:"
        for resource in "${failed_resources[@]}"; do
            log_warn "  - $resource"
        done
    fi
    
    log_info "Cleanup completed"
    return 0
}

# Run main function
main "$@"

