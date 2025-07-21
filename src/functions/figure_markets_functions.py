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
except ImportError:
    try:
        from registry import api_function
    except ImportError:
        from src.registry import api_function

# Set up logging
logger = structlog.get_logger()

# Type alias for JSON response
JSONType = Dict[str, Any]

# Helper function for sync HTTP GET requests (Figure Markets APIs)
def http_get_json(url: str, params=None) -> JSONType:
    """
    Helper function for sync HTTP GET requests with JSON response for Figure Markets APIs.
    
    Args:
        url: The URL to fetch
        params: Optional query parameters
        
    Returns:
        JSON response as dictionary or error dict
    """
    try:
        with httpx.Client() as client:
            client.headers['accept-encoding'] = 'identity'
            response = client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching {url}: {e}")
        return {"MCP-ERROR": f"HTTP error: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        return {"MCP-ERROR": f"Unexpected error: {str(e)}"}


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
    
    # Run sync HTTP call in thread pool to avoid event loop conflicts
    import asyncio
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, http_get_json, url)
    
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
    import asyncio
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, http_get_json, url, params)
    
    if response.get("MCP-ERROR"):
        return response
    
    return response


@api_function(
    protocols=["mcp", "rest"], 
    path="/api/fm_account_balance/{wallet_address}",
    method="GET",
    tags=["account", "balance", "markets"],
    description="Fetch Figure Markets account balance data"
)
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
    url = f'https://api.figuremarkets.com/service-account-balance/api/v1/account/{wallet_address}/balance'
    
    # Run sync HTTP call in thread pool to avoid event loop conflicts  
    import asyncio
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, http_get_json, url)
    
    if response.get("MCP-ERROR"):
        return response
    
    return response


@api_function(
    protocols=["mcp", "rest"],
    path="/api/fm_account_info/{wallet_address}",
    method="GET", 
    tags=["account", "info", "markets"],
    description="Fetch Figure Markets account information"
)
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
    url = f'https://api.figuremarkets.com/service-account/api/v1/account/{wallet_address}'
    
    # Run sync HTTP call in thread pool to avoid event loop conflicts
    import asyncio
    loop = asyncio.get_event_loop() 
    response = await loop.run_in_executor(None, http_get_json, url)
    
    if response.get("MCP-ERROR"):
        return response
        
    return response