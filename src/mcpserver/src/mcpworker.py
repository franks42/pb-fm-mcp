"""
Standardized MCP Worker for Provenance Blockchain and Figure Markets APIs

This module implements MCP proxy functions that call the actual implementations
in pbapis.py. This architecture provides:

1. **Testability**: pbapis.py functions can be tested independently with local webserver
2. **Dual hosting**: Same functions available via MCP server + conventional JSON-RPC
3. **Maintainability**: Single source of truth for API logic in pbapis.py
4. **Docstring synchronization**: Proxy functions automatically inherit docstrings

Architecture Pattern:
- pbapis.py: Contains actual implementation logic (testable independently)
- mcpworker.py: Contains @mcp.tool() proxy functions (MCP server interface)
- Docstrings automatically copied from pbapis.py to ensure consistency
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
from . import pbapis

sys.path.insert(0, "/session/metadata/vendor")
sys.path.insert(0, "/session/metadata")

#########################################################################################
# MCP Server Setup
#########################################################################################

def setup_standardized_server():
    """
    Setup the standardized MCP server with proxy functions.
    
    All MCP functions are simple proxies to pbapis.py implementations,
    following the same pattern as worker.py -> hastra.py.
    """
    from mcp.server.fastmcp import FastMCP
    from starlette.middleware.cors import CORSMiddleware
    from exceptions import HTTPException, http_exception
    import httpx

    mcp = FastMCP("Hastra-FM-MCP-Standardized", stateless_http=True, json_response=True)

    #########################################################################################
    # MCP Proxy Functions - Simple passthrough to pbapis.py
    #########################################################################################

    @mcp.tool()
    async def get_system_context() -> Dict[str, str]:
        """Proxy to pbapis.get_system_context() - docstring automatically synchronized"""
        return await pbapis.get_system_context()

    @mcp.tool()
    async def get_hash_token_statistics() -> Dict[str, Any]:
        """Proxy to pbapis.get_hash_token_statistics() - docstring automatically synchronized"""
        return await pbapis.get_hash_token_statistics()

    @mcp.tool()
    async def get_account_vesting_status(account_address: str) -> Dict[str, Any]:
        """Proxy to pbapis.get_account_vesting_status() - docstring automatically synchronized"""
        return await pbapis.get_account_vesting_status(account_address)

    @mcp.tool()
    async def get_available_hash_balance(account_address: str) -> Dict[str, Any]:
        """Proxy to pbapis.get_available_hash_balance() - docstring automatically synchronized"""
        return await pbapis.get_available_hash_balance(account_address)

    @mcp.tool()
    async def get_complete_wallet_composition(account_address: str) -> Dict[str, Any]:
        """Proxy to pbapis.get_complete_wallet_composition() - docstring automatically synchronized"""
        return await pbapis.get_complete_wallet_composition(account_address)

    @mcp.tool()
    async def get_complete_vesting_status(account_address: str) -> Dict[str, Any]:
        """Proxy to pbapis.get_complete_vesting_status() - docstring automatically synchronized"""
        return await pbapis.get_complete_vesting_status(account_address)

    @mcp.tool()
    async def get_delegation_complete_picture(account_address: str) -> Dict[str, Any]:
        """Proxy to pbapis.get_delegation_complete_picture() - docstring automatically synchronized"""
        return await pbapis.get_delegation_complete_picture(account_address)

    @mcp.tool()
    async def get_multi_asset_balances(account_address: str, page_size: int = 20) -> Dict[str, Any]:
        """Proxy to pbapis.get_multi_asset_balances() - docstring automatically synchronized"""
        return await pbapis.get_multi_asset_balances(account_address, page_size)

    @mcp.tool()
    async def get_figure_markets_trading_price(token_pair: str, size: int = 1) -> Dict[str, Any]:
        """Proxy to pbapis.get_figure_markets_trading_price() - docstring automatically synchronized"""
        return await pbapis.get_figure_markets_trading_price(token_pair, size)

    @mcp.tool()
    async def get_denomination_conversion_table() -> Dict[str, Any]:
        """Proxy to pbapis.get_denomination_conversion_table_data() - docstring automatically synchronized"""
        return await pbapis.get_denomination_conversion_table_data()

    @mcp.tool()
    async def get_system_timezone_info() -> Dict[str, Any]:
        """Proxy to pbapis.get_system_timezone_info_data() - docstring automatically synchronized"""
        return await pbapis.get_system_timezone_info_data()

    @mcp.tool()
    async def validate_attribute_grouping(mcp_function_name: str) -> Dict[str, Any]:
        """Proxy to pbapis.validate_attribute_grouping() - docstring automatically synchronized"""
        return await pbapis.validate_attribute_grouping(mcp_function_name)

    @mcp.tool()
    async def get_portfolio_time_series_data(
        account_address: str,
        hours_back: int = 168,
        output_format: str = 'pandas_dataframe'
    ) -> Dict[str, Any]:
        """Proxy to pbapis.get_portfolio_time_series_data() - docstring automatically synchronized"""
        return await pbapis.get_portfolio_time_series_data(account_address, hours_back, output_format)

    @mcp.tool()
    async def get_multi_asset_correlation_data(
        account_addresses: List[str],
        include_market_data: bool = True,
        output_format: str = 'pandas_dataframe'
    ) -> Dict[str, Any]:
        """Proxy to pbapis.get_multi_asset_correlation_data() - docstring automatically synchronized"""
        return await pbapis.get_multi_asset_correlation_data(account_addresses, include_market_data, output_format)

    @mcp.tool()
    async def get_staking_performance_analytics(
        account_address: str,
        performance_period_hours: int = 720,
        output_format: str = 'pandas_dataframe'
    ) -> Dict[str, Any]:
        """Proxy to pbapis.get_staking_performance_analytics() - docstring automatically synchronized"""
        return await pbapis.get_staking_performance_analytics(account_address, performance_period_hours, output_format)

    @mcp.tool()
    async def list_available_functions() -> Dict[str, Any]:
        """Proxy to pbapis.list_available_functions() - docstring automatically synchronized"""
        return await pbapis.list_available_functions()

    #########################################################################################
    # Automatic Docstring Synchronization
    #########################################################################################

    # Copy docstrings from pbapis.py functions to maintain consistency
    # This ensures MCP function documentation matches the actual implementation
    
    get_system_context.__doc__ = pbapis.get_system_context.__doc__
    get_hash_token_statistics.__doc__ = pbapis.get_hash_token_statistics.__doc__
    get_account_vesting_status.__doc__ = pbapis.get_account_vesting_status.__doc__
    get_available_hash_balance.__doc__ = pbapis.get_available_hash_balance.__doc__
    get_complete_wallet_composition.__doc__ = pbapis.get_complete_wallet_composition.__doc__
    get_complete_vesting_status.__doc__ = pbapis.get_complete_vesting_status.__doc__
    get_delegation_complete_picture.__doc__ = pbapis.get_delegation_complete_picture.__doc__
    get_multi_asset_balances.__doc__ = pbapis.get_multi_asset_balances.__doc__
    get_figure_markets_trading_price.__doc__ = pbapis.get_figure_markets_trading_price.__doc__
    get_denomination_conversion_table.__doc__ = pbapis.get_denomination_conversion_table_data.__doc__
    get_system_timezone_info.__doc__ = pbapis.get_system_timezone_info_data.__doc__
    validate_attribute_grouping.__doc__ = pbapis.validate_attribute_grouping.__doc__
    get_portfolio_time_series_data.__doc__ = pbapis.get_portfolio_time_series_data.__doc__
    get_multi_asset_correlation_data.__doc__ = pbapis.get_multi_asset_correlation_data.__doc__
    get_staking_performance_analytics.__doc__ = pbapis.get_staking_performance_analytics.__doc__
    list_available_functions.__doc__ = pbapis.list_available_functions.__doc__

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

#########################################################################################
# Function for Testing Docstring Synchronization
#########################################################################################

def verify_docstring_sync():
    """
    Utility function to verify that all proxy functions have synchronized docstrings.
    
    This can be called during testing to ensure docstring consistency.
    """
    mcp, app = setup_standardized_server()
    
    # Get all MCP tools
    tools = mcp.get_tools()
    
    verification_results = {}
    
    for tool_name, tool_info in tools.items():
        if hasattr(pbapis, tool_name):
            pbapi_func = getattr(pbapis, tool_name)
            mcp_docstring = tool_info.get('description', '')
            pbapi_docstring = pbapi_func.__doc__ or ''
            
            verification_results[tool_name] = {
                'synchronized': mcp_docstring.strip() == pbapi_docstring.strip(),
                'mcp_docstring': mcp_docstring,
                'pbapi_docstring': pbapi_docstring
            }
    
    return verification_results

#########################################################################################
# Legacy Compatibility Support
#########################################################################################

# For backwards compatibility with existing transformation patterns
# These are kept for any functions that might need the old direct transformation approach

class PBAPITransformer:
    """
    Legacy transformation engine for backwards compatibility.
    
    NOTE: New functions should use the pbapis.py + grouped transformer approach.
    This is maintained only for compatibility with existing patterns.
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
    
    def transform_response(self, raw_response: Dict[str, Any], endpoint_name: str) -> Dict[str, Any]:
        """
        Legacy transformation method - use pbapis.py functions for new implementations.
        
        IMPORTANT: Automatically expands all base64-encoded values before transformation.
        """
        if raw_response.get("MCP-ERROR"):
            return {"error_message": raw_response["MCP-ERROR"]}
        
        # Expand base64 data
        from base64expand import base64expand
        expanded_response = base64expand(raw_response)
        
        # Apply basic transformation for hash statistics
        if endpoint_name == "hash_statistics":
            result = {}
            for raw_field, std_field in self.AMOUNT_FIELD_MAPPINGS.items():
                if raw_field in expanded_response:
                    raw_value = expanded_response[raw_field]
                    if isinstance(raw_value, dict) and 'amount' in raw_value:
                        result[std_field] = int(raw_value['amount'])
            return result
        
        return expanded_response