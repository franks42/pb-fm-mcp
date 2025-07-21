# Development Roadmap - pb-fm-mcp

## Current Status
- ✅ AWS Lambda MCP server with 13 tools
- ✅ Production deployment working
- ✅ **Dual API Architecture**: MCP + REST protocols in single Lambda deployment
- ✅ **Complete Documentation**: Interactive /docs endpoint with external Swagger UI integration
- ✅ **CORS & Async**: Proper async patterns with thread pool execution and cross-origin support
- ✅ Local SAM testing environment
- ✅ jqpy and base64expand preserved for integration

## Improvement Priorities

### 🔴 High Priority

#### 🚨 **CRITICAL: Production/Development Environment Separation**
- **Create separate production and development endpoints** - Ensure colleagues can use stable MCP server while development continues
- **Git branch strategy** - Use `main` branch for production, `dev` branch for active development
- **Separate SAM stack deployments** - `pb-fm-mcp-prod` (stable) and `pb-fm-mcp-dev` (testing)
- **Environment-based configuration** - Different endpoints, logging levels, and feature flags

#### 🚀 **NEXT PHASE: Unified Function Registry Architecture**
- **Create decorator-based function registry** - Single `@api_function` decorator to expose functions via MCP, REST, or both
- **Implement modular business function structure** - Move functions to domain-specific modules (`account_functions.py`, `market_functions.py`, etc.)
- **Auto-generate protocol endpoints** - Automatically create MCP tools and FastAPI routes from registry
- **Separate business logic from protocol handlers** - Pure functions with zero protocol-specific code
- **Full typing system** - Type hints for automatic validation and OpenAPI schema generation

#### API Architecture Refactoring (Partially Complete)
- ✅ **Implement dual API exposure** - Expose both MCP protocol and REST endpoints for the same functionality
- ✅ **Design REST API endpoints** - Mirror MCP tools as REST endpoints for non-MCP AI agents
- 🔄 **Refactor PB-API functions into separate async proxy layer** - Create clean separation between raw API calls and data processing
- 🔄 **Create standardized data transformation layer** - Convert raw PB-API responses into consistent, filtered data structures

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

### Current Architecture (Phase 1 Complete)

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS Lambda Handler                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐           ┌─────────────────────────┐  │
│  │   MCP Protocol  │           │     REST API Layer     │  │
│  │   (13 tools)    │           │   (/api/*)             │  │
│  │   + /docs       │           │   + OpenAPI/CORS       │  │
│  └─────────────────┘           └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│              Mixed Business Logic (lambda_handler.py)       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Manual MCP tools + Manual REST endpoints          │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                Direct API Calls (hastra.py)               │
│  ┌─────────────────┐  ┌─────────────────┐ ┌─────────────┐  │
│  │ Provenance APIs │  │ Figure Markets  │ │ Other APIs  │  │
│  │     (async)     │  │     (async)     │ │   (async)   │  │
│  └─────────────────┘  └─────────────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Proposed Architecture (Phase 2: Unified Function Registry)

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS Lambda Handler                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐           ┌─────────────────────────┐  │
│  │   MCP Protocol  │           │     REST API Layer     │  │
│  │  (auto-generated)│          │   (auto-generated)     │  │
│  └─────────────────┘           └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│              Unified Function Registry                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  @api_function decorators + Auto-route generation  │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│              Modular Business Functions                    │
│  ┌────────────────┐ ┌─────────────┐ ┌──────────────────┐   │
│  │account_funcs.py│ │market_funcs │ │delegation_funcs  │   │
│  │   (typed async)│ │ (typed async│ │   (typed async)  │   │
│  └────────────────┘ └─────────────┘ └──────────────────┘   │
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

### Benefits of Unified Function Registry (Phase 2)

1. **Single Source of Truth**: One function definition serves both MCP and REST protocols
2. **Type Safety**: Full typing with automatic validation and OpenAPI schema generation  
3. **Modular Organization**: Functions organized by domain in separate files
4. **Zero Duplication**: Auto-generation eliminates manual route/tool duplication
5. **Clean Separation**: Business functions contain zero protocol-specific code
6. **Easy Expansion**: Just add `@api_function` decorator to expose new functionality

### Example Function Definition (Phase 2)

```python
# src/functions/account_functions.py
from src.registry.decorator import api_function

@api_function(
    protocols=["mcp", "rest"],  # Available via both protocols
    path="/accounts/{address}/info",  # REST path pattern  
    description="Fetch account information for given address"
)
async def fetch_account_info(address: str) -> dict:
    """Fetch account information for given Provenance address"""
    # Pure business logic - no protocol-specific code
    response = await http_get_json(f"https://api.provenance.io/accounts/{address}")
    return transform_account_data(response)
```

**Auto-generated MCP tool:**
```json
{"name": "fetch_account_info", "description": "Fetch account information", "inputSchema": {...}}
```

**Auto-generated REST endpoint:**
```
GET /api/accounts/{address}/info -> OpenAPI schema + validation
```

### Benefits of Current Dual API Approach (Phase 1)

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