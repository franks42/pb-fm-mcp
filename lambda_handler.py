"""
Provenance Blockchain + Figure Markets MCP Server for AWS Lambda
"""
import sys
import asyncio
import json
from datetime import UTC, datetime
from typing import Dict, Any, Union
from pathlib import Path

# Add src directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import utils
from base64expand import base64expand
from hastra_types import JSONType
from async_wrapper import sync_wrapper, async_to_sync_mcp_tool

# AWS Lambda MCP Handler
from awslabs.mcp_lambda_handler import MCPLambdaHandler
import httpx
import hastra

# FastAPI and Lambda adapter
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from mangum import Mangum

# Unified Function Registry  
from registry import get_registry, MCPIntegration, FastAPIIntegration
import functions  # This will register all @api_function decorated functions

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

# helper function to standardize sync http-get of json return
def http_get_json(
    url: str,
    params: dict | None = None,
    timeout: float = 10.0,
    connect_timeout: float = 5.0
) -> JSONType:
    """Make a sync HTTP GET request and return JSON response.

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

    with httpx.Client(timeout=timeout_config) as client:
        try:
            response = client.get(url, params=params, headers=headers)
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

# Initialize FastAPI app for REST endpoints
fastapi_app = FastAPI(
    title="PB-FM API",
    description="REST API for Provenance Blockchain and Figure Markets data",
    version="0.1.0",
    docs_url=None,  # Disable built-in docs to avoid async issues
    openapi_url="/openapi.json",
    # Configure for API Gateway path
    root_path="/Prod"
)

# Add CORS middleware to enable external Swagger UI access
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for OpenAPI spec access
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

#########################################################################################
# Unified Function Registry Integration
#########################################################################################

# Get the global function registry
registry = get_registry()

# Auto-register all @api_function decorated functions with MCP server
MCPIntegration.register_mcp_tools(mcp_server, registry)
print(f"🔧 Registered {len(registry.get_mcp_functions())} MCP tools from function registry")

# Auto-register all @api_function decorated functions with FastAPI
FastAPIIntegration.register_rest_routes(fastapi_app, registry)
print(f"🌐 Registered {len(registry.get_rest_functions())} REST routes from function registry")

# Create Mangum handler for FastAPI with proper async support
fastapi_handler = Mangum(fastapi_app, lifespan="off")

#########################################################################################
# MCP Tool Functions
#########################################################################################

# Removed manual test MCP tool - replaced with auto-generated tools from unified registry

@mcp_server.tool()
def get_system_context() -> dict:
    """
    REQUIRED READING: Essential system context for the Figure Markets Exchange 
    and the Provenance Blockchain that MUST be read before using any tools.
    Contains critical usage guidelines, data handling protocols, and server capabilities.
    Returns:
        Dict with attribute 'context' and a value of the url where the context description 
        as a markdown formatted str can be retrieved.
    """
    url = "https://raw.githubusercontent.com/franks42/FigureMarkets-MCP-Server/refs/heads/main/FigureMarketsContext.md"
    with httpx.Client() as client:
        client.headers['accept-encoding'] = 'identity'
        r = client.get(url)
        return {'context': r.text}

# Removed manual MCP tool - replaced with auto-generated fetch_last_crypto_token_price from unified registry

# Removed manual MCP tool - replaced with auto-generated fetch_current_fm_data from unified registry

@mcp_server.tool()
def fetch_current_fm_account_balance_data(wallet_address: str) -> JSONType:
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
    response = http_get_json(url, params=params)
    if response.get("MCP-ERROR"):
        return response
    balance_list = response['results']
    return balance_list

@mcp_server.tool()
def fetch_available_total_amount(wallet_address: str) -> JSONType:
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
    response = http_get_json(url, params=params)
    if response.get("MCP-ERROR"):
        return response
    balance_list = response['results']
    for e in balance_list:
        if e['denom'] == "nhash":
            return {'available_total_amount': utils.parse_amount(e['amount']),
                    'denom': e['denom']}
    return {"MCP-ERROR": "fetch_available_total_amount() - No 'nhash' in balance list"}

@async_to_sync_mcp_tool(mcp_server)
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

@async_to_sync_mcp_tool(mcp_server)
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

@async_to_sync_mcp_tool(mcp_server)
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

@async_to_sync_mcp_tool(mcp_server)
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

@async_to_sync_mcp_tool(mcp_server)
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

@async_to_sync_mcp_tool(mcp_server)
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

@async_to_sync_mcp_tool(mcp_server)
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
# FastAPI REST Endpoints
#########################################################################################

@fastapi_app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "PB-FM API",
        "version": "0.1.0",
        "description": "REST API for Provenance Blockchain and Figure Markets data",
        "endpoints": {
            "docs": "/docs",
            "openapi": "/openapi.json",
            "mcp": "/mcp"
        }
    }

# Removed manual /api/markets endpoint - replaced with auto-generated /api/figure_markets_data from unified registry

# Removed manual /api/account/{wallet_address}/balance endpoint - replaced with auto-generated /api/fm_account_balance/{wallet_address} from unified registry

# Removed manual /api/account/{wallet_address}/info endpoint - replaced with auto-generated /api/fm_account_info/{wallet_address} from unified registry

def _generate_docs_html():
    """Generate the documentation HTML content (sync function for thread pool execution)"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PB-FM API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui.css" />
        <style>
            body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
            .header { background: #1f8aed; color: white; padding: 20px; margin: -20px -20px 20px -20px; }
            .quick-links { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .endpoint { background: white; border: 1px solid #e0e0e0; border-radius: 6px; padding: 15px; margin: 10px 0; }
            .method { font-weight: bold; color: #1f8aed; }
            a { color: #1f8aed; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 PB-FM API Documentation</h1>
            <p>REST API for Provenance Blockchain and Figure Markets data</p>
        </div>
        
        <div class="quick-links">
            <h3>📋 Quick Links</h3>
            <p><strong>OpenAPI Spec:</strong> <a href="/Prod/openapi.json" target="_blank">/Prod/openapi.json</a></p>
            <p><strong>Interactive Swagger UI Options:</strong></p>
            <ul style="margin-left: 20px;">
                <li><a href="https://generator3.swagger.io/index.html?url=https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/openapi.json" target="_blank">Swagger UI</a></li>
                <li><a href="https://editor.swagger.io/" target="_blank">Swagger Editor</a> (manual: File → Import URL → paste OpenAPI URL)</li>
                <li><a href="https://redoc.ly/redoc/?url=https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/openapi.json" target="_blank">ReDoc Documentation</a></li>
            </ul>
        </div>

        <h3>🔗 Available Endpoints</h3>
        
        <div class="endpoint">
            <div class="method">GET /api/markets</div>
            <p>Get current Figure Markets trading pairs and prices</p>
            <p><a href="/Prod/api/markets" target="_blank">Try it →</a></p>
        </div>

        <div class="endpoint">
            <div class="method">GET /api/account/{wallet_address}/balance</div>
            <p>Get account balance data for a wallet address</p>
            <p><a href="/Prod/api/account/pb1c9rqwfefggk3s3y79rh8quwvp8rf8ayr7qvmk8/balance" target="_blank">Try example →</a></p>
        </div>

        <div class="endpoint">
            <div class="method">GET /api/account/{wallet_address}/info</div>
            <p>Get account info and vesting status for a wallet address</p>
            <p><a href="/Prod/api/account/pb1c9rqwfefggk3s3y79rh8quwvp8rf8ayr7qvmk8/info" target="_blank">Try example →</a></p>
        </div>

        <div class="endpoint">
            <div class="method">POST /mcp</div>
            <p>MCP (Model Context Protocol) endpoint for AI agents</p>
            <p>Accepts JSON-RPC 2.0 formatted requests with MCP protocol</p>
        </div>

        <h3>💡 Usage Examples</h3>
        <pre style="background: #f8f9fa; padding: 15px; border-radius: 6px; overflow-x: auto;">
# Get all trading pairs
curl "https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/api/markets"

# Get account balance  
curl "https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/api/account/pb1c9rqwfefggk3s3y79rh8quwvp8rf8ayr7qvmk8/balance"

# MCP protocol example
curl -X POST "https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp" \\
  -H "Content-Type: application/json" \\
  -d '{"method": "tools/list", "params": {}, "jsonrpc": "2.0", "id": 1}'
        </pre>
    </body>
    </html>
    """
    return html_content

@fastapi_app.get("/docs", response_class=HTMLResponse)
async def custom_docs():
    """Custom documentation page that works with Lambda async context"""
    # Use thread pool to avoid event loop issues in Lambda
    loop = asyncio.get_event_loop()
    html_content = await loop.run_in_executor(None, _generate_docs_html)
    return HTMLResponse(content=html_content)

#########################################################################################
# AWS Lambda Handler
#########################################################################################

def lambda_handler(event, context):
    """Dual-protocol AWS Lambda handler: MCP + REST API with path-based routing"""
    
    try:
        # Extract request details
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '/mcp')
        
        # Path-based routing: determine which handler to use
        if path.startswith('/api/') or path in ['/', '/docs', '/openapi.json']:
            # Route to FastAPI for REST endpoints and documentation
            print(f"🌐 Routing {http_method} {path} to FastAPI handler")
            return fastapi_handler(event, context)
        else:
            # Route to MCP handler (default for /mcp and unknown paths)
            print(f"🔧 Routing {http_method} {path} to MCP handler")
            # Continue with existing MCP debug logic
            headers = event.get('headers', {})
            query_params = event.get('queryStringParameters') or {}
            body = event.get('body') or ''
        
        # Debug logging
        print("🔍 === MCP REQUEST DEBUG ===")
        print(f"📍 Timestamp: {datetime.now(UTC).isoformat()}")
        print(f"📍 Method: {http_method}")
        print(f"📍 Path: {path}")
        print(f"📍 Query Params: {query_params}")
        print(f"📍 Request Source IP: {event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')}")
        print(f"📍 Request ID: {event.get('requestContext', {}).get('requestId', 'unknown')}")
        print(f"📍 Raw Event: {json.dumps(event, indent=2, default=str)}")
        print(f"📍 Headers:")
        for key, value in headers.items():
            print(f"   {key}: {value}")
        print(f"📍 Body: {body[:200]}{'...' if len(body) > 200 else ''}")
        print(f"📍 Body Length: {len(body)}")
        print(f"📍 Context: {context}")
        
        # Get Accept header (case-insensitive)
        accept_header = ''
        content_type = ''
        origin = ''
        user_agent = ''
        authorization = ''
        connection = ''
        upgrade = ''
        
        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower == 'accept':
                accept_header = value
            elif key_lower == 'content-type':
                content_type = value
            elif key_lower == 'origin':
                origin = value
            elif key_lower == 'user-agent':
                user_agent = value
            elif key_lower == 'authorization':
                authorization = value
            elif key_lower == 'connection':
                connection = value
            elif key_lower == 'upgrade':
                upgrade = value
        
        print(f"📍 Parsed Accept: {accept_header}")
        print(f"📍 Parsed Content-Type: {content_type}")
        print(f"📍 Parsed Origin: {origin}")
        print(f"📍 Parsed User-Agent: {user_agent}")
        print(f"📍 Parsed Authorization: {'[PRESENT]' if authorization else '[NONE]'}")
        print(f"📍 Parsed Connection: {connection}")
        print(f"📍 Parsed Upgrade: {upgrade}")
        
        # Check if this looks like a capability check or connection probe
        if not body and http_method == 'POST':
            print("⚠️ WARNING: Empty body POST request - potential capability check")
        
        if 'upgrade' in connection.lower() or upgrade:
            print("⚠️ WARNING: Client attempting protocol upgrade")
            
        # Check for WebSocket or SSE connection attempts
        if 'websocket' in upgrade.lower():
            print("❌ DETECTED: WebSocket upgrade attempt - unsupported")
            return {
                'statusCode': 426,
                'headers': {
                    'Content-Type': 'text/plain',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept'
                },
                'body': 'Upgrade Required - WebSocket not supported, use HTTP POST'
            }
        
        if 'text/event-stream' in accept_header and http_method != 'GET':
            print("⚠️ WARNING: SSE Accept header on non-GET request")
        
        if http_method == 'GET':
            print("🔎 Processing GET request")
            # MCP Streamable HTTP spec: GET requests for SSE
            if 'text/event-stream' in accept_header:
                print("❌ Client requesting SSE - returning 405")
                # Client wants SSE - we don't support it, return 405
                response = {
                    'statusCode': 405,
                    'headers': {
                        'Content-Type': 'text/plain',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept',
                        'Allow': 'POST, OPTIONS'
                    },
                    'body': 'Method Not Allowed - SSE not supported, use HTTP POST'
                }
            else:
                print("✅ Returning server info for GET request")
                # Regular GET request - return server info
                response = {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept'
                    },
                    'body': json.dumps({
                        'name': 'pb-fm-mcp',
                        'version': '0.1.0',
                        'transport': 'http',  # HTTP-only transport
                        'capabilities': {
                            'tools': True,
                            'streaming': False
                        }
                    })
                }
        
        elif http_method == 'POST':
            print("🔎 Processing POST request")
            
            # Try to parse JSON body if present
            json_body = None
            if body:
                try:
                    json_body = json.loads(body)
                    print(f"📍 Parsed JSON Body: {json.dumps(json_body, indent=2)}")
                except json.JSONDecodeError as e:
                    print(f"⚠️ Failed to parse JSON body: {e}")
            
            # Check if client accepts both application/json and text/event-stream
            if 'application/json' in accept_header and 'text/event-stream' in accept_header:
                print("✅ Proper MCP client detected - using MCP handler")
                # Proper MCP client - use MCP handler
                response = mcp_server.handle_request(event, context)
            else:
                print("⚠️ Non-standard accept header - using MCP handler anyway")
                # Regular POST request - use MCP handler
                response = mcp_server.handle_request(event, context)
        
        elif http_method == 'OPTIONS':
            print("🔎 Processing OPTIONS (CORS preflight) request")
            response = mcp_server.handle_request(event, context)
        
        else:
            print(f"🔎 Processing {http_method} request through MCP handler")
            # Handle other requests through MCP handler
            response = mcp_server.handle_request(event, context)
        
        # Debug response
        print("📤 === MCP RESPONSE DEBUG ===")
        print(f"📍 Status Code: {response.get('statusCode')}")
        print(f"📍 Response Headers:")
        for key, value in response.get('headers', {}).items():
            print(f"   {key}: {value}")
        response_body = response.get('body', '')
        print(f"📍 Response Body: {response_body[:200]}{'...' if len(response_body) > 200 else ''}")
        print(f"📍 Response Body Length: {len(response_body)}")
        print("🔍 === END DEBUG ===\n")
        
        return response
        
    except Exception as e:
        print(f"🚨 EXCEPTION in lambda_handler: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept'
            },
            'body': json.dumps({'error': 'Internal server error', 'message': str(e)})
        }