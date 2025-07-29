#!/bin/bash
# Comprehensive deployment script for pb-fm-mcp
# Handles all dependencies, checks, and deployment steps automatically

set -e  # Exit on any error
set -o pipefail  # Exit on pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN_NAME="creativeapptitude.com"
DEV_DOMAIN="pb-fm-mcp-dev.${DOMAIN_NAME}"
PROD_DOMAIN="pb-fm-mcp.${DOMAIN_NAME}"
TEMPLATE_FILE="template-unified.yaml"
US_EAST_1_REGION="us-east-1"  # For certificates
DEPLOYMENT_REGION="us-west-1"  # For Lambda deployment

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Help function
show_help() {
    cat << EOF
Usage: $0 [ENVIRONMENT] [OPTIONS]

ENVIRONMENT:
  dev     Deploy to development environment (pb-fm-mcp-dev stack)
  prod    Deploy to production environment (pb-fm-mcp-v2 stack)

OPTIONS:
  --no-domain     Skip custom domain setup (use API Gateway URLs only)
  --force         Force deployment even if checks fail
  --clean         Clean build before deployment
  --test          Run tests after deployment
  --skip-check    Skip deployment version check and force deployment
  --help          Show this help message

Examples:
  $0 dev                    # Deploy to dev with custom domain
  $0 prod --clean --test    # Clean deploy to prod with testing
  $0 dev --no-domain        # Deploy to dev without custom domain

Dependencies checked automatically:
  - AWS CLI configuration
  - SAM CLI installation
  - Certificate availability (if using custom domain)
  - Route 53 hosted zone
  - Template file existence
  - Git status and branch validation
EOF
}

# Check if running on correct branch
check_git_branch() {
    local env=$1
    local force=$2
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    
    if [[ "$env" == "prod" && "$current_branch" != "main" ]]; then
        if [[ "$force" == true ]]; then
            print_warning "Production deployment not on main branch. Currently on: $current_branch (--force specified)"
        else
            print_error "Production deployment requires main branch. Currently on: $current_branch"
            print_status "Switch to main branch: git checkout main"
            exit 1
        fi
    fi
    
    if [[ "$env" == "dev" && "$current_branch" != "dev" ]]; then
        if [[ "$force" == true ]]; then
            print_warning "Development deployment not on dev branch. Currently on: $current_branch (--force specified)"
        else
            print_warning "Development deployment usually done from dev branch. Currently on: $current_branch"
            read -p "Continue anyway? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
    
    print_success "Git branch check passed: $current_branch"
}

# Check dependencies
check_dependencies() {
    print_header "Checking Dependencies"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Install: https://aws.amazon.com/cli/"
        exit 1
    fi
    print_success "AWS CLI found: $(aws --version | head -1)"
    
    # Check SAM CLI
    if ! command -v sam &> /dev/null; then
        print_error "SAM CLI not found. Install: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
        exit 1
    fi
    print_success "SAM CLI found: $(sam --version)"
    
    # Check uv
    if ! command -v uv &> /dev/null; then
        print_error "uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    print_success "uv found: $(uv --version)"
    
    # Check template file
    if [[ ! -f "$TEMPLATE_FILE" ]]; then
        print_error "Template file not found: $TEMPLATE_FILE"
        exit 1
    fi
    print_success "Template file found: $TEMPLATE_FILE"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured or invalid"
        exit 1
    fi
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    print_success "AWS credentials valid. Account: $account_id"
}

