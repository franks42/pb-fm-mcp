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


@api_function(
    protocols=["mcp", "rest"],
    path="/api/vesting_total_unvested_amount/{wallet_address}",
    method="GET",
    tags=["vesting", "blockchain"],
    description="Fetch vesting unvested amount for wallet address at specific date-time"
)
async def fetch_vesting_total_unvested_amount(wallet_address: str, date_time: str = None) -> JSONType:
    """
    Fetch the vesting_total_unvested_amount for the given wallet address and date_time.
    
    The vesting schedule is estimated by a linear function for the unvested_amount that starts
    on start_time at vesting_original_amount, and decreases linearly over time to zero at end_time.
    
    Args:
        wallet_address: Wallet's Bech32 address
        date_time: Date-time in ISO 8601 format for which the vesting data is requested.
                  Defaults to current datetime if not provided.
        
    Returns:
        Dictionary containing vesting information:
        - date_time: The date-time for which vesting info was requested
        - vesting_original_amount: Original number of nano-HASH subject to vesting schedule
        - denom: Token denomination
        - vesting_total_vested_amount: Amount of nhash that have vested as of date_time
        - vesting_total_unvested_amount: Amount of nhash still vesting and unvested as of date_time
        - start_time: Date-time when vesting starts
        - end_time: Date-time when vesting ends
        
    Raises:
        HTTPError: If the Provenance blockchain API is unavailable
    """
    try:
        url = f"https://service-explorer.provenance.io/api/v3/accounts/{wallet_address}/vesting"
        response = await async_http_get_json(url)
        
        if response.get("MCP-ERROR"):
            return response

        # Calculate timestamp for vesting calculations
        if date_time:
            from datetime import datetime
            dtms = int(datetime.fromisoformat(date_time).timestamp() * 1000)
        else:
            from datetime import datetime, UTC
            dtms = int(datetime.now(UTC).timestamp() * 1000)

        # Parse vesting schedule dates
        from datetime import datetime
        end_time_ms = int(datetime.fromisoformat(response["endTime"]).timestamp() * 1000)
        start_time_ms = int(datetime.fromisoformat(response["startTime"]).timestamp() * 1000)
        
        # Get original vesting amount
        vesting_original_amount = parse_amount(response['originalVestingList'][0]['amount'])
        denom = response['originalVestingList'][0]['denom']
        
        # Calculate vested amount based on linear schedule
        if dtms < start_time_ms:
            total_vested_amount = 0
        elif dtms > end_time_ms:
            total_vested_amount = vesting_original_amount
        else:
            total_vested_amount = int(
                vesting_original_amount * (dtms - start_time_ms) / (end_time_ms - start_time_ms)
            )
        
        total_unvested_amount = vesting_original_amount - total_vested_amount
        
        # Build result
        from datetime import datetime, UTC
        result_datetime = datetime.fromtimestamp(dtms / 1000, tz=UTC).isoformat()
        
        vesting_data = {
            'date_time': result_datetime,
            'vesting_original_amount': vesting_original_amount,
            'denom': denom,
            'vesting_total_vested_amount': total_vested_amount,
            'vesting_total_unvested_amount': total_unvested_amount,
            'start_time': response["startTime"],
            'end_time': response["endTime"]
        }
        
        return vesting_data
        
    except Exception as e:
        logger.error(f"Could not fetch vesting data: {e}")
        return {"MCP-ERROR": f"Vesting data fetch error: {str(e)}"}


@api_function(
    protocols=["rest"],
    path="/api/wallet_liquid_balance/{wallet_address}",
    method="GET",
    tags=["balance", "blockchain"],
    description="Fetch liquid HASH balance available in wallet"
)
async def fetch_wallet_liquid_balance(wallet_address: str) -> JSONType:
    """
    Fetch the current liquid HASH balance available in the wallet (not delegated or committed).
    
    This is the amount that can be immediately spent, transferred, or delegated.
    
    Args:
        wallet_address: Wallet's Bech32 address
        
    Returns:
        Dictionary containing:
        - wallet_liquid_balance: Available liquid HASH amount in the wallet
        - denom: Token denomination (nhash)
        
    Raises:
        HTTPError: If the Provenance blockchain API is unavailable
    """
    try:
        url = f"https://service-explorer.provenance.io/api/v2/accounts/{wallet_address}/balances"
        params = {"count": 20, "page": 1}
        response = await async_http_get_json(url, params=params)
        
        if response.get("MCP-ERROR"):
            return response
            
        # Find HASH balance in the results
        balance_list = response.get('results', [])
        for balance in balance_list:
            if balance.get('denom') == 'nhash':
                return {
                    'wallet_liquid_balance': parse_amount(balance['amount']),
                    'denom': balance['denom']
                }
        
        # No HASH found - return zero balance
        return {
            'wallet_liquid_balance': 0,
            'denom': 'nhash'
        }
        
    except Exception as e:
        logger.error(f"Could not fetch wallet liquid balance: {e}")
        return {"MCP-ERROR": f"Wallet balance fetch error: {str(e)}"}


