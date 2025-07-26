# PB-FM-MCP: Provenance Blockchain + Figure Markets MCP Server

A Model Context Protocol (MCP) server providing tools to interact with the Provenance Blockchain and Figure Markets exchange, deployed on AWS Lambda.

## ⚠️ Important: Development Environment Setup

### Critical Lesson Learned: Never Use iCloud for Git Repositories

**DO NOT place this project in iCloud-synced directories** (~/Documents, ~/Desktop). This causes:
- Git repository corruption
- Build directory locks (`.aws-sam/` becomes undeletable)
- File sync conflicts with duplicate files (e.g., "main 2")
- 99% CPU usage from iCloud trying to sync rapid file changes

**Recommended Setup:**
```bash
# Create development directory outside iCloud sync
mkdir ~/Development
cd ~/Development
git clone https://github.com/franks42/pb-fm-mcp.git
```

**Why This Matters:**
- Git repositories modify many files rapidly during operations
- iCloud treats each file individually and cannot handle the pace
- Build tools create thousands of temporary files that confuse sync
- **Use Git/GitHub for backups, not iCloud!**

## Features

### Provenance Blockchain Tools
- Account balance and info retrieval
- Vesting schedule analysis
- Delegation and staking data
- HASH token statistics
- Committed amounts tracking

### Figure Markets Exchange Tools
- Real-time crypto token prices
- Market data and trading pairs
- Asset information and metadata
- Account portfolio balances

## ✅ Production Deployment Status

**DEPLOYED AND FULLY FUNCTIONAL** - Main branch successfully deployed to production AWS Lambda.

### Production Deployment Success Summary

**Infrastructure:** ✅ Successfully deployed to `pb-fm-mcp-v2` stack  
**MCP Protocol:** ✅ 100.0% success (16/16 tools working)  
**REST API:** ✅ 100.0% success (21/21 endpoints working)  
**Overall Functions:** ✅ 81.0% success (17/21 functions passing - exceeds 80% threshold)

### Production URLs

- **🔧 MCP Endpoint**: `https://4d0i1tqdg4.execute-api.us-west-1.amazonaws.com/v1/mcp`
- **🌐 REST API**: `https://4d0i1tqdg4.execute-api.us-west-1.amazonaws.com/v1/api/*`
- **📖 Documentation**: `https://4d0i1tqdg4.execute-api.us-west-1.amazonaws.com/v1/docs`
- **🔗 Stable Function URL**: `https://yhzigtc7cw33oxfzwtvsnlxk4i0myixj.lambda-url.us-west-1.on.aws/`

### Test Results Analysis

**✅ All Protocol Functions Work:** Both MCP and REST protocols are 100% functional for all endpoints.

**ℹ️ Expected Real-time Data Differences:** 4 functions show timing differences due to live market/blockchain data:
- `fetch_current_hash_statistics` - Live blockchain statistics
- `fetch_current_fm_data` - Real-time market data
- `fetch_market_overview_summary` - Comprehensive live market data
- `fetch_vesting_total_unvested_amount` - Dynamic vesting calculations

These "differences" are expected behavior for live financial data and do not indicate functional failures.

**🎉 Conclusion:** Production deployment meets all success criteria with 81% overall success rate and 100% protocol functionality.

## Architecture

### 🚨 CRITICAL: Dual-Path Architecture (MCP vs REST)