# Check certificate and domain setup
check_certificate() {
    local env=$1
    local target_domain
    
    if [[ "$env" == "prod" ]]; then
        target_domain="$PROD_DOMAIN"
    else
        target_domain="$DEV_DOMAIN"
    fi
    
    print_header "Checking SSL Certificate"
    
    # List certificates in us-east-1 (required for CloudFront/API Gateway)
    local cert_info=$(aws acm list-certificates --region $US_EAST_1_REGION --output json)
    
    if [[ -z "$cert_info" || "$cert_info" == "null" ]]; then
        print_error "No certificates found in $US_EAST_1_REGION region"
        return 1
    fi
    
    # Find certificate that covers our domain
    local cert_arn=$(echo "$cert_info" | jq -r --arg domain "$target_domain" '
        .CertificateSummaryList[] | 
        select(.Status == "ISSUED") |
        select(.DomainName == $domain or (.SubjectAlternativeNameSummaries // [] | map(select(. == $domain)) | length > 0)) |
        .CertificateArn
    ' | head -1)
    
    if [[ -z "$cert_arn" || "$cert_arn" == "null" ]]; then
        print_error "No valid certificate found for domain: $target_domain"
        print_status "Available certificates:"
        echo "$cert_info" | jq -r '.CertificateSummaryList[] | "  - \(.DomainName) (\(.Status))"'
        return 1
    fi
    
    print_success "Found valid certificate for $target_domain"
    print_status "Certificate ARN: $cert_arn"
    printf "%s" "$cert_arn"
}

# Check Route 53 hosted zone
check_hosted_zone() {
    print_header "Checking Route 53 Hosted Zone"
    
    local zone_id=$(aws route53 list-hosted-zones --query "HostedZones[?Name=='${DOMAIN_NAME}.'].Id" --output text)
    
    if [[ -z "$zone_id" || "$zone_id" == "None" ]]; then
        print_error "Route 53 hosted zone not found for domain: $DOMAIN_NAME"
        return 1
    fi
    
    # Remove /hostedzone/ prefix if present
    zone_id=${zone_id#/hostedzone/}
    
    print_success "Found hosted zone: $zone_id"
    printf "%s" "$zone_id"
}

# Clean build artifacts
clean_build() {
    print_header "Cleaning Build Artifacts"
    
    rm -rf .aws-sam/
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    print_success "Build artifacts cleaned"
}

# Check if deployment is needed
check_deployment_needed() {
    local env=$1
    local stack_name
    
    if [[ "$env" == "prod" ]]; then
        stack_name="pb-fm-mcp-v2"
    else
        stack_name="pb-fm-mcp-dev"
    fi
    
    print_header "Checking if Deployment is Needed"
    
    # Get current git commit hash
    local current_commit=$(git rev-parse HEAD)
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    
    # Check if stack exists
    if ! aws cloudformation describe-stacks --stack-name "$stack_name" --region "$DEPLOYMENT_REGION" &>/dev/null; then
        print_status "Stack $stack_name does not exist, deployment needed"
        echo "true"
        return
    fi
    
    # Get current deployed version from stack tags
    local deployed_commit=$(aws cloudformation describe-stacks --stack-name "$stack_name" --region "$DEPLOYMENT_REGION" --query 'Stacks[0].Tags[?Key==`GitCommit`].Value' --output text 2>/dev/null || echo "")
    local deployed_branch=$(aws cloudformation describe-stacks --stack-name "$stack_name" --region "$DEPLOYMENT_REGION" --query 'Stacks[0].Tags[?Key==`GitBranch`].Value' --output text 2>/dev/null || echo "")
    
    # Check for uncommitted changes
    if ! git diff --quiet || ! git diff --cached --quiet; then
        print_warning "Uncommitted changes detected, deployment recommended"
        echo "true"
        return
    fi
    
    # Compare commits and branches
    if [[ "$deployed_commit" == "$current_commit" && "$deployed_branch" == "$current_branch" ]]; then
        print_success "Deployed version matches current state"
        print_status "Current: $current_commit ($current_branch)"
        print_status "Deployed: $deployed_commit ($deployed_branch)"
        echo "false"
    else
        print_status "Version mismatch detected, deployment needed"
        print_status "Current: $current_commit ($current_branch)"
        print_status "Deployed: $deployed_commit ($deployed_branch)"
        echo "true"
    fi
}

# Build the application
build_application() {
    print_header "Building Application"
    
    sam build --template-file "$TEMPLATE_FILE"
    
    if [[ $? -ne 0 ]]; then
        print_error "Build failed"
        exit 1
    fi
    
    print_success "Build completed successfully"
}

# Deploy the application
deploy_application() {
    local env=$1
    local cert_arn=$2
    local zone_id=$3
    local stack_name
    
    if [[ "$env" == "prod" ]]; then
        stack_name="pb-fm-mcp-v2"
    else
        stack_name="pb-fm-mcp-dev"
    fi
    
    print_header "Deploying to $env environment"
    print_status "Stack: $stack_name"
    print_status "Region: $DEPLOYMENT_REGION"
    
    # Add git tracking tags
    local current_commit=$(git rev-parse HEAD)
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    local deploy_timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    local deploy_cmd="sam deploy --stack-name $stack_name --resolve-s3 --region $DEPLOYMENT_REGION --capabilities CAPABILITY_IAM"
    deploy_cmd="$deploy_cmd --tags 'GitCommit=$current_commit' 'GitBranch=$current_branch' 'DeployTimestamp=$deploy_timestamp' 'Environment=$env'"
    
    # Add parameters if custom domain is enabled
    if [[ -n "$cert_arn" && -n "$zone_id" ]]; then
        deploy_cmd="$deploy_cmd --parameter-overrides 'Environment=$env HostedZoneId=$zone_id CertificateArn=$cert_arn'"
        print_status "Custom domain enabled"
    else
        print_status "Custom domain disabled"
    fi
    
    # Execute deployment
    eval "$deploy_cmd"
    
    if [[ $? -ne 0 ]]; then
        print_error "Deployment failed"
        exit 1
    fi
    
    print_success "Deployment completed successfully"
}

# Get deployment outputs
get_deployment_outputs() {
    local env=$1
    local stack_name
    
    if [[ "$env" == "prod" ]]; then
        stack_name="pb-fm-mcp-v2"
    else
        stack_name="pb-fm-mcp-dev"
    fi
    
    print_header "Deployment Outputs"
    
    local outputs=$(aws cloudformation describe-stacks --stack-name "$stack_name" --region "$DEPLOYMENT_REGION" --query 'Stacks[0].Outputs' --output table)
    
    if [[ -n "$outputs" ]]; then
        echo "$outputs"
    else
        print_warning "No stack outputs found"
    fi
}

# Test deployment
test_deployment() {
    local env=$1
    local stack_name
    
    if [[ "$env" == "prod" ]]; then
        stack_name="pb-fm-mcp-v2"
    else
        stack_name="pb-fm-mcp-dev"
    fi
    
    print_header "Testing Deployment"
    
    # Get API URLs from stack outputs
    local api_url=$(aws cloudformation describe-stacks --stack-name "$stack_name" --region "$DEPLOYMENT_REGION" --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text)
    local custom_url=$(aws cloudformation describe-stacks --stack-name "$stack_name" --region "$DEPLOYMENT_REGION" --query 'Stacks[0].Outputs[?OutputKey==`CustomDomainUrl`].OutputValue' --output text 2>/dev/null || echo "")
    
    # Test MCP endpoints using proper MCP test client
    local test_url="${api_url}mcp"
    if [[ -n "$custom_url" && "$custom_url" != "None" ]]; then
        test_url="${custom_url}mcp"
        print_status "Testing custom domain MCP endpoint: $test_url"
    else
        print_status "Testing API Gateway MCP endpoint: $test_url"
    fi
    
    # Test MCP protocol using proper test client
    print_status "Running MCP connection test..."
    if timeout 30 uv run python -c "
import asyncio
import sys
sys.path.append('scripts')
from mcp_test_client import MCPTestClient

async def test_mcp():
    try:
        client = MCPTestClient('$test_url')
        await client.connect()
        tools = await client.list_tools()
        await client.disconnect()
        print(f'✅ MCP test passed: {len(tools)} tools available')
        return len(tools) > 0
    except Exception as e:
        print(f'❌ MCP test failed: {e}')
        return False

result = asyncio.run(test_mcp())
sys.exit(0 if result else 1)
    " 2>/dev/null; then
        print_success "MCP endpoint working correctly"
    else
        print_warning "MCP endpoint test failed (may still be starting up)"
    fi
    
    # Test REST API endpoints
    local api_base_url="${test_url%/mcp}"
    print_status "Testing REST API endpoints..."
    
    # Test root endpoint
    if curl -s -f "$api_base_url/" | grep -q "pb-fm-mcp" 2>/dev/null; then
        print_success "REST API root endpoint working"
    else
        print_warning "REST API root endpoint not responding"
    fi
    
    # Test health endpoint
    if curl -s -f "$api_base_url/health" | grep -q "status" 2>/dev/null; then
        print_success "REST API health endpoint working"
    else
        print_warning "REST API health endpoint not responding"
    fi
    
    # Test docs endpoint
    if curl -s -f "$api_base_url/docs" | grep -q "swagger" 2>/dev/null; then
        print_success "REST API documentation endpoint working"
    else
        print_warning "REST API documentation endpoint not responding"
    fi
    
    # Test a sample API function endpoint
    if curl -s -f "$api_base_url/api/fetch_current_hash_statistics" | grep -q "maxSupply" 2>/dev/null; then
        print_success "REST API function endpoints working"
    else
        print_warning "REST API function endpoints not responding"
    fi
    
    # Test AI Terminal webpage
    local terminal_url="${api_base_url}/ai-terminal"
    if [[ -n "$custom_url" && "$custom_url" != "None" ]]; then
        terminal_url="${custom_url}ai-terminal"
        print_status "Testing custom domain AI Terminal webpage: $terminal_url"
    else
        print_status "Testing API Gateway AI Terminal webpage: $terminal_url"
    fi
    if curl -s -f "$terminal_url" | grep -q "AI Terminal" 2>/dev/null; then
        print_success "AI Terminal webpage loading"
        
        # Test AI Terminal API endpoints
        local test_input_url="${test_url%/mcp}/api/user-input/deploy-test"
        print_status "Testing AI Terminal input endpoint: $test_input_url"
        if curl -s -f "$test_input_url" -H "Content-Type: application/json" -d '{"input_type":"test","input_value":"deploy test","timestamp":123456}' | grep -q "sent_to_ai" 2>/dev/null; then
            print_success "AI Terminal input endpoint working"
        else
            print_warning "AI Terminal input endpoint not responding"
        fi
    else
        print_warning "AI Terminal webpage not responding"
    fi
    
    # Run comprehensive tests if script exists
    if [[ -f "scripts/test_function_coverage.py" ]]; then
        print_status "Running comprehensive function coverage tests with uv..."
        local mcp_url="${api_url}mcp"
        if [[ -n "$custom_url" && "$custom_url" != "None" ]]; then
            mcp_url="${custom_url}mcp"
        fi
        
        # Use environment variable for wallet address (user must provide)
        if [[ -z "$TEST_WALLET_ADDRESS" ]]; then
            print_warning "TEST_WALLET_ADDRESS not set. Set it before running: export TEST_WALLET_ADDRESS=your_wallet_address"
            print_warning "Skipping function coverage tests"
        else
            env TEST_WALLET_ADDRESS="$TEST_WALLET_ADDRESS" \
            uv run python scripts/test_function_coverage.py \
                --mcp-url "$mcp_url" \
                --rest-url "${api_url%/}" || print_warning "Function coverage tests failed"
        fi
    fi
}

# Main execution
main() {
    local environment=""
    local use_domain=true
    local force=false
    local clean=false
    local test=false
    local skip_check=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            dev|prod)
                environment="$1"
                shift
                ;;
            --no-domain)
                use_domain=false
                shift
                ;;
            --force)
                force=true
                shift
                ;;
            --clean)
                clean=true
                shift
                ;;
            --test)
                test=true
                shift
                ;;
            --skip-check)
                skip_check=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Validate environment
    if [[ -z "$environment" ]]; then
        print_error "Environment required (dev or prod)"
        show_help
        exit 1
    fi
    
    print_header "pb-fm-mcp Deployment Script"
    print_status "Environment: $environment"
    print_status "Custom domain: $use_domain"
    print_status "Template: $TEMPLATE_FILE"
    
    # Check git branch
    check_git_branch "$environment" "$force"
    
    # Check dependencies
    check_dependencies
    
    # Certificate and domain setup
    local cert_arn=""
    local zone_id=""
    
    if [[ "$use_domain" == true ]]; then
        # Use known certificate ARN and hosted zone ID to avoid parsing issues
        cert_arn="arn:aws:acm:us-east-1:289426936662:certificate/cb38bb54-6d10-4dd8-991b-9de88dd0efdd"
        zone_id="Z1CKVEV77P2DUQ"
        
        print_success "Using known certificate: $cert_arn"
        print_success "Using known hosted zone: $zone_id"
        
        # Verify certificate and zone still exist
        if ! aws acm describe-certificate --certificate-arn "$cert_arn" --region "$US_EAST_1_REGION" &>/dev/null; then
            print_error "Certificate not found: $cert_arn"
            if [[ "$force" == true ]]; then
                print_warning "Certificate check failed but --force specified. Deploying without custom domain."
                use_domain=false
            else
                exit 1
            fi
        fi
        
        if ! aws route53 get-hosted-zone --id "$zone_id" &>/dev/null; then
            print_error "Hosted zone not found: $zone_id"
            if [[ "$force" == true ]]; then
                print_warning "Hosted zone check failed but --force specified. Deploying without custom domain."
                use_domain=false
            else
                exit 1
            fi
        fi
    fi
    
    # Check if deployment is needed (unless skip-check is specified)
    local deployment_needed="true"
    if [[ "$skip_check" == false ]]; then
        deployment_needed=$(check_deployment_needed "$environment")
        
        if [[ "$deployment_needed" == "false" ]]; then
            print_success "No deployment needed - current version already deployed"
            
            # Still run tests if requested
            if [[ "$test" == true ]]; then
                test_deployment "$environment"
            fi
            
            print_success "No changes detected - deployment skipped!"
            return 0
        fi
    else
        print_status "Skipping deployment check (--skip-check specified)"
    fi
    
    # Clean build if requested
    if [[ "$clean" == true ]]; then
        clean_build
    fi
    
    # Build application
    build_application
    
    # Deploy application
    if [[ "$use_domain" == true ]]; then
        deploy_application "$environment" "$cert_arn" "$zone_id"
    else
        deploy_application "$environment"
    fi
    
    # Show outputs
    get_deployment_outputs "$environment"
    
    # Test deployment if requested
    if [[ "$test" == true ]]; then
        test_deployment "$environment"
    fi
    
    print_success "Deployment completed successfully!"
    
    if [[ "$use_domain" == true ]]; then
        if [[ "$environment" == "prod" ]]; then
            print_status "Production URL: https://$PROD_DOMAIN/"
            print_status "MCP Endpoint: https://$PROD_DOMAIN/mcp"
        else
            print_status "Development URL: https://$DEV_DOMAIN/"
            print_status "MCP Endpoint: https://$DEV_DOMAIN/mcp"
        fi
        print_warning "DNS propagation may take a few minutes for custom domains"
    fi
}

# Run main function with all arguments
main "$@"