@api_function(
    protocols=["mcp", "rest"],
    path="/api/available_committed_amount/{wallet_address}",
    method="GET",
    tags=["commitment", "blockchain"],
    description="Fetch committed HASH amount to Figure Markets exchange"
)
async def fetch_available_committed_amount(wallet_address: str) -> JSONType:
    """
    Fetch the current committed HASH amount to the Figure Markets exchange for the given wallet address.
    
    API returns amounts in nhash (1 HASH = 1,000,000,000 nhash). Values are converted to integers.
    
    Args:
        wallet_address: Wallet's Bech32 address
        
    Returns:
        Dictionary containing:
        - denom: Token/HASH denomination (nhash)
        - available_committed_amount: Amount of denom committed to the exchange
        
    Raises:
        HTTPError: If the Provenance blockchain API is unavailable
    """
    try:
        url = f"https://api.provenance.io/provenance/exchange/v1/commitments/account/{wallet_address}"
        response = await async_http_get_json(url)
        
        if response.get("MCP-ERROR"):
            return response
        
        # Extract market 1 commitments
        market1_list = [x["amount"] for x in response["commitments"] if x["market_id"] == 1]
        hash_amount_dict_list = [
            x for x in (market1_list[0] if market1_list else []) 
            if x["denom"] == "nhash"
        ]
        
        # Build result with integer amount
        available_committed_amount = 0
        if hash_amount_dict_list:
            available_committed_amount = parse_amount(hash_amount_dict_list[0]["amount"])
        
        hash_amount_dict = {
            "denom": "nhash",
            "available_committed_amount": available_committed_amount
        }
        
        return hash_amount_dict
        
    except Exception as e:
        logger.error(f"Could not fetch committed amount: {e}")
        return {"MCP-ERROR": f"Committed amount fetch error: {str(e)}"}


# @api_function(
#     protocols=["mcp", "rest"],
#     path="/api/complete_hash_summary/{wallet_address}",
#     method="GET",
#     tags=["aggregates", "hash", "summary"],
#     description="Get comprehensive summary of all HASH amounts for a wallet across all sources"
# )
# async def fetch_complete_hash_summary(wallet_address: str) -> JSONType:
#     """
#     Comprehensive summary of all HASH amounts for a wallet including liquid balance,
#     delegation amounts, committed amounts, and vesting amounts (if applicable).
    
#     This function aggregates HASH from all possible sources to provide the most complete
#     picture of a wallet's total HASH holdings across the entire ecosystem.
    
#     Args:
#         wallet_address: Wallet's Bech32 address
        
#     Returns:
#         Dictionary containing complete HASH breakdown:
#         - wallet_liquid_balance: Liquid HASH in wallet (immediately spendable)
#         - delegated_total_amount: Total HASH delegated to validators (from delegation summary)
#         - delegated_earning_amount: HASH earning rewards (staked + redelegated)
#         - delegated_rewards_amount: HASH rewards available to claim
#         - committed_amount: HASH committed to Figure Markets exchange
#         - vesting_unvested_amount: HASH still vesting (if vesting account)
#         - total_hash_all_sources: Grand total of all HASH across all sources
#         - hash_breakdown: Detailed breakdown by category
#         - account_classification: Categorization based on HASH distribution
        
#     Raises:
#         HTTPError: If any of the blockchain APIs are unavailable
#     """
#     logger.info(f"Fetching complete HASH summary for {wallet_address}")
    
#     # First check if account is vesting to determine which data to fetch
#     is_vesting_task = fetch_account_is_vesting(wallet_address)
#     is_vesting_result = await is_vesting_task
    
#     if is_vesting_result.get("MCP-ERROR"):
#         return is_vesting_result
    
#     is_vesting_account = is_vesting_result.get("wallet_is_vesting", False)
    
