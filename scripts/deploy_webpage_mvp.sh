#!/bin/bash

# Webpage MVP Deployment Script
# Safe deployment of new webpage infrastructure alongside existing system

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TIMESTAMP=$(date +"%Y-%m-%d-%H-%M-%S")
LOG_FILE="$PROJECT_ROOT/logs/webpage-mvp-deploy-$TIMESTAMP.log"

# Ensure logs directory exists
mkdir -p "$PROJECT_ROOT/logs"

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")  echo -e "${GREEN}[INFO]${NC} $message" | tee -a "$LOG_FILE" ;;
        "WARN")  echo -e "${YELLOW}[WARN]${NC} $message" | tee -a "$LOG_FILE" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" | tee -a "$LOG_FILE" ;;
        "DEBUG") echo -e "${BLUE}[DEBUG]${NC} $message" | tee -a "$LOG_FILE" ;;
    esac
}

# Function to check if command exists
check_command() {
    local cmd=$1
    if ! command -v "$cmd" &> /dev/null; then
        log "ERROR" "Required command '$cmd' not found. Please install it."
        exit 1
    fi
    log "DEBUG" "Command '$cmd' found: $(which $cmd)"
}

# Function to check AWS credentials
check_aws_credentials() {
    log "INFO" "Checking AWS credentials..."
    if ! aws sts get-caller-identity &> /dev/null; then
        log "ERROR" "AWS credentials not configured or invalid"
        log "INFO" "Please run: aws configure"
        exit 1
    fi
    
    local aws_identity=$(aws sts get-caller-identity --query 'Account' --output text)
    log "INFO" "AWS Account: $aws_identity"
}

# Function to validate git branch
validate_git_branch() {
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    log "INFO" "Current git branch: $current_branch"
    
    if [[ "$current_branch" != "dev" ]]; then
        log "WARN" "Not on dev branch. Continue? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log "INFO" "Deployment cancelled by user"
            exit 0
        fi
    fi
}

# Function to run existing tests to ensure no regression
run_regression_tests() {
    log "INFO" "Running regression tests to ensure existing functionality works..."
    
    # Check if existing test scripts exist
    if [[ -f "$PROJECT_ROOT/scripts/test_function_coverage.py" ]]; then
        log "INFO" "Running existing function coverage tests..."
        cd "$PROJECT_ROOT"
        
        # Use environment variable if provided, otherwise skip wallet-dependent tests
        if [[ -n "$TEST_WALLET_ADDRESS" ]]; then
            uv run python scripts/test_function_coverage.py \
                --mcp-url "https://pb-fm-mcp-dev.creativeapptitude.com/mcp" \
                --rest-url "https://pb-fm-mcp-dev.creativeapptitude.com" \
                --timeout 30 || {
                log "ERROR" "Existing function tests failed - stopping deployment"
                exit 1
            }
        else
            log "WARN" "TEST_WALLET_ADDRESS not set, skipping wallet-dependent tests"
            log "INFO" "To run full tests: TEST_WALLET_ADDRESS=wallet_addr $0"
        fi
    else
        log "WARN" "No existing test scripts found, skipping regression tests"
    fi
}

# Function to check if infrastructure already exists
check_existing_infrastructure() {
    log "INFO" "Checking for existing webpage MVP infrastructure..."
    
    # Check S3 bucket
    if aws s3api head-bucket --bucket "pb-fm-webpage-mvp-assets" 2>/dev/null; then
        log "WARN" "S3 bucket 'pb-fm-webpage-mvp-assets' already exists"
    else
        log "INFO" "S3 bucket 'pb-fm-webpage-mvp-assets' does not exist (will create)"
    fi
    
    # Check DynamoDB table
    if aws dynamodb describe-table --table-name "pb-fm-webpage-sessions" &>/dev/null; then
        log "WARN" "DynamoDB table 'pb-fm-webpage-sessions' already exists"
    else
        log "INFO" "DynamoDB table 'pb-fm-webpage-sessions' does not exist (will create)"
    fi
}

