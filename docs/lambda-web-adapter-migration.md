# AWS Lambda Web Adapter + Uvicorn Migration Guide

## 🎯 **Overview**

This guide documents the migration from Mangum + FastAPI to AWS Lambda Web Adapter + Uvicorn for the pb-fm-mcp project. This migration will solve the persistent async event loop issues while maintaining the elegant `@api_function` decorator architecture.

## 📋 **Current State Analysis**

### **What's Working:**
- ✅ MCP Protocol via AWS MCP Lambda Handler (16 tools)
- ✅ `@api_function` decorator architecture
- ✅ Unified function registry
- ✅ AWS MCP Handler monkey patch for snake_case

### **What's Broken:**
- ❌ REST API endpoints (async event loop errors)
- ❌ FastAPI + Mangum async compatibility
- ❌ Thread-based wrapper solutions

### **Root Cause:**
FastAPI + Mangum + AWS Lambda creates incompatible async contexts, causing "There is no current event loop in thread 'MainThread'" errors.

## 🚀 **Migration Strategy**

### **Phase 1: REST API Migration (First Priority)**
Migrate REST endpoints to container-based deployment with AWS Lambda Web Adapter while keeping MCP handler unchanged.

### **Phase 2: Unified Container (Optional Future)**
Optionally combine both MCP and REST in a single container deployment.

## 📝 **Detailed Migration Steps**

### **Step 1: Create Dockerfile**

Create `Dockerfile` in project root:

```dockerfile
# Use AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.12

# Add AWS Lambda Web Adapter
# This allows running standard web frameworks on Lambda
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.7.1 /lambda-adapter /opt/extensions/

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies using pip (uv not available in Lambda container)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY lambda_handler.py .
COPY version.json .
COPY version.py .

# Environment variables for Lambda Web Adapter
ENV PORT=8080
ENV AWS_LWA_READINESS_CHECK_PATH="/health"
ENV AWS_LWA_READINESS_CHECK_PROTOCOL="http"

# Run with Uvicorn
CMD ["uvicorn", "src.web_app:app", "--host", "0.0.0.0", "--port", "8080"]
```

### **Step 2: Create New FastAPI Application**

Create `src/web_app.py`:

```python
"""
FastAPI application for AWS Lambda Web Adapter deployment.
Simplified version without Mangum complexity.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.registry import get_registry, FastAPIIntegration
from version import get_version_string, get_full_version_info

# Create FastAPI app without Lambda-specific configuration
app = FastAPI(
    title="PB-FM API",
    description="REST API for Provenance Blockchain and Figure Markets data",
    version=get_version_string(),
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Health check endpoint for Lambda Web Adapter
@app.get("/health")
async def health_check():
    """Health check endpoint for container readiness."""
    return {"status": "healthy", "version": get_version_string()}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    version_info = get_full_version_info()
    return {
        "name": "PB-FM API",
        "version": version_info["version"],
        "build_number": version_info["build_number"],
        "build_datetime": version_info["build_datetime"],
        "environment": version_info["deployment_environment"],
        "description": "REST API for Provenance Blockchain and Figure Markets data",
        "endpoints": {
            "docs": "/docs",
            "openapi": "/openapi.json",
            "health": "/health"
        }
    }

# Register all @api_function decorated functions as routes
print("🔧 Registering API functions...")
registry = get_registry()
FastAPIIntegration.register_rest_routes(app, registry)
print(f"✅ Registered {len(registry.get_rest_functions())} REST endpoints")

# Update OpenAPI schema
FastAPIIntegration.update_openapi_schema(app, registry)
print("📝 Updated OpenAPI schema with registry documentation")
```

### **Step 3: Simplify FastAPI Integration**

Update `src/registry/integrations.py`:

```python
# In FastAPIIntegration.register_rest_routes method, simplify the route handler:

def create_route_handler(function_meta: FunctionMeta):
    async def route_handler(request: Request):
        try:
            # Extract parameters (same parameter extraction logic)
            sig = function_meta.signature
            kwargs = {}
            
            # ... (keep existing parameter extraction) ...
            
            # SIMPLIFIED: Direct async execution without thread wrapper
            if asyncio.iscoroutinefunction(function_meta.func):
                result = await function_meta.func(**kwargs)  # Direct await!
            else:
                result = function_meta.func(**kwargs)
            
            # Handle error responses
            if isinstance(result, dict) and result.get("MCP-ERROR"):
                raise HTTPException(status_code=500, detail=result["MCP-ERROR"])
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return route_handler
```

### **Step 4: Update SAM Template**

Create `template-container.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: pb-fm-mcp REST API with Lambda Web Adapter

Globals:
  Function:
    Timeout: 30
    MemorySize: 512

Resources:
  # REST API Function (Container)
  RestApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      PackageType: Image
      ImageUri: !Sub ${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/pb-fm-mcp-rest:latest
      Description: REST API endpoints with Lambda Web Adapter
      Environment:
        Variables:
          # Add any environment variables needed
          ENVIRONMENT: !Ref Environment
      Events:
        ApiEvent:
          Type: HttpApi
          Properties:
            Path: /{proxy+}
            Method: ANY
    Metadata:
      DockerTag: latest
      DockerContext: .
      Dockerfile: Dockerfile

  # Keep existing MCP Function (ZIP deployment)
  McpFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: lambda_handler.lambda_handler
      Runtime: python3.12
      Description: MCP Protocol endpoint
      Events:
        McpApi:
          Type: Api
          Properties:
            Path: /mcp
            Method: POST

Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - prod

Outputs:
  RestApiUrl:
    Description: REST API endpoint URL
    Value: !Sub https://${ServerlessHttpApi}.execute-api.${AWS::Region}.amazonaws.com/
  McpApiUrl:
    Description: MCP endpoint URL
    Value: !Sub https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/mcp
```

