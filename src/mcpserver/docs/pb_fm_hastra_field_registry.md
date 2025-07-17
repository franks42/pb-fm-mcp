# PB-FM-Hastra Field Registry

This is the authoritative registry of ALL field names, parameter names, and attribute names used across the Provenance Blockchain, Figure Markets, and Hastra ecosystem. Every name must be unique and consistently used across functions, APIs, docstrings, documentation, and AI-context documents.

## Field Registry Table

| Name | Short Description | Long Description | Data Type | Denomination | PB-Equivalent | Usage Context |
|------|------------------|------------------|-----------|--------------|---------------|---------------|
| **account_address** | Wallet address | Bech32-encoded Provenance blockchain account address | string | - | address, acc_address, account_address | Parameters, Returns |
| **account_number** | Account ID | Unique numeric identifier for blockchain account | integer | - | account_number, acc_number | Returns |
| **sequence_number** | Transaction sequence | Account transaction sequence number for nonce | integer | - | sequence, seq_number, sequence_number | Returns |
| **wallet_address** | Wallet address param | Parameter name for wallet address in function calls | string | - | address, acc_address | Parameters |
| **is_vesting** | Vesting status | Boolean indicating if account has active vesting restrictions | boolean | - | isVesting, vesting, has_vesting | Returns |
| **wallet_is_vesting** | Legacy vesting flag | Legacy return field name for vesting status (deprecated) | boolean | - | isVesting | Returns (deprecated) |
| | | | | | | |
| **max_supply_nhash** | Max HASH supply | Maximum HASH tokens that can ever exist | integer | nhash | maxSupply.amount | Returns |
| **current_supply_nhash** | Current HASH supply | Current total HASH supply (max_supply - burned) | integer | nhash | currentSupply.amount | Returns |
| **circulating_supply_nhash** | Circulating HASH | HASH tokens available for trading and transfer | integer | nhash | circulation.amount | Returns |
| **burned_nhash** | Burned HASH | HASH tokens permanently removed from circulation | integer | nhash | burned.amount | Returns |
| **community_pool_nhash** | Community pool HASH | HASH tokens managed by Provenance governance | integer | nhash | communityPool.amount | Returns |
| **bonded_nhash** | Bonded HASH | HASH tokens staked with validators for network security | integer | nhash | bonded.amount | Returns |
| **locked_nhash** | Locked HASH | HASH tokens locked in vesting schedules (calculated) | integer | nhash | locked.amount (calculated) | Returns |
| | | | | | | |
| **available_total_amount_nhash** | Total available HASH | All HASH available in wallet (spendable + committed + unvested) | integer | nhash | available_total_amount | Returns |
| **available_spendable_amount_nhash** | Spendable HASH | HASH tokens immediately spendable | integer | nhash | spendable, available_spendable | Returns |
| **available_committed_amount_nhash** | Committed HASH | HASH tokens committed to Figure Markets exchange | integer | nhash | available_committed_amount | Returns |
| **available_unvested_amount_nhash** | Unvested available HASH | Available HASH subject to vesting restrictions | integer | nhash | unvested, available_unvested | Returns |
| | | | | | | |
| **delegated_total_amount_nhash** | Total delegated HASH | All HASH delegated to validators | integer | nhash | delegated, delegated_total, delegated_total_delegated_amount | Returns |
| **delegated_staked_amount_nhash** | Staked HASH | HASH actively staked and earning rewards | integer | nhash | staked, delegated_staked_amount | Returns |
| **delegated_rewards_amount_nhash** | Reward HASH | Accumulated staking rewards (not earning additional rewards) | integer | nhash | rewards, delegated_rewards_amount | Returns |
| **delegated_redelegated_amount_nhash** | Redelegated HASH | HASH in 21-day redelegation transition (earning rewards) | integer | nhash | redelegated, delegated_redelegated_amount | Returns |
| **delegated_unbonding_amount_nhash** | Unbonding HASH | HASH in 21-day unbonding period (not earning rewards) | integer | nhash | unbonding, delegated_unbonding_amount | Returns |
| **delegated_earning_amount_nhash** | Earning delegated HASH | Delegated HASH earning rewards (staked + redelegated) | integer | nhash | delegated_earning_amount | Returns |
| **delegated_not_earning_amount_nhash** | Non-earning delegated HASH | Delegated HASH not earning rewards (rewards + unbonding) | integer | nhash | delegated_not_earning_amount | Returns |
| | | | | | | |
| **vesting_original_amount_nhash** | Original vesting amount | Initial HASH amount when vesting period started | integer | nhash | vesting_original_amount | Returns |
| **vesting_total_vested_amount_nhash** | Total vested HASH | HASH amount that has completed vesting as of date | integer | nhash | vesting_total_vested_amount | Returns |
| **vesting_total_unvested_amount_nhash** | Total unvested HASH | HASH amount still subject to vesting schedule | integer | nhash | vesting_total_unvested_amount | Returns |
| **vesting_coverage_deficit_nhash** | Vesting coverage deficit | Unvested HASH not covered by delegation (can be negative) | integer | nhash | calculated field | Returns |
| **vesting_start_date** | Vesting start date | ISO timestamp when vesting period began | string | - | start_time, vesting_start | Returns |
| **vesting_end_date** | Vesting end date | ISO timestamp when vesting period completes | string | - | end_time, vesting_end | Returns |
| | | | | | | |
| **controllable_hash_nhash** | Controllable HASH | HASH tokens user can freely control (spend/delegate) | integer | nhash | calculated field | Returns |
| **wallet_total_amount_nhash** | Total wallet HASH | Total HASH in wallet (all categories combined) | integer | nhash | total, wallet_total | Returns |
| | | | | | | |
| **block_height** | Block number | Current blockchain block number | integer | - | blockHeight, block_number, height | Returns |
| **block_time** | Block timestamp | ISO timestamp of block creation | string | - | block_time, timestamp | Returns |
| **validator_address** | Validator address | Bech32-encoded validator operator address | string | - | operator_address, validator_address | Returns |
| | | | | | | |
| **amount_neth** | Ethereum amount | Amount in nano-Ethereum base units | integer | neth.figure.se | amount (when denom=neth.figure.se) | Returns |
| **amount_uusd** | USD amount | Amount in micro-USD base units | integer | uusd.trading | amount (when denom=uusd.trading) | Returns |
| **amount_uusdc** | USDC amount | Amount in micro-USDC base units | integer | uusdc.figure.se | amount (when denom=uusdc.figure.se) | Returns |
| **amount_nsol** | Solana amount | Amount in nano-Solana base units | integer | nsol.figure.se | amount (when denom=nsol.figure.se) | Returns |
| **amount_uxrp** | XRP amount | Amount in micro-XRP base units | integer | uxrp.figure.se | amount (when denom=uxrp.figure.se) | Returns |
| **amount_uylds** | YLDS amount | Amount in micro-YLDS base units | integer | uylds.fcc | amount (when denom=uylds.fcc) | Returns |
| | | | | | | |
| **asset_name** | Asset identifier | Primary identifier to use for asset | string | - | name | Returns |
| **asset_description** | Asset description | Detailed description of the asset | string | - | description | Returns |
| **asset_display_name** | Asset display name | Human-readable display name for asset | string | - | displayName | Returns |
| **asset_type** | Asset type | Asset category: CRYPTO, STABLECOIN, or FUND | string | - | type | Returns |
| **asset_exponent** | Asset exponent | Decimal exponent for amount conversion (10^exponent) | integer | - | exponent | Returns |
| **asset_denom** | Asset denomination | Technical denomination identifier | string | - | provenanceMarkerName | Returns |
| | | | | | | |
| **trading_pair_id** | Trading pair ID | Unique identifier for trading pair | string | - | id | Returns |
| **base_denom** | Base token | Base token name in trading pair | string | - | denom | Returns |
| **quote_denom** | Quote currency | Quote currency denomination in trading pair | string | - | quoteDenum | Returns |
| **trading_matches** | Trade matches | List of individual trade execution details | list | - | matches | Returns |
| **trading_pairs** | Trading pairs | List of available trading pair information | list | - | data | Returns |
| **asset_balances** | Asset balances | List of balance information for all assets | list | - | results | Returns |
| | | | | | | |
| **token_pair** | Token pair param | Trading pair parameter (e.g., 'HASH-USD') | string | - | - | Parameters |
| **last_number_of_trades** | Trade count param | Number of recent trades to return | integer | - | size | Parameters |
| **date_time** | Date time param | ISO 8601 timestamp for vesting calculations | string | - | - | Parameters |
| **date_time_result** | Date time result | ISO timestamp for which vesting info was calculated | string | - | date_time | Returns |
| | | | | | | |
| **context** | System context | Complete system context markdown documentation | string | - | - | Returns |
| **error_message** | Error message | Standardized error message for failed operations | string | - | MCP-ERROR | Returns |

