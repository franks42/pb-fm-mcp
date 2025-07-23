"""
Aggregate Functions for Common MCP Usage Patterns

These functions combine multiple individual API calls to provide comprehensive
data summaries that are especially useful for MCP agents. Each aggregate function
uses asyncio.gather() for concurrent API calls and provides comprehensive error handling.

All functions are decorated with @api_function to be automatically exposed via MCP and/or REST protocols.
"""

import asyncio
from typing import Any

import structlog

from functions.blockchain_functions import (
    fetch_account_info,
    fetch_account_is_vesting,
    fetch_available_committed_amount,
    fetch_total_delegation_data,
    fetch_vesting_total_unvested_amount,
)
from functions.figure_markets_functions import (
    fetch_current_fm_account_balance_data,
    fetch_current_fm_account_info,
    fetch_current_fm_data,
    fetch_figure_markets_assets_info,
    fetch_last_crypto_token_price,
)
from functions.stats_functions import fetch_current_hash_statistics, get_system_context
from registry import api_function
from utils import JSONType

# Set up logging
logger = structlog.get_logger()



@api_function(
    protocols=["mcp", "rest"],
    path="/api/fetch_complete_wallet_summary/{wallet_address}",
    description="Get comprehensive wallet summary including blockchain account info, delegation data, vesting info, and Figure Markets balance",
    tags=["aggregates", "wallet", "summary"]
)
async def fetch_complete_wallet_summary(wallet_address: str) -> JSONType:
    """
    Get comprehensive wallet summary including blockchain account info, delegation data,
    vesting info, and Figure Markets trading balance in a single call.
    
    This aggregate function makes concurrent calls to multiple APIs to provide a complete
    wallet overview, ideal for AI agents that need comprehensive wallet information.
    
    Args:
        wallet_address: Wallet's Bech32 address
        
    Returns:
        Dictionary containing comprehensive wallet information:
        - account_info: Basic account information from blockchain
        - is_vesting: Whether account has vesting tokens
        - vesting_data: Unvested amount if vesting account
        - available_committed: Available committed amount 
        - delegation_summary: Complete delegation data (staked, rewards, unbonding, etc.)
        - trading_balance: Figure Markets account balance
        - trading_account: Figure Markets account info
        - summary_totals: Calculated total values across all sources
    """
    logger.info(f"Fetching complete wallet summary for {wallet_address}")
    
    # Define all concurrent tasks
    tasks = [
        fetch_account_info(wallet_address),
        fetch_account_is_vesting(wallet_address), 
        fetch_total_delegation_data(wallet_address),
        fetch_current_fm_account_balance_data(wallet_address),
        fetch_current_fm_account_info(wallet_address)
    ]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Extract individual results with error handling
    account_info = results[0] if not isinstance(results[0], Exception) else {"MCP-ERROR": str(results[0])}
    is_vesting_result = results[1] if not isinstance(results[1], Exception) else {"MCP-ERROR": str(results[1])}
    delegation_data = results[2] if not isinstance(results[2], Exception) else {"MCP-ERROR": str(results[2])}
    trading_balance = results[3] if not isinstance(results[3], Exception) else {"MCP-ERROR": str(results[3])}
    trading_account = results[4] if not isinstance(results[4], Exception) else {"MCP-ERROR": str(results[4])}
    
    # Handle vesting-specific data if account is vesting
    vesting_data = {}
    available_committed = {}
    
    if is_vesting_result.get("is_vesting_account") is True:
        # Fetch additional vesting data concurrently
        vesting_tasks = [
            fetch_vesting_total_unvested_amount(wallet_address),
            fetch_available_committed_amount(wallet_address)
        ]
        
        vesting_results = await asyncio.gather(*vesting_tasks, return_exceptions=True)
        
        vesting_data = vesting_results[0] if not isinstance(vesting_results[0], Exception) else {"MCP-ERROR": str(vesting_results[0])}
        available_committed = vesting_results[1] if not isinstance(vesting_results[1], Exception) else {"MCP-ERROR": str(vesting_results[1])}
    
    # Calculate summary totals (only if no critical errors)
    summary_totals = {}
    
    if not delegation_data.get("MCP-ERROR") and not account_info.get("MCP-ERROR"):
        try:
            # Extract amounts from delegation data
            delegated_total = delegation_data.get("delegated_total_delegated_amount", 0)
            
            # Extract account balance
            account_balance = 0
            if account_info.get("account"):
                coins = account_info["account"].get("coins", [])
                for coin in coins:
                    if coin.get("denom") == "nhash":
                        account_balance = int(coin.get("amount", 0))
                        break
            
            # Extract trading balance
            trading_hash_balance = 0
            if not trading_balance.get("MCP-ERROR"):
                for balance in trading_balance.get("balances", []):
                    if balance.get("denom") == "nhash":
                        trading_hash_balance = int(balance.get("available", 0))
                        break
            
            # Calculate total wallet value
            total_hash_across_all_sources = account_balance + delegated_total + trading_hash_balance
            
            summary_totals = {
                "account_liquid_hash": account_balance,
                "delegation_total_hash": delegated_total, 
                "trading_liquid_hash": trading_hash_balance,
                "total_hash_all_sources": total_hash_across_all_sources
            }
            
            # Add vesting amounts if applicable
            if vesting_data and not vesting_data.get("MCP-ERROR"):
                vesting_amount = vesting_data.get("vesting_total_unvested_amount", 0)
                summary_totals["vesting_unvested_hash"] = vesting_amount
                summary_totals["total_hash_all_sources"] += vesting_amount
                
        except Exception as e:
            logger.error(f"Error calculating summary totals: {e}")
            summary_totals = {"MCP-ERROR": f"Error calculating totals: {e!s}"}
    
    return {
        "wallet_address": wallet_address,
        "account_info": account_info,
        "is_vesting": is_vesting_result,
        "vesting_data": vesting_data,
        "available_committed": available_committed,
        "delegation_summary": delegation_data,
        "trading_balance": trading_balance,
        "trading_account": trading_account,
        "summary_totals": summary_totals
    }


