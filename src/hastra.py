import asyncio
import copy
import json
import httpx
import sys

from datetime import datetime, timezone
from typing import Tuple, Any, Dict, List, Union

import utils
from utils import current_ms, ms_to_datetime, datetime_to_ms, async_http_get_json
from hastra_types import JSONType


###

async def fetch_account_info(wallet_address: str) -> JSONType:
    """Fetch whether or not this wallet_address represents a Figure Markets exchange account 
    that is subject to a vesting schedule restrictions.
    The boolean returned for attribute 'wallet_is_vesting' indicates the vesting status.
    Args:
        wallet_address (str): Wallet's Bech32 address.
    Returns:
        JSONType: dict
    """
    url = "https://service-explorer.provenance.io/api/v2/accounts/" + wallet_address
    response = await async_http_get_json(url)
    if response.get("MCP-ERROR"):
        return response
    
    result = {}
    result['account_is_vesting'] = response['flags']['isVesting']
    result['account_type'] = response['accountType']
    # "accountAum": {
    #     "amount": "19657.70364228479",
    #     "denom": "USD"}
    result['account_aum'] = response['accountAum']
    
    return result

async def fetch_account_is_vesting(wallet_address: str) -> JSONType:
    """Fetch whether or not this wallet_address represents a Figure Markets exchange account 
    that is subject to a vesting schedule restrictions.
    The boolean returned for attribute 'wallet_is_vesting' indicates the vesting status.
    Args:
        wallet_address (str): Wallet's Bech32 address.
    Returns:
        JSONType: dict
    """
    url = "https://service-explorer.provenance.io/api/v2/accounts/" + wallet_address
    response = await async_http_get_json(url)
    if response.get("MCP-ERROR"):
        return response
    return {'wallet_is_vesting': response['flags']['isVesting']}


async def fetch_delegated_rewards_amount(wallet_address: str) -> JSONType:
    """For the given wallet address, fetch the current, total amount of earned rewards
    from the staked/delegated hash with the validators.
    The returned dict has the following attributes:
    'delegated_rewards_amount' : total amount of rewarded hash
    'denom' : hash denomination
    Args: wallet_address (str): Wallet's Bech32 address.
    Returns:
        JSONType: json dict with attrubutes 'delegated_rewards_amount' and 'denom'
    """
    url = "https://service-explorer.provenance.io/api/v2/accounts/" + \
        wallet_address + "/rewards"
    response = await async_http_get_json(url)
    if response.get("MCP-ERROR"):
        return response
    if response['total']:
        return {'delegated_rewards_amount':
                {"amount": utils.parse_amount(response['total'][0]['amount']),
                 'denom': response['total'][0]['denom']}}
    else:
        return {'delegated_rewards_amount':
                {'amount': utils.parse_amount(0), 'denom': 'nhash'}}

async def fetch_delegated_staked_amount(wallet_address: str) -> JSONType:
    """For the given wallet address, fetch the current, total amount of staked hash
    with the validators.
    The returned dict has the following attributes:
    'staking_validators': number of validators used for staking
    'delegated_staked_amount' : total amount of staked hash
    'denom' : hash denomination
    Args: wallet_address (str): Wallet's Bech32 address.
    Returns:
        JSONType: json dict with attributes 'staking_validators', 'delegated_staked_amount' and 'denom'
    """
    url = "https://service-explorer.provenance.io/api/v2/accounts/" + \
        wallet_address + "/delegations"
    response = await async_http_get_json(url)
    if response.get("MCP-ERROR"):
        return response
    return {'staking_validators': int(response['total']),
            'delegated_staked_amount':
                {'amount': utils.parse_amount(response['rollupTotals']['bondedTotal']['amount']),
                 'denom': response['rollupTotals']['bondedTotal']['denom']}}

async def fetch_delegated_unbonding_amount(wallet_address: str) -> JSONType:
    """For the given wallet address, fetch the current, total amount of hash
    that is unbonding with the validators.
    The returned dict has the following attributes:
    'delegated_unbonding_amount' : total amount of unbonding hash
    'denom' : hash denomination
    Args: wallet_address (str): Wallet's Bech32 address.
    Returns:
        JSONType: json dict with attributes 'delegated_unbonding_amount' and 'denom'
    """
    url = "https://service-explorer.provenance.io/api/v2/accounts/" + \
        wallet_address + "/unbonding"
    response = await async_http_get_json(url)
    if response.get("MCP-ERROR"):
        return response
    return {'delegated_unbonding_amount':
            {'amount': utils.parse_amount(response['rollupTotals']['unbondingTotal']['amount']),
             'denom': response['rollupTotals']['unbondingTotal']['denom']}}


