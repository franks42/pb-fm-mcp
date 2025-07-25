#!/bin/bash
set -e

echo "🔧 Building PB-FM MCP Application..."

# Check if TEST_WALLET_ADDRESS is set
if [ -z "$TEST_WALLET_ADDRESS" ]; then
    echo "❌ ERROR: TEST_WALLET_ADDRESS environment variable is required"
    echo "   Please set it before running this script:"
    echo "   export TEST_WALLET_ADDRESS=\"your_wallet_address\""
    exit 1
fi

# Build the SAM application
echo "📦 Running SAM build..."
sam build

echo "✅ Build completed successfully!"
echo ""
echo "Next steps:"
echo "  Local testing: ./scripts/start-local.sh"
echo "  Deploy dev:    ./scripts/deploy-dev.sh"
echo "  Deploy prod:   ./scripts/deploy-prod.sh"