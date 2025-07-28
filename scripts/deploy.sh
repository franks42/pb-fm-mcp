#!/bin/bash

# Automated deployment script with git commit + datetime versioning
# Usage: ./scripts/deploy.sh [prod|dev]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
STACK_NAME="pb-fm-mcp-dev"

# Parse arguments
if [ $# -ge 1 ]; then
    ENVIRONMENT=$1
fi

# Set stack name based on environment
case $ENVIRONMENT in
    "prod"|"production")
        STACK_NAME="pb-fm-mcp-v2"
        ENVIRONMENT="prod"
        echo -e "${RED}⚠️  WARNING: Deploying to PRODUCTION environment!${NC}"
        echo -e "${RED}This will affect colleagues' integrations. Continue? (y/N)${NC}"
        read -r response
        if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            echo "Deployment cancelled."
            exit 1
        fi
        ;;
    "dev"|"development")
        STACK_NAME="pb-fm-mcp-dev"
        ENVIRONMENT="dev"
        ;;
    *)
        echo -e "${RED}❌ Error: Environment must be 'prod' or 'dev'${NC}"
        echo "Usage: $0 [prod|dev]"
        exit 1
        ;;
esac

echo -e "${BLUE}🚀 pb-fm-mcp Automated Deployment${NC}"
echo "=================================="
echo "Environment: $ENVIRONMENT"
echo "Stack: $STACK_NAME"
echo ""

# Check git status
echo -e "${BLUE}📋 Checking git status...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Warning: Uncommitted changes detected${NC}"
    git status --short
    echo ""
fi

# Check current branch
BRANCH=$(git branch --show-current)
echo "Current branch: $BRANCH"

if [ "$ENVIRONMENT" = "prod" ] && [ "$BRANCH" != "main" ]; then
    echo -e "${RED}❌ Error: Production deployments must be from 'main' branch${NC}"
    exit 1
fi

if [ "$ENVIRONMENT" = "dev" ] && [ "$BRANCH" != "dev" ]; then
    echo -e "${YELLOW}⚠️  Warning: Development deployment from '$BRANCH' branch${NC}"
fi

echo ""

# Show current version
echo -e "${BLUE}📊 Current version info:${NC}"
uv run python version.py
echo ""

# Generate version with git commit + datetime
echo -e "${BLUE}🔄 Generating version (git commit + datetime)...${NC}"
NEW_VERSION=$(uv run python version.py deploy $ENVIRONMENT)
echo "New version: $NEW_VERSION"
echo ""

# Clean build as per CLAUDE.md directive
echo -e "${BLUE}🧹 Cleaning build directory...${NC}"
rm -rf .aws-sam/
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
echo ""

# Build
echo -e "${BLUE}🔨 Building SAM project...${NC}"
sam build --template-file template-dual-path.yaml
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

# Manual pruning to reduce Lambda package size (until .samignore works)
echo -e "${BLUE}✂️  Pruning unnecessary dependencies...${NC}"
BUILD_DIR=".aws-sam/build/McpFunction"
if [ -d "$BUILD_DIR" ]; then
    # Remove large unnecessary packages
    rm -rf "$BUILD_DIR/uvloop/" 2>/dev/null || true
    rm -rf "$BUILD_DIR/httptools/" 2>/dev/null || true
    rm -rf "$BUILD_DIR/watchfiles/" 2>/dev/null || true
    rm -rf "$BUILD_DIR/websockets/" 2>/dev/null || true
    rm -rf "$BUILD_DIR/tests/" 2>/dev/null || true
    rm -rf "$BUILD_DIR/.ruff_cache/" 2>/dev/null || true
    
    # Show reduced size
    SIZE_MB=$(du -sm "$BUILD_DIR" | cut -f1)
    echo "   📦 Lambda package size: ${SIZE_MB}MB"
fi
echo ""

# Deploy
echo -e "${BLUE}🚀 Deploying to $ENVIRONMENT environment...${NC}"

