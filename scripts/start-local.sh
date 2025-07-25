#!/bin/bash
set -e

echo "🚀 Starting local SAM API server..."

# Check if TEST_WALLET_ADDRESS is set
if [ -z "$TEST_WALLET_ADDRESS" ]; then
    echo "❌ ERROR: TEST_WALLET_ADDRESS environment variable is required"
    echo "   Please set it before running this script:"
    echo "   export TEST_WALLET_ADDRESS=\"your_wallet_address\""
    exit 1
fi

# Start SAM local API
echo "🌐 Starting SAM local on http://localhost:3000"
echo "📝 Documentation: http://localhost:3000/docs"
echo "🔧 MCP endpoint: http://localhost:3000/mcp"
echo "🌍 REST API: http://localhost:3000/api/*"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

sam local start-api --port 3000