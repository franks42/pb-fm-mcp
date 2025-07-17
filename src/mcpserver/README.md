# MCP Server for Provenance Blockchain and Figure Markets API Standardization

This module provides a comprehensive transformation engine for standardizing Provenance Blockchain and Figure Markets APIs into AI-friendly formats using the PB-FM-Hastra Field Registry naming conventions.

## 🏗️ Architecture Overview

The mcpserver module implements a configuration-driven approach to API standardization with the following key components:

### Core Transformation Engine
- **Configuration-driven mappings** from raw API responses to standardized field names
- **Logical attribute groupings** that make sense for AI agent understanding
- **Denomination conversion system** supporting all Figure Markets assets
- **Stateless server optimizations** with AI agent caching strategies

### Module Structure

```
src/mcpserver/
├── __init__.py                 # Module exports and version info
├── src/                        # Core transformation source code
│   ├── mcpworker.py           # Main MCP server with standardized functions  
│   ├── grouped_transformer.py # Multi-API logical grouping transformer
│   ├── config_driven_transformer.py # Base configuration-driven transformer
│   ├── denomination_converter.py    # Asset denomination conversion system
│   └── state_management_functions.py # AI agent caching functions
├── docs/                       # Configuration files and documentation
│   ├── pb_api_endpoint_mappings.yaml    # API endpoint transformation configs
│   ├── pb_api_attribute_groups.yaml    # Logical and API call groupings
│   ├── denomination_registry.yaml      # Complete denomination system
│   ├── pb_fm_hastra_field_registry.md  # Standardized field registry
│   └── ...                            # Additional documentation
├── examples/                   # JSON response examples and test scenarios
│   └── json_response_examples/ # Real API response examples with wallet scenarios
└── tests/                      # Test fixtures and validation data
    └── fixtures/              # Test data for transformation validation
```

## 🚀 Quick Start

### Using the Standardized MCP Server

```python
from mcpserver import setup_standardized_server

# Setup the server with all standardized functions
mcp, app = setup_standardized_server()

# The server includes these standardized functions:
# - get_complete_wallet_composition()
# - get_complete_vesting_status()  
# - get_delegation_complete_picture()
# - get_multi_asset_balances()
# - get_figure_markets_trading_price()
# - get_denomination_conversion_table()
# - get_system_timezone_info()
```

### Using Individual Components

```python
from mcpserver.src import GroupedAttributeTransformer

# Initialize transformer with default configurations
transformer = GroupedAttributeTransformer()

# Transform multiple API responses into logical groups
api_responses = {
    'pb_account_balances_call': {...},
    'pb_delegation_info_call': {...}
}

result = transformer.transform_grouped_response(
    'get_complete_wallet_composition',
    api_responses,
    {'account_address': 'tp1****'},
    stateless_optimized=True
)
```

## 📊 Key Features

### 1. Logical Attribute Groupings

Instead of individual API endpoints, the system provides **logical groups** that make sense together:

- **`wallet_composition_complete`**: Available + committed + delegated amounts
- **`vesting_complete_picture`**: All vesting-related information  
- **`delegation_complete_picture`**: Complete delegation and staking data
- **`multi_asset_portfolio`**: All assets across different denominations

### 2. Standardized Field Registry

All field names follow the **PB-FM-Hastra Field Registry** for consistency:

```yaml
# Raw PB API Response
{
  "maxSupply": {"amount": "100000000000000000", "denom": "nhash"},
  "burned": {"amount": "5000000000000000", "denom": "nhash"}
}

# Standardized Response  
{
  "max_supply_nhash": 100000000000000000,
  "burned_nhash": 5000000000000000
}
```

### 3. Denomination Handling

Comprehensive support for all Figure Markets assets:

- **HASH** (`nhash`) - Provenance native token
- **USD** (`uusd.trading`) - USD trading pairs
- **ETH** (`neth.figure.se`) - Ethereum 
- **USDC** (`uusdc.figure.se`) - USD Coin
- **SOL** (`nsol.figure.se`) - Solana
- **XRP** (`uxrp.figure.se`) - Ripple  
- **YLDS** (`uylds.fcc`) - Yield tokens

### 4. Stateless Server Optimization

Optimized for stateless Cloudflare Workers deployment:

