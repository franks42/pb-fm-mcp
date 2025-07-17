# Provenance Blockchain API Data Dictionary

This document defines the standardized data dictionary for transforming Provenance Blockchain REST API responses into AI-friendly, consistent formats.

## Core Naming Conventions

### Field Naming Standards
- **snake_case**: All standardized field names use snake_case (e.g., `max_supply_nhash`)
- **Suffix notation**: Amount fields include denomination suffix (e.g., `_nhash`, `_usd`)
- **Clear semantics**: Field names clearly indicate their purpose and units

### Type Standardization
- **Integer amounts**: All token amounts as integers in base units (nhash, micro-units)
- **String addresses**: Bech32-encoded addresses remain as strings
- **Boolean flags**: Consistent boolean representation
- **ISO timestamps**: Standardized datetime format where needed

## Denomination System

### Primary Denominations
```yaml
nhash:
  description: "nano-HASH base units (1 HASH = 1,000,000,000 nhash)"
  type: integer
  examples: [1000000000, 500000000]

uusd_trading:
  description: "micro-USD for trading (1 USD = 1,000,000 uusd)"
  type: integer
  examples: [1000000, 500000]

uusdc_figure_se:
  description: "micro-USDC from Figure Markets"
  type: integer
  examples: [1000000, 500000]

neth_figure_se:
  description: "nano-Ethereum from Figure Markets"
  type: integer
  examples: [1000000000, 500000000]
```

## Wallet Architecture Fields

### Core Wallet Composition
```yaml
wallet_total_amount_nhash:
  description: "Total HASH tokens in wallet (all categories)"
  type: integer
  maps_from: ["total", "wallet_total"]

available_total_amount_nhash:
  description: "Total available HASH (spendable + committed + unvested)"
  type: integer
  maps_from: ["available", "available_total"]

available_spendable_amount_nhash:
  description: "HASH tokens immediately spendable"
  type: integer
  maps_from: ["spendable", "available_spendable"]

available_committed_amount_nhash:
  description: "HASH tokens committed but not yet spent"
  type: integer
  maps_from: ["committed", "available_committed"]

available_unvested_amount_nhash:
  description: "HASH tokens available but subject to vesting"
  type: integer
  maps_from: ["unvested", "available_unvested"]

delegated_total_amount_nhash:
  description: "Total HASH delegated to validators"
  type: integer
  maps_from: ["delegated", "delegated_total"]

delegated_staked_amount_nhash:
  description: "HASH actively staked and earning rewards"
  type: integer
  maps_from: ["staked", "delegated_staked"]
  note: "⭐ Earns Rewards"

delegated_rewards_amount_nhash:
  description: "Accumulated staking rewards (not earning additional rewards)"
  type: integer
  maps_from: ["rewards", "delegated_rewards"] 
  note: "❌ No Additional Rewards"

delegated_redelegated_amount_nhash:
  description: "HASH in 21-day redelegation transition (still earning rewards)"
  type: integer
  maps_from: ["redelegated", "delegated_redelegated"]
  note: "⭐ Earns Rewards during transition"

delegated_unbonding_amount_nhash:
  description: "HASH in 21-day unbonding period (not earning rewards)"
  type: integer
  maps_from: ["unbonding", "delegated_unbonding"]
  note: "❌ No Rewards during unbonding"
```

### Vesting System Fields
```yaml
is_vesting:
  description: "Boolean indicating if account has vesting restrictions"
  type: boolean
  maps_from: ["isVesting", "vesting", "has_vesting"]

vesting_total_unvested_amount_nhash:
  description: "Total HASH still subject to vesting schedule"
  type: integer
  maps_from: ["vesting_unvested", "unvested_total"]

vesting_initial_amount_nhash:
  description: "Original amount when vesting period started"
  type: integer
  maps_from: ["vesting_initial", "initial_vesting"]

vesting_start_date:
  description: "ISO timestamp when vesting period began"
  type: string
  format: "ISO 8601"
  maps_from: ["vesting_start", "start_date"]

vesting_end_date:
  description: "ISO timestamp when vesting period completes"
  type: string
  format: "ISO 8601"
  maps_from: ["vesting_end", "end_date"]

vesting_coverage_deficit_nhash:
  description: "Amount of unvested HASH not covered by delegation"
  type: integer
  calculation: "vesting_total_unvested_amount_nhash - delegated_total_amount_nhash"
  note: "Negative values indicate surplus delegation coverage"
```

