#!/bin/bash
# Deploy with automatic documentation updates

echo "🚀 Starting deployment with documentation update..."

# Build and deploy
echo "📦 Building and deploying to AWS..."
sam build && sam deploy --resolve-s3

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    
    # Wait for API to be ready
    echo "⏳ Waiting for API to be ready..."
    sleep 10
    
    # Test that API is responding
    echo "🧪 Testing API availability..."
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/openapi.json")
    
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "✅ API is responding"
        
        # Run comprehensive validation and documentation update
        echo "📚 Validating API and updating documentation..."
        if ./scripts/validate-and-update-docs.sh; then
            echo "🎉 Deployment and documentation update complete!"
        else
            echo "⚠️  Deployment succeeded but documentation validation failed"
            exit 1
        fi
    else
        echo "❌ API not responding (HTTP $HTTP_STATUS)"
        exit 1
    fi
else
    echo "❌ Deployment failed!"
    exit 1
fi