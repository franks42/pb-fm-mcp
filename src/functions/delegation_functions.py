"""
Delegation Functions for Provenance Blockchain

Functions for fetching validator delegation data including staking, rewards, unbonding, and redelegation.
Functions are decorated with @api_function to be automatically exposed via MCP and/or REST protocols.
"""

import asyncio
from typing import Dict, Any
import httpx
import structlog

# Handle import for both relative and absolute path contexts
try:
    from ..registry import api_function
except ImportError:
    try:
        from registry import api_function
    except ImportError:
        from src.registry import api_function

# Set up logging
logger = structlog.get_logger()

# Type alias for JSON response
JSONType = Dict[str, Any]

# Helper function for async HTTP GET requests (reused from stats_functions)
async def async_http_get_json(url: str, params=None) -> JSONType:
    """
    Helper function for async HTTP GET requests with JSON response.
    
    Args:
        url: The URL to fetch
        params: Optional query parameters
        
    Returns:
        JSON response as dictionary or error dict
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching {url}: {e}")
        return {"MCP-ERROR": f"HTTP error: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        return {"MCP-ERROR": f"Unexpected error: {str(e)}"}


#########################################################################################
# Individual Delegation Detail Functions (REST API only)
#########################################################################################

@api_function(
    protocols=["rest"],
    path="/api/delegated_rewards_amount/{wallet_address}",
    method="GET", 
    tags=["delegation", "rewards"],
    description="Fetch delegated rewards amount for a wallet address"
)
async def fetch_delegated_rewards_amount(wallet_address: str) -> JSONType:
    """
    For the given wallet address, fetch the current total amount of earned rewards
    from the staked/delegated HASH with validators.
    
    Args:
        wallet_address: Wallet's Bech32 address
        
    Returns:
        Dictionary containing:
        - delegated_rewards_amount: Total amount of rewarded HASH
        - denom: HASH denomination (nhash)
        
    Raises:
        HTTPError: If the Provenance blockchain API is unavailable
    """
    url = f"https://service-explorer.provenance.io/api/v2/accounts/{wallet_address}/rewards"
    response = await async_http_get_json(url)
    
    if response.get("MCP-ERROR"):
        return response
    
    # Extract rewards data
    try:
        rewards_data = response.get("rewards", [])
        total_rewards = sum(int(reward.get("amount", 0)) for reward in rewards_data)
        
        return {
            "delegated_rewards_amount": {
                "amount": total_rewards,
                "denom": "nhash"
            }
        }
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Could not parse rewards data: {e}")
        return {"MCP-ERROR": f"Data parsing error: {str(e)}"}


@api_function(
    protocols=["rest"],
    path="/api/delegated_staked_amount/{wallet_address}",
    method="GET",
    tags=["delegation", "staking"],
    description="Fetch delegated staked amount for a wallet address"
)
async def fetch_delegated_staked_amount(wallet_address: str) -> JSONType:
    """
    For the given wallet address, fetch the current total amount of staked HASH
    with validators.
    
    Args:
        wallet_address: Wallet's Bech32 address
        
    Returns:
        Dictionary containing:
        - staking_validators: Number of validators used for staking
        - delegated_staked_amount: Total amount of staked HASH
        - denom: HASH denomination (nhash)
        
    Raises:
        HTTPError: If the Provenance blockchain API is unavailable
    """
    url = f"https://service-explorer.provenance.io/api/v2/accounts/{wallet_address}/delegations"
    response = await async_http_get_json(url)
    
    if response.get("MCP-ERROR"):
        return response
        
    # Extract delegation data
    try:
        delegations = response.get("results", [])
        total_staked = sum(int(delegation.get("amount", {}).get("amount", 0)) for delegation in delegations)
        validator_count = len(delegations)
        
        return {
            "staking_validators": validator_count,
            "delegated_staked_amount": {
                "amount": total_staked,
                "denom": "nhash"
            }
        }
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Could not parse delegation data: {e}")
        return {"MCP-ERROR": f"Data parsing error: {str(e)}"}


@api_function(
    protocols=["rest"],
    path="/api/delegated_unbonding_amount/{wallet_address}",
    method="GET",
    tags=["delegation", "unbonding"],
    description="Fetch delegated unbonding amount for a wallet address"
)
async def fetch_delegated_unbonding_amount(wallet_address: str) -> JSONType:
    """
    For the given wallet address, fetch the current total amount of HASH
    that is unbonding with validators.
    
    Args:
        wallet_address: Wallet's Bech32 address
        
    Returns:
        Dictionary containing:
        - delegated_unbonding_amount: Total amount of unbonding HASH
        - denom: HASH denomination (nhash)
        
    Raises:
        HTTPError: If the Provenance blockchain API is unavailable
    """
    url = f"https://service-explorer.provenance.io/api/v2/accounts/{wallet_address}/unbonding"
    response = await async_http_get_json(url)
    
    if response.get("MCP-ERROR"):
        return response
        
    # Extract unbonding data
    try:
        rollup_totals = response.get('rollupTotals', {})
        unbonding_total = rollup_totals.get('unbondingTotal', {'amount': '0', 'denom': 'nhash'})
        
        return {
            "delegated_unbonding_amount": {
                "amount": int(unbonding_total['amount']),
                "denom": unbonding_total['denom']
            }
        }
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Could not parse unbonding data: {e}")
        return {"MCP-ERROR": f"Data parsing error: {str(e)}"}


@api_function(
    protocols=["rest"],
    path="/api/delegated_redelegation_amount/{wallet_address}",
    method="GET",
    tags=["delegation", "redelegation"],
    description="Fetch delegated redelegation amount for a wallet address"
)
async def fetch_delegated_redelegation_amount(wallet_address: str) -> JSONType:
    """
    For the given wallet address, fetch the current total amount of HASH
    that is redelegated with validators.
    
    Args:
        wallet_address: Wallet's Bech32 address
        
    Returns:
        Dictionary containing:
        - delegated_redelegated_amount: Total amount of redelegated HASH
        - denom: HASH denomination (nhash)
        
    Raises:
        HTTPError: If the Provenance blockchain API is unavailable
    """
    url = f"https://service-explorer.provenance.io/api/v2/accounts/{wallet_address}/redelegations"
    response = await async_http_get_json(url)
    
    if response.get("MCP-ERROR"):
        return response
        
    # Extract redelegation data
    try:
        rollup_totals = response.get('rollupTotals', {})
        redelegation_total = rollup_totals.get('redelegationTotal', {'amount': '0', 'denom': 'nhash'})
        
        return {
            "delegated_redelegated_amount": {
                "amount": int(redelegation_total['amount']),
                "denom": redelegation_total['denom']
            }
        }
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Could not parse redelegation data: {e}")
        return {"MCP-ERROR": f"Data parsing error: {str(e)}"}


# Note: The comprehensive total delegation function is now in blockchain_functions.py
# to avoid duplication and ensure consistency. This avoids having multiple versions
# of aggregate functions that could return different results.