async def fetch_delegated_redelegation_amount(wallet_address: str) -> JSONType:
    """For the given wallet address, fetch the current, total amount of hash
    that is redelegated with the validators.
    The returned dict has the following attributes:
    'delegated_redelegated_amount' : total amount of redelegated hash
    'denom' : hash denomination
    Args: wallet_address (str): Wallet's Bech32 address.
    Returns:
        JSONType: json dict with attributes 'delegated_redelegated_amount' and 'denom'
    """
    url = "https://service-explorer.provenance.io/api/v2/accounts/" + \
        wallet_address + "/redelegations"
    response = await async_http_get_json(url)
    if response.get("MCP-ERROR"):
        return response
    return {'delegated_redelegated_amount':
            {'amount': utils.parse_amount(response['rollupTotals']['redelegationTotal']['amount']),
             'denom': response['rollupTotals']['redelegationTotal']['denom']}}


###

async def fetch_total_delegation_data(wallet_address: str) -> JSONType:
    """
    For a wallet_address, the cumulative delegation hash amounts for all validators are returned,
    which are the amounts for the staked, redelegated, rewards and unbonding hash.
    The returned attribute-names with their values are the following:
    'delegated_staked_amount': 
        - amount of hash staked with the validators 
        - staked hash does earn rewards
        - staked hash can be undelegated which will return that hash back to the wallet after an unbonding waiting period
    'delegated_redelegated_amount': 
        - amount of hash redelegated with the validators
        - redelegated hash is subject to a 21 day waiting period before it gets added to validator's staked hash pool
        - during the waiting period, redelegated hash cannot be redelegated (to avoid too frequent 'validator-hopping')
        - redelegated hash can be undelegated during the redelegated waiting period, 
          and is then subject to the unbonding waiting period before it is returned to the wallet.
        - redelegated hash does earn rewards
    'delegated_rewards_amount': 
        - amount of hash earned as rewards 
        - rewarded hash does not earn rewards
        - rewarded hash can be claimed which will return that hash to the wallet immediately
    'delegated_unbonding_amount': 
        - amount of hash undelegated from validators 
        - undelegated hash is subject to a 21 day waiting period before is gets returned to the wallet 
        - undelegated hash does not earn rewards
    'delegated_total_delegated_amount': (calculated value)
        - the total amount of hash that is delegated to the validators and outside of the wallet
        - delegated hash cannot be traded or transferred
        - delegated hash can be returned to the wallet through undelegation for staked and redelegated hash
          (subject to a unbonding waiting period), and claiming for rewarded hash (immediately returned)
        - 'delegated_total_delegated_amount'='delegated_staked_amount'+'delegated_redelegated_amount'+'delegated_rewards_amount'+'delegated_unbonding_amount'
    'delegated_earning_amount':  (calculated value)
        - all delegated hash that earns rewards from the validators, which are staked and redelegated hash
        - 'delegated_earning_amount'='delegated_staked_amount'+'delegated_redelegated_amount'
    'delegated_not_earning_amount':  (calculated value)
        - all delegated hash that does not earn any rewards, which are the rewarded and unbonding hash
        - 'delegated_not_earning_amount'='delegated_rewards_amount'+'delegated_unbonding_amount'

    Args:
        wallet_address (str): Wallet's Bech32 address.

    Returns:
        JSONType: dict with delegation specific attributes and values
    """
    
    tasks = [fetch_delegated_staked_amount(wallet_address),
             fetch_delegated_redelegation_amount(wallet_address),
             fetch_delegated_unbonding_amount(wallet_address),
             fetch_delegated_rewards_amount(wallet_address)]

    r = await asyncio.gather(*tasks)

    # Gather returned values from a list into a dict
    r_dict = {}
    for item in r:
        if item.get("MCP-ERROR"): # if one of the fetch's failed, stop and return error
            return item
        r_dict.update(item)

    r_dict['delegated_earning_amount'] = utils.amount_denom_add(r_dict['delegated_staked_amount'],
                                                                r_dict['delegated_redelegated_amount'])

    r_dict['delegated_not_earning_amount'] = utils.amount_denom_add(r_dict['delegated_rewards_amount'],
                                                                    r_dict['delegated_unbonding_amount'])

    r_dict['delegated_total_delegated_amount'] = utils.amount_denom_add(r_dict['delegated_earning_amount'],
                                                                        r_dict['delegated_not_earning_amount'])

    # json_string = json.dumps(r_dict)
    return r_dict
