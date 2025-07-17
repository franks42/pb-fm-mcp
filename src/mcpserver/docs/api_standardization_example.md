# API Standardization Example: HASH Token Statistics

## Current Implementation Analysis

### Endpoint
- **URL**: `https://service-explorer.provenance.io/api/v3/utility_token/stats`
- **Method**: GET
- **Parameters**: None

### Current Function
```python
async def fetch_current_hash_statistics() -> JSONType:
    """Fetch the current overall statistics for the Provenance Blockchain's utility token HASH."""
    url = "https://service-explorer.provenance.io/api/v3/utility_token/stats"
    response = await async_http_get_json(url)
    if response.get("MCP-ERROR"):
        return response
    response["locked"] = {"amount": str(int(response["currentSupply"]["amount"]) -
                                        int(response["circulation"]["amount"]) -
                                        int(response["communityPool"]["amount"]) -
                                        int(response["bonded"]["amount"])),
                          "denom": "nhash"}
    return response
```

### Raw API Response (Hypothetical)
```json
{
  "maxSupply": {"amount": "100000000000000000", "denom": "nhash"},
  "burned": {"amount": "1000000000000000", "denom": "nhash"},
  "currentSupply": {"amount": "99000000000000000", "denom": "nhash"},
  "circulation": {"amount": "50000000000000000", "denom": "nhash"},
  "communityPool": {"amount": "10000000000000000", "denom": "nhash"},
  "bonded": {"amount": "25000000000000000", "denom": "nhash"},
  "lastUpdated": "2024-07-17T10:30:00Z",
  "blockHeight": 12345678,
  "validatorCount": 150,
  "bondedRatio": "0.252525"
}
```

## Issues Identified

### 1. Naming Inconsistencies
- **camelCase**: `maxSupply`, `currentSupply`, `communityPool`, `lastUpdated`, `blockHeight`, `bondedRatio`
- **snake_case preference**: We want consistent naming for AI comprehension

### 2. Data Type Issues
- **String amounts**: All amounts are strings but should be handled consistently
- **Mixed types**: Some fields might be numbers vs strings inconsistently

### 3. Redundant/Confusing Data
- **`lastUpdated`**: Might not be needed for AI agents
- **`blockHeight`**: Could be confusing unless specifically needed
- **`validatorCount`**: Might be superfluous for token statistics
- **`bondedRatio`**: String representation of ratio could be confusing

### 4. Missing Standardization
- **Amount formatting**: No consistent denomination handling
- **Calculated fields**: Ad-hoc calculation in function rather than standardized approach

## Proposed Standardization

### 1. Data Dictionary Mapping
```yaml
field_mappings:
  # Raw API field -> Standardized field
  maxSupply: max_supply_nhash
  burned: burned_nhash  
  currentSupply: current_supply_nhash
  circulation: circulating_supply_nhash
  communityPool: community_pool_nhash
  bonded: bonded_nhash
  # Calculated field
  locked: locked_nhash

# Fields to remove (superfluous for AI)
excluded_fields:
  - lastUpdated
  - blockHeight  
  - validatorCount
  - bondedRatio

# Data type conversions
type_conversions:
  "*_nhash": 
    from: "string"
    to: "integer"
    description: "Convert string amounts to integer base units"
```

### 2. Standardized Response Structure
```json
{
  "max_supply_nhash": 100000000000000000,
  "burned_nhash": 1000000000000000,
  "current_supply_nhash": 99000000000000000,
  "circulating_supply_nhash": 50000000000000000,
  "community_pool_nhash": 10000000000000000,
  "bonded_nhash": 25000000000000000,
  "locked_nhash": 14000000000000000
}
```

### 3. Enhanced Function Documentation
```python
@mcp_tool("get_hash_token_statistics")
async def get_hash_token_statistics() -> Dict:
    """
    Get current HASH token supply and distribution statistics.
    
    Returns comprehensive information about HASH token supply across different
    categories: total supply, burned tokens, circulating supply, and locked tokens.
    
    Returns:
        Dict containing:
        - max_supply_nhash: Total HASH tokens ever created (in nhash base units)
        - burned_nhash: Total HASH tokens permanently removed from circulation
        - current_supply_nhash: Current total supply (max_supply - burned)
        - circulating_supply_nhash: HASH tokens available for trading/transfer
        - community_pool_nhash: HASH tokens managed by Provenance Foundation
        - bonded_nhash: HASH tokens staked with validators for network security
        - locked_nhash: HASH tokens subject to vesting schedules
        
    Example Response:
        {
            "max_supply_nhash": 100000000000000000,
            "current_supply_nhash": 99000000000000000,
            "circulating_supply_nhash": 50000000000000000,
            "locked_nhash": 14000000000000000
        }
    """
```

### 4. Transformation Engine Implementation
```python
class HashStatisticsTransformer:
    FIELD_MAPPINGS = {
        'maxSupply': 'max_supply_nhash',
        'burned': 'burned_nhash',
        'currentSupply': 'current_supply_nhash',
        'circulation': 'circulating_supply_nhash',
        'communityPool': 'community_pool_nhash',
        'bonded': 'bonded_nhash'
    }
    
    EXCLUDED_FIELDS = ['lastUpdated', 'blockHeight', 'validatorCount', 'bondedRatio']
    
    def transform_response(self, raw_response: Dict) -> Dict:
        """Transform raw API response to standardized format."""
        result = {}
        
        # Apply field mappings and type conversions
        for raw_field, std_field in self.FIELD_MAPPINGS.items():
            if raw_field in raw_response:
                raw_value = raw_response[raw_field]
                if isinstance(raw_value, dict) and 'amount' in raw_value:
                    # Convert amount string to integer
                    result[std_field] = int(raw_value['amount'])
        
        # Calculate locked amount using standardized fields
        if all(field in result for field in ['current_supply_nhash', 'circulating_supply_nhash', 
                                           'community_pool_nhash', 'bonded_nhash']):
            result['locked_nhash'] = (
                result['current_supply_nhash'] - 
                result['circulating_supply_nhash'] - 
                result['community_pool_nhash'] - 
                result['bonded_nhash']
            )
        
        return result
```

## Standardization Workflow Pattern

This example establishes the pattern for all other APIs:

### Step 1: Analyze Current Implementation
1. Document endpoint and current function
2. Identify response structure and field types
3. List naming inconsistencies and data issues

### Step 2: Design Standardization
1. Create field mapping dictionary
2. Identify fields to exclude
3. Define type conversions needed
4. Plan calculated field handling

### Step 3: Implement Transformation
1. Build transformer class for the endpoint
2. Implement clean, documented MCP function
3. Add comprehensive documentation with examples
4. Test with real API responses

### Step 4: Validate & Document
1. Verify data integrity (no information loss)
2. Test AI agent comprehension
3. Document transformation rules
4. Create usage examples

## Benefits Demonstrated

### Before (Current)
- **Confusing naming**: `maxSupply`, `communityPool`
- **Mixed data types**: String amounts, inconsistent structures
- **Ad-hoc calculations**: Inline math in function
- **Superfluous data**: Extra fields that could confuse AI
- **Poor documentation**: Inconsistent with actual field names

### After (Standardized)
- **Consistent naming**: `max_supply_nhash`, `community_pool_nhash`
- **Standardized types**: All amounts as integers in base units
- **Systematic calculations**: Reusable transformation logic
- **Focused data**: Only essential fields for AI consumption
- **Clear documentation**: Matches actual response structure

This pattern can be applied to all 20+ other APIs in the codebase for consistent AI-friendly data access.