"""
Standardized MCP Worker for Provenance Blockchain and Figure Markets APIs

This module implements a fully standardized and consistent MCP server that transforms
raw Provenance Blockchain and Figure Markets API responses into AI-friendly formats
using the PB-FM-Hastra Field Registry naming conventions.

All field names, data types, and response structures follow the standardized data
dictionary to ensure consistent AI agent comprehension across all endpoints.
"""

import sys
from datetime import UTC, datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

# Import from main project (these modules remain in src/)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import utils
from base64expand import base64expand
from hastra_types import JSONType

# Import from mcpserver module
from .grouped_transformer import GroupedAttributeTransformer
from .state_management_functions import (
    get_denomination_conversion_table,
    get_system_timezone_info
)

sys.path.insert(0, "/session/metadata/vendor")
sys.path.insert(0, "/session/metadata")

#########################################################################################
# Data Transformation Engine
#########################################################################################

class PBAPITransformer:
    """
    Transformation engine for converting raw PB/FM API responses to standardized format.
    
    Uses the PB-FM-Hastra Field Registry to ensure consistent naming, data types,
    and response structures across all API endpoints.
    """
    
    # Amount field transformations - convert {amount: string, denom: string} to integer
    AMOUNT_FIELD_MAPPINGS = {
        'maxSupply': 'max_supply_nhash',
        'burned': 'burned_nhash', 
        'currentSupply': 'current_supply_nhash',
        'circulation': 'circulating_supply_nhash',
        'communityPool': 'community_pool_nhash',
        'bonded': 'bonded_nhash',
        'locked': 'locked_nhash'
    }
    
    # Direct field name mappings
    FIELD_MAPPINGS = {
        'isVesting': 'is_vesting',
        'wallet_is_vesting': 'is_vesting',
        'available_total_amount': 'available_total_amount_nhash',
        'available_committed_amount': 'available_committed_amount_nhash',
        'delegated_total_delegated_amount': 'delegated_total_amount_nhash',
        'delegated_staked_amount': 'delegated_staked_amount_nhash',
        'delegated_redelegated_amount': 'delegated_redelegated_amount_nhash',
        'delegated_rewards_amount': 'delegated_rewards_amount_nhash',
        'delegated_unbonding_amount': 'delegated_unbonding_amount_nhash',
        'delegated_earning_amount': 'delegated_earning_amount_nhash',
        'delegated_not_earning_amount': 'delegated_not_earning_amount_nhash',
        'vesting_original_amount': 'vesting_original_amount_nhash',
        'vesting_total_vested_amount': 'vesting_total_vested_amount_nhash',
        'vesting_total_unvested_amount': 'vesting_total_unvested_amount_nhash',
        'start_time': 'vesting_start_date',
        'end_time': 'vesting_end_date',
        'date_time': 'date_time_result',
        'acc_address': 'account_address',
        'address': 'account_address',
        'account_number': 'account_number',
        'sequence': 'sequence_number',
        'seq_number': 'sequence_number',
        'blockHeight': 'block_height',
        'block_time': 'block_time',
        'operator_address': 'validator_address',
        'name': 'asset_name',
        'description': 'asset_description',
        'displayName': 'asset_display_name',
        'type': 'asset_type',
        'exponent': 'asset_exponent',
        'provenanceMarkerName': 'asset_denom',
        'id': 'trading_pair_id',
        'denom': 'base_denom',
        'quoteDenum': 'quote_denom',
        'matches': 'trading_matches',
        'data': 'trading_pairs',
        'results': 'asset_balances'
    }
    
    # Fields to exclude from responses (superfluous for AI)
    EXCLUDED_FIELDS = {
        'lastUpdated', 'last_updated', 'validatorCount', 'validator_count',
        'bondedRatio', 'bonded_ratio', 'consensus_pubkey', 'pubkey'
    }
    
    # Denomination mappings for multi-asset balances
    DENOMINATION_MAPPINGS = {
        'nhash': 'amount_nhash',
        'neth.figure.se': 'amount_neth',
        'uusd.trading': 'amount_uusd', 
        'uusdc.figure.se': 'amount_uusdc',
        'nsol.figure.se': 'amount_nsol',
        'uxrp.figure.se': 'amount_uxrp',
        'uylds.fcc': 'amount_uylds'
    }
    
    def transform_response(self, raw_response: Dict[str, Any], endpoint_name: str) -> Dict[str, Any]:
        """
        Transform raw API response to standardized format.
        
        IMPORTANT: Automatically expands all base64-encoded values before transformation
        to ensure hidden data is captured and available for field extraction.
        
        Args:
            raw_response: Raw response from PB/FM API
            endpoint_name: Name of the endpoint for context-specific transformations
            
        Returns:
            Standardized response following Field Registry conventions
        """
        if raw_response.get("MCP-ERROR"):
            return {"error_message": raw_response["MCP-ERROR"]}
        
        # CRITICAL: Expand all base64-encoded values before transformation
        # This ensures that any relevant information hidden in base64 blobs is available
        from base64expand import base64expand
        expanded_response = base64expand(raw_response)
        
        # Apply endpoint-specific transformation (using expanded response)
        if endpoint_name == "hash_statistics":
            return self._transform_hash_statistics(expanded_response)
        elif endpoint_name == "account_balance_data":
            return self._transform_account_balance_data(expanded_response)
        elif endpoint_name == "vesting_data":
            return self._transform_vesting_data(expanded_response)
        elif endpoint_name == "delegation_data":
            return self._transform_delegation_data(expanded_response)
        elif endpoint_name == "asset_info":
            return self._transform_asset_info(expanded_response)
        elif endpoint_name == "trading_data":
            return self._transform_trading_data(expanded_response)
        else:
            return self._transform_generic(expanded_response)
    
    def _transform_hash_statistics(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Transform HASH token statistics response."""
        result = {}
        
        # Transform amount fields
        for raw_field, std_field in self.AMOUNT_FIELD_MAPPINGS.items():
            if raw_field in raw:
                raw_value = raw[raw_field]
                if isinstance(raw_value, dict) and 'amount' in raw_value:
                    result[std_field] = int(raw_value['amount'])
        
        return result
    
    def _transform_account_balance_data(self, raw: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transform account balance data response."""
        result = {"asset_balances": []}
        
        for balance_item in raw:
            denom = balance_item.get('denom', '')
            amount_str = balance_item.get('amount', '0')
            
            # Map denomination to standardized field name
            if denom in self.DENOMINATION_MAPPINGS:
                std_field = self.DENOMINATION_MAPPINGS[denom]
                standardized_balance = {
                    "asset_denom": denom,
                    std_field: int(amount_str) if amount_str.isdigit() else 0
                }
                result["asset_balances"].append(standardized_balance)
        
        return result
    
    def _transform_vesting_data(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Transform vesting data response."""
        result = {}
        
        # Apply direct field mappings
        for raw_field, std_field in self.FIELD_MAPPINGS.items():
            if raw_field in raw:
                result[std_field] = raw[raw_field]
        
        # Transform amount fields to integers with nhash suffix
        for field in ['vesting_original_amount', 'vesting_total_vested_amount', 'vesting_total_unvested_amount']:
            if field in raw:
                result[f"{field}_nhash"] = int(raw[field]) if isinstance(raw[field], (int, str)) else raw[field]
        
        return result
    
    def _transform_delegation_data(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Transform delegation data response."""
        result = {}
        
        # Transform delegation amount fields
        delegation_fields = [
            'delegated_staked_amount', 'delegated_redelegated_amount',
            'delegated_rewards_amount', 'delegated_unbonding_amount',
            'delegated_total_delegated_amount', 'delegated_earning_amount',
            'delegated_not_earning_amount'
        ]
        
        for field in delegation_fields:
            if field in raw:
                result[f"{field}_nhash"] = int(raw[field]) if isinstance(raw[field], (int, str)) else raw[field]
        
        # Rename delegated_total_delegated_amount to delegated_total_amount for consistency
        if 'delegated_total_delegated_amount_nhash' in result:
            result['delegated_total_amount_nhash'] = result.pop('delegated_total_delegated_amount_nhash')
        
        return result
    
    def _transform_asset_info(self, raw: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transform asset information response."""
        result = {"assets": []}
        
        for asset in raw:
            standardized_asset = {}
            for raw_field, std_field in self.FIELD_MAPPINGS.items():
                if raw_field in asset:
                    standardized_asset[std_field] = asset[raw_field]
            result["assets"].append(standardized_asset)
        
        return result
    
    def _transform_trading_data(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Transform trading/market data response."""
        result = {}
        
        # Apply direct field mappings
        for raw_field, std_field in self.FIELD_MAPPINGS.items():
            if raw_field in raw:
                result[std_field] = raw[raw_field]
        
        return result
    
    def _transform_generic(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Generic transformation for any response."""
        result = {}
        
        # Apply direct field mappings
        for raw_field, std_field in self.FIELD_MAPPINGS.items():
            if raw_field in raw:
                result[std_field] = raw[raw_field]
        
        # Filter out excluded fields
        for field in list(result.keys()):
            if field in self.EXCLUDED_FIELDS:
                del result[field]
        
        return result

#########################################################################################
# Helper Functions
#########################################################################################

def datetime_to_ms(dt: datetime) -> int:
    """Convert datetime to milliseconds since epoch."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return int(dt.timestamp() * 1000)

def ms_to_datetime(ms_timestamp: int, tz=UTC) -> datetime:
    """Convert milliseconds since epoch to datetime."""
    return datetime.fromtimestamp(ms_timestamp / 1000, tz=tz)

def current_ms() -> int:
    """Get current time in milliseconds since epoch."""
    return int(datetime.now(UTC).timestamp() * 1000)

#########################################################################################
# Standardized MCP Server Setup
#########################################################################################

def setup_standardized_server():
    """
    Setup the standardized MCP server with grouped transformations and logical attribute groupings.
    
    All functions follow the PB-FM-Hastra Field Registry naming conventions
    and return standardized, AI-friendly responses with logical attribute groupings.
    """
    from mcp.server.fastmcp import FastMCP
    from starlette.middleware.cors import CORSMiddleware
    from exceptions import HTTPException, http_exception
    import httpx
    import hastra

    mcp = FastMCP("Hastra-FM-MCP-Standardized", stateless_http=True, json_response=True)
    
    # Initialize grouped transformer with comprehensive transformation capabilities
    transformer = GroupedAttributeTransformer()
    legacy_transformer = PBAPITransformer()  # Keep for backwards compatibility

    async def async_http_get_json(
        url: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 10.0,
        connect_timeout: float = 5.0
    ) -> JSONType:
        """
        Standardized async HTTP GET with comprehensive error handling.
        
        IMPORTANT: Automatically expands all base64-encoded values in PB/FM API responses
        to ensure any relevant information hidden in base64 blobs is available.
        
        Returns either JSON data (with base64 expanded) or standardized error response with 'error_message' key.
        """
        if params is None:
            params = {}

        timeout_config = httpx.Timeout(timeout, connect=connect_timeout)
        headers = {"Accept": "application/json"}

        async with httpx.AsyncClient(timeout=timeout_config) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "")
                if not content_type.startswith("application/json"):
                    return {"error_message": f"Expected JSON, got {content_type}"}

                json_data = response.json()
                
                # CRITICAL: Expand all base64-encoded values in PB/FM API responses
                # This ensures that any relevant information hidden in base64 blobs is available
                # for subsequent transformation and analysis
                from base64expand import base64expand
                return base64expand(json_data)

            except httpx.TimeoutException:
                return {"error_message": "Network Error: Request timed out"}
            except httpx.HTTPStatusError as e:
                return {"error_message": f"HTTP error: {e.response.status_code}"}
            except httpx.RequestError as e:
                return {"error_message": f"Request error: {e}"}
            except ValueError as e:
                return {"error_message": f"Invalid JSON response: {e}"}
            except Exception as e:
                return {"error_message": f"Unknown exception raised: {e}"}

    #########################################################################################
    # Standardized MCP Tool Functions
    #########################################################################################

    @mcp.tool()
    async def get_system_context() -> Dict[str, str]:
        """
        Get essential system context for Figure Markets Exchange and Provenance Blockchain.
        
        REQUIRED READING: Contains critical usage guidelines, data handling protocols,
        and server capabilities that MUST be read before using any tools.
        
        Returns:
            Dict containing:
            - context: Complete system context as markdown formatted string
        """
        url = "https://raw.githubusercontent.com/franks42/FigureMarkets-MCP-Server/refs/heads/main/FigureMarketsContext.md"
        async with httpx.AsyncClient() as client:
            client.headers['accept-encoding'] = 'identity'
            r = await client.get(url)
            return {'context': r.text}

    @mcp.tool()
    async def get_hash_token_statistics() -> Dict[str, Any]:
        """
        Get current HASH token supply and distribution statistics.
        
        Returns comprehensive information about HASH token supply across different
        categories: total supply, burned tokens, circulating supply, and locked tokens.
        All amounts are in nhash base units (1 HASH = 1,000,000,000 nhash).
        
        Returns:
            Dict containing:
            - max_supply_nhash: Total HASH tokens ever created (integer)
            - burned_nhash: Total HASH tokens permanently removed from circulation (integer)
            - current_supply_nhash: Current total supply (max_supply - burned) (integer)
            - circulating_supply_nhash: HASH tokens available for trading/transfer (integer)
            - community_pool_nhash: HASH tokens managed by Provenance Foundation (integer)
            - bonded_nhash: HASH tokens staked with validators for network security (integer)
            - locked_nhash: HASH tokens subject to vesting schedules (integer, calculated)
        """
        url = "https://service-explorer.provenance.io/api/v3/utility_token/stats"
        response = await async_http_get_json(url)
        
        if response.get("error_message"):
            return response
        
        # Add calculated locked field before transformation
        response["locked"] = {
            "amount": str(int(response["currentSupply"]["amount"]) -
                         int(response["circulation"]["amount"]) -
                         int(response["communityPool"]["amount"]) -
                         int(response["bonded"]["amount"])),
            "denom": "nhash"
        }
        
        return legacy_transformer.transform_response(response, "hash_statistics")

    @mcp.tool()
    async def get_account_vesting_status(account_address: str) -> Dict[str, Any]:
        """
        Check if account has active vesting restrictions.
        
        Args:
            account_address: Bech32-encoded Provenance account address (e.g., 'tp1abc...')
            
        Returns:
            Dict containing:
            - is_vesting: Boolean indicating if account has vesting restrictions
            - account_address: The queried account address
        """
        url = f"https://service-explorer.provenance.io/api/v2/accounts/{account_address}"
        response = await async_http_get_json(url)
        
        if response.get("error_message"):
            return response
            
        return {
            "is_vesting": response.get('flags', {}).get('isVesting', False),
            "account_address": account_address
        }

    @mcp.tool()
    async def get_available_hash_balance(account_address: str) -> Dict[str, Any]:
        """
        Get available HASH balance in account wallet.
        
        Returns the total available HASH amount which equals:
        available_spendable + available_committed + available_unvested
        
        Note: This does NOT include delegated HASH. Use get_delegation_data() for that.
        
        Args:
            account_address: Bech32-encoded Provenance account address
            
        Returns:
            Dict containing:
            - available_total_amount_nhash: Total available HASH in wallet (integer)
            - account_address: The queried account address
        """
        url = f"https://service-explorer.provenance.io/api/v2/accounts/{account_address}/balances"
        params = {"count": 20, "page": 1}
        response = await async_http_get_json(url, params=params)
        
        if response.get("error_message"):
            return response
            
        balance_list = response.get('results', [])
        for balance_item in balance_list:
            if balance_item.get('denom') == "nhash":
                return {
                    'available_total_amount_nhash': int(balance_item.get('amount', 0)),
                    'account_address': account_address
                }
        
        return {
            "error_message": "No HASH balance found for account",
            "account_address": account_address
        }

    @mcp.tool()
    async def get_complete_wallet_composition(account_address: str) -> Dict[str, Any]:
        """
        Get complete wallet composition showing all HASH holdings across different states.
        
        Combines available, committed, and delegated amounts for comprehensive wallet picture.
        Returns the 'wallet_composition_complete' logical attribute group.
        
        Args:
            account_address: Bech32-encoded Provenance account address
            
        Returns:
            Dict containing complete wallet composition:
            - available_total_amount_nhash: HASH available in wallet for transactions
            - available_committed_amount_nhash: HASH committed to Figure Markets exchange
            - delegated_total_amount_nhash: Total HASH delegated to validators
            - delegated_staked_amount_nhash: HASH earning staking rewards
            - delegated_rewards_amount_nhash: Pending staking rewards
            - delegated_unbonding_amount_nhash: HASH in unbonding period
            - wallet_total_amount_nhash: Sum of all HASH (calculated field)
            - wallet_earning_amount_nhash: HASH currently earning rewards (calculated)
            - account_address: The queried account address
        """
        # Collect required API responses
        api_responses = {}
        
        # Get account balances
        balances_url = f"https://service-explorer.provenance.io/api/v2/accounts/{account_address}/balances"
        balances_response = await async_http_get_json(balances_url, {"count": 20, "page": 1})
        if balances_response.get("error_message"):
            return balances_response
        api_responses['pb_account_balances_call'] = balances_response
        
        # Get delegation data from hastra function
        delegation_data = await hastra.fetch_total_delegation_data(account_address)
        if delegation_data.get("error_message"):
            return delegation_data
        api_responses['pb_delegation_info_call'] = delegation_data
        
        # Get exchange commitments
        commitments_url = f"https://api.provenance.io/provenance/exchange/v1/commitments/account/{account_address}"
        commitments_response = await async_http_get_json(commitments_url)
        if commitments_response.get("error_message"):
            return commitments_response
        api_responses['fm_exchange_commitments_call'] = commitments_response
        
        # Transform using grouped transformer
        result = transformer.transform_grouped_response(
            'get_complete_wallet_composition',
            api_responses,
            {'account_address': account_address},
            stateless_optimized=True
        )
        
        return result
    
    @mcp.tool()
    async def get_complete_vesting_status(account_address: str) -> Dict[str, Any]:
        """
        Get comprehensive vesting status including schedule details and current state.
        
        Returns the 'vesting_complete_picture' logical attribute group with all
        vesting-related information required for complete understanding.
        
        Args:
            account_address: Bech32-encoded Provenance account address
            
        Returns:
            Dict containing complete vesting information:
            - is_vesting: Boolean indicating if account has vesting restrictions
            - vesting_original_amount_nhash: Original amount subject to vesting
            - vesting_total_vested_amount_nhash: Amount already vested (available)
            - vesting_total_unvested_amount_nhash: Amount still subject to vesting
            - vesting_start_date: ISO timestamp when vesting began
            - vesting_end_date: ISO timestamp when vesting completes
            - vesting_progress_percentage: Calculated progress (0-100)
            - account_address: The queried account address
        """
        # Check if account has vesting first
        account_url = f"https://service-explorer.provenance.io/api/v2/accounts/{account_address}"
        account_response = await async_http_get_json(account_url)
        if account_response.get("error_message"):
            return account_response
            
        is_vesting = account_response.get('flags', {}).get('isVesting', False)
        
        if not is_vesting:
            return {
                "is_vesting": False,
                "account_address": account_address,
                "_metadata": {
                    "message": "Account does not have vesting restrictions",
                    "logical_group": "vesting_complete_picture"
                }
            }
        
        # Get detailed vesting information
        api_responses = {}
        api_responses['pb_account_info_call'] = account_response
        
        vesting_url = f"https://service-explorer.provenance.io/api/v3/accounts/{account_address}/vesting"
        vesting_response = await async_http_get_json(vesting_url)
        if vesting_response.get("error_message"):
            return vesting_response
        api_responses['pb_vesting_info_call'] = vesting_response
        
        # Transform using grouped transformer
        result = transformer.transform_grouped_response(
            'get_complete_vesting_status',
            api_responses,
            {'account_address': account_address},
            stateless_optimized=True
        )
        
        return result
    
    @mcp.tool()
    async def get_delegation_complete_picture(account_address: str) -> Dict[str, Any]:
        """
        Get complete delegation information including all validator relationships and rewards.
        
        Returns the 'delegation_complete_picture' logical attribute group with comprehensive
        delegation data for understanding staking position and earnings.
        
        Args:
            account_address: Bech32-encoded Provenance account address
            
        Returns:
            Dict containing complete delegation information:
            - delegated_total_amount_nhash: Total HASH delegated across all validators
            - delegated_staked_amount_nhash: HASH actively staked and earning rewards
            - delegated_redelegated_amount_nhash: HASH in redelegation process
            - delegated_rewards_amount_nhash: Pending rewards across all validators
            - delegated_unbonding_amount_nhash: HASH in unbonding period
            - delegated_earning_amount_nhash: HASH currently earning rewards (active stake)
            - delegated_not_earning_amount_nhash: HASH not earning (redelegating/unbonding)
            - account_address: The queried account address
        """
        # Get delegation data from hastra function
        delegation_data = await hastra.fetch_total_delegation_data(account_address)
        if delegation_data.get("error_message"):
            return delegation_data
        
        api_responses = {'pb_delegation_info_call': delegation_data}
        
        # Transform using grouped transformer
        result = transformer.transform_grouped_response(
            'get_delegation_complete_picture',
            api_responses,
            {'account_address': account_address},
            stateless_optimized=True
        )
        
        return result
    
    @mcp.tool()
    async def get_multi_asset_balances(account_address: str, page_size: int = 20) -> Dict[str, Any]:
        """
        Get all asset balances for account (HASH, USD, ETH, SOL, XRP, YLDS).
        
        Returns standardized multi-asset balance information with proper denomination handling.
        Supports both singular (one asset) and plural (multiple assets) response variants.
        
        Args:
            account_address: Bech32-encoded Provenance account address
            page_size: Number of balance records to return (1-100)
            
        Returns:
            Dict containing asset balances:
            - asset_balances: List of balance objects, each containing:
              - asset_denom: Base denomination (nhash, uusd.trading, etc.)
              - amount_[denom]: Amount in base units with denomination suffix
            - total_assets_count: Number of different assets held
            - account_address: The queried account address
        """
        url = f"https://service-explorer.provenance.io/api/v2/accounts/{account_address}/balances"
        params = {"count": min(max(page_size, 1), 100), "page": 1}
        
        response = await async_http_get_json(url, params=params)
        if response.get("error_message"):
            return response
        
        api_responses = {'pb_account_balances_call': response}
        
        # Transform using grouped transformer
        result = transformer.transform_grouped_response(
            'get_multi_asset_balances',
            api_responses,
            {'account_address': account_address, 'page_size': page_size},
            stateless_optimized=True
        )
        
        return result
    
    @mcp.tool()
    async def get_figure_markets_trading_price(token_pair: str, size: int = 1) -> Dict[str, Any]:
        """
        Get recent trading prices for token pair with singular/plural variants.
        
        Returns standardized trading data with proper handling of size parameter affecting
        response structure (size=1 returns single object, size>1 returns array).
        
        Args:
            token_pair: Trading pair identifier (e.g., 'HASH-USD', 'ETH-USD')
            size: Number of recent trades to return (1-100)
            
        Returns:
            Dict containing trading information:
            For size=1 (singular):
            - latest_trade_price_usd: Most recent trade price in USD
            - latest_trade_size_nhash: Most recent trade size in base units
            - latest_trade_timestamp: ISO timestamp of most recent trade
            - trading_pair_id: Trading pair identifier
            
            For size>1 (plural):
            - trading_matches: Array of trade objects
            - trades_count: Number of trades returned
            - price_range_high_usd: Highest price in period
            - price_range_low_usd: Lowest price in period
            - trading_pair_id: Trading pair identifier
        """
        url = f"https://figuremarkets.com/service-hft-exchange/api/v1/trades/{token_pair}"
        params = {"size": min(max(size, 1), 100)}
        
        response = await async_http_get_json(url, params=params)
        if response.get("error_message"):
            return response
        
        api_responses = {'fm_trading_data_call': response}
        
        # Transform using grouped transformer with size-aware processing
        result = transformer.transform_grouped_response(
            'get_figure_markets_trading_price',
            api_responses,
            {'token_pair': token_pair, 'size': size},
            stateless_optimized=True
        )
        
        return result
    
    @mcp.tool()
    async def get_denomination_conversion_table() -> Dict[str, Any]:
        """
        Get denomination conversion table for AI agent caching.
        
        Returns comprehensive conversion information for all supported assets
        to enable local conversions by AI agents in stateless server environment.
        
        Returns:
            Dict containing conversion information:
            - conversion_table: Complete denomination conversion data
            - supported_assets: List of all supported assets
            - exponent_mapping: Asset exponents for calculations
            - base_denominations: Map of display symbols to base denominations
            - cache_duration_seconds: Recommended cache duration
        """
        return get_denomination_conversion_table()
    
    @mcp.tool()
    async def get_system_timezone_info() -> Dict[str, Any]:
        """
        Get system timezone information for AI agent caching.
        
        Returns timezone conversion data to enable local timestamp conversions
        by AI agents in stateless server environment.
        
        Returns:
            Dict containing timezone information:
            - server_timezone: Server timezone identifier
            - utc_offset_seconds: Current UTC offset
            - timezone_abbreviation: Standard timezone abbreviation
            - supported_timezones: List of common timezone identifiers
            - cache_duration_seconds: Recommended cache duration
        """
        return get_system_timezone_info()
    
    @mcp.tool()
    async def validate_attribute_grouping(mcp_function_name: str) -> Dict[str, Any]:
        """
        Validate and explain attribute grouping for an MCP function.
        
        Provides detailed information about logical attribute groups, API efficiency,
        and bandwidth optimization for educational and debugging purposes.
        
        Args:
            mcp_function_name: Name of MCP function to analyze
            
        Returns:
            Dict containing grouping analysis:
            - function_info: Function description and reasoning
            - logical_groups: Detailed logical group information
            - api_efficiency: API call optimization analysis
            - bandwidth_optimization: Data filtering information
        """
        try:
            explanation = transformer.explain_attribute_grouping(mcp_function_name)
            return {
                "function_info": {
                    "name": explanation['function_name'],
                    "description": explanation['description'],
                    "reasoning": explanation['reasoning']
                },
                "logical_groups": explanation['logical_groups'],
                "api_efficiency": explanation['api_efficiency'],
                "validation_status": "success"
            }
        except ValueError as e:
            return {
                "error_message": str(e),
                "available_functions": [
                    "get_complete_wallet_composition",
                    "get_complete_vesting_status", 
                    "get_delegation_complete_picture",
                    "get_multi_asset_balances",
                    "get_figure_markets_trading_price"
                ]
            }

    #########################################################################################
    # Server Configuration
    #########################################################################################

    app = mcp.streamable_http_app()
    app.add_exception_handler(HTTPException, http_exception)
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )
    
    return mcp, app

#########################################################################################
# Entry Point
#########################################################################################

async def on_fetch(request, env, ctx):
    """Cloudflare Workers entry point."""
    mcp, app = setup_standardized_server()
    import asgi
    return await asgi.fetch(app, request, env, ctx)