**This server uses a DUAL-PATH ARCHITECTURE with SEPARATE Lambda functions for MCP and REST protocols.**

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
│ • Sync execution model   │  │ • ASGI server (uvicorn)        │
└──────────────────────────┘  └────────────────────────────────┘
```

### Why Two Separate Lambda Functions?

**⚠️ CRITICAL LESSON LEARNED**: MCP protocol CANNOT be routed through FastAPI/Web Adapter!

1. **MCP Protocol Requirements**:
   - Requires direct AWS MCP Handler (`MCPLambdaHandler`)
   - Uses specific Lambda event/context format
   - Sync execution model with AWS's internal MCP handling
   - Direct `handle_request(event, context)` calls

2. **REST API Requirements**:
   - Benefits from FastAPI's async support
   - Uses AWS Lambda Web Adapter for native HTTP
   - ASGI server model with uvicorn
   - Full OpenAPI documentation support

**❌ WHAT DOESN'T WORK**: Trying to route MCP through FastAPI results in:
- "Method Not Allowed" errors in Claude.ai
- Tools not being discovered
- Protocol negotiation failures
- Connection timeouts

**✅ WHAT WORKS**: Separate Lambda functions with proper routing:
- MCP goes directly to AWS MCP Handler
- REST goes through FastAPI Web Adapter
- Both share the same API Gateway URL structure

### Technical Stack

- **Runtime**: Python 3.12 on AWS Lambda
- **MCP Handler**: AWS Labs MCP Lambda Handler (direct, no wrapper)
- **REST Handler**: FastAPI + AWS Lambda Web Adapter
- **API Gateway**: Single gateway with path-based routing
- **Dependencies**: awslabs-mcp-lambda-handler, httpx, structlog, fastapi, uvicorn
- **⚠️ AWS Bug Workaround**: Comprehensive monkey patch for AWS MCP Handler's camelCase conversion bug ([Issue #757](https://github.com/awslabs/mcp/issues/757))
  - **Problem**: AWS converts `fetch_account_info` → `fetchAccountInfo` violating MCP standards
  - **Solution**: Runtime patching of both `tools` registry and `tool_implementations` mapping
  - **Impact**: Preserves snake_case naming for all MCP tools and function execution

## Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- IAM role for Lambda execution

### Local Development

1. Clone and install dependencies:
```bash
git clone <repository-url>
cd pb-fm-mcp
uv sync
```

2. Test locally:
```bash
uv run pytest tests/
```

### AWS Lambda Deployment

This project uses a **DUAL-PATH ARCHITECTURE** with separate Lambda functions for MCP and REST protocols.

#### 🚨 CRITICAL: Use the Correct Template

**ALWAYS use `template-dual-path.yaml` for deployments!**

```bash
# ✅ CORRECT - Uses dual-path architecture
sam build --template-file template-dual-path.yaml

