# New Function Implementation Guide

This guide shows you the complete step-by-step process to create a new function using our unified registry system. With our architecture, adding a single function automatically creates both MCP tools and REST API endpoints.

## 🛠️ Step-by-Step: Creating a New Function

Let's walk through creating `fetch_interesting_pb_data()` as an example.

### Step 1: Choose the Right Module

First, decide which module in `src/functions/` to add your function to:

- **`blockchain_functions.py`** - For Provenance blockchain data
- **`figure_markets_functions.py`** - For Figure Markets exchange data  
- **`stats_functions.py`** - For statistics and metrics
- **Create new module** - Like `analytics_functions.py` for specialized functions

### Step 2: Add the Function with @api_function Decorator

```python
@api_function(
    protocols=["mcp", "rest"],  # or ["mcp"] or ["rest"] for single protocol
    path="/api/interesting_pb_data",  # REST endpoint path
    method="GET",  # HTTP method
    tags=["analytics", "blockchain"],  # OpenAPI tags
    description="Fetch interesting Provenance blockchain data and insights"
)
async def fetch_interesting_pb_data() -> JSONType:
    """
    Fetch interesting and insightful data about the Provenance blockchain
    including network statistics, active validators, recent activity metrics,
    and ecosystem health indicators.
    
    Returns:
        Dictionary containing:
        - network_stats: Current network statistics
        - validator_activity: Active validator information  
        - recent_metrics: Recent blockchain activity
        - ecosystem_health: Health indicators and trends
        
    Raises:
        HTTPError: If the Provenance blockchain APIs are unavailable
    """
    try:
        # Your implementation here - can call multiple APIs
        network_data = await async_http_get_json("https://service-explorer.provenance.io/api/v1/network")
        validator_data = await async_http_get_json("https://service-explorer.provenance.io/api/v1/validators")
        
        # Process and combine data
        result = {
            "network_stats": {
                "block_height": network_data.get("block_height"),
                "total_validators": len(validator_data.get("validators", []))
            },
            "interesting_insight": "This is interesting PB data!",
            "timestamp": current_ms()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Could not fetch interesting PB data: {e}")
        return {"MCP-ERROR": f"Data fetch error: {str(e)}"}
```

### Step 3: That's It! 🎉

**Seriously, that's the entire process.** The unified registry automatically:

✅ **Creates MCP Tool**: `fetchInterestingPbData()` function  
✅ **Creates REST Endpoint**: `GET /api/interesting_pb_data`  
✅ **Generates OpenAPI Schema**: From type hints and docstring  
✅ **Handles Async**: Proper async execution in both protocols  
✅ **Validates Types**: Automatic validation from type hints  
✅ **Documentation**: Docstring becomes both MCP description and API docs

### Step 4: Deploy and Test

```bash
# Build and deploy
sam build && sam deploy --stack-name pb-fm-mcp-dev --resolve-s3

# Test MCP (through our equivalence tester)
python scripts/test_equivalence.py

# Test REST directly
curl https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod/api/interesting_pb_data
```

## 🔍 Real Example from Our Codebase

Here's how we created `fetch_current_hash_statistics`:

```python
@api_function(
    protocols=["mcp", "rest"],
    path="/api/current_hash_statistics", 
    method="GET",
    tags=["statistics", "blockchain"],
    description="Fetch current HASH token statistics"
)
async def fetch_current_hash_statistics() -> JSONType:
    """
    Fetch the current overall statistics for the Provenance Blockchain's utility token HASH.
    
    Provides comprehensive statistics including supply, circulation, staking, and community pool data.
    Pie chart visualization also available at: https://explorer.provenance.io/network/token-stats
    
    Returns:
        Dictionary containing HASH statistics with the following attributes:
        - maxSupply: The total initial amount of all HASH minted
        - burned: The total amount of all burned HASH  
        - currentSupply: Current total supply (maxSupply - burned)
        - circulation: Total amount of HASH in circulation
        - communityPool: HASH managed by Provenance Foundation for community
        - bonded: Total HASH delegated/staked with validators
        - locked: HASH locked in vesting schedules (calculated field)
        
    Raises:
        HTTPError: If the Provenance blockchain API is unavailable
    """
    url = "https://service-explorer.provenance.io/api/v3/utility_token/stats"
    response = await async_http_get_json(url)
    
    if response.get("MCP-ERROR"):
        return response
    
    # Calculate locked amount: currentSupply - circulation - communityPool - bonded
    try:
        locked_amount = (
            int(response["currentSupply"]["amount"]) -
            int(response["circulation"]["amount"]) - 
            int(response["communityPool"]["amount"]) -
            int(response["bonded"]["amount"])
        )
        
        response["locked"] = {
            "amount": locked_amount,
            "denom": "nhash"
        }
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Could not calculate locked amount: {e}")
        # Return response without locked field rather than failing
    
    return response
```

**Result**: 
- ✅ MCP Tool: `fetchCurrentHashStatistics()`
- ✅ REST API: `GET /api/current_hash_statistics` 
- ✅ Auto-documented in OpenAPI spec
- ✅ Equivalence tested automatically

## 🎯 Key Benefits of This Pattern

