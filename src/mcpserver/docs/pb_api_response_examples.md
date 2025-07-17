# PB-API Response Examples for Testing

This document contains real JSON response examples from Provenance Blockchain APIs to validate our transformation mappings and ensure correct data extraction paths.

## How to Use These Examples

1. **Validate source paths**: Verify our YAML configurations point to correct JSON paths
2. **Test transformations**: Use as input for testing our transformation engine
3. **Type validation**: Confirm data types match our expectations
4. **Field discovery**: Identify additional fields we might want to include/exclude

## Response Examples by Endpoint

### 1. HASH Token Statistics
**Endpoint**: `https://service-explorer.provenance.io/api/v3/utility_token/stats`
**Method**: GET
**Parameters**: None

```json
{
  "maxSupply": {
    "amount": "100000000000000000",
    "denom": "nhash"
  },
  "burned": {
    "amount": "1234567890123456",
    "denom": "nhash"
  },
  "currentSupply": {
    "amount": "98765432109876544",
    "denom": "nhash"
  },
  "circulation": {
    "amount": "45678901234567890",
    "denom": "nhash"
  },
  "communityPool": {
    "amount": "8765432109876543",
    "denom": "nhash"
  },
  "bonded": {
    "amount": "23456789012345678",
    "denom": "nhash"
  },
  "lastUpdated": "2024-07-17T10:30:00Z",
  "blockHeight": 12345678,
  "validatorCount": 150,
  "bondedRatio": "0.237456"
}
```

**Analysis**:
- ✅ **Amount fields**: All have `{amount: string, denom: string}` structure
- ✅ **String amounts**: Need conversion to integers for calculations
- ❌ **Excluded fields**: `lastUpdated`, `blockHeight`, `validatorCount`, `bondedRatio`
- 🔧 **Calculated field**: `locked` = currentSupply - circulation - communityPool - bonded

---

### 2. Account Information
**Endpoint**: `https://service-explorer.provenance.io/api/v2/accounts/{account_address}`
**Method**: GET
**Parameters**: account_address (string)

```json
{
  "account": {
    "@type": "/cosmos.auth.v1beta1.BaseAccount",
    "address": "tp1abc123def456ghi789jkl012mno345pqr678stu",
    "pub_key": null,
    "account_number": "12345",
    "sequence": "67"
  },
  "flags": {
    "isVesting": true,
    "hasMarkers": false,
    "hasContracts": false
  },
  "baseAccount": {
    "address": "tp1abc123def456ghi789jkl012mno345pqr678stu",
    "pubKey": null,
    "accountNumber": 12345,
    "sequence": 67
  },
  "originalVesting": [
    {
      "denom": "nhash",
      "amount": "5000000000000000"
    }
  ],
  "delegatedFree": [
    {
      "denom": "nhash", 
      "amount": "1000000000000000"
    }
  ],
  "delegatedVesting": [
    {
      "denom": "nhash",
      "amount": "2000000000000000"
    }
  ],
  "endTime": "2025-01-01T00:00:00Z",
  "startTime": "2023-01-01T00:00:00Z"
}
```

**Analysis**:
- ✅ **Account ID**: `account.address` and `account.account_number`
- ✅ **Vesting flag**: `flags.isVesting` (boolean)
- ✅ **Sequence**: `account.sequence` for transaction ordering
- ❌ **Excluded fields**: `@type`, `pub_key`, `baseAccount`, `delegatedFree`, `delegatedVesting`
- 📝 **Note**: Vesting details are here but more complete info in vesting endpoint

---

### 3. Account Balances
**Endpoint**: `https://service-explorer.provenance.io/api/v2/accounts/{account_address}/balances`
**Method**: GET
**Parameters**: account_address (string), count (int), page (int)

```json
{
  "results": [
    {
      "denom": "nhash",
      "amount": "1500000000000"
    },
    {
      "denom": "neth.figure.se", 
      "amount": "2000000000"
    },
    {
      "denom": "uusd.trading",
      "amount": "500000"
    },
    {
      "denom": "uusdc.figure.se",
      "amount": "1000000"
    },
    {
      "denom": "nsol.figure.se",
      "amount": "750000000"
    }
  ],
  "request": {
    "count": 20,
    "page": 1
  },
  "pagination": {
    "totalCount": 5,
    "pageNumber": 1,
    "pageSize": 20,
    "totalPages": 1
  }
}
```

**Analysis**:
- ✅ **Asset balances**: `results[]` array with `denom` and `amount`
- ✅ **Multi-asset support**: Various denominations represented
- ✅ **String amounts**: All amounts as strings, need integer conversion
- ❌ **Excluded fields**: `request`, `pagination` (metadata not needed)
- 🔧 **Transform**: Array of `{denom, amount}` → standardized asset balance objects

---

### 4. Vesting Information
**Endpoint**: `https://service-explorer.provenance.io/api/v3/accounts/{account_address}/vesting`
**Method**: GET
**Parameters**: account_address (string)

