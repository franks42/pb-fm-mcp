# MCP Client Usage Guide

Simple HTTP-based MCP (Model Context Protocol) client for testing pb-fm-mcp server functionality.

## Overview

The `scripts/simple_mcp_client.py` client provides a command-line interface for testing MCP servers using direct JSON-RPC over HTTP. It's specifically designed for AWS Lambda MCP handlers and supports both local and production testing.

## Features

- ✅ **Direct HTTP transport** - Uses JSON-RPC over HTTP (no SSE complexity)
- ✅ **Tool discovery** - Lists all available MCP tools with schemas
- ✅ **Tool execution** - Call tools with JSON parameters and see results
- ✅ **MCP vs REST comparison** - Compare identical calls across protocols
- ✅ **Interactive mode** - Manual testing and exploration
- ✅ **Production ready** - Works with AWS Lambda MCP endpoints

## Installation

The client requires the MCP Python SDK:

```bash
uv add mcp
```

## Usage Examples

### Basic Tool Discovery

List all available tools on the server:

```bash
uv run python scripts/simple_mcp_client.py --mcp-url http://localhost:3000/mcp
```

### Production Testing

Test against production Lambda:

```bash
uv run python scripts/simple_mcp_client.py \
  --mcp-url https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp
```

### Run Predefined Tests

Execute automated test suite:

```bash
# Local testing
uv run python scripts/simple_mcp_client.py --mcp-url http://localhost:3000/mcp --test

# Production testing  
uv run python scripts/simple_mcp_client.py \
  --mcp-url https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp \
  --test
```

### Interactive Mode

Manual testing and exploration:

```bash
uv run python scripts/simple_mcp_client.py \
  --mcp-url http://localhost:3000/mcp \
  --interactive
```

#### Interactive Commands

```
mcp> list                           # List all available tools
mcp> call fetchCurrentHashStatistics {}    # Call a tool with parameters
mcp> rest /api/current_hash_statistics {}  # Call REST API directly  
mcp> compare fetchCurrentHashStatistics /api/current_hash_statistics {}  # Compare protocols
mcp> quit                           # Exit
```

### MCP vs REST Comparison

Compare identical functionality across protocols:

```bash
uv run python scripts/simple_mcp_client.py \
  --mcp-url http://localhost:3000/mcp \
  --interactive

# Then use compare command:
mcp> compare fetchCurrentHashStatistics /api/current_hash_statistics {}
```

## Command Line Options

```bash
usage: simple_mcp_client.py [-h] [--mcp-url MCP_URL] [--rest-url REST_URL]
                            [--interactive] [--test]

Simple HTTP-based MCP Test Client

options:
  -h, --help           show this help message and exit
  --mcp-url MCP_URL    MCP server URL (default: http://localhost:3000/mcp)
  --rest-url REST_URL  REST API base URL (auto-detected from MCP URL)
  --interactive, -i    Run in interactive mode
  --test, -t          Run predefined tests
```

## URL Configuration

### Local Development

```bash
--mcp-url http://localhost:3000/mcp
# REST base URL: http://localhost:3000/ (auto-detected)
```

### AWS Lambda Production

```bash
--mcp-url https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp  
# REST base URL: https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/ (auto-detected)
```

### Custom REST URL

```bash
--mcp-url http://localhost:3000/mcp --rest-url http://different-host/api/
```

## Example Tool Calls

### Simple Tools (No Parameters)

```bash
# Get system context
mcp> call getSystemContext {}

# Get current HASH statistics  
mcp> call fetchCurrentHashStatistics {}

# Get Figure Markets data
mcp> call fetchCurrentFmData {}
```

### Tools with Parameters

```bash
# Get account information
mcp> call fetchAccountInfo {"wallet_address": "pb1gghjut3ccd8ay0zduzj64hwre2fxs9ldmqhffj"}

# Get delegation data
mcp> call fetchTotalDelegationData {"wallet_address": "pb1gghjut3ccd8ay0zduzj64hwre2fxs9ldmqhffj"}

# Get crypto token price
mcp> call fetchLastCryptoTokenPrice {"token_pair": "HASH-USD", "last_number_of_trades": 5}
```

## Testing Workflows

### Development Workflow

1. **Start local server**:
   ```bash
   sam build && sam local start-api --port 3000
   ```

2. **Test MCP functionality**:
   ```bash
   uv run python scripts/simple_mcp_client.py --test
   ```

3. **Compare protocols**:
   ```bash
   uv run python scripts/simple_mcp_client.py --interactive
   ```

### Production Validation

1. **Test production MCP**:
   ```bash
   uv run python scripts/simple_mcp_client.py \
     --mcp-url https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp \
     --test
   ```

2. **Validate specific tools**:
   ```bash
   uv run python scripts/simple_mcp_client.py \
     --mcp-url https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp \
     --interactive
   ```

## Troubleshooting

### Connection Issues

**Problem**: Connection failed or timeout
```
❌ Connection failed: Client error '404 Not Found'
```

**Solutions**:
- Check MCP URL is correct
- Verify server is running (local) or deployed (production)
- Ensure network connectivity

### URL Construction Issues

**Problem**: 403 Forbidden on REST calls
```
❌ REST API call failed: Client error '403 Forbidden'
```

**Solutions**:
- Verify REST base URL includes correct path prefix
- For Lambda: ensure `/Prod` prefix is included
- Check API Gateway configuration

### Tool Execution Issues

**Problem**: Tool returns error or unexpected data
```
❌ Tool call failed: MCP Error: {...}
```

**Solutions**:
- Check tool parameters match required schema
- Validate wallet addresses are correctly formatted
- Review tool documentation for parameter requirements

### JSON Parsing Issues

**Problem**: JSON decode error in interactive mode
```
❌ JSON error: Expecting value: line 1 column 1 (char 0)
```

**Solutions**:
- Ensure parameters are valid JSON: `{"key": "value"}`
- Use empty object for no parameters: `{}`
- Quote strings properly: `{"wallet_address": "pb1..."}`

## Advanced Usage

### Custom Test Scenarios

Create custom test sequences in interactive mode:

```bash
mcp> call fetchAccountInfo {"wallet_address": "pb1test..."}
mcp> call fetchTotalDelegationData {"wallet_address": "pb1test..."}  
mcp> call fetchAvailableCommittedAmount {"wallet_address": "pb1test..."}
```

### Performance Testing

Time tool execution by observing response times in output.

### Protocol Validation

Use comparison commands to ensure MCP and REST return identical data:

```bash
mcp> compare fetchCurrentHashStatistics /api/current_hash_statistics {}
```

Expected: Small timing differences in dynamic data (normal blockchain behavior)
Unexpected: Different data structures or significant value differences

## Integration with Development

### Pre-deployment Testing

Test new tools before deployment:

```bash
# Test locally first
uv run python scripts/simple_mcp_client.py --test

# Then test production  
uv run python scripts/simple_mcp_client.py \
  --mcp-url https://your-lambda-url/Prod/mcp \
  --test
```

### CI/CD Integration

Include client in automated testing:

```bash
# In CI pipeline
uv run python scripts/simple_mcp_client.py \
  --mcp-url $PROD_MCP_URL \
  --test
```

## Architecture Notes

The client uses:
- **Direct JSON-RPC over HTTP** (not SSE) for AWS Lambda compatibility
- **Automatic URL construction** for REST endpoint mapping
- **Proper async/await** patterns with httpx
- **Session-based MCP protocol** with initialization handshake

This design makes it ideal for testing AWS Lambda MCP handlers where traditional SSE transport may not be available.