1. **Single Source of Truth**: One function → Two protocols
2. **Automatic Documentation**: Docstring serves both protocols  
3. **Type Safety**: Automatic validation and schema generation
4. **Consistent Naming**: Function name → API path → Response keys
5. **Zero Duplication**: No manual REST routes or MCP tools needed
6. **Built-in Testing**: Equivalence testing ensures consistency

## 📝 Function Naming Conventions

### Flat API Structure Rationale

**MCP Protocol Constraint**: MCP tool functions require a flat naming structure with no namespace hierarchy support. Function names like `fetchAccountInfo` or `fetchDelegatedRewardsAmount` cannot be organized into namespaces like `account.fetchInfo` or `delegation.fetchRewards`.

**Design Decision**: To maintain perfect 1:1 mapping between MCP tools and REST endpoints, we use a flat API structure:

- **MCP Function**: `fetch_delegated_rewards_amount` 
- **REST Endpoint**: `/api/delegated_rewards_amount/{wallet_address}`
- **Response Key**: `delegated_rewards_amount`

This eliminates any impedance mismatch between protocols and creates a clean data dictionary where function names directly correspond to API paths and response keys.

### Naming Examples

| Function Name | MCP Tool | REST Endpoint | Response Keys |
|---------------|----------|---------------|---------------|
| `fetch_current_hash_statistics` | `fetchCurrentHashStatistics` | `/api/current_hash_statistics` | `maxSupply`, `currentSupply`, etc. |
| `fetch_account_info` | `fetchAccountInfo` | `/api/account_info/{wallet_address}` | `account_is_vesting`, `account_type`, etc. |
| `fetch_total_delegation_data` | `fetchTotalDelegationData` | `/api/total_delegation_data/{wallet_address}` | `delegated_staked_amount`, etc. |

## 🔧 Advanced Features

### Protocol Selection

```python
# Both MCP and REST
protocols=["mcp", "rest"]

# MCP only
protocols=["mcp"]

# REST only  
protocols=["rest"]
```

### Path Parameters

```python
@api_function(
    protocols=["mcp", "rest"],
    path="/api/account_balance/{wallet_address}",  # Path parameter
    method="GET"
)
async def fetch_account_balance(wallet_address: str) -> JSONType:
    # wallet_address automatically extracted from URL path
    return {"balance": "data"}
```

### HTTP Methods

```python
@api_function(
    protocols=["rest"],  # POST usually doesn't make sense for MCP
    path="/api/update_account",
    method="POST"  # GET, POST, PUT, DELETE, etc.
)
async def update_account_data(account_data: dict) -> JSONType:
    # Implementation
    return {"status": "updated"}
```

### Error Handling

Always return `{"MCP-ERROR": "error message"}` for errors to ensure consistent error handling across protocols:

```python
try:
    result = await some_api_call()
    return result
except Exception as e:
    logger.error(f"API call failed: {e}")
    return {"MCP-ERROR": f"Failed to fetch data: {str(e)}"}
```

## 🧪 Testing Your New Function

### Automatic Equivalence Testing

If your function supports both MCP and REST (`protocols=["mcp", "rest"]`), add it to the equivalence test in `scripts/test_equivalence.py`:

```python
test_cases = [
    # ... existing test cases ...
    ("Interesting PB Data", "fetch_interesting_pb_data", {}, "/api/interesting_pb_data"),
]
```

### Manual Testing

```bash
# Test REST endpoint
curl -s "https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod/api/interesting_pb_data" | python3 -m json.tool

# Test MCP endpoint (requires MCP client)
# The function will be automatically available as fetchInterestingPbData()
```

## 📁 File Structure

When adding functions, follow this structure:

```
src/functions/
├── __init__.py              # Imports all function modules
├── blockchain_functions.py  # Provenance blockchain data
├── figure_markets_functions.py # Figure Markets exchange data
├── stats_functions.py       # Statistics and metrics
└── your_new_module.py       # Your specialized functions
```

Remember to add your new module to `src/functions/__init__.py`:

```python
try:
    from . import your_new_module
except Exception as e:
    print(f"❌ Failed to import your_new_module: {e}")

__all__ = [
    "stats_functions",
    "delegation_functions", 
    "blockchain_functions",
    "figure_markets_functions",
    "your_new_module",  # Add here
]
```

## 🚀 Quick Start Template

Copy this template to get started quickly:

```python
from typing import Dict, Any
import structlog

# Handle import for both relative and absolute path contexts
try:
    from ..registry import api_function
except ImportError:
    try:
        from registry import api_function
    except ImportError:
        from src.registry import api_function

# Set up logging
logger = structlog.get_logger()

# Type alias for JSON response
JSONType = Dict[str, Any]

@api_function(
    protocols=["mcp", "rest"],
    path="/api/your_function_name",
    method="GET",
    tags=["your", "tags"],
    description="Brief description of your function"
)
async def fetch_your_data() -> JSONType:
    """
    Detailed description of what your function does.
    
    Returns:
        Dictionary containing:
        - your_data: Description of the data
        
    Raises:
        HTTPError: If the API is unavailable
    """
    try:
        # Your implementation here
        result = {"your_data": "some value"}
        return result
        
    except Exception as e:
        logger.error(f"Could not fetch your data: {e}")
        return {"MCP-ERROR": f"Data fetch error: {str(e)}"}
```

That's it! You now have everything you need to add new functions to the unified registry system. 🎉