## Naming Convention Rules

### 1. Field Name Structure
- **Format**: `{category}_{subcategory}_{unit}` (if applicable)
- **Examples**: 
  - `delegated_staked_amount_nhash`
  - `vesting_start_date`
  - `asset_display_name`

### 2. Denomination Suffixes
- **nhash**: All HASH amounts in nano-HASH base units
- **neth**: Ethereum amounts in nano-ETH base units
- **uusd**: USD amounts in micro-USD base units
- **uusdc**: USDC amounts in micro-USDC base units
- **nsol**: Solana amounts in nano-SOL base units
- **uxrp**: XRP amounts in micro-XRP base units
- **uylds**: YLDS amounts in micro-YLDS base units

### 3. Category Prefixes
- **available_**: HASH available in wallet (not delegated)
- **delegated_**: HASH delegated to validators
- **vesting_**: Vesting-related information
- **asset_**: Asset/token metadata
- **trading_**: Trading and market data
- **account_**: Account identification
- **wallet_**: Wallet-specific parameters

### 4. Data Type Standards
- **integer**: All token amounts in base units
- **string**: Addresses (bech32), timestamps (ISO 8601), identifiers
- **boolean**: Status flags (is_vesting, etc.)
- **list**: Collections of objects

### 5. Consistency Requirements
- **Function parameters**: Use exact names from this registry
- **Return values**: Use exact names from this registry
- **Documentation**: Reference exact names from this registry
- **API responses**: Transform to exact names from this registry
- **Error messages**: Reference exact names from this registry

## Deprecated/Legacy Names

These names should be phased out in favor of standardized names:

| Deprecated Name | Standardized Name | Reason |
|-----------------|-------------------|---------|
| wallet_is_vesting | is_vesting | Redundant "wallet_" prefix |
| available_total_amount | available_total_amount_nhash | Missing denomination suffix |
| delegated_total_delegated_amount | delegated_total_amount_nhash | Redundant "delegated_" repetition |
| start_time | vesting_start_date | Ambiguous context |
| end_time | vesting_end_date | Ambiguous context |
| acc_address | account_address | Abbreviated form |
| denom | base_denom or quote_denom | Context-specific naming |

## Usage Validation

Before adding any new field name:
1. **Check uniqueness**: Ensure name doesn't exist in registry
2. **Follow conventions**: Use established prefixes and suffixes
3. **Add to registry**: Document in this table with all required columns
4. **Update functions**: Use exact name across all code
5. **Update documentation**: Reference exact name in all docs