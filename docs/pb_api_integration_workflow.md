# PB-API Integration Workflow

This document outlines the comprehensive workflow for integrating new Provenance Blockchain APIs into the standardized MCP system.

## Overview

The workflow ensures that every PB-API is properly analyzed, standardized, and integrated following the PB-FM-Hastra Field Registry conventions. The goal is to create AI-friendly, consistent interfaces that reduce confusion and improve bandwidth efficiency.

## Phase 1: API Discovery and Analysis

### 1.1 Identify Target PB-API
- **URL**: Record the complete API endpoint URL
- **Method**: Confirm HTTP method (usually GET)
- **Parameters**: Document all query parameters and path variables
- **Authentication**: Note any authentication requirements
- **Rate Limits**: Document any rate limiting constraints

**Example:**
```
URL: https://service-explorer.provenance.io/api/v3/utility_token/stats
Method: GET
Parameters: None
Authentication: None required
Rate Limits: Unknown (test and document)
```

### 1.2 Capture Raw Response
- **Make live API call** with various parameter combinations
- **Save raw JSON responses** in `docs/raw_api_responses/`
- **Document response variations** (different parameters, edge cases)
- **Identify error response formats**
- **Test with real vs. testnet data**

**Example:**
```bash
# Capture raw response
curl "https://service-explorer.provenance.io/api/v3/utility_token/stats" \
  | jq . > docs/raw_api_responses/utility_token_stats_raw.json

# Test with different parameters (if applicable)
curl "https://service-explorer.provenance.io/api/v2/accounts/tp1.../balances?count=5" \
  | jq . > docs/raw_api_responses/account_balances_raw_small.json
```

### 1.3 Apply Base64 Expansion
- **Run base64expand()** on all captured responses
- **Document any hidden data** found in base64 fields
- **Save expanded responses** alongside raw responses
- **Note which fields contained base64 data**

**Example:**
```bash
# Expand base64 data
python -c "
from src.base64expand import base64expand
import json
with open('docs/raw_api_responses/utility_token_stats_raw.json') as f:
    data = json.load(f)
expanded = base64expand(data)
with open('docs/raw_api_responses/utility_token_stats_expanded.json', 'w') as f:
    json.dump(expanded, f, indent=2)
"
```

## Phase 2: Attribute Analysis and Mapping

### 2.1 Catalog All Response Attributes
For each attribute in the response:

**Basic Information:**
- **Source Path**: Exact JSON path in response (e.g., `currentSupply.amount`)
- **Data Type**: string, integer, float, boolean, object, array
- **Sample Values**: Multiple examples from different calls
- **Value Range**: Min/max values, typical ranges
- **Null Handling**: Can it be null/empty?

**Business Context:**
- **Purpose**: What does this attribute represent?
- **Units**: Currency, time, percentage, count, etc.
- **Calculation**: Is it calculated or raw from blockchain?
- **Relationship**: How does it relate to other attributes?
- **Temporal**: Does it change over time? How frequently?

**Example Analysis:**
```yaml
currentSupply:
  source_path: "currentSupply.amount"
  data_type: "string"
  sample_values: ["99000000000000000", "99001234567890000"]
  value_range: "Large integers as strings"
  null_handling: "Never null"
  purpose: "Current total supply of HASH tokens in circulation"
  units: "nhash (base units)"
  calculation: "maxSupply - burned"
  relationship: "Parent to maxSupply and burned"
  temporal: "Changes when tokens are burned"
  business_importance: "critical"
```

### 2.2 Data Dictionary Integration
For each attribute:

**Check Existing Registry:**
1. **Search field registry** for similar concepts
2. **Check denomination registry** for unit types  
3. **Review logical groups** for related attributes
4. **Examine existing transformations** for patterns

**Create New Entries (if needed):**
1. **Generate standardized name** (snake_case, descriptive)
2. **Add to field registry** with full documentation
3. **Update denomination registry** if new units found
4. **Consider logical groupings** with other attributes

**Naming Convention Rules:**
- Use `snake_case` for all field names
- Include units in name for amounts: `total_supply_nhash`
- Use consistent prefixes: `delegated_`, `vesting_`, `available_`
- Avoid abbreviations unless widely understood
- Make names self-documenting

**Example:**
```yaml
# BEFORE (PB-API response)
currentSupply:
  amount: "99000000000000000"
  denom: "nhash"

# AFTER (Standardized)
current_supply_nhash: 99000000000000000
```

### 2.3 Value Assessment and Filtering
For each attribute, determine:

**Communication Value:**
- **High Value**: Critical for user decisions, frequently needed
- **Medium Value**: Useful for specific use cases, occasional need
- **Low Value**: Nice-to-have, rarely needed
- **No Value**: Internal API metadata, confusing to users

**Filtering Rules:**
- **Always Include**: Account balances, delegation amounts, prices
- **Usually Include**: Timestamps, counts, calculated fields
- **Sometimes Include**: Metadata that adds context
- **Never Include**: Internal IDs, API pagination, debug info

