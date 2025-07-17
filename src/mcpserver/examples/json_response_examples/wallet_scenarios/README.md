# Wallet Scenario Examples

This directory contains realistic wallet examples covering different combinations of vesting, delegation, and multi-asset scenarios. All examples use real data patterns with obfuscated addresses.

## Wallet Scenarios

| Wallet ID | Vesting | Delegation | Multi-Asset | Description |
|-----------|---------|------------|-------------|-------------|
| `basic_holder` | ❌ | ❌ | ❌ | Simple HASH holder, no vesting or delegation |
| `multi_asset_holder` | ❌ | ❌ | ✅ | Holds HASH + USD + ETH + SOL, no vesting/delegation |
| `vesting_only` | ✅ | ❌ | ❌ | Has vesting schedule, no delegation |
| `delegation_only` | ❌ | ✅ | ❌ | Active staker with multiple validators |
| `vesting_delegator` | ✅ | ✅ | ❌ | Vesting account that also delegates |
| `power_trader` | ❌ | ❌ | ✅ | Figure Markets trader with commitments across all assets |
| `complete_portfolio` | ✅ | ✅ | ✅ | Full scenario: vesting, delegation, multi-asset |

## API Response Structure

Each wallet scenario includes:
- `account_info_{wallet_id}.json` - Basic account information
- `balances_{wallet_id}.json` - Asset balances 
- `vesting_{wallet_id}.json` - Vesting details (if applicable)
- `delegation_{wallet_id}.json` - Delegation data (if applicable)
- `commitments_{wallet_id}.json` - Exchange commitments (if applicable)

## Real Data Patterns

All examples use realistic:
- **Amount distributions** based on actual network data
- **Vesting schedules** matching common patterns
- **Delegation patterns** across multiple validators
- **Asset combinations** found on Figure Markets
- **Timestamp patterns** with proper UTC formatting

## Usage in Testing

These examples enable comprehensive testing of:
- Logical attribute grouping completeness
- Denomination handling across all assets
- Singular/plural response variants
- Transformation accuracy
- Edge case handling