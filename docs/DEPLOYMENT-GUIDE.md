# 🚀 Comprehensive Deployment Guide for pb-fm-mcp

This guide provides detailed, step-by-step instructions for deploying the pb-fm-mcp server to AWS Lambda, including all prerequisites, best practices, and troubleshooting.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Understanding the Architecture](#understanding-the-architecture)
3. [Pre-Deployment Best Practices](#pre-deployment-best-practices)
4. [Deployment Process](#deployment-process)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Rollback Procedures](#rollback-procedures)
7. [Troubleshooting](#troubleshooting)
8. [Deployment History Tracking](#deployment-history-tracking)

## Prerequisites

### Required Tools

1. **AWS CLI** (v2.x)
   ```bash
   aws --version
   # Should show: aws-cli/2.x.x
   ```

2. **AWS SAM CLI** (v1.100+)
   ```bash
   sam --version
   # Should show: SAM CLI, version 1.100.0 or higher
   ```

3. **Python 3.12+** with **uv** package manager
   ```bash
   python --version
   # Should show: Python 3.12.x
   
   uv --version
   # Should show: uv 0.x.x
   ```

4. **Git** configured with GitHub access
   ```bash
   git remote -v
   # Should show: origin https://github.com/franks42/pb-fm-mcp.git
   ```

### AWS Configuration

1. **AWS Credentials**
   ```bash
   aws configure list
   # Should show your configured profile
   ```

2. **Required AWS Permissions**
   - Lambda: Create/Update functions
   - API Gateway: Create/Update APIs
   - CloudFormation: Create/Update stacks
   - S3: Upload deployment artifacts
   - IAM: Create/Update roles (for Lambda execution)
   - DynamoDB: Access for dashboard storage

3. **Environment Variables** (Optional)
   ```bash
   export AWS_PROFILE=your-profile  # If using named profiles
   export AWS_REGION=us-west-1      # Default region
   ```

## Understanding the Architecture

### Dual-Path Lambda Architecture

This project uses a **critical dual-path architecture** that MUST be understood before deployment:

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (v1)                          │
├─────────────────────────────────────────────────────────────┤
│  /mcp endpoint          │  /api/*, /docs, /health endpoints │
└──────────┬──────────────┴─────────────┬─────────────────────┘
           │                            │
           ▼                            ▼
┌──────────────────────────┐  ┌────────────────────────────────┐
│   McpFunction Lambda     │  │   RestApiFunction Lambda       │
│ ━━━━━━━━━━━━━━━━━━━━━━━ │  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ • Direct AWS MCP Handler │  │ • FastAPI + Web Adapter        │
│ • lambda_handler.py      │  │ • web_app_unified.py           │
│ • NO FastAPI wrapper     │  │ • Native async support         │
└──────────────────────────┘  └────────────────────────────────┘
```

### Key Points
- **Two separate Lambda functions** are deployed
- **MCP protocol** requires direct handler (no FastAPI)
- **REST API** uses FastAPI with AWS Lambda Web Adapter
- **NEVER** try to combine them into single function

### Important Files
- `template-dual-path.yaml` - **THE ONLY TEMPLATE TO USE**
- `lambda_handler_unified.py` - MCP protocol handler
- `src/web_app_unified.py` - REST API handler

## Pre-Deployment Best Practices

### 🏷️ The Golden Rule: Tag Everything

**ALWAYS follow this workflow to ensure safe, reproducible deployments:**

### Step 1: Clean Working Directory

```bash
# Check for uncommitted changes
git status

# If you see uncommitted files, commit them ALL
git add .
git commit -m "🔧 Pre-deployment: [describe what changed]"
```

**Why?** Even unrelated changes might affect deployment. Better to have everything committed.

### Step 2: Create Deployment Tag

```bash
# Format: deploy-{date}-{sequence}
git tag deploy-2025-07-26-1 -m "Deployment to dev: MCP session support, dynamic config"

# For environment-specific tags:
git tag deploy-dev-2025-07-26-1 -m "Dev deployment: [features]"
git tag deploy-prod-2025-07-26-1 -m "Production deployment: [features]"
```

**Tag Message Should Include:**
- Target environment (dev/prod)
- Key features being deployed
- Any known issues or limitations

### Step 3: Push Everything to GitHub

```bash
# Push your branch
git push origin mcp-ui  # or whatever branch you're on

# Push the deployment tag
git push origin deploy-2025-07-26-1
```

**Why?** This creates a complete backup before deployment. If anything goes wrong, you can recover.

## Deployment Process

### Option 1: Automated Deployment (Recommended) 🚀

The project includes a smart deployment script that handles everything:

```bash
# For development environment
./scripts/deploy.sh dev

# For production environment (requires confirmation)
./scripts/deploy.sh prod
```

**What the script does:**
1. ✅ Checks git status
2. ✅ Generates version info
3. ✅ Cleans build directory
4. ✅ Runs pruning to stay under Lambda limits
5. ✅ Builds with correct template
6. ✅ Deploys to specified environment
7. ✅ Runs post-deployment tests

### Option 2: Manual Deployment 🔧

If you need more control or the script fails:

#### Step 1: Clean Build Directory

```bash
# CRITICAL: Always clean first to prevent poisoned builds
rm -rf .aws-sam/
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
```

#### Step 2: Build Application

```bash
# MUST use dual-path template
sam build --template-file template-dual-path.yaml
```

**Expected output:**
```
Building codeuri: /path/to/pb-fm-mcp runtime: python3.12 metadata: {} architecture: x86_64 functions: McpFunction, RestApiFunction
Running PythonPipBuilder:ResolveDependencies
Running PythonPipBuilder:CopySource
Build Succeeded
```

#### Step 3: Deploy to AWS

**Development:**
```bash
sam deploy --stack-name pb-fm-mcp-dev --resolve-s3
```

**Production:**
```bash
# ONLY from main branch with explicit approval
git checkout main
sam deploy --stack-name pb-fm-mcp-v2 --resolve-s3
```

**Deployment Parameters:**
- `--resolve-s3` - Automatically creates/uses S3 bucket for artifacts
- `--parameter-overrides` - Override template parameters if needed

#### Step 4: Monitor Deployment

```bash
# Watch CloudFormation progress
aws cloudformation describe-stack-events \
  --stack-name pb-fm-mcp-dev \
  --max-items 10
```

## Post-Deployment Verification

### 1. Check Lambda Functions

```bash
# List deployed functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `pb-fm-mcp`)].FunctionName'

# Check function configuration
aws lambda get-function --function-name pb-fm-mcp-dev-McpFunction-XXX
```

### 2. Test MCP Endpoint

```bash
# Test MCP server info
curl https://your-api-url/v1/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":"1","params":{"protocolVersion":"2024-11-05"}}'
```

### 3. Test REST API

```bash
# Test health endpoint
curl https://your-api-url/v1/health

# Test API documentation
curl https://your-api-url/v1/docs
```

### 4. Run Comprehensive Tests

```bash
# Set test wallet address
export TEST_WALLET_ADDRESS=pb1c9rqwfefggk3s3y79rh8quwvp8rf8ayr7qvmk8

# Run function coverage tests
uv run python scripts/test_function_coverage.py \
  --mcp-url https://your-api-url/v1/mcp \
  --rest-url https://your-api-url/v1

# Expected output:
# ✅ MCP: 16/16 (100.0%)
# ✅ REST: 21/21 (100.0%)
# ✅ Overall: 17+/21 (80%+)
```

## Rollback Procedures

### Quick Rollback to Previous Version

```bash
# 1. Checkout previous deployment tag
git checkout deploy-2025-07-25-3  # Previous working version

# 2. Rebuild and deploy
rm -rf .aws-sam/
sam build --template-file template-dual-path.yaml
sam deploy --stack-name pb-fm-mcp-dev --resolve-s3
```

### CloudFormation Rollback

```bash
# If deployment fails, CloudFormation auto-rollback occurs
# To manually trigger rollback:
aws cloudformation cancel-update-stack --stack-name pb-fm-mcp-dev
```

### Finding Previous Good Deployment

```bash
# List all deployment tags
git tag -l "deploy-*" | sort -V

# Show tag details
git show deploy-2025-07-25-3 --no-patch
```

## Troubleshooting

### Common Issues and Solutions

#### 1. "Internal Server Error" After Deployment

**Cause**: Poisoned build cache
**Solution**: 
```bash
rm -rf .aws-sam/
# Rebuild and redeploy
```

#### 2. Lambda Package Too Large

**Cause**: Dependencies exceed 250MB limit
**Solution**: 
- Check `.samignore` file is present
- Run pruning script: `./scripts/prune_deployment.sh`
- Review large dependencies

#### 3. MCP Tools Not Discovered

**Cause**: Using wrong template or routing issue
**Solution**: 
- Verify using `template-dual-path.yaml`
- Check API Gateway routing
- Ensure `/mcp` routes to McpFunction

#### 4. Async Event Loop Errors

**Cause**: REST API Lambda missing Web Adapter
**Solution**: 
- Verify RestApiFunction has AWS Lambda Web Adapter layer
- Check `run.sh` script is included

### Debug Commands

```bash
# View Lambda logs
aws logs tail /aws/lambda/pb-fm-mcp-dev-McpFunction-XXX --follow

# Check API Gateway configuration
aws apigateway get-rest-apis

# Verify stack status
aws cloudformation describe-stacks --stack-name pb-fm-mcp-dev
```

## Deployment History Tracking

### Create DEPLOYMENTS.md

Track all deployments in a `DEPLOYMENTS.md` file:

```markdown
# Deployment History

## deploy-2025-07-26-1
- **Date**: July 26, 2025
- **Time**: 14:30 UTC
- **Environment**: dev
- **Stack**: pb-fm-mcp-dev
- **Git Commit**: 71d1630
- **Deployed By**: @franks42
- **Key Features**:
  - MCP session-based dashboard URLs
  - Enhanced debugging for AI instances
  - Dynamic configuration support
- **Test Results**:
  - MCP: 16/16 (100%)
  - REST: 21/21 (100%)
  - Overall: 17/21 (81%)
- **Known Issues**: None
- **Rollback To**: deploy-2025-07-25-3

## deploy-2025-07-25-3
- **Date**: July 25, 2025
- **Time**: 22:15 UTC
- **Environment**: prod
- **Stack**: pb-fm-mcp-v2
...
```

### Deployment Checklist Template

```markdown
- [ ] All tests passing locally
- [ ] Git status clean
- [ ] Deployment tag created
- [ ] Tag pushed to GitHub
- [ ] CloudFormation stack updated successfully
- [ ] MCP endpoint responding
- [ ] REST API endpoints working
- [ ] Function coverage tests passing
- [ ] Deployment documented in DEPLOYMENTS.md
```

## Summary

### Key Takeaways

1. **Always use `template-dual-path.yaml`** - Never use other templates
2. **Tag every deployment** - Format: `deploy-{date}-{sequence}`
3. **Clean builds are critical** - Always `rm -rf .aws-sam/` first
4. **Test after deployment** - Use comprehensive function coverage tests
5. **Document everything** - Update DEPLOYMENTS.md

### Quick Reference Card

```bash
# Complete deployment in 5 commands:
git tag deploy-2025-07-26-1 -m "Deployment: [features]"
git push origin deploy-2025-07-26-1
./scripts/deploy.sh dev
# Wait for completion...
TEST_WALLET_ADDRESS=pb1test... uv run python scripts/test_function_coverage.py --mcp-url ... --rest-url ...
```

### Getting Help

- **CloudWatch Logs**: Primary debugging tool
- **GitHub Issues**: Report deployment problems
- **CLAUDE.md**: Additional context and warnings
- **AWS Support**: For infrastructure issues

---

**Remember**: A failed deployment is better than a broken production. Always follow the process!