- **Base denominations only** (calculations in base units)
- **UTC timestamps** with explicit timezone info
- **AI agent caching** for conversion tables and timezone data
- **Bandwidth optimization** by filtering irrelevant metadata

## 🧪 Testing with Real Scenarios

The module includes comprehensive wallet scenarios for testing:

### Wallet Test Scenarios

| Scenario | Vesting | Delegation | Multi-Asset | Description |
|----------|---------|------------|-------------|-------------|
| `basic_holder` | ❌ | ❌ | ❌ | Simple HASH holder |
| `multi_asset_holder` | ❌ | ❌ | ✅ | 6 different assets |
| `vesting_only` | ✅ | ❌ | ❌ | Active vesting schedule |
| `delegation_only` | ❌ | ✅ | ❌ | Multi-validator staking |
| `vesting_delegator` | ✅ | ✅ | ❌ | Complex vesting + delegation |
| `power_trader` | ❌ | ❌ | ✅ | Figure Markets trader |
| `complete_portfolio` | ✅ | ✅ | ✅ | All features combined |

### Using Test Scenarios

```python
# Load wallet scenario for testing
scenario_path = "src/mcpserver/examples/json_response_examples/wallet_scenarios/"
with open(f"{scenario_path}/balances_multi_asset_holder.json") as f:
    test_response = json.load(f)

# Test transformation
result = transformer.transform_response("asset_balances", test_response)
```

## ⚙️ Configuration

### API Endpoint Mappings

Configure transformations in `docs/pb_api_endpoint_mappings.yaml`:

```yaml
endpoints:
  hash_statistics:
    pb_api_url: "https://service-explorer.provenance.io/api/v3/utility_token/stats"
    transformations:
      - source_path: "maxSupply.amount"
        target_path: "max_supply_nhash"
        type: "string_to_int"
```

### Logical Groupings

Define attribute groups in `docs/pb_api_attribute_groups.yaml`:

```yaml
attribute_groups:
  wallet_composition_complete:
    description: "Complete wallet holdings across all states"
    attributes:
      - "available_total_amount_nhash"
      - "delegated_total_amount_nhash"
      - "wallet_total_amount_nhash"
    reasoning: "These amounts must be understood together for complete wallet picture"
```

## 🔒 Privacy & Security

- **Address obfuscation**: All wallet addresses replaced with `tp1****` / `pb1****`
- **Real amounts preserved**: For accurate transformation testing
- **No API keys required**: All examples use public endpoints
- **Stateless design**: No sensitive data persistence

## 📚 Documentation

- **[Field Registry](docs/pb_fm_hastra_field_registry.md)**: Complete standardized field definitions
- **[API Mappings](docs/pb_api_endpoint_mappings.yaml)**: Endpoint transformation configurations
- **[Denomination System](docs/denomination_registry.yaml)**: Asset conversion system
- **[Attribute Groups](docs/pb_api_attribute_groups.yaml)**: Logical grouping definitions

## 🤝 Integration with Existing Codebase

The mcpserver module is designed to **complement, not replace** the existing codebase:

- **Isolated in `src/mcpserver/`**: No modifications to existing `worker.py`, `hastra.py`, `utils.py`
- **Optional usage**: Existing MCP server continues to work unchanged
- **Shared dependencies**: Uses existing `utils`, `hastra_types`, `base64expand` from main project
- **Progressive adoption**: Can be adopted function by function

### Using with Existing Worker

```python
# Option 1: Use new standardized server entirely
from mcpserver import setup_standardized_server
mcp, app = setup_standardized_server()

# Option 2: Add standardized functions to existing server  
from mcpserver.src import GroupedAttributeTransformer
transformer = GroupedAttributeTransformer()
# Add transformer.transform_grouped_response() to existing worker functions
```

## 🎯 Benefits

1. **AI-Friendly**: Consistent naming, logical groupings, comprehensive documentation
2. **Bandwidth Optimized**: Filters out irrelevant data, uses base denominations
3. **Testable**: Comprehensive scenarios covering all edge cases
4. **Maintainable**: Configuration-driven approach vs hand-crafted transformations
5. **Scalable**: Easy to add new APIs following established patterns
6. **Stateless-Ready**: Optimized for Cloudflare Workers deployment

This standardization system transforms inconsistent PB/FM APIs (developed over 6 years) into a clean, consistent interface that AI agents can easily understand and use effectively.