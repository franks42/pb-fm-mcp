"""
Provenance Blockchain + Figure Markets MCP Server for AWS Lambda
"""
import sys
from datetime import UTC, datetime
from typing import Dict, Any, Union
from pathlib import Path

# Add src directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import utils
from base64expand import base64expand
from hastra_types import JSONType

# AWS Lambda MCP Handler
from awslabs.mcp_lambda_handler import MCPLambdaHandler
import httpx
import hastra

#########################################################################################
# helper functions
#########################################################################################

def datetime_to_ms(dt):
    """Convert datetime to milliseconds since epoch"""
    if dt.tzinfo is None:
        # Assume UTC if no timezone specified
        dt = dt.replace(tzinfo=UTC)
    return int(dt.timestamp() * 1000)

def ms_to_datetime(ms_timestamp, tz=UTC):
    """Convert milliseconds since epoch to datetime"""
    return datetime.fromtimestamp(ms_timestamp / 1000, tz=tz)

def current_ms():
    """Get current time in milliseconds since epoch"""
    return int(datetime.now(UTC).timestamp() * 1000)

# helper function to standardize async http-get of json return
async def async_http_get_json(
    url: str,
    params: dict | None = None,
    timeout: float = 10.0,
    connect_timeout: float = 5.0
) -> JSONType:
    """Make an async HTTP GET request and return JSON response.

    Args:
        url: The URL to send the GET request to
        params: Query parameters to include
        timeout: Total request timeout in seconds
        connect_timeout: Connection timeout in seconds

    Returns:
        JSON response data on success, or error dict with 'MCP-ERROR' key on failure
    """

    if params is None:
        params = {}

    timeout_config = httpx.Timeout(timeout, connect=connect_timeout)
    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient(timeout=timeout_config) as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            # Validate content type
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                return {"MCP-ERROR": f"Expected JSON, got {content_type}"}

            return response.json()

        except httpx.TimeoutException:
            return {"MCP-ERROR": "Network Error: Request timed out"}
        except httpx.HTTPStatusError as e:
            return {"MCP-ERROR": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"MCP-ERROR": f"Request error: {e}"}
        except ValueError as e:
            return {"MCP-ERROR": f"Invalid JSON response: {e}"}
        except Exception as e:
            return {"MCP-ERROR": f"Unknown exception raised: {e}"}

#########################################################################################
# Initialize MCP Server for AWS Lambda
#########################################################################################

# Initialize the MCP server with a name and version
mcp_server = MCPLambdaHandler(name="pb-fm-mcp", version="0.1.0")

#########################################################################################
# MCP Tool Functions
#########################################################################################

@mcp_server.tool()
def adt(a: int, b: int) -> int:
    """Adt is a special operation on two numbers because it always returns the ultimate answer."""
    return 42

@mcp_server.tool()
async def get_system_context() -> dict:
    """
    REQUIRED READING: Essential system context for the Figure Markets Exchange 
    and the Provenance Blockchain that MUST be read before using any tools.
    Contains critical usage guidelines, data handling protocols, and server capabilities.
    Returns:
        Dict with attribute 'context' and a value of the url where the context description 
        as a markdown formatted str can be retrieved.
    """
    url = "https://raw.githubusercontent.com/franks42/FigureMarkets-MCP-Server/refs/heads/main/FigureMarketsContext.md"
    async with httpx.AsyncClient() as client:
        client.headers['accept-encoding'] = 'identity'
        r = await client.get(url)
        return {'context': r.text}

@mcp_server.tool()
async def fetch_last_crypto_token_price(token_pair: str = "HASH-USD", last_number_of_trades: int = 1) -> JSONType:
    """For the crypto token_pair, e.g. HASH-USD, fetch the prices for the last_number_of_trades 
    from the Figure Markets exchange.
    Args:
        token_pair (str, optional): Two token/crypto symbols separated by '-', like BTC-USDC. Defaults to HASH-USD.
        last_number_of_trades (int, optional): Ask for specified number of trades to return. Defaults to 1.
    Returns:
        JSONType: json dict where attribute 'matches' has a list of individual trade details
    """
    url = 'https://www.figuremarkets.com/service-hft-exchange/api/v1/trades/' + token_pair
    params = {'size': last_number_of_trades}
    response = await async_http_get_json(url, params=params)
    if response.get("MCP-ERROR"):
        return response
    # massage json response data
    return response

@mcp_server.tool()
async def fetch_current_fm_data() -> JSONType:
    """Fetch the current market data from the Figure Markets exchange.
    The data is a list of trading pair details.
    The 'id' attribute is the identifier for the trading pair.
    Each trading pair's 'denom' attribute is the token name and the 'quoteDenum' denotes the currency.
    Returns:
        JSONType: json list of trading pair details
    """
    url = 'https://www.figuremarkets.com/service-hft-exchange/api/v1/markets'
    response = await async_http_get_json(url)
    if response.get("MCP-ERROR"):
        return response
    data = response['data']
    return data

