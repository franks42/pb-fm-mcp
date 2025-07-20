# Development Roadmap - pb-fm-mcp

## Current Status
- ✅ AWS Lambda MCP server with 13 tools
- ✅ Production deployment working
- ✅ Local SAM testing environment
- ✅ jqpy and base64expand preserved for integration

## Improvement Priorities

### 🔴 High Priority

#### API Architecture Refactoring
- **Refactor PB-API functions into separate async proxy layer** - Create clean separation between raw API calls and data processing
- **Create standardized data transformation layer** - Convert raw PB-API responses into consistent, filtered data structures
- **Implement dual API exposure** - Expose both MCP protocol and REST endpoints for the same functionality
- **Design REST API endpoints** - Mirror MCP tools as REST endpoints for non-MCP AI agents

#### Core Integrations
- **Integrate jqpy JSON processing** - Add jq-like query capabilities to MCP tools
- **Dynamic JSON transformation tool** - Let users apply jq syntax via MCP for custom data filtering

### 🟡 Medium Priority

#### Production Quality
- **Remove debug logging from production** - Clean up lambda_handler.py for better performance
- **Environment-based logging** - Debug mode for local, clean logs for production
- **Error handling & retry logic** - Robust external API calls with timeouts and retries
- **Input validation** - Comprehensive parameter checking for all MCP tools
- **base64expand integration** - Handle encoded blockchain data in responses
- **Unit testing** - Comprehensive test coverage for Lambda handler and tools
- **API documentation** - OpenAPI/Swagger spec for REST endpoints

### 🟢 Lower Priority

#### Performance & Monitoring
- **Fix jqpy CLI integration** - Resolve 28 failing CLI tests
- **Optimize Lambda cold starts** - Reduce initialization time
- **Implement caching layer** - Cache frequent API calls (token prices, account info)
- **Monitoring and alerting** - Production observability and health checks

## Architectural Vision

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS Lambda Handler                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐           ┌─────────────────────────┐  │
│  │   MCP Protocol  │           │     REST API Layer     │  │
│  │   (13 tools)    │           │   (/api/v1/*)          │  │
│  └─────────────────┘           └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│              Standardized Data Layer                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Data Transformation & Filtering (jqpy + base64)   │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                PB-API Proxy Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐ ┌─────────────┐  │
│  │ Provenance APIs │  │ Figure Markets  │ │ Other APIs  │  │
│  │     (async)     │  │     (async)     │ │   (async)   │  │
│  └─────────────────┘  └─────────────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Benefits of Dual API Approach

1. **MCP Protocol**: Full integration with Claude, MCP Inspector, and other MCP clients
2. **REST APIs**: Direct access for AI agents, web apps, and non-MCP integrations
3. **Shared Logic**: Both APIs use the same underlying proxy functions and data transformation
4. **Standardized Responses**: Consistent data format regardless of access method

### Example Usage

**MCP Client:**
```json
{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "fetchAccountInfo", "arguments": {"address": "tp1..."}}}
```

**REST Client:**
```bash
curl https://api/v1/accounts/tp1.../info
```

Both return the same standardized, filtered data structure.

## Next Steps

1. **Architecture Design** - Define proxy layer interfaces and data schemas
2. **Proxy Layer Implementation** - Extract async PB-API functions with standardization
3. **REST API Design** - Create endpoint structure mirroring MCP tools
4. **jqpy Integration** - Add dynamic JSON transformation capabilities
5. **Testing & Documentation** - Comprehensive coverage and API documentation

This approach maximizes the utility of the Lambda function by serving both MCP and traditional REST clients while maintaining clean, testable code architecture.