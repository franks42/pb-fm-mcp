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

1. Create deployment package:
```bash
uv run python deploy.py --package-only
```

2. Deploy to AWS Lambda:
```bash
uv run python deploy.py \
  --function-name pb-fm-mcp-server \
  --role-arn arn:aws:iam::123456789012:role/lambda-execution-role \
  --region us-east-1 \
  --api-gateway
```

3. Manual API Gateway setup (if --api-gateway flag used):
   - Go to AWS Console > API Gateway
   - Create new HTTP API
   - Add integration to Lambda function
   - Add route: `POST /mcp`
   - Enable CORS if needed
   - Deploy API

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