**Bandwidth Impact:**
- **Large Fields**: Consider compression or summarization
- **Redundant Fields**: Remove duplicates or choose best version
- **Nested Objects**: Flatten if it reduces complexity

**Example Assessment:**
```yaml
maxSupply:
  communication_value: "high"
  reasoning: "Essential for understanding tokenomics"
  include: true

lastUpdated:
  communication_value: "low"
  reasoning: "Rarely needed, changes frequently"
  include: false
  
pagination:
  communication_value: "none"
  reasoning: "API metadata, not business data"
  include: false
  filter_rule: "Remove all pagination metadata"
```

## Phase 3: Transformation Design

### 3.1 Source-to-Target Mapping
For each included attribute:

**Path Mapping:**
- **Source Path**: Exact path in raw PB-API response
- **Target Path**: Standardized field name in output
- **Transform Type**: direct, calculation, format_conversion, etc.
- **Dependencies**: Other fields needed for calculation

**Transform Types:**
- `direct`: Simple field rename/copy
- `string_to_int`: Convert string numbers to integers
- `amount_object_to_int`: Extract amount from {amount, denom} objects
- `calculated`: Formula based on other fields
- `timestamp_format`: Standardize date/time format
- `denomination_suffix`: Add denom suffix to field name

**Example Mapping:**
```yaml
field_mappings:
  - source_path: "currentSupply.amount"
    target_path: "current_supply_nhash"
    transform: "string_to_int"
    dependencies: ["currentSupply.denom"]
    
  - source_path: "circulation.amount"
    target_path: "circulating_supply_nhash"
    transform: "string_to_int"
    dependencies: []

calculated_fields:
  - target_path: "locked_nhash"
    formula: "current_supply_nhash - circulating_supply_nhash - community_pool_nhash - bonded_nhash"
    dependencies: ["current_supply_nhash", "circulating_supply_nhash", "community_pool_nhash", "bonded_nhash"]
```

### 3.2 Logical Grouping
Determine if attributes should be grouped:

**Grouping Criteria:**
- **Business Logic**: Attributes that must be understood together
- **Decision Making**: Fields needed for a specific decision
- **Calculation Dependencies**: Fields that are used in calculations together
- **User Workflow**: Attributes used in the same user tasks

**Group Types:**
- **Logical Groups**: Business concepts (wallet_composition_complete)
- **API Call Groups**: Data from same endpoint (pb_hash_statistics_call)
- **Calculation Groups**: Fields used in formulas together

**Example Grouping:**
```yaml
logical_groups:
  hash_supply_complete:
    description: "Complete HASH token supply information"
    attributes:
      - max_supply_nhash
      - current_supply_nhash
      - circulating_supply_nhash
      - locked_nhash
      - burned_nhash
    reasoning: "All needed to understand HASH tokenomics"
    required_together: true
```

### 3.3 Error Handling Strategy
Define how to handle:

**Missing Fields:**
- **Required fields**: Return error if missing
- **Optional fields**: Use default values or null
- **Calculated fields**: Handle when dependencies missing

**Invalid Data:**
- **Type mismatches**: String where number expected
- **Range violations**: Negative amounts, future dates
- **Format errors**: Invalid timestamps, malformed addresses

**API Failures:**
- **Network errors**: Timeout, connection refused
- **HTTP errors**: 404, 500, rate limiting
- **Authentication**: Token expired, permission denied

## Phase 4: Implementation

### 4.1 Create Primitive Function
Follow the established pattern:

```python
async def fetch_[descriptive_name](parameters...) -> Dict[str, Any]:
    """
    Fetch [description] from PB-API.
    
    Maps to: [HTTP_METHOD] [API_ENDPOINT]
    
    Args:
        param1: Description and type
        param2: Description and type
        
    Returns:
        Dict containing:
        - standardized_field_1: Description
        - standardized_field_2: Description
        - [original_parameter]: The queried parameter
    """
    url = "https://..."
    params = {...}
    
    response = await async_http_get_json(url, params)
    
    if response.get("error_message"):
        return response
    
    # Transform to standardized format
    result = {
        'standardized_field_1': transform_field_1(response),
        'standardized_field_2': transform_field_2(response),
        'original_parameter': parameter_value
    }
    
    return result
```

### 4.2 Create Configuration
Add to YAML configuration files:

**Endpoint Mapping** (`pb_api_endpoint_mappings.yaml`):
```yaml
endpoints:
  new_endpoint_name:
    pb_api_url: "https://..."
    pb_api_method: "GET"
    pb_api_parameters: [...]
    field_mappings: [...]
    calculated_fields: [...]
    excluded_fields: [...]
```