@mcp_server.tool()
async def fetch_current_fm_account_balance_data(wallet_address: str) -> JSONType:
    """Fetch the current account balance data from the Figure Markets exchange for the given wallet address' portfolio.
    The data is a list of dictionaries with balance details for all assets in the wallet.
    The relevant attributes are:
    'denom', which is the asset identifier. Note that 'neth.figure.se' denotes ETH, 'nhash' denotes nano-HASH, 'nsol.figure.se' denotes SOL, 
    'uusd.trading' denotes micro-USD, 'uusdc.figure.se' denotes USDC, 'uxrp.figure.se' denotes XRP, 'uylds.fcc' denotes YLDS, and ignore others.
    Note that the amount for denom 'nhash' represents only the AVAILABLE HASH in the wallet (non-delegated).
    To get total HASH holdings, you must also fetch delegation amounts separately.
    Args:
        wallet_address (str): Wallet's Bech32 address.
    Returns:
        JSONType: json list of balance item details
    """
    url = "https://service-explorer.provenance.io/api/v2/accounts/" + \
        wallet_address + "/balances"
    params = {"count": 20, "page": 1}
    response = await async_http_get_json(url, params=params)
    if response.get("MCP-ERROR"):
        return response
    balance_list = response['results']
    return balance_list

@mcp_server.tool()
async def fetch_available_total_amount(wallet_address: str) -> JSONType:
    """Fetch the current available_total_amount of HASH in the wallet.

    available_total_amount = available_spendable_amount + available_committed_amount + available_unvested_amount

    The relevant attributes in the returned json dict are:
    'available_total_amount': amount in denom units
    'denom': the asset identifier and denom for the amount (nhash).
    Args:
        wallet_address (str): Wallet's Bech32 address.
    Returns:
        JSONType: json dict
    """
    url = "https://service-explorer.provenance.io/api/v2/accounts/" + \
        wallet_address + "/balances"
    params = {"count": 20, "page": 1}
    response = await async_http_get_json(url, params=params)
    if response.get("MCP-ERROR"):
        return response
    balance_list = response['results']
    for e in balance_list:
        if e['denom'] == "nhash":
            return {'available_total_amount': utils.parse_amount(e['amount']),
                    'denom': e['denom']}
    return {"MCP-ERROR": "fetch_available_total_amount() - No 'nhash' in balance list"}

@mcp_server.tool()
async def fetch_current_fm_account_info(wallet_address: str) -> JSONType:
    """Fetch the current account/wallet info from the Figure Markets exchange for the given wallet address.
    Important attributes in the json response:
    'isVesting' : If True, then the account/wallet is subject to vesting restrictions. 
                If False then the wallet has no applicable or active vesting schedule, no vesting hash amounts and therefore no vesting restrictions.
    Args:
        wallet_address (str): Wallet's Bech32 address.
    Returns:
        JSONType: json dict of account details
    """
    url = "https://service-explorer.provenance.io/api/v2/accounts/" + wallet_address
    response = await async_http_get_json(url)
    if response.get("MCP-ERROR"):
        return response
    return base64expand(response)

@mcp_server.tool()
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

@mcp_server.tool()
async def fetch_vesting_total_unvested_amount(wallet_address: str, date_time: str | None = None) -> JSONType:
    """Fetch the vesting_total_unvested_amount from the Figure Markets exchange for the given wallet address and the given `date_time`.
    `date_time` is current datetime.now() by default.
    The vesting schedule is estimated by a linear function for the unvested_amount that starts on start_time at vesting_original_amount, 
    and decreases linearly over time to zero at end_time.
    The returned dictionary has the following attributes:
    'date_time': the date-time for which the vesting info was requested
    'vesting_original_amount': the original number of nano-HASH that are subject to vesting schedule
    'denom': token denomination
    'vesting_total_vested_amount': amount of nhash that have vested as of `date_time`
    'vesting_total_unvested_amount': amount of nhash that is still vesting and is unvested as of `date_time`
    'start_time': date-time for when the vesting starts
    'end_time': date-time for when the vesting ends, and the unvested amount is zero and vested amount equals the vesting_original_amount
    Args:
        wallet_address (str): Wallet's Bech32 address.
        date_time (str): date_time in ISO 8601 format for which the vesting date is requested.
    Returns:
        JSONType: json dict of vesting details
    """

    url = "https://service-explorer.provenance.io/api/v3/accounts/" + \
        wallet_address + "/vesting"
    response = await async_http_get_json(url)
    if response.get("MCP-ERROR"):
        return response

    if date_time:
        dtms = datetime_to_ms(datetime.fromisoformat(date_time))
    else:
        dtms = current_ms()

    end_time_ms = datetime_to_ms(
        datetime.fromisoformat(response["endTime"]))
    start_time_ms = datetime_to_ms(
        datetime.fromisoformat(response["startTime"]))
    vesting_original_amount = utils.parse_amount(
        response['originalVestingList'][0]['amount'])
    denom = response['originalVestingList'][0]['denom']
    if dtms < start_time_ms:
        total_vested_amount = utils.parse_amount(0)
    elif dtms > end_time_ms:
        total_vested_amount = vesting_original_amount
    else:
        total_vested_amount = utils.parse_amount(
            vesting_original_amount * (dtms - start_time_ms)/(end_time_ms - start_time_ms))
    total_unvested_amount = vesting_original_amount - total_vested_amount

    vesting_data = {'date_time': ms_to_datetime(dtms).isoformat()}
    vesting_data['vesting_original_amount'] = vesting_original_amount
    vesting_data['denom'] = denom
    vesting_data['vesting_total_vested_amount'] = total_vested_amount
    vesting_data['vesting_total_unvested_amount'] = total_unvested_amount
    vesting_data['start_time'] = response["startTime"]
    vesting_data['end_time'] = response["endTime"]

    return vesting_data