#     # Define base tasks that we always need
#     base_tasks = [
#         fetch_wallet_liquid_balance(wallet_address),
#         fetch_total_delegation_data(wallet_address),
#         fetch_available_committed_amount(wallet_address)
#     ]
    
#     # Add vesting task if account is vesting
#     if is_vesting_account:
#         base_tasks.append(fetch_vesting_total_unvested_amount(wallet_address))
    
#     # Execute all tasks concurrently
#     results = await asyncio.gather(*base_tasks, return_exceptions=True)
    
#     # Extract results with error handling
#     liquid_balance = results[0] if not isinstance(results[0], Exception) else {"MCP-ERROR": str(results[0])}
#     delegation_data = results[1] if not isinstance(results[1], Exception) else {"MCP-ERROR": str(results[1])}
#     committed_data = results[2] if not isinstance(results[2], Exception) else {"MCP-ERROR": str(results[2])}
    
#     # Handle vesting data if account is vesting
#     vesting_data = {}
#     if is_vesting_account and len(results) > 3:
#         vesting_data = results[3] if not isinstance(results[3], Exception) else {"MCP-ERROR": str(results[3])}
    
#     # Check for critical errors
#     if liquid_balance.get("MCP-ERROR") or delegation_data.get("MCP-ERROR"):
#         error_msg = liquid_balance.get("MCP-ERROR") or delegation_data.get("MCP-ERROR")
#         return {"MCP-ERROR": f"Critical data fetch error: {error_msg}"}
    
#     try:
#         # Extract individual amounts
#         liquid_amount = liquid_balance.get("wallet_liquid_balance", 0)
#         committed_amount = committed_data.get("available_committed_amount", 0) if not committed_data.get("MCP-ERROR") else 0
        
#         # Extract delegation amounts using the amount/denom structure
#         delegation_total_amount_data = delegation_data.get("delegated_total_delegated_amount", {"amount": 0})
#         delegation_earning_amount_data = delegation_data.get("delegated_earning_amount", {"amount": 0})
#         delegation_rewards_amount_data = delegation_data.get("delegated_rewards_amount", {"amount": 0})
        
#         delegation_total = delegation_total_amount_data.get("amount", 0)
#         delegation_earning = delegation_earning_amount_data.get("amount", 0)
#         delegation_rewards = delegation_rewards_amount_data.get("amount", 0)
#         staking_validators = delegation_data.get("staking_validators", 0)
        
#         # Extract vesting amount if applicable
#         vesting_unvested_amount = 0
#         if is_vesting_account and not vesting_data.get("MCP-ERROR"):
#             vesting_unvested_amount = vesting_data.get("vesting_total_unvested_amount", 0)
        
#         # Calculate total across all sources
#         total_hash_all_sources = liquid_amount + delegation_total + committed_amount + vesting_unvested_amount
        
#         # Create detailed breakdown
#         hash_breakdown = {
#             "liquid_hash": liquid_amount,
#             "delegated_hash": delegation_total,
#             "committed_hash": committed_amount,
#             "vesting_hash": vesting_unvested_amount,
#             "total_earning_hash": delegation_earning,
#             "claimable_rewards_hash": delegation_rewards
#         }
        
#         # Classify account based on HASH distribution
#         account_classification = []
#         if liquid_amount > 0:
#             account_classification.append("liquid_holder")
#         if delegation_total > 0:
#             account_classification.append("validator_delegator")
#         if committed_amount > 0:
#             account_classification.append("trading_participant")
#         if vesting_unvested_amount > 0:
#             account_classification.append("vesting_participant")
#         if delegation_rewards > (delegation_total * 0.01):  # More than 1% rewards
#             account_classification.append("rewards_accumulator")
        
#         # Build comprehensive response
#         result = {
#             "wallet_address": wallet_address,
#             "is_vesting_account": is_vesting_account,
#             "wallet_liquid_balance": liquid_amount,
#             "delegated_total_amount": delegation_total,
#             "delegated_earning_amount": delegation_earning,
#             "delegated_rewards_amount": delegation_rewards,
#             "staking_validators": staking_validators,
#             "committed_amount": committed_amount,
#             "vesting_unvested_amount": vesting_unvested_amount,
#             "total_hash_all_sources": total_hash_all_sources,
#             "hash_breakdown": hash_breakdown,
#             "account_classification": account_classification,
#             "denom": "nhash"
#         }
        
#         return result
        
#     except Exception as e:
#         logger.error(f"Could not calculate HASH summary: {e}")
#         return {"MCP-ERROR": f"HASH summary calculation error: {str(e)}"}