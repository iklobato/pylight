#!/usr/bin/env bash
# Orchestrate complete Helm chart testing workflow
# 
# This script runs the complete test suite:
# 1. Deploy chart
# 2. Validate deployment
# 3. Test scaling (1 to 5 replicas)
# 4. Test upgrades
# 5. Cleanup

set -euo pipefail

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Default values
RELEASE_NAME="${DEFAULT_RELEASE_NAME}"
VALUES_FILE="${DEFAULT_VALUES_FILE}"
NAMESPACE="${DEFAULT_NAMESPACE}"
SKIP_SCALING=false
SKIP_UPGRADE=false
SKIP_CLEANUP=false
DEBUG=false
NON_INTERACTIVE=false

# Exit codes
EXIT_SUCCESS=0
EXIT_ERROR=1
EXIT_PREREQ_FAILURE=2
EXIT_TIMEOUT=3
EXIT_VALIDATION_FAILURE=4

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
        --skip-scaling)
            SKIP_SCALING=true
            shift
            ;;
        --skip-upgrade)
            SKIP_UPGRADE=true
            shift
            ;;
        --skip-cleanup)
            SKIP_CLEANUP=true
            shift
            ;;
        --debug)
            DEBUG=true
            export DEBUG=1
            shift
            ;;
        --non-interactive)
            NON_INTERACTIVE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Orchestrate complete Helm chart testing workflow"
            echo ""
            echo "Options:"
            echo "  -r, --release NAME      Helm release name (default: $DEFAULT_RELEASE_NAME)"
            echo "  -f, --values FILE       Path to values file (default: $DEFAULT_VALUES_FILE)"
            echo "  -n, --namespace NAME    Kubernetes namespace (default: $DEFAULT_NAMESPACE)"
            echo "  --skip-scaling          Skip scaling tests"
            echo "  --skip-upgrade          Skip upgrade tests"
            echo "  --skip-cleanup          Skip cleanup (keep resources after tests)"
            echo "  --debug                 Enable debug output"
            echo "  --non-interactive        Non-interactive mode for CI/CD"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Exit codes:"
            echo "  0 = Success"
            echo "  1 = General error"
            echo "  2 = Prerequisite failure"
            echo "  3 = Timeout"
            echo "  4 = Validation failure"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit $EXIT_ERROR
            ;;
    esac
done

# Track test results
TEST_PHASES_PASSED=0
TEST_PHASES_FAILED=0
FAILED_PHASE=""

# Run test phase with error handling
run_test_phase() {
    local phase_name="$1"
    local phase_command="$2"
    local phase_exit_code="${3:-$EXIT_ERROR}"
    
    log_info ""
    log_info "=========================================="
    log_info "Phase: $phase_name"
    log_info "=========================================="
    
    if eval "$phase_command"; then
        log_info "✓ Phase '$phase_name' completed successfully"
        ((TEST_PHASES_PASSED++))
        return 0
    else
        local exit_code=$?
        log_error "✗ Phase '$phase_name' failed with exit code: $exit_code"
        ((TEST_PHASES_FAILED++))
        FAILED_PHASE="$phase_name"
        
        # Preserve logs on failure
        preserve_logs "$RELEASE_NAME" "$NAMESPACE"
        
        # Determine exit code based on phase
        case "$phase_name" in
            "Prerequisites")
                return $EXIT_PREREQ_FAILURE
                ;;
            "Deployment"|"Scaling"|"Upgrade")
                if [[ $exit_code -eq 124 ]] || [[ $exit_code -eq 130 ]]; then
                    return $EXIT_TIMEOUT
                fi
                return $EXIT_VALIDATION_FAILURE
                ;;
            *)
                return $EXIT_ERROR
                ;;
        esac
    fi
}

