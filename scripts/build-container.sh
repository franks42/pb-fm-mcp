#!/bin/bash
set -e

echo "🔨 Building container for Lambda Web Adapter deployment..."

# Build the Docker image
docker build -t pb-fm-mcp-rest:latest .

# Get AWS account info
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region || echo "us-west-1")

# Create ECR URI
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/pb-fm-mcp-rest"

# Tag for ECR
docker tag pb-fm-mcp-rest:latest ${ECR_URI}:latest

echo "✅ Container built and tagged"
echo "📦 Image: ${ECR_URI}:latest"