### Calculated Fields
```yaml
controllable_hash_nhash:
  description: "HASH tokens user can freely control (spend/delegate)"
  type: integer
  calculation: "available_spendable_amount_nhash + max(0, delegated_total_amount_nhash - vesting_total_unvested_amount_nhash)"
  note: "Critical field that differs from available amounts for vesting accounts"

locked_nhash:
  description: "HASH tokens locked in various restrictions"
  type: integer
  calculation: "current_supply_nhash - circulating_supply_nhash - community_pool_nhash - bonded_nhash"
  context: "Token statistics calculation"
```

## Account Identification
```yaml
account_address:
  description: "Bech32-encoded Provenance account address"
  type: string
  format: "bech32"
  examples: ["tp1abc123...", "pb1xyz789..."]
  maps_from: ["address", "acc_address", "account_address"]

account_number:
  description: "Unique numeric account identifier"
  type: integer
  maps_from: ["account_number", "acc_number"]

sequence_number:
  description: "Account transaction sequence number"
  type: integer
  maps_from: ["sequence", "seq_number", "sequence_number"]
```

## Token Supply Statistics
```yaml
max_supply_nhash:
  description: "Maximum HASH tokens that can ever exist"
  type: integer
  maps_from: ["maxSupply.amount", "max_supply"]

current_supply_nhash:
  description: "Current total HASH supply (max_supply - burned)"
  type: integer
  maps_from: ["currentSupply.amount", "current_supply"]

circulating_supply_nhash:
  description: "HASH tokens available for trading and transfer"
  type: integer
  maps_from: ["circulation.amount", "circulating"]

burned_nhash:
  description: "HASH tokens permanently removed from circulation"
  type: integer
  maps_from: ["burned.amount", "burned_tokens"]

community_pool_nhash:
  description: "HASH tokens managed by Provenance governance"
  type: integer
  maps_from: ["communityPool.amount", "community_pool"]

bonded_nhash:
  description: "HASH tokens staked with validators for network security"
  type: integer
  maps_from: ["bonded.amount", "total_bonded"]
```

## Blockchain Metadata
```yaml
block_height:
  description: "Current blockchain block number"
  type: integer
  maps_from: ["blockHeight", "block_number", "height"]

block_time:
  description: "ISO timestamp of block creation"
  type: string
  format: "ISO 8601"
  maps_from: ["block_time", "timestamp"]

validator_address:
  description: "Bech32-encoded validator operator address"
  type: string
  format: "bech32"
  examples: ["pbvaloper1abc...", "tpvaloper1xyz..."]
  maps_from: ["operator_address", "validator_address"]
```

## Field Exclusion Rules

### Excluded Fields (Superfluous for AI)
```yaml
excluded_always:
  - lastUpdated        # Timestamp not needed for most AI operations
  - last_updated       # Redundant timing information
  - validatorCount     # Not relevant for token statistics
  - validator_count    # Statistical noise for core operations
  - bondedRatio       # String representation confusing for AI
  - bonded_ratio      # Can be calculated if needed

excluded_conditionally:
  - blockHeight       # Only exclude if not specifically requested
  - block_height      # Include for transaction/block-specific queries
  - consensus_pubkey  # Complex validator data, exclude unless needed
  - pubkey           # Technical validator details
```

## Transformation Rules

### Amount Conversions
```yaml
string_to_integer:
  pattern: "*.amount"
  rule: "Convert string amounts to integer base units"
  examples:
    input: {"amount": "1000000000", "denom": "nhash"}
    output: 1000000000

nested_amount_extraction:
  pattern: "{amount: {amount: string, denom: string}}"
  rule: "Extract amount value, add denomination suffix to field name"
  examples:
    input: {"maxSupply": {"amount": "100000000000000000", "denom": "nhash"}}
    output: {"max_supply_nhash": 100000000000000000}
```