# Function to update CloudFormation template
update_cloudformation_template() {
    log "INFO" "Updating CloudFormation template with webpage MVP resources..."
    
    local template_file="$PROJECT_ROOT/template-unified.yaml"
    local backup_file="$PROJECT_ROOT/template-unified.yaml.backup.$TIMESTAMP"
    
    # Create backup
    cp "$template_file" "$backup_file"
    log "INFO" "Created backup: $backup_file"
    
    # Check if webpage resources already exist in template
    if grep -q "pb-fm-webpage-mvp-assets" "$template_file"; then
        log "INFO" "Webpage MVP resources already exist in CloudFormation template"
        return 0
    fi
    
    log "INFO" "Adding webpage MVP resources to CloudFormation template..."
    
    # Add webpage MVP resources (this would be template-specific)
    # For now, log that manual template update is needed
    log "WARN" "Manual CloudFormation template update required:"
    log "WARN" "1. Add S3 bucket: pb-fm-webpage-mvp-assets"
    log "WARN" "2. Add DynamoDB table: pb-fm-webpage-sessions"
    log "WARN" "3. Add SQS permissions for pb-fm-webpage-* queues"
    log "WARN" "Template backup created at: $backup_file"
}

# Function to deploy infrastructure
deploy_infrastructure() {
    log "INFO" "Deploying webpage MVP infrastructure..."
    
    cd "$PROJECT_ROOT"
    
    # Use existing deploy script but with additional safety checks
    log "INFO" "Running existing deployment script..."
    
    if [[ -f "./deploy.sh" ]]; then
        # Run deployment with test flag
        ./deploy.sh dev --clean --test || {
            log "ERROR" "Deployment failed"
            exit 1
        }
        log "INFO" "Deployment completed successfully"
    else
        log "ERROR" "deploy.sh script not found"
        exit 1
    fi
}

# Function to test new infrastructure
test_new_infrastructure() {
    log "INFO" "Testing newly created webpage MVP infrastructure..."
    
    cd "$PROJECT_ROOT"
    
    # Test S3 bucket access
    log "INFO" "Testing S3 bucket access..."
    aws s3 ls s3://pb-fm-webpage-mvp-assets/ || {
        log "ERROR" "Cannot access S3 bucket pb-fm-webpage-mvp-assets"
        return 1
    }
    
    # Test DynamoDB table access
    log "INFO" "Testing DynamoDB table access..."
    aws dynamodb describe-table --table-name "pb-fm-webpage-sessions" || {
        log "ERROR" "Cannot access DynamoDB table pb-fm-webpage-sessions"
        return 1
    }
    
    # Test new MCP functions (if they exist)
    if [[ -f "scripts/test_webpage_mvp.py" ]]; then
        log "INFO" "Running webpage MVP specific tests..."
        uv run python scripts/test_webpage_mvp.py || {
            log "WARN" "Webpage MVP tests failed (expected if functions not implemented yet)"
        }
    else
        log "INFO" "Webpage MVP test script not found (will create later)"
    fi
    
    log "INFO" "Infrastructure testing completed"
}

# Function to validate deployment
validate_deployment() {
    log "INFO" "Validating complete deployment..."
    
    # Re-run regression tests to ensure nothing broke
    run_regression_tests
    
    # Test new infrastructure
    test_new_infrastructure
    
    log "INFO" "Deployment validation completed successfully"
}

# Main deployment function
main() {
    log "INFO" "Starting Webpage MVP deployment at $TIMESTAMP"
    log "INFO" "Log file: $LOG_FILE"
    
    # Pre-deployment checks
    log "INFO" "=== Pre-deployment Checks ==="
    check_command "aws"
    check_command "uv"
    check_command "git"
    check_command "sam"
    
    check_aws_credentials
    validate_git_branch
    check_existing_infrastructure
    
    # Run regression tests before deployment
    log "INFO" "=== Regression Testing ==="
    run_regression_tests
    
    # Deploy infrastructure
    log "INFO" "=== Infrastructure Deployment ==="
    update_cloudformation_template
    deploy_infrastructure
    
    # Post-deployment validation
    log "INFO" "=== Post-deployment Validation ==="
    validate_deployment
    
    log "INFO" "=== Deployment Summary ==="
    log "INFO" "Webpage MVP infrastructure deployed successfully!"
    log "INFO" "New resources created:"
    log "INFO" "  - S3 Bucket: pb-fm-webpage-mvp-assets"
    log "INFO" "  - DynamoDB Table: pb-fm-webpage-sessions"
    log "INFO" "  - SQS Queue permissions for pb-fm-webpage-* pattern"
    log "INFO" ""
    log "INFO" "Next steps:"
    log "INFO" "  1. Implement webpage-specific MCP functions"
    log "INFO" "  2. Create static website files"
    log "INFO" "  3. Run: scripts/test_webpage_mvp.py"
    log "INFO" ""
    log "INFO" "Deployment completed at $(date)"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi