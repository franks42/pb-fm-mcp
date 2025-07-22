"""
Figure Markets Exchange Functions

Functions for fetching trading data from Figure Markets exchange.
All functions are decorated with @api_function to be automatically exposed via MCP and/or REST protocols.
"""

from typing import Dict, Any
import httpx
import structlog

# Handle import for both relative and absolute path contexts
try:
    from ..registry import api_function
    from ..utils import async_http_get_json
except ImportError:
    try:
        from registry import api_function
        from utils import async_http_get_json
    except ImportError:
        from src.registry import api_function
        from src.utils import async_http_get_json

# Set up logging
logger = structlog.get_logger()

# Type alias for JSON response
JSONType = Dict[str, Any]



#########################################################################################
# Figure Markets Exchange Functions
#########################################################################################

@api_function(
    protocols=["mcp", "rest"],
    path="/api/figure_markets_data",
    method="GET",
    tags=["markets", "trading"],
    description="Fetch current market data from Figure Markets exchange"
)
async def fetch_current_fm_data() -> JSONType:
    """
    Fetch the current market data from the Figure Markets exchange.
    
    The data is a list of trading pair details including identifiers,
    token denominations, and quote currencies for all available trading pairs.
    
    Returns:
        Dictionary containing:
        - List of trading pair details
        - Each pair includes 'id', 'denom', and 'quoteDenom' attributes
        
    Raises:
        HTTPError: If the Figure Markets API is unavailable
    """
    url = 'https://www.figuremarkets.com/service-hft-exchange/api/v1/markets'
    
    # Use async HTTP call directly
    response = await async_http_get_json(url)
    
    if response.get("MCP-ERROR"):
        return response
    
    return response


@api_function(
    protocols=["mcp", "rest"],
    path="/api/crypto_token_price/{token_pair}",
    method="GET",
    tags=["markets", "prices"],
    description="Fetch last crypto token prices from Figure Markets exchange"
)
async def fetch_last_crypto_token_price(token_pair: str = "HASH-USD", last_number_of_trades: int = 1) -> JSONType:
    """
    For the crypto token_pair, fetch the prices for the last number of trades 
    from the Figure Markets exchange.
    
    Args:
        token_pair: Two token/crypto symbols separated by '-', like BTC-USDC or HASH-USD
        last_number_of_trades: Number of recent trades to return (default: 1)
        
    Returns:
        Dictionary containing:
        - matches: List of individual trade details with prices and volumes
        
    Raises:
        HTTPError: If the Figure Markets API is unavailable
    """
    url = f'https://www.figuremarkets.com/service-hft-exchange/api/v1/trades/{token_pair}'
    params = {'size': last_number_of_trades}
    
    # Run sync HTTP call in thread pool to avoid event loop conflicts
    # Use async HTTP call directly
    response = await async_http_get_json(url, params=params)
    
    if response.get("MCP-ERROR"):
        return response
    
    return response


# NOTE: This API endpoint is not publicly accessible - Figure Markets account APIs are private
# @api_function(
#     protocols=["mcp", "rest"], 
#     path="/api/fm_account_balance/{wallet_address}",
#     method="GET",
#     tags=["account", "balance", "markets"],
#     description="Fetch Figure Markets account balance data"
# )
async def fetch_current_fm_account_balance_data(wallet_address: str) -> JSONType:
    """
    Fetch the current account balance data from the Figure Markets exchange 
    for the given wallet address' portfolio.
    
    The data includes balance details for all assets in the wallet including
    ETH ('neth.figure.se'), nano-HASH ('nhash'), SOL ('nsol.figure.se'), and others.
    
    Args:
        wallet_address: Wallet's Bech32 address
        
    Returns:
        Dictionary containing:
        - List of balance details for all assets
        - Each balance includes 'denom', 'amount', and other asset information
        
    Raises:
        HTTPError: If the Figure Markets API is unavailable
    """
    url = f'https://www.figuremarkets.com/service-account-balance/api/v1/account/{wallet_address}/balance'
    
    # Run sync HTTP call in thread pool to avoid event loop conflicts  
    # Use async HTTP call directly
    response = await async_http_get_json(url)
    
    if response.get("MCP-ERROR"):
        return response
    
    return response


# NOTE: This API endpoint is not publicly accessible - Figure Markets account APIs are private
# @api_function(
#     protocols=["mcp", "rest"],
#     path="/api/fm_account_info/{wallet_address}",
#     method="GET", 
#     tags=["account", "info", "markets"],
#     description="Fetch Figure Markets account information"
# )
async def fetch_current_fm_account_info(wallet_address: str) -> JSONType:
    """
    Fetch comprehensive account information from Figure Markets exchange
    for the given wallet address.
    
    Args:
        wallet_address: Wallet's Bech32 address
        
    Returns:
        Dictionary containing Figure Markets account information and status
        
    Raises:
        HTTPError: If the Figure Markets API is unavailable
    """
    url = f'https://www.figuremarkets.com/service-account/api/v1/account/{wallet_address}'
    
    # Use async HTTP call directly
    response = await async_http_get_json(url)
    
    if response.get("MCP-ERROR"):
        return response
        
    return response


@api_function(
    protocols=["mcp", "rest"],
    path="/api/figure_markets_assets_info",
    method="GET",
    tags=["assets", "markets"],
    description="Fetch list of assets traded on Figure Markets exchange"
)
async def fetch_figure_markets_assets_info() -> JSONType:
    """
    Fetch the list of assets, like crypto tokens, stable coins, and funds,
    that are traded on the Figure Markets exchange.
    
    Returns:
        List of dictionaries with asset information:
        - asset_name: Identifier to use for asset
        - asset_description: Description of the asset
        - asset_display_name: Display name for the asset
        - asset_type: Type of asset (CRYPTO, STABLECOIN, or FUND)
        - asset_exponent: 10 to the power of asset_exponent multiplied by amount of asset_denom yields the asset amount
        - asset_denom: Asset denomination
        
    Raises:
        HTTPError: If the Figure Markets API is unavailable
    """
    url = 'https://www.figuremarkets.com/service-hft-exchange/api/v1/assets'
    
    # Use async HTTP call directly
    response = await async_http_get_json(url)
    
    if isinstance(response, dict) and response.get("MCP-ERROR"):
        return response
    
    # Ensure we have valid response structure
    if not isinstance(response, dict) or 'data' not in response:
        return {"MCP-ERROR": f"Invalid response structure: {type(response)}"}
    
    asset_details_list = [{
        'asset_name': details['name'],
        'asset_description': details['description'],
        'asset_display_name': details['displayName'],
        'asset_type': details['type'],
        'asset_exponent': details['exponent'],
        'asset_denom': details['provenanceMarkerName']
    } for details in response['data']]
    
    return asset_details_list