**Attribute Groups** (`pb_api_attribute_groups.yaml`):
```yaml
attribute_groups:
  new_logical_group:
    description: "..."
    attributes: [...]
    reasoning: "..."
    required_together: true

api_call_groups:
  new_api_call_group:
    pb_api_url: "https://..."
    relevant_attributes: [...]
    filtered_out_attributes: [...]
```

### 4.3 Add to Registries
Update function registries:

```python
# In pb_primitive_apis.py
PRIMITIVE_FUNCTIONS = {
    # ... existing functions
    "fetch_new_function": fetch_new_function,
}

# In pbapis.py (if creating aggregate function)
AVAILABLE_FUNCTIONS = {
    # ... existing functions
    "get_new_aggregate_function": get_new_aggregate_function,
}
```

### 4.4 Create Tests
Add to test suite:

**Unit Tests:**
- Test primitive function with mock data
- Test error handling scenarios
- Test parameter validation

**Integration Tests:**
- Test with real API calls
- Test with various parameter combinations
- Test error scenarios

**Example Tests:**
```python
async def test_fetch_new_function():
    # Test with valid data
    result = await fetch_new_function("valid_param")
    assert "standardized_field_1" in result
    assert isinstance(result["standardized_field_1"], int)
    
    # Test error handling
    result = await fetch_new_function("invalid_param")
    assert "error_message" in result
```

## Phase 5: Validation and Documentation

### 5.1 Response Validation
Verify the implementation:

**Data Accuracy:**
- Compare transformed output with raw API data
- Verify calculations are correct
- Test with multiple data samples

**Performance:**
- Measure response times
- Test concurrent call efficiency
- Monitor memory usage

**Error Handling:**
- Test all error scenarios
- Verify graceful degradation
- Check error message clarity

### 5.2 Documentation
Create comprehensive documentation:

**Function Documentation:**
- Clear docstrings with examples
- Parameter descriptions and types
- Return value documentation
- Error scenarios

**API Mapping Documentation:**
- Source API documentation reference
- Field mapping tables
- Business logic explanations
- Usage examples

**Integration Guide:**
- How to use the function
- Common use cases
- Troubleshooting guide

### 5.3 Example Responses
Create example responses for testing:

**Create JSON Examples:**
```bash
mkdir -p docs/api_examples/new_function/
# Save example responses with obfuscated addresses
```

**Document Scenarios:**
- Typical response
- Edge cases (empty data, maximum values)
- Error responses
- Different parameter variations

## Phase 6: Integration Testing

### 6.1 End-to-End Testing
Test the complete flow:

**Web Server Testing:**
```bash
# Start test server
python src/test_webserver.py

# Test new function
curl -X POST http://localhost:8080/fetch_new_function \
     -H "Content-Type: application/json" \
     -d '{"param": "test_value"}'
```

**MCP Integration:**
- Test through MCP proxy functions
- Verify docstring synchronization
- Test with MCP clients

### 6.2 Performance Testing
Measure and optimize:

**Concurrent Performance:**
- Test multiple simultaneous calls
- Measure aggregate function performance
- Verify asyncio.gather() efficiency

**Bandwidth Efficiency:**
- Compare raw vs. transformed response sizes
- Verify filtering effectiveness
- Test with large datasets

### 6.3 AI Agent Testing
Verify AI-friendliness:

**Data Format Testing:**
- Test with pandas DataFrame creation
- Verify numpy array compatibility
- Test visualization library integration

**Usage Pattern Testing:**
- Test common AI analysis patterns
- Verify metadata usefulness
- Test with actual AI workflows

## Quality Checklist

Before considering integration complete:

- [ ] **API Analysis Complete**: All attributes cataloged and assessed
- [ ] **Data Dictionary Updated**: New fields added with proper documentation
- [ ] **Transformation Tested**: Source-to-target mapping verified
- [ ] **Error Handling Complete**: All error scenarios covered
- [ ] **Documentation Written**: Function docs, API mapping, examples
- [ ] **Tests Created**: Unit tests, integration tests, performance tests
- [ ] **Performance Validated**: Concurrent calls, bandwidth efficiency
- [ ] **AI-Friendly Verified**: Data formats, usage patterns tested
- [ ] **Configuration Updated**: YAML files, registries, exposure config
- [ ] **Examples Created**: JSON examples, usage documentation

## Continuous Improvement

### Monitor and Maintain
- **Track API Changes**: Monitor PB-API for breaking changes
- **Performance Monitoring**: Track response times and error rates
- **Usage Analytics**: Monitor which functions are used most
- **Feedback Integration**: Incorporate user feedback and suggestions

### Optimization Opportunities
- **Batch Operations**: Combine related API calls when possible
- **Caching Strategies**: Cache stable data to reduce API calls
- **Predictive Loading**: Pre-fetch related data based on usage patterns
- **Response Compression**: Optimize large responses for bandwidth

This workflow ensures that every PB-API integration follows consistent patterns, maintains high quality, and provides maximum value to AI agents and users.