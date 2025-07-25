#!/bin/bash
set -e

STACK_NAME=${1:-pb-fm-mcp-container-dev}
ENVIRONMENT=${2:-dev}

echo "🚀 Deploying to stack: ${STACK_NAME}"
echo "🌍 Environment: ${ENVIRONMENT}"

# Get AWS account info
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region || echo "us-west-1")
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/pb-fm-mcp-rest"

echo "📍 Region: ${REGION}"
echo "🏗️ ECR URI: ${ECR_URI}"

# Create ECR repository if it doesn't exist
echo "📦 Checking ECR repository..."
aws ecr describe-repositories --repository-names pb-fm-mcp-rest --region ${REGION} 2>/dev/null || \
  aws ecr create-repository --repository-name pb-fm-mcp-rest --region ${REGION}

# Login to ECR
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region ${REGION} | \
  docker login --username AWS --password-stdin ${ECR_URI}

# Build and push
echo "🔨 Building container..."
./scripts/build-container.sh

echo "📤 Pushing to ECR..."
docker push ${ECR_URI}:latest

# Deploy with SAM
echo "🚀 Deploying with SAM..."
sam build -t template-container.yaml
sam deploy \
  --stack-name ${STACK_NAME} \
  --image-repository ${ECR_URI} \
  --parameter-overrides Environment=${ENVIRONMENT} \
  --capabilities CAPABILITY_IAM \
  --resolve-s3

echo "✅ Deployment complete!"
echo "🌐 Check CloudFormation stack: ${STACK_NAME}"