# Check if custom domain parameters are provided
if [ -n "$HOSTED_ZONE_ID" ] && [ -n "$CERTIFICATE_ARN" ]; then
    echo -e "${YELLOW}🌐 Using custom domain configuration${NC}"
    sam deploy --stack-name "$STACK_NAME" --resolve-s3 --capabilities CAPABILITY_IAM \
        --parameter-overrides \
        "Environment=$ENVIRONMENT" \
        "HostedZoneId=$HOSTED_ZONE_ID" \
        "CertificateArn=$CERTIFICATE_ARN"
else
    echo -e "${YELLOW}📝 Using default configuration (no custom domain)${NC}"
    sam deploy --stack-name "$STACK_NAME" --resolve-s3 --capabilities CAPABILITY_IAM \
        --parameter-overrides "Environment=$ENVIRONMENT"
fi
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Deployment successful!${NC}"
echo ""

# Get deployment URLs from CloudFormation outputs
echo -e "${GREEN}🌐 Deployment URLs:${NC}"
MCP_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='McpUrl'].OutputValue" --output text 2>/dev/null || echo "Not available")
API_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text 2>/dev/null || echo "Not available") 
DOCS_URL="${API_URL}docs"
STABLE_MCP_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='StableMcpUrl'].OutputValue" --output text 2>/dev/null || echo "Not available")
CUSTOM_DOMAIN_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='CustomDomainUrl'].OutputValue" --output text 2>/dev/null || echo "Not available")
CUSTOM_DOMAIN_MCP=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='CustomDomainMcpUrl'].OutputValue" --output text 2>/dev/null || echo "Not available")

echo "🔗 API Gateway MCP: $MCP_URL"
echo "🔗 API Gateway REST: $API_URL"

if [ "$CUSTOM_DOMAIN_MCP" != "Not available" ]; then
    echo ""
    echo -e "${GREEN}🎯 CUSTOM DOMAIN URLs (recommended for Claude.ai):${NC}"
    echo "🔗 Custom Domain Base: $CUSTOM_DOMAIN_URL"
    echo "🔗 Custom Domain MCP: $CUSTOM_DOMAIN_MCP"
    echo ""
    echo -e "${YELLOW}🌐 Custom domains are stable and won't change between deployments!${NC}"
    echo -e "${YELLOW}🌐 Environment: ${ENVIRONMENT} (clearly visible in domain name)${NC}"
elif [ "$STABLE_MCP_URL" != "Not available" ]; then
    echo ""
    echo -e "${GREEN}🌟 STABLE Lambda Function URL:${NC}"
    echo "🔗 Stable MCP URL: $STABLE_MCP_URL"
    echo ""
    echo -e "${YELLOW}📌 This Lambda Function URL is stable and won't change between deployments!${NC}"
fi

echo ""
echo "🔗 Documentation: $DOCS_URL"

echo ""
echo -e "${BLUE}📋 Final version info:${NC}"
uv run python version.py
echo ""

# Optional: Test deployment
echo -e "${BLUE}🧪 Testing deployment...${NC}"
echo "Testing MCP endpoint: $MCP_URL"
curl -s "$MCP_URL" | uv run python -m json.tool || echo "Test failed"

echo ""
echo -e "${GREEN}🎉 Deployment complete! Version $NEW_VERSION is now live.${NC}"

# Show Claude.ai configuration info
echo ""
echo -e "${BLUE}🤖 Claude.ai MCP Configuration:${NC}"
if [ "$CUSTOM_DOMAIN_MCP" != "Not available" ]; then
    echo "Add this CUSTOM DOMAIN MCP server URL to Claude.ai:"
    echo -e "${GREEN}$CUSTOM_DOMAIN_MCP${NC}"
    echo ""
    echo "This custom domain is stable and won't change between deployments!"
    echo "Environment: ${ENVIRONMENT} (visible in domain name)"
elif [ "$STABLE_MCP_URL" != "Not available" ]; then
    echo "Add this STABLE MCP server URL to Claude.ai:"
    echo -e "${GREEN}$STABLE_MCP_URL${NC}"
    echo ""
    echo "This Lambda Function URL is stable and won't change between deployments!"
    echo "Environment: ${ENVIRONMENT}"
else
    echo "Add this MCP server URL to Claude.ai:"
    echo "$MCP_URL"
fi