# Main test orchestration
main() {
    log_info "=========================================="
    log_info "Helm Chart Complete Test Suite"
    log_info "=========================================="
    log_info "Release name: $RELEASE_NAME"
    log_info "Namespace: $NAMESPACE"
    log_info "Values file: $VALUES_FILE"
    log_info ""
    
    # Phase 1: Prerequisites
    run_test_phase "Prerequisites" \
        "validate_prerequisites && validate_postgres_prerequisite && (validate_redis_prerequisite || true)"
    if [[ $? -ne 0 ]]; then
        log_error "Prerequisites validation failed. Cannot proceed with tests."
        exit $EXIT_PREREQ_FAILURE
    fi
    
    # Phase 2: Deploy
    run_test_phase "Deployment" \
        "\"${SCRIPT_DIR}/deploy.sh\" -r \"$RELEASE_NAME\" -f \"$VALUES_FILE\" -n \"$NAMESPACE\""
    if [[ $? -ne 0 ]]; then
        log_error "Deployment failed. Cannot proceed with remaining tests."
        exit $EXIT_VALIDATION_FAILURE
    fi
    
    # Phase 3: Validate
    run_test_phase "Validation" \
        "\"${SCRIPT_DIR}/validate.sh\" -r \"$RELEASE_NAME\" -n \"$NAMESPACE\""
    if [[ $? -ne 0 ]]; then
        log_error "Validation failed. Continuing with remaining tests..."
    fi
    
    # Phase 4: Scaling (if not skipped)
    if [[ "$SKIP_SCALING" != "true" ]]; then
        run_test_phase "Scaling" \
            "\"${SCRIPT_DIR}/scale.sh\" -r \"$RELEASE_NAME\" -n \"$NAMESPACE\" --test-sequence"
        # Don't exit on scaling failure, continue with other tests
    else
        log_info "Skipping scaling tests (--skip-scaling)"
    fi
    
    # Phase 5: Upgrade (if not skipped)
    if [[ "$SKIP_UPGRADE" != "true" ]]; then
        # Create a temporary updated values file for upgrade testing
        local updated_values_file="${SCRIPT_DIR}/test-upgrade-values.yaml"
        cp "$VALUES_FILE" "$updated_values_file"
        # Modify a non-critical value (e.g., add description)
        if command_exists yq; then
            yq eval '.config.inline.swagger.description = "Updated for upgrade test"' -i "$updated_values_file" 2>/dev/null || true
        fi
        
        run_test_phase "Upgrade" \
            "\"${SCRIPT_DIR}/upgrade.sh\" -r \"$RELEASE_NAME\" -f \"$updated_values_file\" -n \"$NAMESPACE\""
        # Clean up temporary file
        rm -f "$updated_values_file"
        # Don't exit on upgrade failure, continue with cleanup
    else
        log_info "Skipping upgrade tests (--skip-upgrade)"
    fi
    
    # Phase 6: Cleanup (if not skipped)
    if [[ "$SKIP_CLEANUP" != "true" ]]; then
        log_info ""
        log_info "=========================================="
        log_info "Phase: Cleanup"
        log_info "=========================================="
        
        if "${SCRIPT_DIR}/cleanup.sh" -r "$RELEASE_NAME" -n "$NAMESPACE"; then
            log_info "✓ Cleanup completed successfully"
        else
            log_warn "⚠ Cleanup had issues (non-critical)"
        fi
    else
        log_info "Skipping cleanup (--skip-cleanup)"
        log_info "Resources remain deployed for manual inspection"
    fi
    
    # Final summary
    log_info ""
    log_info "=========================================="
    log_info "Test Suite Summary"
    log_info "=========================================="
    log_info "Phases passed: $TEST_PHASES_PASSED"
    log_info "Phases failed: $TEST_PHASES_FAILED"
    
    if [[ $TEST_PHASES_FAILED -gt 0 ]]; then
        log_error "Test suite completed with failures"
        log_error "Failed phase: $FAILED_PHASE"
        log_error "Review logs in: ${SCRIPT_DIR}/logs/"
        
        # Determine exit code based on failure type
        if [[ "$FAILED_PHASE" == "Prerequisites" ]]; then
            exit $EXIT_PREREQ_FAILURE
        elif [[ "$FAILED_PHASE" == "Deployment" ]] || [[ "$FAILED_PHASE" == "Validation" ]]; then
            exit $EXIT_VALIDATION_FAILURE
        else
            exit $EXIT_ERROR
        fi
    else
        log_info "✓ All test phases passed successfully"
        exit $EXIT_SUCCESS
    fi
}

# Run main function
main "$@"