@api_function(
    protocols=["mcp", "rest"],
    path="/api/fetch_market_overview_summary",
    description="Get comprehensive market overview including Figure Markets data, HASH statistics, and trading assets",
    tags=["aggregates", "market", "overview"]
)
async def fetch_market_overview_summary() -> JSONType:
    """
    Get comprehensive market overview including Figure Markets data, HASH token statistics,
    trading assets, and key token prices in a single call.
    
    This aggregate function provides a complete market snapshot ideal for AI agents
    that need to understand current market conditions across all platforms.
    
    Returns:
        Dictionary containing comprehensive market information:
        - figure_markets_data: Trading pairs and market data
        - hash_statistics: Current HASH token statistics
        - trading_assets: Available trading assets information
        - key_token_prices: Prices for major tokens (HASH.USD, BTC.USD, ETH.USD)
        - system_context: Overall system information
    """
    logger.info("Fetching comprehensive market overview")
    
    # Define concurrent market data tasks
    tasks = [
        fetch_current_fm_data(),
        fetch_current_hash_statistics(), 
        fetch_figure_markets_assets_info(),
        get_system_context()
    ]
    
    # Execute market data tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Extract results with error handling
    fm_data = results[0] if not isinstance(results[0], Exception) else {"MCP-ERROR": str(results[0])}
    hash_stats = results[1] if not isinstance(results[1], Exception) else {"MCP-ERROR": str(results[1])}
    trading_assets = results[2] if not isinstance(results[2], Exception) else {"MCP-ERROR": str(results[2])}
    system_context = results[3] if not isinstance(results[3], Exception) else {"MCP-ERROR": str(results[3])}
    
    # Fetch key token prices concurrently
    price_tasks = [
        fetch_last_crypto_token_price("HASH-USD", 1),
        fetch_last_crypto_token_price("BTC-USD", 1), 
        fetch_last_crypto_token_price("ETH-USD", 1)
    ]
    
    price_results = await asyncio.gather(*price_tasks, return_exceptions=True)
    
    key_token_prices = {
        "HASH_USD": price_results[0] if not isinstance(price_results[0], Exception) else {"MCP-ERROR": str(price_results[0])},
        "BTC_USD": price_results[1] if not isinstance(price_results[1], Exception) else {"MCP-ERROR": str(price_results[1])},
        "ETH_USD": price_results[2] if not isinstance(price_results[2], Exception) else {"MCP-ERROR": str(price_results[2])}
    }
    
    return {
        "figure_markets_data": fm_data,
        "hash_statistics": hash_stats,
        "trading_assets": trading_assets,
        "key_token_prices": key_token_prices,
        "system_context": system_context
    }


# Large commented-out function removed to improve code maintainability