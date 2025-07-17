# JSON Response Examples

This directory contains real JSON response examples from Provenance Blockchain and Figure Markets APIs. These examples are used for:

1. **Validating transformation mappings** - Ensure our YAML configurations point to correct JSON paths
2. **Testing transformation engine** - Use as input for testing our transformation logic
3. **Type validation** - Confirm data types match our expectations
4. **Path verification** - Validate that source paths in our configurations work with real data

## File Naming Convention

Files are named based on the API URL pattern with special characters replaced:

- `.` → `_` (dots become underscores)
- `/` → `_` (slashes become underscores)  
- `{parameter}` → `PARAMETER` (parameters in uppercase)

## Examples by Endpoint

| File | API Endpoint | Description |
|------|-------------|-------------|
| `service-explorer_api_v3_utility_token_stats.json` | `https://service-explorer.provenance.io/api/v3/utility_token/stats` | HASH token supply statistics |
| `service-explorer_api_v2_accounts_ADDRESS.json` | `https://service-explorer.provenance.io/api/v2/accounts/{address}` | Account information and vesting flag |
| `service-explorer_api_v2_accounts_ADDRESS_balances.json` | `https://service-explorer.provenance.io/api/v2/accounts/{address}/balances` | Multi-asset account balances |
| `service-explorer_api_v3_accounts_ADDRESS_vesting.json` | `https://service-explorer.provenance.io/api/v3/accounts/{address}/vesting` | Detailed vesting information |
| `api_provenance_io_provenance_exchange_v1_commitments_account_ADDRESS.json` | `https://api.provenance.io/provenance/exchange/v1/commitments/account/{address}` | Exchange commitments |
| `figuremarkets_com_service-hft-exchange_api_v1_assets.json` | `https://figuremarkets.com/service-hft-exchange/api/v1/assets` | Figure Markets asset information |
| `figuremarkets_com_service-hft-exchange_api_v1_markets.json` | `https://figuremarkets.com/service-hft-exchange/api/v1/markets` | Trading pairs/markets |
| `figuremarkets_com_service-hft-exchange_api_v1_trades_HASH-USD_size1.json` | `https://figuremarkets.com/service-hft-exchange/api/v1/trades/HASH-USD?size=1` | Single trade (singular response) |
| `figuremarkets_com_service-hft-exchange_api_v1_trades_HASH-USD_size3.json` | `https://figuremarkets.com/service-hft-exchange/api/v1/trades/HASH-USD?size=3` | Multiple trades (plural response) |
| `hastra_fetch_total_delegation_data.json` | `hastra.fetch_total_delegation_data(wallet_address)` | Delegation data from Hastra function |

## Privacy and Data Protection

**Important**: All private information has been obfuscated in these examples:
- **Wallet addresses**: Real addresses replaced with `tp1****` or `pb1****` placeholders
- **Account numbers**: Real account numbers replaced with example values
- **Amounts**: Keep real values for testing transformation logic
- **Public data**: Trading pairs, market data, and statistics remain as-is

## Key Observations from Real Data

### Amount Field Patterns
- **PB APIs**: Use `{amount: "string", denom: "string"}` structure
- **Hastra functions**: Return integer amounts directly
- **All amounts as strings**: Need conversion to integers for calculations

### Timestamp Patterns  
- **UTC format**: Most timestamps end with `Z` (UTC)
- **ISO 8601**: Standard format `YYYY-MM-DDTHH:MM:SS.sssZ`
- **Millisecond precision**: Some include milliseconds, others don't

### Response Structure Patterns
- **Pagination metadata**: Often included but should be filtered out
- **Nested arrays**: Complex structures like `commitments[].amount[]`
- **Singular vs plural**: Trading APIs change structure based on `size` parameter

### Denomination Coverage
- **Base denominations**: `nhash`, `neth.figure.se`, `uusd.trading`, `uusdc.figure.se`, `nsol.figure.se`, `uxrp.figure.se`, `uylds.fcc`
- **Consistent naming**: Figure Markets uses same denomination strings as PB APIs
- **Exponent validation**: Asset exponents match our conversion factors

## Usage in Testing

```python
import json
from pathlib import Path

def load_example(filename):
    """Load JSON example for testing."""
    path = Path("json_response_examples") / filename
    with open(path, 'r') as f:
        return json.load(f)

# Example usage
hash_stats = load_example("service-explorer_api_v3_utility_token_stats.json")
max_supply = hash_stats["maxSupply"]["amount"]  # "100000000000000000"
```

## Validation Checklist

When adding new examples:

- ✅ **Real data**: Use actual API responses, not fabricated data
- ✅ **Representative**: Include typical field values and edge cases
- ✅ **Complete**: Include all fields returned by the API
- ✅ **Consistent**: Follow established naming patterns
- ✅ **Documented**: Add entry to this README with endpoint info

## Related Files

- `docs/pb_api_response_examples.md` - Detailed analysis of each response
- `docs/pb_api_endpoint_mappings.yaml` - Source path configurations
- `docs/denomination_registry.yaml` - Denomination conversion mappings
- `src/config_driven_transformer.py` - Transformation engine that uses these examples