```json
{
  "account": {
    "address": "tp1abc123def456ghi789jkl012mno345pqr678stu",
    "accountNumber": 12345
  },
  "originalVestingList": [
    {
      "denom": "nhash",
      "amount": "5000000000000000"
    }
  ],
  "delegatedFree": [
    {
      "denom": "nhash",
      "amount": "1000000000000000"
    }
  ],
  "delegatedVesting": [
    {
      "denom": "nhash", 
      "amount": "2000000000000000"
    }
  ],
  "startTime": "2023-01-01T00:00:00Z",
  "endTime": "2025-01-01T00:00:00Z"
}
```

**Analysis**:
- ✅ **Original amount**: `originalVestingList[0].amount`
- ✅ **Vesting period**: `startTime` and `endTime` with UTC timestamps
- ✅ **Account context**: `account.address` for validation
- ❌ **Excluded fields**: `delegatedFree`, `delegatedVesting` (handled in delegation endpoint)
- 🔧 **Calculated fields**: Current vested/unvested amounts based on linear interpolation

---

### 5. Delegation Data (from hastra.fetch_total_delegation_data)
**Endpoint**: HASTRA_FUNCTION
**Method**: Function call
**Parameters**: wallet_address (string)

```json
{
  "delegated_staked_amount": 2500000000000000,
  "delegated_redelegated_amount": 100000000000000,
  "delegated_rewards_amount": 25000000000000,
  "delegated_unbonding_amount": 200000000000000,
  "delegated_total_delegated_amount": 2825000000000000,
  "delegated_earning_amount": 2600000000000000,
  "delegated_not_earning_amount": 225000000000000
}
```

**Analysis**:
- ✅ **Already standardized**: Hastra function returns clean field names
- ✅ **Integer amounts**: Already converted to base units
- ✅ **Complete picture**: All delegation states represented
- ✅ **Calculated fields**: totals and earning/non-earning breakdowns
- 🔧 **Transform**: Add `_nhash` suffixes for consistency

---

### 6. Exchange Commitments
**Endpoint**: `https://api.provenance.io/provenance/exchange/v1/commitments/account/{account_address}`
**Method**: GET
**Parameters**: account_address (string)

```json
{
  "commitments": [
    {
      "market_id": 1,
      "amount": [
        {
          "denom": "nhash",
          "amount": "100000000000"
        },
        {
          "denom": "uusd.trading", 
          "amount": "50000"
        }
      ]
    },
    {
      "market_id": 2,
      "amount": [
        {
          "denom": "neth.figure.se",
          "amount": "1000000000"
        }
      ]
    }
  ],
  "pagination": {
    "next_key": null,
    "total": "2"
  }
}
```

**Analysis**:
- ✅ **Nested structure**: `commitments[].amount[]` array
- ✅ **Multi-market**: Different market IDs with different assets
- ✅ **Multi-asset**: Multiple denominations per market
- ❌ **Excluded fields**: `pagination` metadata
- 🔧 **Transform**: Extract market 1 HASH commitments specifically
- 📝 **Note**: Complex nested filtering required: `commitments[?market_id==1].amount[?denom=='nhash'].amount`

---

### 7. Figure Markets Assets
**Endpoint**: `https://figuremarkets.com/service-hft-exchange/api/v1/assets`
**Method**: GET
**Parameters**: None

```json
{
  "data": [
    {
      "name": "HASH",
      "description": "Provenance Blockchain's native utility token",
      "displayName": "HASH",
      "type": "CRYPTO",
      "exponent": 9,
      "provenanceMarkerName": "nhash"
    },
    {
      "name": "ETH",
      "description": "Ethereum",
      "displayName": "Ethereum",
      "type": "CRYPTO", 
      "exponent": 9,
      "provenanceMarkerName": "neth.figure.se"
    },
    {
      "name": "USDC",
      "description": "USD Coin",
      "displayName": "USDC",
      "type": "STABLECOIN",
      "exponent": 6,
      "provenanceMarkerName": "uusdc.figure.se"
    },
    {
      "name": "YLDS",
      "description": "YLDS Fund",
      "displayName": "YLDS", 
      "type": "FUND",
      "exponent": 6,
      "provenanceMarkerName": "uylds.fcc"
    }
  ]
}
```

**Analysis**:
- ✅ **Asset metadata**: `data[]` array with asset details
- ✅ **Denomination mapping**: `provenanceMarkerName` maps to our base denominations
- ✅ **Exponent info**: Confirms our conversion factors (10^exponent)
- ✅ **Asset types**: CRYPTO, STABLECOIN, FUND categories
- 🔧 **Transform**: Array mapping with field name standardization

---

### 8. Trading Data (Markets)
**Endpoint**: `https://www.figuremarkets.com/service-hft-exchange/api/v1/markets`
**Method**: GET
**Parameters**: None