@mcp_server.tool()
async def fetch_available_committed_amount(wallet_address: str) -> JSONType:
    """Fetch the current committed HASH amount to the the Figure Markets exchange for the given wallet address.
    API returns amounts in nhash (1 HASH = 1,000,000,000 nhash). Convert to HASH for display purposes.
    The returned dictionary has the following attributes:
    'denom': token/HASH denomination
    'available_committed_amount': the number of 'denom' that are committed to the exchange
    Args:
        wallet_address (str): Wallet's Bech32 address.
    Returns:
        JSONType: json dict of committed hash amount
    """
    url = "https://api.provenance.io/provenance/exchange/v1/commitments/account/" + wallet_address
    response = await async_http_get_json(url)
    if response.get("MCP-ERROR"):
        return response
    market1_list = [x["amount"]
                    for x in response["commitments"] if x["market_id"] == 1]
    hash_amount_dict_list = [x for x in (
        market1_list[0] if market1_list else []) if x["denom"] == "nhash"]
    hash_amount_dict = {"denom": "nhash"}
    hash_amount_dict["available_committed_amount"] = hash_amount_dict_list[0]["amount"] if hash_amount_dict_list else 0
    return hash_amount_dict

@mcp_server.tool()
async def fetch_figure_markets_assets_info() -> JSONType:
    """Fetch the list of assets, like (crypto) tokens, stable coins, and funds,
    that are traded on the Figure Markets exchange.
    The returned list of dictionaries of asset's info has the following attributes:
    'asset_name' : identifier to use for asset
    'asset_description' : 
    'asset_display_name' : 
    'asset_type' : CRYPTO, STABLECOIN or FUND
    'asset_exponent' : 10 to the power asset_exponent multiplied by amount of asset_denom,
                        yields the asset amount
    'asset_denom' : asset denomination
    Args:
    Returns:
        JSONType: json list of asset details
    """
    url = "https://figuremarkets.com/service-hft-exchange/api/v1/assets"
    response = await async_http_get_json(url)
    if response.get("MCP-ERROR"):
        return response
    asset_details_list = [{'asset_name': details['name'],
                           'asset_description': details['description'],
                           'asset_display_name': details['displayName'],
                           'asset_type': details['type'],
                           'asset_exponent': details['exponent'],
                           'asset_denom': details['provenanceMarkerName']}
                          for details in response['data']]
    return asset_details_list

@mcp_server.tool()
async def fetch_current_hash_statistics() -> JSONType:
    """Fetch the current overall statistics for the Provenance Blockchain's utility token HASH.
    Pie chart of stats also available at 'https://explorer.provenance.io/network/token-stats'.
    Attributes in the json response:
    'maxSupply' : The total initial amount of all the HASH minted.
    'burned' : The total amount of all the burned HASH. 
    'currentSupply' : The current total supply of HASH that is not burned: 
                      currentSupply = maxSupply - burned
    'circulation' : The total amount of HASH in circulation.
    'communityPool' : The total amount of HASH managed by the Provenance Foundation for the community.
    'bonded' : The total amount of HASH that is delegated to or staked with validators.
    'locked' : The total amount of HASH that is locked and subject to a vesting schedule: 
               locked = currentSupply - circulation - communityPool - bonded
    Args:
    Returns:
        JSONType: json dict of HASH statistics details
    """
    url = "https://service-explorer.provenance.io/api/v3/utility_token/stats"
    response = await async_http_get_json(url)
    if response.get("MCP-ERROR"):
        return response
    response["locked"] = {"amount": str(int(response["currentSupply"]["amount"]) -
                                        int(response["circulation"]["amount"]) -
                                        int(response["communityPool"]["amount"]) -
                                        int(response["bonded"]["amount"])),
                          "denom": "nhash"}
    return response

@mcp_server.tool()
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
    
    r = await hastra.fetch_total_delegation_data(wallet_address)
    return r

#########################################################################################
# AWS Lambda Handler
#########################################################################################

def lambda_handler(event, context):
    """Standard AWS Lambda handler"""
    return mcp_server.handle_request(event, context)