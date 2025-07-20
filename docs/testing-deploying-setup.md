# Testing Setup Guide

This document provides instructions for testing the pb-fm-mcp MCP server both locally and in production.

## Local Testing with AWS SAM

### Prerequisites
- Docker Desktop installed and running
- AWS SAM CLI installed
- AWS CLI configured with valid credentials

### Starting the Local Test Server

1. **Start Docker Desktop**
   ```bash
   open -a Docker
   ```

2. **Build the SAM application** (required after code changes)
   ```bash
   sam build
   ```

3. **Start the local API Gateway**
   ```bash
   # Foreground (with logs in terminal)
   sam local start-api --port 3000
   
   # Background (with logs to file)
   sam local start-api --port 3000 > sam_local.log 2>&1 &
   ```

### Code Changes and Server Restart

**Important**: The local test server does **not** automatically pick up code changes. After making changes, you need to rebuild and restart:

```bash
# 1. Make code changes
# 2. Rebuild 
sam build

# 3. Restart the server (it doesn't auto-reload)
# Kill existing server
lsof -ti:3000 | xargs kill -9

# Start fresh server with updated code
sam local start-api --port 3000
```

**Why no auto-reload:**
- SAM local uses Docker containers with mounted code
- `sam build` creates new artifacts in `.aws-sam/build/`
- Running server uses old container with old code
- Container needs restart to use new build artifacts

### How SAM Local Works

**Architecture:**
```
HTTP Request → SAM CLI (port 3000) → Docker Container → Lambda Handler → Response
```

**Communication flow:**

1. **HTTP Listener**: SAM CLI listens on localhost:3000
2. **Request Processing**: SAM CLI receives HTTP requests
3. **Event Translation**: Converts HTTP to AWS Lambda event format
4. **Container Invocation**: SAM sends event to Docker container via Docker API
5. **Lambda Execution**: Container runs `lambda_handler.lambda_handler(event, context)`
6. **Response Translation**: SAM converts Lambda response back to HTTP response

**Technical details:**
- **Docker API**: SAM uses Docker's REST API to invoke containers
- **Event Format**: HTTP requests are converted to API Gateway Lambda proxy events
- **Volume Mounting**: Code is mounted as `/var/task` in container
- **Environment**: SAM injects Lambda-like environment variables
- **Networking**: Container communicates back through Docker bridge network

**What you see in logs:**
```
Mounting /path/.aws-sam/build/Function as /var/task:ro,delegated
START RequestId: xyz Version: $LATEST
[Your lambda handler logs]
END RequestId: xyz
```

SAM essentially simulates the AWS Lambda service locally using Docker as the runtime environment.

### Testing the Local Server

**Server endpoint**: `http://localhost:3000/mcp`

#### Basic connectivity test
```bash
curl "http://localhost:3000/mcp"
```
*Expected: Server info JSON response*

#### Test tools list
```bash
curl -s -X POST "http://localhost:3000/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | jq -r '.result.tools | length'
```
*Expected: `13` (number of available tools)*

#### Test specific tool call
```bash
curl -s -X POST "http://localhost:3000/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "fetchLastCryptoTokenPrice", "arguments": {"token_pair": "HASH-USD", "last_number_of_trades": 1}}}'
```

### Stopping the Local Server
```bash
# Kill processes using port 3000
lsof -ti:3000 | xargs kill -9

# Or stop Docker containers
docker stop $(docker ps -q)
```

**How the kill command works:**
- `lsof -ti:3000` finds the **SAM CLI process** listening on port 3000
- `kill -9` terminates the **SAM local start-api** process  
- When SAM CLI dies, it automatically **stops and removes** the Docker container
- Port 3000 becomes available again

**What gets killed:**
- ✅ SAM CLI process (`sam local start-api`)
- ✅ Docker container (automatically stopped by SAM)
- ✅ Port 3000 binding released

**Alternative methods:**
```bash
# Kill SAM process directly
pkill -f "sam local start-api"

# Stop all Docker containers (more aggressive)
docker stop $(docker ps -q)
```

