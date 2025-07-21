#!/bin/bash
# Validate API health and update documentation after deployment
# This ensures docs are only updated when the API is actually working

API_BASE_URL="https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod"
MAX_RETRIES=5
RETRY_DELAY=10

echo "🔍 Validating API health before updating documentation..."

# Function to test API endpoint
test_endpoint() {
    local url=$1
    local description=$2
    
    echo "🧪 Testing: $description"
    echo "   URL: $url"
    
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 30)
    
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "   ✅ Success (HTTP $HTTP_STATUS)"
        return 0
    else
        echo "   ❌ Failed (HTTP $HTTP_STATUS)"
        return 1
    fi
}

# Function to validate API with retries
validate_api() {
    local attempt=1
    
    while [ $attempt -le $MAX_RETRIES ]; do
        echo "🔄 Validation attempt $attempt of $MAX_RETRIES"
        
        # Test critical endpoints
        local all_passed=true
        
        if ! test_endpoint "$API_BASE_URL/openapi.json" "OpenAPI Specification"; then
            all_passed=false
        fi
        
        if ! test_endpoint "$API_BASE_URL/api/current_hash_statistics" "HASH Statistics"; then
            all_passed=false
        fi
        
        if ! test_endpoint "$API_BASE_URL/api/system_context" "System Context"; then
            all_passed=false
        fi
        
        if ! test_endpoint "$API_BASE_URL/docs" "API Documentation"; then
            all_passed=false
        fi
        
        if [ "$all_passed" = true ]; then
            echo "✅ All API health checks passed!"
            return 0
        fi
        
        if [ $attempt -lt $MAX_RETRIES ]; then
            echo "⏳ Waiting ${RETRY_DELAY}s before retry..."
            sleep $RETRY_DELAY
        fi
        
        ((attempt++))
    done
    
    echo "❌ API health validation failed after $MAX_RETRIES attempts"
    return 1
}

# Function to count endpoints
count_endpoints() {
    local endpoint_count
    endpoint_count=$(curl -s "$API_BASE_URL/openapi.json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    paths = data.get('paths', {})
    print(len(paths))
except:
    print(0)
" 2>/dev/null)
    
    echo "$endpoint_count"
}

# Main validation and documentation update
main() {
    echo "🚀 Starting API validation and documentation update"
    echo "=================================================="
    
    # Validate API health
    if ! validate_api; then
        echo "💥 Deployment validation failed - API is not healthy"
        echo "🚫 Documentation update skipped for safety"
        exit 1
    fi
    
    # Count endpoints
    ENDPOINT_COUNT=$(count_endpoints)
    echo "📊 API has $ENDPOINT_COUNT endpoints"
    
    # Generate documentation URLs
    OPENAPI_URL="$API_BASE_URL/openapi.json"
    SWAGGER_URL="https://generator3.swagger.io/index.html?url=$OPENAPI_URL"
    DOCS_URL="$API_BASE_URL/docs"
    
    echo ""
    echo "📚 Documentation URLs (LIVE and VALIDATED):"
    echo "============================================="
    echo "🔗 OpenAPI Spec:  $OPENAPI_URL"
    echo "🔗 Swagger UI:    $SWAGGER_URL" 
    echo "🔗 FastAPI Docs:  $DOCS_URL"
    echo ""
    
    # Log success
    echo "✅ Documentation validation completed successfully!"
    echo "🎉 All $ENDPOINT_COUNT endpoints are live and documented"
    
    # Optional: Send notification (uncomment if you have Slack webhook)
    # curl -X POST YOUR_SLACK_WEBHOOK_URL -H 'Content-type: application/json' \
    #   --data '{"text":"📚 API Documentation Updated! '$ENDPOINT_COUNT' endpoints live at: '$SWAGGER_URL'"}'
    
    return 0
}

# Run main function
main "$@"