### **Step 5: Create Build and Deploy Scripts**

Create `scripts/build-container.sh`:

```bash
#!/bin/bash
set -e

echo "🔨 Building container for Lambda Web Adapter deployment..."

# Build the Docker image
docker build -t pb-fm-mcp-rest:latest .

# Tag for ECR
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/pb-fm-mcp-rest"

docker tag pb-fm-mcp-rest:latest ${ECR_URI}:latest

echo "✅ Container built and tagged"
```

Create `scripts/deploy-container.sh`:

```bash
#!/bin/bash
set -e

STACK_NAME=${1:-pb-fm-mcp-container-dev}
ENVIRONMENT=${2:-dev}

echo "🚀 Deploying to stack: ${STACK_NAME}"

# Get AWS account info
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/pb-fm-mcp-rest"

# Create ECR repository if it doesn't exist
aws ecr describe-repositories --repository-names pb-fm-mcp-rest 2>/dev/null || \
  aws ecr create-repository --repository-name pb-fm-mcp-rest

# Login to ECR
aws ecr get-login-password --region ${REGION} | \
  docker login --username AWS --password-stdin ${ECR_URI}

# Build and push
./scripts/build-container.sh
docker push ${ECR_URI}:latest

# Deploy with SAM
sam build -t template-container.yaml
sam deploy \
  --stack-name ${STACK_NAME} \
  --image-repository ${ECR_URI} \
  --parameter-overrides Environment=${ENVIRONMENT} \
  --capabilities CAPABILITY_IAM \
  --resolve-s3

echo "✅ Deployment complete!"
```

### **Step 6: Update Requirements**

Update `requirements.txt` to include Uvicorn:

```txt
# Existing dependencies...

# Add for Lambda Web Adapter deployment
uvicorn[standard]==0.30.1
```

### **Step 7: Testing Strategy**

1. **Local Testing with Docker:**
```bash
# Build container
docker build -t pb-fm-mcp-test .

# Run locally
docker run -p 8080:8080 pb-fm-mcp-test

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:8080/api/current_hash_statistics
```

2. **Lambda Testing:**
```bash
# Deploy to dev
./scripts/deploy-container.sh pb-fm-mcp-container-dev dev

# Test deployed endpoints
curl https://[api-id].execute-api.us-west-1.amazonaws.com/api/current_hash_statistics
```

## 🔄 **Migration Phases**

### **Phase 1: Parallel Deployment (Recommended)**
1. Deploy new container-based REST API alongside existing deployment
2. Test all endpoints thoroughly
3. Update documentation with new endpoints
4. Gradually migrate clients to new endpoints
5. Deprecate old Mangum-based endpoints

### **Phase 2: Full Cutover**
1. Update DNS/routing to point to new endpoints
2. Monitor for issues
3. Decommission old deployment

### **Phase 3: Optional MCP Integration**
1. Add MCP handler to container
2. Create unified deployment
3. Simplify infrastructure

## ⚠️ **Important Considerations**

### **1. Cold Start Performance**
- Container images have slightly slower cold starts than ZIP deployments
- Mitigate with provisioned concurrency if needed

### **2. Image Size Optimization**
- Use multi-stage builds to minimize final image size
- Only include necessary dependencies

### **3. Environment Variables**
- Migrate any Lambda environment variables to container
- Ensure secrets are properly managed

### **4. Monitoring**
- Set up CloudWatch logs for new container
- Monitor performance metrics
- Track error rates during migration

## 🎯 **Expected Benefits**

1. **✅ Async Functions Work Natively** - No more event loop errors
2. **✅ Simplified Code** - Remove complex thread wrappers
3. **✅ Better Performance** - Native async execution
4. **✅ Standard Patterns** - Familiar FastAPI development
5. **✅ Easier Debugging** - Standard web server behavior

## 📊 **Success Metrics**

- [ ] All REST endpoints return 200 OK
- [ ] Async aggregate functions work without errors
- [ ] Response times equal or better than current
- [ ] No "event loop" errors in CloudWatch logs
- [ ] OpenAPI documentation accessible

## 🚨 **Rollback Plan**

If issues arise:
1. Keep existing deployment running
2. Route traffic back to old endpoints
3. Debug issues in development environment
4. Fix and redeploy

## 📚 **Resources**

- [AWS Lambda Web Adapter GitHub](https://github.com/awslabs/aws-lambda-web-adapter)
- [Lambda Container Image Support](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [FastAPI with Uvicorn](https://fastapi.tiangolo.com/deployment/server-workers/)
- [SAM Container Support](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-container-image.html)