## Production Testing

### Production Endpoint
**URL**: `https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp`

### Testing Production Deployment

#### Test tools list
```bash
curl -s -X POST "https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | jq -r '.result.tools | length'
```
*Expected: `13`*

#### Test specific tool call
```bash
curl -s -X POST "https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "fetchLastCryptoTokenPrice", "arguments": {"token_pair": "HASH-USD", "last_number_of_trades": 1}}}'
```

## MCP Client Testing

### Using MCP Inspector (Official Tool)
```bash
# Install MCP Inspector (optional - can use npx)
npm install -g @modelcontextprotocol/inspector

# For our HTTP-based AWS Lambda server, you should use:

# Test local SAM server
npx @modelcontextprotocol/inspector http://localhost:3000/mcp

# Test production Lambda
npx @modelcontextprotocol/inspector https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp

# Note: The template "node path/to/server/index.js args..." is for local Node.js 
# MCP servers, not our HTTP/Lambda deployment
```

### Using Web-based MCP Test Client
Connect your MCP test client to either:
- **Local**: `http://localhost:3000/mcp`
- **Production**: `https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp`

## Deployment

### Deploy to Production
```bash
# 1. Build the SAM application (packages dependencies)
sam build

# 2. Deploy to AWS Lambda
sam deploy --resolve-s3
```

**Alternative deployment options:**
```bash
# Deploy with specific S3 bucket
sam deploy --s3-bucket your-bucket-name

# Guided deployment (interactive setup)
sam deploy --guided
```

**Full deployment workflow:**
```bash
# After making code changes
sam build

# Deploy to production
sam deploy --resolve-s3

# Test the deployment
curl -s -X POST "https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | jq -r '.result.tools | length'
```

**Note:** The deployment uses the existing `template.yaml` and `samconfig.toml` configuration, targeting the `pb-fm-mcp-v2` CloudFormation stack in `us-west-1`.

### Verify Deployment
After deployment, test the production endpoint to ensure all 13 tools are available and functioning.

## Troubleshooting

### Local Testing Issues

1. **Docker not running**
   ```
   Error: Running AWS SAM projects locally requires Docker
   ```
   *Solution*: Start Docker Desktop with `open -a Docker`

2. **Port already in use**
   ```
   Port 3000 is in use by another program
   ```
   *Solution*: Kill existing processes with `lsof -ti:3000 | xargs kill -9`

3. **Missing dependencies**
   ```
   Unable to import module 'lambda_handler': No module named 'httpx'
   ```
   *Solution*: Run `sam build` to rebuild with dependencies

### Production Issues

1. **S3 bucket not specified**
   ```
   S3 Bucket not specified
   ```
   *Solution*: Use `sam deploy --resolve-s3` for automatic bucket management

2. **Package size too large**
   *Solution*: Ensure `.samignore` excludes unnecessary files

## Performance Notes

- **Local SAM**: ~900-1600ms per request (includes Docker overhead and debug logging)
- **Production Lambda**: Much faster due to optimized AWS infrastructure and warm starts
- **Local SAM** is ideal for development/debugging
- **Production Lambda** provides optimal performance for actual usage

## Available Tools

The MCP server exposes 13 tools for interacting with Provenance Blockchain and Figure Markets:

1. `adt` - Special operation returning ultimate answer
2. `fetchAccountInfo` - Get account information
3. `fetchAccountBalances` - Get account balances
4. `fetchAccountVesting` - Get vesting information
5. `fetchAccountDelegations` - Get delegation data
6. `fetchAccountRedelegations` - Get redelegation data
7. `fetchAccountUnbonding` - Get unbonding data
8. `fetchAccountRewards` - Get staking rewards
9. `fetchTokenStats` - Get HASH token statistics
10. `fetchMarketData` - Get trading pairs and markets
11. `fetchLastCryptoTokenPrice` - Get recent token prices
12. `fetchAssetInfo` - Get asset information
13. `fetchTotalDelegationData` - Get comprehensive delegation data

Each tool accepts specific parameters and returns structured data from the respective APIs.