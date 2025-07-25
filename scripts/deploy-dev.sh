#!/bin/bash
set -e

echo "🚀 Deploying to development environment..."

# Check if TEST_WALLET_ADDRESS is set
if [ -z "$TEST_WALLET_ADDRESS" ]; then
    echo "❌ ERROR: TEST_WALLET_ADDRESS environment variable is required"
    echo "   Please set it before running this script:"
    echo "   export TEST_WALLET_ADDRESS=\"your_wallet_address\""
    exit 1
fi

# Deploy to dev stack
echo "📦 Deploying to pb-fm-mcp-dev stack..."
sam deploy --stack-name pb-fm-mcp-dev --resolve-s3

echo "✅ Deployment to development completed!"
echo ""
echo "🌐 Development endpoints:"
echo "  MCP: https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod/mcp"
echo "  REST: https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod/api/*"
echo "  Docs: https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod/docs"