### Field Name Transformations
```yaml
camelCase_to_snake_case:
  examples:
    maxSupply: max_supply_nhash
    currentSupply: current_supply_nhash
    communityPool: community_pool_nhash
    lastUpdated: last_updated
    bondedRatio: bonded_ratio

denomination_suffixes:
  rule: "Add denomination suffix for clarity"
  examples:
    available: available_spendable_amount_nhash
    bonded: bonded_nhash
    rewards: delegated_rewards_amount_nhash
```

## Usage Guidelines

### Implementation Priority
1. **Core wallet fields**: Start with essential balance and delegation data
2. **Token statistics**: Implement supply and circulation metrics
3. **Account metadata**: Add identification and sequence information
4. **Calculated fields**: Implement derived values like controllable_hash
5. **Blockchain context**: Add block and validator information as needed

### Validation Rules
1. **Data integrity**: Ensure no critical information is lost in transformation
2. **Type consistency**: All amounts must be integers in base units
3. **Field completeness**: Include all standardized fields or mark as null
4. **Calculation accuracy**: Verify all derived field calculations

### Error Handling
- **Missing fields**: Return null for optional fields, error for required fields
- **Type mismatches**: Log warnings and attempt conversion where safe
- **Invalid calculations**: Return null for impossible calculations with error details

## MCP Function Inventory

### Current Function Signatures and Return Attributes

#### System Functions
```yaml
get_system_context:
  parameters: []
  returns:
    context: "string - Complete system context markdown document"

adt:
  parameters:
    - a: int
    - b: int  
  returns: "int - Always returns 42"
```

#### Figure Markets Exchange Functions
```yaml
fetch_last_crypto_token_price:
  parameters:
    - token_pair: "str = 'HASH-USD'"
    - last_number_of_trades: "int = 1"
  returns:
    matches: "list - Individual trade details"
  standardized_returns:
    trading_matches: "list - Standardized trade data"

fetch_current_fm_data:
  parameters: []
  returns:
    - id: "string - Trading pair identifier"
    - denom: "string - Token name" 
    - quoteDenum: "string - Currency denomination"
  standardized_returns:
    trading_pairs: "list - Standardized market data"
    
fetch_current_fm_account_balance_data:
  parameters:
    - wallet_address: "str"
  returns:
    - denom: "string - Asset identifier (neth.figure.se=ETH, nhash=nano-HASH, etc.)"
    - amount: "string - Balance amount"
  standardized_returns:
    asset_balances: "list - Standardized balance data with denomination suffixes"

fetch_current_fm_account_info:
  parameters:
    - wallet_address: "str"
  returns:
    isVesting: "boolean - Vesting restriction status"
  standardized_returns:
    is_vesting: "boolean - Standardized vesting flag"
    account_address: "string - Bech32 address"
```

#### Account Balance Functions  
```yaml
fetch_available_total_amount:
  parameters:
    - wallet_address: "str"
  returns:
    available_total_amount: "int - Total available HASH amount"
    denom: "string - Always 'nhash'"
  standardized_returns:
    available_total_amount_nhash: "int - Standardized field name"

fetch_account_is_vesting:
  parameters:
    - wallet_address: "str"
  returns:
    wallet_is_vesting: "boolean - Vesting status"
  standardized_returns:
    is_vesting: "boolean - Standardized vesting flag"

fetch_available_committed_amount:
  parameters:
    - wallet_address: "str"
  returns:
    denom: "string - Token denomination"
    available_committed_amount: "int|string - Committed amount"
  standardized_returns:
    available_committed_amount_nhash: "int - Standardized amount"
```

#### Vesting Functions
```yaml
fetch_vesting_total_unvested_amount:
  parameters:
    - wallet_address: "str"
    - date_time: "str|None - ISO 8601 format"
  returns:
    date_time: "string - ISO timestamp"
    vesting_original_amount: "int - Original vesting amount"
    denom: "string - Token denomination"
    vesting_total_vested_amount: "int - Vested amount"
    vesting_total_unvested_amount: "int - Unvested amount"
    start_time: "string - Vesting start ISO timestamp"
    end_time: "string - Vesting end ISO timestamp"
  standardized_returns:
    date_time: "string - Preserved"
    vesting_original_amount_nhash: "int - With denomination suffix"
    vesting_total_vested_amount_nhash: "int - With denomination suffix"
    vesting_total_unvested_amount_nhash: "int - With denomination suffix"
    vesting_start_date: "string - Renamed for clarity"
    vesting_end_date: "string - Renamed for clarity"
```

