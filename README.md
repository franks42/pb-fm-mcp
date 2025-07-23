# PB-FM-MCP: Provenance Blockchain + Figure Markets MCP Server

A Model Context Protocol (MCP) server providing tools to interact with the Provenance Blockchain and Figure Markets exchange, deployed on AWS Lambda.

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

## Architecture

- **Runtime**: Python 3.12 on AWS Lambda
- **Protocol**: Model Context Protocol with streamable HTTP transport
- **API Gateway**: HTTP API for external access
- **Dependencies**: AWS Labs MCP Lambda Handler, httpx, structlog
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

This project uses AWS Lambda Web Adapter for unified MCP + REST API deployment with native async support.

#### Architecture
- **Deployment Type**: ZIP package with AWS Lambda Web Adapter Layer
- **Runtime**: Python 3.12 with uvicorn ASGI server
- **Protocols**: Both MCP (`/mcp`) and REST (`/api/*`) in single Lambda
- **Key Innovation**: Solves async event loop issues via Web Adapter's native HTTP handling

#### Prerequisites
- AWS SAM CLI installed
- AWS credentials configured
- Python 3.12+ with uv package manager

#### Deployment Steps

1. **Build the application**:
```bash
sam build
```

2. **Deploy to AWS** (development):
```bash
sam deploy --stack-name pb-fm-mcp-dev --resolve-s3
```

3. **Deploy to production** (when ready):
```bash
sam deploy --stack-name pb-fm-mcp-v2 --resolve-s3
```

#### Key Configuration Details

The deployment uses AWS Lambda Web Adapter as a Lambda Layer (not embedded in code):
- **Layer ARN**: `arn:aws:lambda:us-west-1:753240598075:layer:LambdaAdapterLayerX86:25`
- **Handler**: `run.sh` (startup script, not Python handler)
- **Environment Variables**:
  - `AWS_LAMBDA_EXEC_WRAPPER`: `/opt/bootstrap`
  - `PORT`: `8000`
  - `PYTHONPATH`: Set in run.sh to `/var/task/src:$PYTHONPATH`

#### Startup Script (`run.sh`)
```bash
#!/bin/sh
export PATH="/var/runtime:/var/task:$PATH"
export PYTHONPATH="/var/task/src:$PYTHONPATH"
exec python -m uvicorn web_app_unified:app --host 0.0.0.0 --port $PORT
```

This script:
1. Sets up Python paths correctly for Lambda environment
2. Launches uvicorn with our unified FastAPI application
3. Web Adapter translates Lambda events ↔ HTTP requests

#### Endpoints

Once deployed, your Lambda function provides:
- **MCP Protocol**: `https://your-api-url/Prod/mcp`
- **REST API**: `https://your-api-url/Prod/api/*`
- **API Documentation**: `https://your-api-url/Prod/docs`
- **OpenAPI Spec**: `https://your-api-url/Prod/openapi.json`

#### Testing Deployment

```bash
# Test MCP protocol
curl -X POST https://your-api-url/Prod/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": "1"}'

# Test REST API
curl https://your-api-url/Prod/api/fetch_current_hash_statistics

# View API docs
open https://your-api-url/Prod/docs
```

## Usage

### MCP Client Connection

Connect to your deployed server using any MCP-compatible client:

```bash
# Using MCP client
mcp connect https://your-api-gateway-url.amazonaws.com/mcp
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

## Cost Optimization

- **Lambda**: Pay per request/execution time
- **API Gateway**: Pay per API call
- **Free Tier**: 1M Lambda requests/month included

## Troubleshooting

### Common Issues
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