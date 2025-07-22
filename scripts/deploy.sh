#!/bin/bash

# Automated deployment script with version incrementation
# Usage: ./scripts/deploy.sh [prod|dev] [major|minor|patch]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
VERSION_COMPONENT="patch"
STACK_NAME="pb-fm-mcp-dev"

# Parse arguments
if [ $# -ge 1 ]; then
    ENVIRONMENT=$1
fi

if [ $# -ge 2 ]; then
    VERSION_COMPONENT=$2
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
        echo "Usage: $0 [prod|dev] [major|minor|patch]"
        exit 1
        ;;
esac

echo -e "${BLUE}🚀 pb-fm-mcp Automated Deployment${NC}"
echo "=================================="
echo "Environment: $ENVIRONMENT"
echo "Stack: $STACK_NAME"
echo "Version component: $VERSION_COMPONENT"
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

# Increment version
echo -e "${BLUE}🔼 Incrementing version ($VERSION_COMPONENT)...${NC}"
NEW_VERSION=$(uv run python version.py increment $VERSION_COMPONENT $ENVIRONMENT)
echo "New version: $NEW_VERSION"
echo ""

# Show updated version info
echo -e "${BLUE}📊 Updated version info:${NC}"
uv run python version.py
echo ""

# Build
echo -e "${BLUE}🔨 Building SAM project...${NC}"
sam build
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi
echo ""

# Deploy
echo -e "${BLUE}🚀 Deploying to $ENVIRONMENT environment...${NC}"
sam deploy --stack-name "$STACK_NAME" --resolve-s3
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Deployment successful!${NC}"
echo ""

# Show deployment URLs based on environment
case $ENVIRONMENT in
    "prod")
        echo -e "${GREEN}🌐 Production URLs:${NC}"
        echo "MCP: https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp"
        echo "REST API: https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/"
        echo "Docs: https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/docs"
        ;;
    "dev")
        echo -e "${GREEN}🌐 Development URLs:${NC}"
        echo "MCP: https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod/mcp"
        echo "REST API: https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod/"
        echo "Docs: https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod/docs"
        ;;
esac

echo ""
echo -e "${BLUE}📋 Final version info:${NC}"
uv run python version.py
echo ""

# Optional: Test deployment
echo -e "${BLUE}🧪 Testing deployment...${NC}"
case $ENVIRONMENT in
    "prod")
        TEST_URL="https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/"
        ;;
    "dev")
        TEST_URL="https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod/"
        ;;
esac

echo "Testing REST API: $TEST_URL"
curl -s "$TEST_URL" | uv run python -m json.tool | head -10

echo ""
NEW_VERSION_ONLY=$(echo "$NEW_VERSION" | awk '{print $NF}')
echo -e "${GREEN}🎉 Deployment complete! Version $NEW_VERSION_ONLY is now live.${NC}"