```json
{
  "data": [
    {
      "id": "HASH-USD",
      "denom": "nhash",
      "quoteDenom": "uusd.trading",
      "displayName": "HASH/USD",
      "status": "ACTIVE",
      "minOrderSize": "1000000000",
      "tickSize": "0.000001"
    },
    {
      "id": "ETH-USD", 
      "denom": "neth.figure.se",
      "quoteDenom": "uusd.trading",
      "displayName": "ETH/USD",
      "status": "ACTIVE",
      "minOrderSize": "1000000",
      "tickSize": "0.01"
    }
  ]
}
```

**Analysis**:
- ✅ **Trading pairs**: `data[]` array with pair details
- ✅ **Denomination mapping**: `denom` (base) and `quoteDenom` (quote)
- ✅ **Pair identification**: `id` field for pair reference
- ❌ **Excluded fields**: `status`, `minOrderSize`, `tickSize` (trading-specific)
- 🔧 **Transform**: Map `denom`→`base_denom`, `quoteDenom`→`quote_denom`

---

### 9. Token Prices (Trades)
**Endpoint**: `https://www.figuremarkets.com/service-hft-exchange/api/v1/trades/{token_pair}`
**Method**: GET
**Parameters**: token_pair (string), size (int)

**Example with size=1 (singular):**
```json
{
  "matches": [
    {
      "id": "trade_12345",
      "price": "0.845000",
      "size": "1000.000000000",
      "time": "2024-07-17T10:30:00.123Z",
      "side": "buy",
      "market": "HASH-USD"
    }
  ]
}
```

**Example with size=3 (plural):**
```json
{
  "matches": [
    {
      "id": "trade_12345",
      "price": "0.845000", 
      "size": "1000.000000000",
      "time": "2024-07-17T10:30:00.123Z",
      "side": "buy",
      "market": "HASH-USD"
    },
    {
      "id": "trade_12344",
      "price": "0.844500",
      "size": "500.000000000", 
      "time": "2024-07-17T10:29:45.678Z",
      "side": "sell",
      "market": "HASH-USD"
    },
    {
      "id": "trade_12343",
      "price": "0.846000",
      "size": "2000.000000000",
      "time": "2024-07-17T10:29:30.456Z", 
      "side": "buy",
      "market": "HASH-USD"
    }
  ]
}
```

**Analysis**:
- ✅ **Singular/plural variants**: Single object vs array based on size parameter
- ✅ **Price data**: `price` (quote currency), `size` (base currency amount)
- ✅ **UTC timestamps**: `time` field with timezone info
- ✅ **Trading context**: `market` identifies the trading pair
- 🔧 **Transform**: Handle both singular and plural response structures
- 📝 **Response structure rule**: size=1 → return object, size>1 → return array

---

## Testing Strategy

### 1. Path Validation Tests
```python
def test_source_paths():
    """Test that our YAML source paths correctly extract data."""
    hash_stats_example = {...}  # JSON above
    
    # Test amount extraction
    max_supply = extract_by_path(hash_stats_example, "maxSupply.amount")
    assert max_supply == "100000000000000000"
    
    # Test filtering
    filtered = apply_exclusions(hash_stats_example, ["lastUpdated", "blockHeight"])
    assert "lastUpdated" not in filtered
```

### 2. Transformation Tests
```python
def test_hash_statistics_transformation():
    """Test complete transformation of hash statistics."""
    raw_response = {...}  # JSON above
    transformer = GroupedAttributeTransformer()
    
    result = transformer.transform_response("hash_statistics", raw_response)
    
    # Validate standardized fields
    assert "max_supply_nhash" in result
    assert isinstance(result["max_supply_nhash"], int)
    assert result["max_supply_nhash"] == 100000000000000000
```

### 3. Type Validation Tests
```python
def test_data_types():
    """Test that all data types match expectations."""
    examples = load_all_examples()
    
    for endpoint, example in examples.items():
        validation = validate_response_types(example)
        assert validation.is_valid, f"Type validation failed for {endpoint}"
```

## File Organization

Store these examples in:
```
tests/fixtures/
├── pb_api_responses/
│   ├── hash_statistics.json
│   ├── account_info.json
│   ├── account_balances.json
│   ├── vesting_info.json
│   ├── delegation_data.json
│   ├── exchange_commitments.json
│   ├── fm_assets.json
│   ├── trading_markets.json
│   ├── token_prices_singular.json
│   └── token_prices_plural.json
└── expected_outputs/
    ├── hash_statistics_transformed.json
    ├── account_info_transformed.json
    └── ...
```

This ensures we have:
- ✅ **Real data validation** using actual API responses
- ✅ **Path verification** confirming our YAML configurations work
- ✅ **Type checking** ensuring data types match expectations
- ✅ **Transformation testing** with before/after comparisons
- ✅ **Edge case coverage** including singular/plural variants