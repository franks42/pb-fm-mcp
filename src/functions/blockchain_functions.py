"""
Comprehensive Blockchain Functions for Provenance Blockchain

Complete set of blockchain API functions with proper async handling and integer values.
All functions are decorated with @api_function to be automatically exposed via MCP and/or REST protocols.
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

# Helper function for async HTTP GET requests
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

# Utility functions for amount handling
def parse_amount(amount_str) -> int:
    """Parse amount string/number to integer"""
    if isinstance(amount_str, str):
        return int(float(amount_str))
    return int(amount_str)

def amount_denom_add(amount1: Dict[str, Any], amount2: Dict[str, Any]) -> Dict[str, Any]:
    """Add two amount/denom dictionaries together"""
    if amount1.get("denom") != amount2.get("denom"):
        raise ValueError("Cannot add amounts with different denominations")
    
    total_amount = amount1["amount"] + amount2["amount"]
    return {
        "amount": total_amount,
        "denom": amount1["denom"]
    }


#########################################################################################
# Account Information Functions
#########################################################################################

@api_function(
    protocols=["mcp", "rest"],
    path="/api/account_info/{wallet_address}",
    method="GET",
    tags=["account", "information"],
    description="Fetch account information including vesting status and AUM"
)
async def fetch_account_info(wallet_address: str) -> JSONType:
    """
    Fetch comprehensive account information for a wallet address including
    vesting status, account type, and assets under management (AUM).
    
    Args:
        wallet_address: Wallet's Bech32 address
        
    Returns:
        Dictionary containing:
        - account_is_vesting: Boolean indicating if account is subject to vesting
        - account_type: Type of account (e.g., "BASE_ACCOUNT")
        - account_aum: Assets under management with amount and denomination
        
    Raises:
        HTTPError: If the Provenance blockchain API is unavailable
    """
    url = f"https://service-explorer.provenance.io/api/v2/accounts/{wallet_address}"
    response = await async_http_get_json(url)
    
    if response.get("MCP-ERROR"):
        return response
    
    try:
        result = {
            'account_is_vesting': response['flags']['isVesting'],
            'account_type': response['accountType'],
            'account_aum': response['accountAum']
        }
        return result
    except (KeyError, TypeError) as e:
        logger.warning(f"Could not parse account info: {e}")
        return {"MCP-ERROR": f"Data parsing error: {str(e)}"}


@api_function(
    protocols=["mcp", "rest"],
    path="/api/account_is_vesting/{wallet_address}",
    method="GET",
    tags=["account", "vesting"],
    description="Check if wallet address is subject to vesting restrictions"
)
async def fetch_account_is_vesting(wallet_address: str) -> JSONType:
    """
    Fetch whether a wallet address represents a Figure Markets exchange account 
    that is subject to vesting schedule restrictions.
    
    Args:
        wallet_address: Wallet's Bech32 address
        
    Returns:
        Dictionary containing:
        - wallet_is_vesting: Boolean indicating the vesting status
        
    Raises:
        HTTPError: If the Provenance blockchain API is unavailable
    """
    url = f"https://service-explorer.provenance.io/api/v2/accounts/{wallet_address}"
    response = await async_http_get_json(url)
    
    if response.get("MCP-ERROR"):
        return response
        
    try:
        return {'wallet_is_vesting': response['flags']['isVesting']}
    except (KeyError, TypeError) as e:
        logger.warning(f"Could not parse vesting status: {e}")
        return {"MCP-ERROR": f"Data parsing error: {str(e)}"}


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
        - delegated_rewards_amount: Total amount of rewarded HASH with amount and denom
        
    Raises:
        HTTPError: If the Provenance blockchain API is unavailable
    """
    url = f"https://service-explorer.provenance.io/api/v2/accounts/{wallet_address}/rewards"
    response = await async_http_get_json(url)
    
    if response.get("MCP-ERROR"):
        return response
    
    try:
        if response.get('total') and len(response['total']) > 0:
            total_rewards = response['total'][0]
            return {
                'delegated_rewards_amount': {
                    "amount": parse_amount(total_rewards['amount']),
                    'denom': total_rewards['denom']
                }
            }
        else:
            return {
                'delegated_rewards_amount': {
                    'amount': 0, 
                    'denom': 'nhash'
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
        - delegated_staked_amount: Total amount of staked HASH with amount and denom
        
    Raises:
        HTTPError: If the Provenance blockchain API is unavailable
    """
    url = f"https://service-explorer.provenance.io/api/v2/accounts/{wallet_address}/delegations"
    response = await async_http_get_json(url)
    
    if response.get("MCP-ERROR"):
        return response
        
    try:
        total_validators = int(response.get('total', 0))
        rollup_totals = response.get('rollupTotals', {})
        bonded_total = rollup_totals.get('bondedTotal', {'amount': '0', 'denom': 'nhash'})
        
        return {
            'staking_validators': total_validators,
            'delegated_staked_amount': {
                'amount': parse_amount(bonded_total['amount']),
                'denom': bonded_total['denom']
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
        - delegated_unbonding_amount: Total amount of unbonding HASH with amount and denom
        
    Raises:
        HTTPError: If the Provenance blockchain API is unavailable
    """
    url = f"https://service-explorer.provenance.io/api/v2/accounts/{wallet_address}/unbonding"
    response = await async_http_get_json(url)
    
    if response.get("MCP-ERROR"):
        return response
        
    try:
        rollup_totals = response.get('rollupTotals', {})
        unbonding_total = rollup_totals.get('unbondingTotal', {'amount': '0', 'denom': 'nhash'})
        
        return {
            'delegated_unbonding_amount': {
                'amount': parse_amount(unbonding_total['amount']),
                'denom': unbonding_total['denom']
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
        - delegated_redelegated_amount: Total amount of redelegated HASH with amount and denom
        
    Raises:
        HTTPError: If the Provenance blockchain API is unavailable
    """
    url = f"https://service-explorer.provenance.io/api/v2/accounts/{wallet_address}/redelegations"
    response = await async_http_get_json(url)
    
    if response.get("MCP-ERROR"):
        return response
        
    try:
        rollup_totals = response.get('rollupTotals', {})
        redelegation_total = rollup_totals.get('redelegationTotal', {'amount': '0', 'denom': 'nhash'})
        
        return {
            'delegated_redelegated_amount': {
                'amount': parse_amount(redelegation_total['amount']),
                'denom': redelegation_total['denom']
            }
        }
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Could not parse redelegation data: {e}")
        return {"MCP-ERROR": f"Data parsing error: {str(e)}"}


#########################################################################################
# Aggregate Delegation Function (MCP + REST API)
#########################################################################################

@api_function(
    protocols=["mcp", "rest"],
    path="/api/total_delegation_data/{wallet_address}",
    method="GET",
    tags=["delegation", "summary"],
    description="Fetch comprehensive delegation data summary for a wallet address"
)
async def fetch_total_delegation_data(wallet_address: str) -> JSONType:
    """
    For a wallet address, fetch cumulative delegation HASH amounts for all validators,
    including staked, redelegated, rewards and unbonding amounts with calculated totals.
    
    This function aggregates data from multiple blockchain API endpoints to provide
    a comprehensive view of all delegation activities for the wallet.
    
    Args:
        wallet_address: Wallet's Bech32 address
        
    Returns:
        Dictionary containing detailed delegation information:
        - staking_validators: Number of validators used for staking
        - delegated_staked_amount: Amount of HASH staked with validators (earns rewards)
        - delegated_redelegated_amount: Amount of HASH redelegated (earns rewards, 21-day waiting period)
        - delegated_rewards_amount: Amount of HASH earned as rewards (can be claimed immediately)
        - delegated_unbonding_amount: Amount of HASH unbonding (21-day waiting period, no rewards)
        - delegated_total_delegated_amount: Total HASH delegated (calculated sum of all above)
        - delegated_earning_amount: Total HASH earning rewards (staked + redelegated)
        - delegated_not_earning_amount: Total HASH not earning rewards (rewards + unbonding)
        
    Raises:
        HTTPError: If any of the Provenance blockchain APIs are unavailable
    """
    # Fetch all delegation data concurrently for better performance
    tasks = [
        fetch_delegated_staked_amount(wallet_address),
        fetch_delegated_redelegation_amount(wallet_address),
        fetch_delegated_unbonding_amount(wallet_address),
        fetch_delegated_rewards_amount(wallet_address)
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Check for errors in any of the results
    for result in results:
        if result.get("MCP-ERROR"):
            return result
    
    try:
        # Extract individual amounts from the results
        staked_data = results[0]
        redelegation_data = results[1]  
        unbonding_data = results[2]
        rewards_data = results[3]
        
        # Get the amount/denom structures
        staked_amount_data = staked_data["delegated_staked_amount"]
        redelegated_amount_data = redelegation_data["delegated_redelegated_amount"]
        unbonding_amount_data = unbonding_data["delegated_unbonding_amount"]
        rewards_amount_data = rewards_data["delegated_rewards_amount"]
        
        # Calculate derived amounts using the utility function
        earning_amount_data = amount_denom_add(staked_amount_data, redelegated_amount_data)
        not_earning_amount_data = amount_denom_add(rewards_amount_data, unbonding_amount_data)
        total_delegated_amount_data = amount_denom_add(earning_amount_data, not_earning_amount_data)
        
        # Build the comprehensive response
        result = {
            "staking_validators": staked_data.get("staking_validators", 0),
            "delegated_staked_amount": staked_amount_data,
            "delegated_redelegated_amount": redelegated_amount_data,
            "delegated_unbonding_amount": unbonding_amount_data,
            "delegated_rewards_amount": rewards_amount_data,
            "delegated_earning_amount": earning_amount_data,
            "delegated_not_earning_amount": not_earning_amount_data,
            "delegated_total_delegated_amount": total_delegated_amount_data
        }
        
        return result
        
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Could not calculate delegation totals: {e}")
        return {"MCP-ERROR": f"Calculation error: {str(e)}"}