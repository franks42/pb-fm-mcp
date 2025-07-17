# Provenance Blockchain API Standardization for AI-MCP Integration

## Project Overview

### Current Title
"Adapting the Provenance Blockchain REST APIs for easy, concise and unambiguous AI-MCP Ingestion"
*(Working title - to be refined)*

### Alternative Titles to Consider
- "Provenance Blockchain API Standardization Layer"
- "PB API AI-Optimization Framework" 
- "Standardized Provenance Data Gateway"
- "AI-Ready Provenance API Adapter"

## Problem Statement

The Provenance Blockchain REST API has evolved over ~6 years, resulting in:

### Inconsistencies
- **Parameter naming**: Inconsistent conventions across endpoints
- **Response structure**: Varying JSON key naming patterns
- **Data types**: Mixed formats for similar data across endpoints
- **Denominations**: Inconsistent unit representations

### Information Overload
- **Excessive data**: APIs return more information than typically needed
- **Redundant fields**: Multiple representations of the same data
- **Confusing terminology**: Legacy naming that could mislead AI agents

### AI Integration Challenges
- **Ambiguous responses**: Inconsistent data makes AI interpretation difficult
- **Cognitive overhead**: Too much irrelevant data confuses AI decision-making
- **Poor discoverability**: Unclear function purposes and parameters

## Solution Architecture

### Core Components

#### 1. Data Dictionary & Mapping System
```
PB API Field → Standardized Field → AI-Friendly Description
"acc_address" → "account_address" → "Bech32-encoded account identifier"
"amount.denom" → "denomination" → "Token denomination (e.g., 'nhash', 'uusd')"
"amount.amount" → "amount_base_units" → "Amount in smallest denomination units"
```

#### 2. Transformation Engine
- **Field Mapping**: Consistent naming across all endpoints
- **Type Conversion**: Standardized data types (strings → numbers, etc.)
- **Denomination Handling**: Consistent unit representation and conversion
- **Data Filtering**: Remove superfluous/confusing fields

#### 3. MCP Function Framework
- **Clear Documentation**: Concise purpose statements for each function
- **Consistent Signatures**: Standardized parameter patterns
- **Error Handling**: Comprehensive validation and helpful error messages
- **Response Standardization**: Uniform JSON structure across all functions

## Implementation Strategy

### Phase 1: Foundation & Analysis

#### API Audit Matrix
Create comprehensive mapping of existing endpoints:

```
Endpoint | Current Parameters | Response Fields | Issues | Priority
---------|-------------------|-----------------|--------|----------
/accounts/{address} | acc_address | account.account_number, account.address | Redundant naming | High
/balances/{address} | address | balances[].amount.denom, balances[].amount.amount | Nested complexity | High
/validators | status, page | validators[].operator_address, validators[].consensus_pubkey | Inconsistent IDs | Medium
```

#### Data Dictionary Design
```yaml
standardized_fields:
  account_address:
    type: string
    format: bech32
    description: "Provenance blockchain account address"
    examples: ["tp1abc...", "pb1xyz..."]
  
  amount_hash:
    type: integer
    format: int64
    description: "Amount in nhash (10^-9 HASH)"
    examples: [1000000000, 500000000]
  
  block_height:
    type: integer
    format: int64
    description: "Blockchain block number"
    examples: [12345678, 12345679]
```

### Phase 2: Core Infrastructure

#### Transformation Engine Architecture
```python
class PBAPITransformer:
    def __init__(self, data_dictionary: Dict, field_mappings: Dict):
        self.data_dict = data_dictionary
        self.field_map = field_mappings
    
    def transform_response(self, raw_response: Dict, endpoint_config: Dict) -> Dict:
        """Transform raw PB API response to standardized format"""
        
    def filter_fields(self, data: Dict, allowed_fields: List[str]) -> Dict:
        """Remove superfluous data fields"""
        
    def convert_denominations(self, amount_data: Dict) -> Dict:
        """Standardize denomination formats"""
```

#### MCP Function Framework
```python
@mcp_tool("get_account_info")
async def get_account_info(address: str) -> Dict:
    """
    Get comprehensive account information for a Provenance address.
    
    Args:
        address: Bech32-encoded Provenance account address (e.g., 'tp1abc...')
    
    Returns:
        {
            "account_address": "tp1abc...",
            "account_number": 12345,
            "sequence_number": 67,
            "balances": [
                {
                    "denomination": "nhash",
                    "amount_base_units": 1000000000,
                    "amount_display": "1.0 HASH"
                }
            ]
        }
    """
```

### Phase 3: Implementation Priorities

#### High Priority Endpoints
1. **Account Operations**
   - Account info and balances
   - Transaction history
   - Delegation information

2. **Market Data**
   - Token prices and trading data
   - Market statistics
   - Exchange rates

3. **Blockchain Data**
   - Block information
   - Validator data
   - Network statistics

#### Medium Priority Endpoints
1. **Governance**
   - Proposals and voting
   - Parameter queries

2. **Smart Contracts**
   - Contract state queries
   - Execution history

3. **NFT/Metadata**
   - Scope and metadata queries
   - Asset information

## Expected Benefits

### For AI Agents
- **Predictable Responses**: Consistent field names and structures
- **Clear Semantics**: Unambiguous data meanings and formats
- **Reduced Confusion**: Filtered data focuses on essential information
- **Better Documentation**: Clear function purposes and examples

### For Developers
- **Maintainability**: Centralized data dictionary for easy updates
- **Extensibility**: Framework supports adding new endpoints easily
- **Testing**: Standardized responses enable comprehensive testing
- **Documentation**: Auto-generated docs from data dictionary

### For Users
- **Reliability**: Consistent behavior across all API functions
- **Performance**: Filtered responses reduce bandwidth and processing
- **Clarity**: Human-readable field names and descriptions

## Success Metrics

1. **Consistency Score**: % of fields following naming conventions
2. **Data Reduction**: % reduction in response payload size
3. **AI Comprehension**: Accuracy of AI agent interpretations
4. **Developer Experience**: Time to integrate new endpoints
5. **Documentation Quality**: Coverage and clarity metrics

## Risk Mitigation

### Potential Challenges
1. **API Changes**: Upstream PB API modifications
2. **Performance**: Additional transformation overhead
3. **Completeness**: Ensuring no critical data is lost in filtering
4. **Backwards Compatibility**: Maintaining existing integrations

### Mitigation Strategies
1. **Version Monitoring**: Track PB API changes and update mappings
2. **Caching**: Cache transformed responses to reduce overhead
3. **Validation**: Comprehensive testing to ensure data integrity
4. **Gradual Migration**: Phased rollout with fallback options

## Next Steps

1. **Start API Audit**: Begin systematic review of PB API endpoints
2. **Design Data Dictionary**: Create initial standardized field definitions
3. **Build Prototype**: Implement transformation engine for 2-3 key endpoints
4. **Validate Approach**: Test with AI agents and gather feedback
5. **Scale Implementation**: Gradually expand to all priority endpoints

---

*This document will be updated as the project evolves and requirements are refined.*