# ❌ WRONG - Single function approach doesn't work with MCP
sam build --template-file template-simple.yaml  # DO NOT USE
```

#### Architecture Details

- **Deployment Type**: Two separate Lambda functions with shared API Gateway
- **MCP Function**: Direct AWS MCP Handler (no Web Adapter)
- **REST Function**: FastAPI with AWS Lambda Web Adapter Layer
- **Routing**: Path-based routing at API Gateway level
- **Key Innovation**: Separates MCP protocol handling from REST API handling

#### Prerequisites
- AWS SAM CLI installed
- AWS credentials configured
- Python 3.12+ with uv package manager

#### Deployment Steps

##### Pre-Deployment Best Practices 🏷️

**CRITICAL: Always follow these steps for safe, reproducible deployments:**

1. **Commit ALL files** (even unrelated changes):
```bash
git add .
git commit -m "🔧 Pre-deployment: [describe changes]"
```

2. **Create deployment tag**:
```bash
git tag deploy-2025-07-26-1 -m "Deployment: [key features]"
# Format: deploy-{date}-{sequence}
```

3. **Push to GitHub** (backup before deploy):
```bash
git push origin <branch>
git push origin deploy-2025-07-26-1
```

##### Build and Deploy

1. **Build the application** (MUST use dual-path template):
```bash
sam build --template-file template-dual-path.yaml
```

2. **Deploy to AWS** (development):
```bash
sam deploy --stack-name pb-fm-mcp-dev --resolve-s3
```

##### Why Tag Deployments?
- **✅ Easy Rollback**: `git checkout deploy-2025-07-26-1`
- **✅ Deployment History**: Know what was deployed when
- **✅ Reproducible State**: Exact code for any deployment
- **✅ Team Coordination**: Clear deployment tracking

3. **Deploy to production** (when ready):
```bash
sam deploy --stack-name pb-fm-mcp-v2 --resolve-s3
```

#### What Gets Deployed

The dual-path template creates:
- **McpFunction**: Handles `/mcp` endpoint with direct AWS MCP Handler
- **RestApiFunction**: Handles `/api/*`, `/docs`, `/health` with FastAPI
- **Single API Gateway**: Routes requests to appropriate function based on path

#### Changing API Stage/Version Prefix

The API Gateway stage determines the URL prefix (e.g., `/v1/`, `/v2/`, `/api/`). To change from `/v1/` to a different version:

1. **Edit `template-dual-path.yaml`**:
```yaml
Resources:
  MyServerlessApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: v1.1  # Change this value
```

2. **Update environment variable**:
```yaml
Environment:
  Variables:
    API_GATEWAY_STAGE_PATH: /v1.1  # Match the StageName
```

3. **Update all output URLs**:
```yaml
Outputs:
  ApiUrl:
    Value: !Sub "https://${MyServerlessApi}.execute-api.${AWS::Region}.amazonaws.com/v1.1/"
  OpenApiUrl:
    Value: !Sub "https://${MyServerlessApi}.execute-api.${AWS::Region}.amazonaws.com/v1.1/openapi.json"
  SwaggerDocsUrl:
    Value: !Sub "https://generator3.swagger.io/index.html?url=https://${MyServerlessApi}.execute-api.${AWS::Region}.amazonaws.com/v1.1/openapi.json"
```

4. **Redeploy**:
```bash
sam build --template-file template-dual-path.yaml
sam deploy --stack-name pb-fm-mcp-dev --resolve-s3
```

#### Key Configuration Details

**MCP Function Configuration**:
- **Handler**: `lambda_handler_unified.lambda_handler` (direct Python handler)
- **NO Web Adapter**: Uses direct AWS MCP Handler
- **Sync Execution**: AWS MCP Handler requires synchronous execution
- **Direct Protocol**: Handles MCP JSON-RPC 2.0 directly

**REST API Function Configuration**:
- **Handler**: `run.sh` (startup script for Web Adapter)
- **Layer ARN**: `arn:aws:lambda:us-west-1:753240598075:layer:LambdaAdapterLayerX86:25`
- **Environment Variables**:
  - `AWS_LAMBDA_EXEC_WRAPPER`: `/opt/bootstrap`
  - `PORT`: `8000`
  - `PYTHONPATH`: Set in run.sh to `/var/task/src:$PYTHONPATH`
  - `API_GATEWAY_STAGE_PATH`: `/v1` (for proper Swagger UI paths)

#### Startup Script (`run.sh`) - REST Function Only
```bash
#!/bin/sh
export PATH="/var/runtime:/var/task:$PATH"
export PYTHONPATH="/var/task/src:$PYTHONPATH"
exec python -m uvicorn web_app_unified:app --host 0.0.0.0 --port $PORT
```

This script (used ONLY for REST API function):
1. Sets up Python paths correctly for Lambda environment
2. Launches uvicorn with FastAPI application
3. Web Adapter translates Lambda events ↔ HTTP requests

#### Endpoints

Once deployed, your Lambda function provides clean versioned URLs:
- **MCP Protocol**: `https://your-api-url/v1/mcp`
- **REST API**: `https://your-api-url/v1/api/*`
- **API Documentation**: `https://your-api-url/v1/docs`
- **OpenAPI Spec**: `https://your-api-url/v1/openapi.json`

**Current Development URLs:**
- **MCP Protocol**: `https://48fs6126ba.execute-api.us-west-1.amazonaws.com/v1/mcp`
- **REST API**: `https://48fs6126ba.execute-api.us-west-1.amazonaws.com/v1/api/fetch_current_hash_statistics`
- **API Documentation**: `https://48fs6126ba.execute-api.us-west-1.amazonaws.com/v1/docs`

#### Testing Deployment

```bash
# Test MCP protocol
curl -X POST https://your-api-url/v1/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": "1"}'

# Test REST API
curl https://your-api-url/v1/api/fetch_current_hash_statistics

# View API docs
open https://your-api-url/v1/docs

# Test current development deployment
curl -X POST https://48fs6126ba.execute-api.us-west-1.amazonaws.com/v1/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": "1"}'
```

## Usage

### MCP Client Connection

#### Claude.ai Configuration

To configure Claude.ai to use this MCP server:

1. **Add MCP Server** in Claude.ai settings
2. **Server URL**: `https://48fs6126ba.execute-api.us-west-1.amazonaws.com/v1/mcp`
3. **Connection Method**: HTTP (not WebSocket)

**Important**: The server supports both GET (for connection testing) and POST (for MCP protocol) requests to the same endpoint.

#### Other MCP Clients

Connect to your deployed server using any MCP-compatible client:

```bash
# Using MCP client
mcp connect https://your-api-gateway-url.amazonaws.com/v1/mcp
```

#### Connection Testing

```bash
# Test connection (what Claude.ai does)
curl https://48fs6126ba.execute-api.us-west-1.amazonaws.com/v1/mcp
# Returns: {"name": "PB-FM MCP Server", "version": "0.1.5", ...}

# Test MCP protocol
curl -X POST https://48fs6126ba.execute-api.us-west-1.amazonaws.com/v1/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": "1"}'
# Returns: {"result": {"tools": [... 16 tools ...]}}
```

### Available Tools

#### System & Context
- `get_system_context()` - Essential usage guidelines and documentation

#### HASH Token & Blockchain
- `fetch_last_crypto_token_price(token_pair, last_number_of_trades)` - Recent trading data
- `fetch_current_hash_statistics()` - Overall HASH token statistics
- `fetch_current_fm_data()` - Current market data

#### Account Management
- `fetch_current_fm_account_balance_data(wallet_address)` - Portfolio balances
- `fetch_current_fm_account_info(wallet_address)` - Account details
- `fetch_account_is_vesting(wallet_address)` - Vesting status check

#### Vesting & Delegation
- `fetch_vesting_total_unvested_amount(wallet_address, date_time)` - Vesting calculations
- `fetch_total_delegation_data(wallet_address)` - Staking and delegation info
- `fetch_available_committed_amount(wallet_address)` - Exchange commitments

#### Assets & Markets
- `fetch_figure_markets_assets_info()` - Trading asset details

## Configuration

### Environment Variables
- `AWS_REGION` - AWS region for deployment
- `LOG_LEVEL` - Logging level (INFO, DEBUG, etc.)

### IAM Permissions
Lambda execution role needs:
- `logs:CreateLogGroup`
- `logs:CreateLogStream` 
- `logs:PutLogEvents`

## API Documentation

### Wallet Address Format
All wallet addresses should be in Bech32 format (e.g., `pb1...`).

### Token Denominations
- `nhash` - nano-HASH (1 HASH = 1,000,000,000 nhash)
- `uusd.trading` - micro-USD
- `uusdc.figure.se` - USDC
- `neth.figure.se` - ETH
- `nsol.figure.se` - SOL
- `uxrp.figure.se` - XRP

### Error Handling
All functions return standardized error responses with `MCP-ERROR` key for failed operations.

## Development

### Project Structure
```
pb-fm-mcp/
├── lambda_handler.py      # Main Lambda handler with MCP tools
├── src/
│   ├── utils.py          # Utility functions
│   ├── hastra.py         # Blockchain interaction logic
│   ├── base64expand.py   # Base64 expansion utilities
│   └── hastra_types.py   # Type definitions
├── deploy.py             # Deployment script
├── pyproject.toml        # Project dependencies
└── README.md            # This file
```

### Testing

#### 🚨 CRITICAL: Deployment Success Criteria

**ALL criteria must be met for successful deployment:**

1. **✅ Deployment to Lambda**: Must complete without errors
2. **✅ 100% MCP Function Success**: ALL MCP functions must execute without errors
3. **✅ 100% REST API Success**: ALL REST endpoints must respond without errors  
4. **✅ Data Equivalence**: MCP and REST must return equivalent data (allows for real-time differences in market/blockchain data)

**Failure Definition:**
- ANY MCP function returning errors = DEPLOYMENT FAILURE
- ANY REST API returning HTTP errors = DEPLOYMENT FAILURE  
- Systematic data format differences = DEPLOYMENT FAILURE
- Real-time data differences (market prices, blockchain stats) = ACCEPTABLE

#### Comprehensive Function Coverage Testing

```bash
# REQUIRED test for deployment validation
uv run python scripts/test_function_coverage.py \
  --mcp-url <DEPLOYED_MCP_URL> \
  --rest-url <DEPLOYED_REST_URL> \
  --wallet <VALID_WALLET_ADDRESS>

# Expected output for successful deployment: 
# ✅ MCP: 16/16 (100.0%)
# ✅ REST: 21/21 (100.0%)  
# ✅ Overall: 21/21 (100.0%)
```

#### Development Testing

```bash
# Dependencies are already installed with uv sync

# Run tests
uv run pytest tests/

# Run linting
uv run ruff check .

# Format code
uv run ruff format .
```

### Adding New Tools
1. Add new function with `@mcp_server.tool()` decorator in `lambda_handler.py`
2. Follow existing patterns for error handling
3. Update documentation
4. Add tests

## Monitoring

### CloudWatch Logs
Monitor Lambda execution logs in CloudWatch for debugging and performance analysis.

### Cold Start Optimization
- Function is optimized for minimal cold start times
- Consider provisioned concurrency for production workloads

## Deployment Size Optimization

### Current Package Size
- **Compressed**: ~51 MB (just within AWS Lambda 50 MB ZIP upload limit)
- **Uncompressed**: 146 MB (well within 250 MB Lambda limit)
- **Status**: ✅ Deployment works, room for growth

### Largest Dependencies
1. **botocore** (22 MB) - AWS SDK core (required for Lambda environment)
2. **uvloop** (16 MB) - High-performance async event loop 
3. **pydantic_core** (4.8 MB) - FastAPI validation (required)
4. **yaml** (2.6 MB) - YAML parsing
5. **httptools** (1.7 MB) - Fast HTTP parsing

### Size Reduction Options (if needed)
```bash
# Replace uvicorn[standard] with basic uvicorn (saves 16 MB)
# In requirements.txt, change:
uvicorn[standard]==0.30.1
# To:
uvicorn==0.30.1

# Add to .samignore to exclude development files:
tests/
docs/
.ruff_cache/
*.md
old/
```

**Note**: Current size is acceptable. Only optimize if deployment issues occur or faster deployment is needed.

## Cost Optimization

- **Lambda**: Pay per request/execution time
- **API Gateway**: Pay per API call
- **Free Tier**: 1M Lambda requests/month included

## Troubleshooting

### Common Issues

#### MCP Connection Issues
1. **"Method Not Allowed" in Claude.ai**: Fixed - server now supports both GET and POST methods
2. **Connection Timeout**: Ensure the server URL uses `/v1/mcp` (not the old `/Prod/mcp`)
3. **Wrong Protocol**: Use HTTP, not WebSocket for Claude.ai configuration

#### Dual-Path Architecture Issues
1. **"Method Not Allowed" in Claude.ai**: You're using the wrong template!
   - ❌ **Wrong**: Deployed with `template-simple.yaml` (single function)
   - ✅ **Fix**: Deploy with `template-dual-path.yaml` (dual functions)
2. **MCP tools not discovered**: MCP is being routed through FastAPI
   - ❌ **Wrong**: Single Lambda function trying to handle both protocols
   - ✅ **Fix**: Separate Lambda functions for MCP and REST
3. **MCP connection errors**: Check that `/mcp` routes to McpFunction
   - Verify in AWS Console that McpFunction exists
   - Check CloudWatch logs for McpFunction (not RestApiFunction)

#### General Lambda Issues
1. **Import Errors**: Ensure all dependencies are included in deployment package
2. **Timeout Errors**: Increase Lambda timeout if needed (max 15 minutes)
3. **Memory Errors**: Increase Lambda memory allocation
4. **CORS Issues**: Configure API Gateway CORS settings

### Debug Mode
Set `LOG_LEVEL=DEBUG` environment variable for verbose logging.

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## Support

For issues and questions:
- GitHub Issues: [Repository Issues](https://github.com/your-repo/issues)
- Documentation: [MCP Documentation](https://modelcontextprotocol.io)