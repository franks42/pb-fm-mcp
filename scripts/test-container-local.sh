#!/bin/bash
set -e

echo "🧪 Testing container locally..."

# Build the container
echo "🔨 Building Docker image..."
docker build -t pb-fm-mcp-test .

# Run the container locally
echo "🚀 Starting container on port 8080..."
docker run -d --name pb-fm-mcp-test -p 8080:8080 pb-fm-mcp-test

# Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 5

# Test endpoints
echo "🔍 Testing endpoints..."

echo -e "\n1️⃣ Testing health endpoint:"
curl -s http://localhost:8080/health | jq

echo -e "\n2️⃣ Testing root endpoint:"
curl -s http://localhost:8080/ | jq

echo -e "\n3️⃣ Testing docs endpoint:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/docs

echo -e "\n\n4️⃣ Testing registry summary:"
curl -s http://localhost:8080/api/registry_summary | jq

echo -e "\n5️⃣ Testing hash statistics (async aggregate):"
curl -s http://localhost:8080/api/current_hash_statistics | jq '.maxSupply.amount'

# Cleanup
echo -e "\n🧹 Cleaning up..."
docker stop pb-fm-mcp-test
docker rm pb-fm-mcp-test

echo "✅ Local test complete!"