#### Asset Information Functions
```yaml
fetch_figure_markets_assets_info:
  parameters: []
  returns:
    - asset_name: "string - Asset identifier"
    - asset_description: "string - Asset description"
    - asset_display_name: "string - Display name"
    - asset_type: "string - CRYPTO, STABLECOIN, or FUND"
    - asset_exponent: "int - Decimal exponent for amount conversion"
    - asset_denom: "string - Asset denomination"
  standardized_returns:
    assets: "list - Standardized asset information"
```

#### Token Statistics Functions
```yaml
fetch_current_hash_statistics:
  parameters: []
  returns:
    maxSupply: "object - {amount: string, denom: string}"
    burned: "object - {amount: string, denom: string}"
    currentSupply: "object - {amount: string, denom: string}"
    circulation: "object - {amount: string, denom: string}"
    communityPool: "object - {amount: string, denom: string}"
    bonded: "object - {amount: string, denom: string}"
    locked: "object - {amount: string, denom: string} (calculated)"
  standardized_returns:
    max_supply_nhash: "int - Converted to integer base units"
    burned_nhash: "int - Converted to integer base units"
    current_supply_nhash: "int - Converted to integer base units"
    circulating_supply_nhash: "int - Converted to integer base units"
    community_pool_nhash: "int - Converted to integer base units"
    bonded_nhash: "int - Converted to integer base units"
    locked_nhash: "int - Calculated field in base units"
```

#### Delegation Functions
```yaml
fetch_total_delegation_data:
  parameters:
    - wallet_address: "str"
  returns:
    delegated_staked_amount: "int - Staked HASH earning rewards"
    delegated_redelegated_amount: "int - Redelegated HASH earning rewards"
    delegated_rewards_amount: "int - Reward HASH not earning additional rewards"
    delegated_unbonding_amount: "int - Unbonding HASH not earning rewards"
    delegated_total_delegated_amount: "int - Total delegated (calculated)"
    delegated_earning_amount: "int - Amount earning rewards (calculated)"
    delegated_not_earning_amount: "int - Amount not earning rewards (calculated)"
  standardized_returns:
    delegated_staked_amount_nhash: "int - With denomination suffix"
    delegated_redelegated_amount_nhash: "int - With denomination suffix"
    delegated_rewards_amount_nhash: "int - With denomination suffix"
    delegated_unbonding_amount_nhash: "int - With denomination suffix"
    delegated_total_amount_nhash: "int - Renamed for consistency"
    delegated_earning_amount_nhash: "int - Amount earning rewards"
    delegated_not_earning_amount_nhash: "int - Amount not earning rewards"
```

## Function Transformation Mapping

### Priority 1: Core Account Functions (High Priority)
1. **fetch_current_hash_statistics** ✅ (Example implementation complete)
2. **fetch_available_total_amount** - Simple balance data
3. **fetch_account_is_vesting** - Boolean vesting flag
4. **fetch_current_fm_account_info** - Core account information

### Priority 2: Wallet Composition Functions (High Priority)  
5. **fetch_current_fm_account_balance_data** - Multi-asset balances
6. **fetch_total_delegation_data** - Delegation amounts
7. **fetch_available_committed_amount** - Committed amounts
8. **fetch_vesting_total_unvested_amount** - Vesting details

### Priority 3: Market Data Functions (Medium Priority)
9. **fetch_current_fm_data** - Trading pair information
10. **fetch_last_crypto_token_price** - Price data
11. **fetch_figure_markets_assets_info** - Asset metadata

### Field Standardization Examples

#### Amount Object Transformation
```yaml
# Before (Raw API)
maxSupply:
  amount: "100000000000000000"
  denom: "nhash"

# After (Standardized)  
max_supply_nhash: 100000000000000000
```

#### Boolean Flag Standardization
```yaml
# Before (Raw API)
flags:
  isVesting: true

# After (Standardized)
is_vesting: true
```

#### List Field Renaming
```yaml
# Before (Raw API)
results: [...]

# After (Standardized)
asset_balances: [...]
```

This data dictionary serves as the foundation for consistent API transformations across all Provenance Blockchain endpoints.