#!/bin/bash

# Deploy script with custom domain support
# Usage: ./scripts/deploy-with-custom-domain.sh [dev|prod] [hosted-zone-id] [certificate-arn]

set -e

ENVIRONMENT=${1:-dev}
HOSTED_ZONE_ID=$2
CERTIFICATE_ARN=$3

if [ -z "$HOSTED_ZONE_ID" ] || [ -z "$CERTIFICATE_ARN" ]; then
    echo "❌ Error: Missing required parameters"
    echo ""
    echo "Usage: $0 [dev|prod] [hosted-zone-id] [certificate-arn]"
    echo ""
    echo "Example:"
    echo "  $0 dev Z1234567890ABC arn:aws:acm:us-west-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"
    echo ""
    echo "Steps to get these values:"
    echo "1. Go to Route 53 → Hosted zones → creativeapptitude.com → Copy Hosted Zone ID"
    echo "2. Go to Certificate Manager → Request certificate for:"
    echo "   - pb-fm-mcp.creativeapptitude.com"
    echo "   - pb-fm-mcp-dev.creativeapptitude.com"
    echo "3. Use DNS validation → Create records in Route 53 → Copy Certificate ARN"
    exit 1
fi

echo "🌐 Deploying with custom domain configuration..."
echo "Environment: $ENVIRONMENT"
echo "Hosted Zone ID: $HOSTED_ZONE_ID"
echo "Certificate ARN: $CERTIFICATE_ARN"
echo ""

# Export environment variables for the main deploy script
export HOSTED_ZONE_ID
export CERTIFICATE_ARN

# Call the main deployment script
./scripts/deploy.sh "$ENVIRONMENT"