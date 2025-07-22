# Development Roadmap - pb-fm-mcp

## Current Status
- ✅ **AWS Lambda MCP server with 21 functions** - 16 MCP tools, 19 REST endpoints ✅ COMPLETE
- ✅ **Unified Function Registry Architecture**: `@api_function` decorator system ✅ COMPLETE
- ✅ **Version Management System**: Automated version tracking with deployment hooks ✅ COMPLETE  
- ✅ **System Introspection Tools**: Registry analysis and Lambda warmup functions ✅ COMPLETE
- ✅ **Cross-Server MCP Testing**: Dev-to-prod Lambda MCP communication testing ✅ COMPLETE
- ✅ **Async Event Loop Issue Resolution**: Permanent fix for recurring Lambda async problems ✅ COMPLETE
- ✅ **Automated Deployment Scripts**: One-command deployment with version increment ✅ COMPLETE
- ✅ **Dual API Architecture**: MCP + REST protocols in single Lambda deployment ✅ COMPLETE
- ✅ **Complete Documentation**: Interactive /docs endpoint with external Swagger UI integration ✅ COMPLETE
- ✅ **CORS & Async**: Proper async patterns with consistent async HTTP calls ✅ COMPLETE  
- ✅ **Production/Development Separation**: Separate endpoints and deployment stacks ✅ COMPLETE
- ✅ **Comprehensive Equivalence Testing**: 91% pass rate with automated MCP vs REST validation ✅ COMPLETE
- ✅ **Security Hardening**: Environment variable protection for sensitive data ✅ COMPLETE
- ✅ **Asset Amount Standardization**: Consistent `{"amount": int, "denom": "nhash"}` format ✅ COMPLETE
- ✅ **Figure Markets API Integration**: Public trading and asset data (private APIs disabled) ✅ COMPLETE
- ✅ Local SAM testing environment ✅ COMPLETE
- ✅ jqpy and base64expand preserved for integration ✅ COMPLETE

## Improvement Priorities

### 🔴 High Priority

#### ✅ **COMPLETED: Production/Development Environment Separation**
- ✅ **Separate production and development endpoints** - Colleagues use stable production, development continues on dev stack
- ✅ **Git branch strategy** - `main` branch for production, `dev` branch for active development
- ✅ **Separate SAM stack deployments** - `pb-fm-mcp-v2` (stable) and `pb-fm-mcp-dev` (testing)
- ✅ **Environment-based configuration** - Different endpoints, logging levels, and feature flags

#### ✅ **COMPLETED: Unified Function Registry Architecture**
- ✅ **Created decorator-based function registry** - Single `@api_function` decorator exposes functions via MCP, REST, or both
- ✅ **Implemented modular business function structure** - Functions organized in domain-specific modules (`stats_functions.py`, `delegation_functions.py`, etc.)
- ✅ **Auto-generate protocol endpoints** - Automatically create MCP tools and FastAPI routes from registry
- ✅ **Separated business logic from protocol handlers** - Pure functions with zero protocol-specific code
- ✅ **Full typing system** - Type hints for automatic validation and OpenAPI schema generation

#### ✅ **COMPLETED: System Operations & Monitoring**
- ✅ **Version Management System** - Automated semantic versioning with deployment tracking
- ✅ **System Introspection Tools** - Registry analysis, function counts, and protocol distribution
- ✅ **Lambda Container Warming** - Fast ping function for cold start mitigation
- ✅ **Cross-Server MCP Testing** - Dev/prod MCP server communication testing with performance analysis
- ✅ **Automated Deployment Scripts** - One-command deployment with version increment and environment validation
- ✅ **Async Event Loop Resolution** - Permanent fix for recurring Lambda async/thread pool issues

#### ✅ **COMPLETED: API Architecture Refactoring**
- ✅ **Implement dual API exposure** - Expose both MCP protocol and REST endpoints for the same functionality
- ✅ **Design REST API endpoints** - Mirror MCP tools as REST endpoints for non-MCP AI agents
- ✅ **Refactor PB-API functions into async proxy layer** - Clean separation between raw API calls and data processing
- ✅ **Create standardized data transformation layer** - Consistent async HTTP patterns across all functions

#### 🚀 **NEXT PHASE: Enhanced Integrations**
- **Integrate jqpy JSON processing** - Add jq-like query capabilities to MCP tools (162/193 tests passing)
- **Dynamic JSON transformation tool** - Let users apply jq syntax via MCP for custom data filtering
- **Base64 data expansion** - Handle encoded blockchain data in responses

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
2. **Unified Documentation**: Function docstrings and type hints automatically become MCP tool descriptions AND OpenAPI documentation
3. **Type Safety**: Full typing with automatic validation and OpenAPI schema generation  
4. **Modular Organization**: Functions organized by domain in separate files
5. **Zero Duplication**: Auto-generation eliminates manual route/tool duplication
6. **Clean Separation**: Business functions contain zero protocol-specific code
7. **Easy Expansion**: Just add `@api_function` decorator to expose new functionality
8. **Consistent Introspection**: Same documentation visible in MCP tool discovery and REST API docs

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
    """
    Fetch account information for given Provenance address.
    
    Args:
        address: Bech32-encoded Provenance blockchain address (e.g., tp1...)
        
    Returns:
        Account data including balances, sequence number, and account type
        
    Raises:
        ValueError: If address format is invalid
        APIError: If blockchain API is unavailable
    """
    # Pure business logic - no protocol-specific code
    response = await http_get_json(f"https://api.provenance.io/accounts/{address}")
    return transform_account_data(response)
```

**Auto-generated MCP tool:**
```json
{
  "name": "fetch_account_info", 
  "description": "Fetch account information for given Provenance address.\n\nArgs:\n  address: Bech32-encoded Provenance blockchain address (e.g., tp1...)",
  "inputSchema": {
    "type": "object",
    "properties": {
      "address": {"type": "string", "description": "Bech32-encoded Provenance blockchain address"}
    },
    "required": ["address"]
  }
}
```

**Auto-generated REST endpoint:**
```yaml
GET /api/accounts/{address}/info:
  summary: Fetch account information for given address
  description: |
    Fetch account information for given Provenance address.
    
    Args:
        address: Bech32-encoded Provenance blockchain address (e.g., tp1...)
        
    Returns:
        Account data including balances, sequence number, and account type
  parameters:
    - name: address
      in: path
      required: true
      schema:
        type: string
      description: Bech32-encoded Provenance blockchain address
  responses:
    200:
      description: Account data including balances, sequence number, and account type
```

**🎯 Key Advantage**: The same docstring and type hints automatically populate BOTH the MCP tool description AND the OpenAPI documentation - true single source of documentation!

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