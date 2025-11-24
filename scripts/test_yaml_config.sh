#!/bin/bash

# Test script for YAML table configuration
# 
# Purpose:
#   Starts Pylight server with a YAML configuration file and validates Docker services.
#   This script enables developers to quickly test YAML table configurations locally.
#
# Usage:
#   ./scripts/test_yaml_config.sh <yaml_file> [--host HOST] [--port PORT]
#
# Examples:
#   ./scripts/test_yaml_config.sh docs/examples/yaml_configs/basic_config.yaml
#   ./scripts/test_yaml_config.sh docs/examples/yaml_configs/auth_config.yaml --port 8001
#
# Prerequisites:
#   - Docker installed and running
#   - PostgreSQL Docker container (for database)
#   - Redis Docker container (optional, for caching)
#   - Pylight framework installed
#   - Python 3.11+ with required dependencies
#
# Environment Variables:
#   PYLIGHT_CONFIG - Can be used instead of yaml_file argument

set -euo pipefail

# Default values
DEFAULT_HOST="127.0.0.1"
DEFAULT_PORT="8000"
HOST="${DEFAULT_HOST}"
PORT="${DEFAULT_PORT}"
YAML_FILE=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print error messages
error() {
    echo -e "${RED}Error: $1${NC}" >&2
}

# Function to print success messages
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print info messages
info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Function to check if Docker container is running
checkDockerContainer() {
    local container_name="$1"
    if docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
        return 0
    else
        return 1
    fi
}

# Function to check if a port is accessible
checkPortAccessible() {
    local host="$1"
    local port="$2"
    local timeout="${3:-2}"
    
    if command -v nc >/dev/null 2>&1; then
        if nc -z -w "${timeout}" "${host}" "${port}" 2>/dev/null; then
            return 0
        else
            return 1
        fi
    elif command -v timeout >/dev/null 2>&1; then
        if timeout "${timeout}" bash -c "echo > /dev/tcp/${host}/${port}" 2>/dev/null; then
            return 0
        else
            return 1
        fi
    else
        error "Neither 'nc' nor 'timeout' command available for port checking"
        return 1
    fi
}

# Function to check PostgreSQL service
checkPostgreSQL() {
    local host="localhost"
    local port="5432"
    
    if ! checkDockerContainer "postgres" && ! checkDockerContainer "postgresql"; then
        return 1
    fi
    
    if ! checkPortAccessible "${host}" "${port}"; then
        return 1
    fi
    
    return 0
}

# Function to check Redis service
checkRedis() {
    local host="localhost"
    local port="6379"
    
    if ! checkDockerContainer "redis"; then
        return 1
    fi
    
    if ! checkPortAccessible "${host}" "${port}"; then
        return 1
    fi
    
    return 0
}

# Function to show usage
showUsage() {
    cat << EOF
Usage: $0 <yaml_file> [options]

Start Pylight test server with YAML table configuration.

Arguments:
  yaml_file              Path to YAML configuration file (required)

Options:
  --host HOST           Server host (default: ${DEFAULT_HOST})
  --port PORT           Server port (default: ${DEFAULT_PORT})
  --help                Show this help message

Examples:
  $0 docs/examples/yaml_configs/basic_config.yaml
  $0 docs/examples/yaml_configs/auth_config.yaml --port 8001

Environment:
  PYLIGHT_CONFIG        Can be used instead of yaml_file argument
EOF
}

# Parse command-line arguments
parseArguments() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --host)
                HOST="$2"
                shift 2
                ;;
            --port)
                PORT="$2"
                shift 2
                ;;
            --help|-h)
                showUsage
                exit 0
                ;;
            -*)
                error "Unknown option: $1"
                showUsage
                exit 1
                ;;
            *)
                if [[ -z "${YAML_FILE}" ]]; then
                    YAML_FILE="$1"
                else
                    error "Multiple YAML files specified. Only one file allowed."
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Check if YAML file is provided via environment variable
    if [[ -z "${YAML_FILE}" ]] && [[ -n "${PYLIGHT_CONFIG:-}" ]]; then
        YAML_FILE="${PYLIGHT_CONFIG}"
    fi
    
    # Validate that YAML file path is provided
    if [[ -z "${YAML_FILE}" ]]; then
        error "YAML configuration file path required"
        echo ""
        showUsage
        exit 1
    fi
}

# Function to validate YAML file
validateYamlFile() {
    local yaml_file="$1"
    
    if [[ ! -f "${yaml_file}" ]]; then
        error "YAML file not found: ${yaml_file}"
        return 1
    fi
    
    if [[ ! -r "${yaml_file}" ]]; then
        error "YAML file is not readable: ${yaml_file}"
        return 1
    fi
    
    # Basic YAML syntax check (if python available)
    if command -v python3 >/dev/null 2>&1; then
        if ! python3 -c "import yaml; yaml.safe_load(open('${yaml_file}'))" 2>/dev/null; then
            error "Invalid YAML syntax in file: ${yaml_file}"
            return 1
        fi
    fi
    
    return 0
}

# Function to start Pylight server
startServer() {
    local yaml_file="$1"
    local host="$2"
    local port="$3"
    
    info "Loading configuration from: ${yaml_file}"
    
    if ! validateYamlFile "${yaml_file}"; then
        exit 1
    fi
    
    success "Configuration file validated"
    
    # Validate required Docker services
    info "Checking required services..."
    if ! validateRequiredServices "${yaml_file}"; then
        error "Required services are not available. Please start the required Docker containers."
        exit 1
    fi
    
    info "Starting server on http://${host}:${port}"
    info "API documentation: http://${host}:${port}/docs"
    echo ""
    
    # Start Pylight server
    python -m cli start --config "${yaml_file}" --host "${host}" --port "${port}"
}

# Trap Ctrl+C for graceful shutdown
trap 'echo ""; info "Server stopped by user"; exit 0' INT TERM

# Main execution
main() {
    parseArguments "$@"
    
    # Start server with YAML configuration
    startServer "${YAML_FILE}" "${HOST}" "${PORT}"
}

# Run main function
main "$@"

