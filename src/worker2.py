import asgi
# import httpx
import sys

# from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from typing import Tuple, Any, Dict, List, Union

from exceptions import HTTPException, http_exception

###

# Union type for mixed JSON values
JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]


sys.path.insert(0, "/session/metadata/vendor")
sys.path.insert(0, "/session/metadata")

###

mcp = FastMCP("Hastra-FM-MCP", stateless_http=True, json_response=True)
# mcp.mcp_context_read = False
mcp.mcp_context_read = True

###

#########################################################################################
## helper functions
#########################################################################################

# def datetime_to_ms(dt):
#     """Convert datetime to milliseconds since epoch"""
#     if dt.tzinfo is None:
#         # Assume UTC if no timezone specified
#         dt = dt.replace(tzinfo=timezone.utc)
#     return int(dt.timestamp() * 1000)

# def ms_to_datetime(ms_timestamp, tz=timezone.utc):
#     """Convert milliseconds since epoch to datetime"""
#     return datetime.fromtimestamp(ms_timestamp / 1000, tz=tz)

# def current_ms():
#     """Get current time in milliseconds since epoch"""
#     return int(datetime.now(timezone.utc).timestamp() * 1000)

###

# async def async_http_get_json(
#     url: str, 
#     params: dict | None = None,
#     timeout: float = 10.0,
#     connect_timeout: float = 5.0
# ) -> JSONValue:
#     """Make an async HTTP GET request and return JSON response.
    
#     Args:
#         url: The URL to send the GET request to
#         params: Query parameters to include
#         timeout: Total request timeout in seconds
#         connect_timeout: Connection timeout in seconds
        
#     Returns:
#         JSON response data on success, or error dict with 'MCP-ERROR' key on failure
#     """
    
#     if mcp.mcp_context_read == False:
#         mcp.mcp_context_read = True
#         return {"MCP-ERROR": "Must review MCP server's context first! - Call get_system_context() before using this or other functions."}

#     if params is None:
#         params = {}
        
#     timeout_config = httpx.Timeout(timeout, connect=connect_timeout)
#     headers = {"Accept": "application/json"}
    
#     async with httpx.AsyncClient(timeout=timeout_config) as client:
#         try:
#             response = await client.get(url, params=params, headers=headers)
#             response.raise_for_status()
            
#             # Validate content type
#             content_type = response.headers.get("content-type", "")
#             if not content_type.startswith("application/json"):
#                 return {"MCP-ERROR": f"Expected JSON, got {content_type}"}
                
#             return response.json()
            
#         except httpx.TimeoutException:
#             return {"MCP-ERROR": "Network Error: Request timed out"}
#         except httpx.HTTPStatusError as e:
#             return {"MCP-ERROR": f"HTTP error: {e.response.status_code}"}
#         except httpx.RequestError as e:
#             return {"MCP-ERROR": f"Request error: {e}"}
#         except ValueError as e:
#             return {"MCP-ERROR": f"Invalid JSON response: {e}"}
#         except Exception as e:
#             return {"MCP-ERROR": f"Unknown exception raised: {e}"}


#########################################################################################
## resources
#########################################################################################

# @mcp.resource("system://context")
# @mcp.tool()
# async def get_system_context() -> str:
#     """
#     REQUIRED READING: Essential system context that MUST be read before using any tools.
#     Contains critical usage guidelines, data handling protocols, and server capabilities.
#     Returns:
#         str: return is md formatted
#     """
#     url = "https://raw.githubusercontent.com/franks42/FigureMarkets-MCP-Server/refs/heads/main/FigureMarketsContext.md"
    
#     timeout = httpx.Timeout(10.0, connect=5.0)
    
#     async with httpx.AsyncClient(timeout=timeout) as client:
#         try:
#             response = await client.get(url)
#             response.raise_for_status()  # Raises exception for 4xx/5xx
#             return response.text
#         except httpx.TimeoutException:
#             return "Network Error: Request timed out"
#         except httpx.HTTPStatusError as e:
#             return f"HTTP error: {e.response.status_code}"
#         except httpx.RequestError as e:
#             return f"Request error: {e}"

#########################################################################################
## tools
#########################################################################################

# @mcp.tool()
# async def fetch_last_crypto_token_price(token_pair : str="HASH-USD", last_number_of_trades : int=1) -> JSONValue:
#     """For the crypto token_pair, e.g. HASH-USD, fetch the prices for the last_number_of_trades 
#     from the Figure Markets exchange.
#     Args:
#         token_pair (str, optional): Two token/crypto symbols separated by '-', like BTC-USDC. Defaults to HASH-USD.
#         last_number_of_trades (int, optional): Ask for specified number of trades to return. Defaults to 1.
#     Returns:
#         JSONValue: json dict where attribute 'matches' has a list of individual trade details
#     """
#     url = 'https://www.figuremarkets.com/service-hft-exchange/api/v1/trades/' + token_pair 
#     params = {'size': last_number_of_trades}
#     response = await async_http_get_json(url, params=params)
#     if response.get("MCP-ERROR"): return response
#     #massage json response data
#     return response

###

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def adt(a: int, b: int) -> int:
    """Adt is a special operation on two numbers because it always returns the ultimate answer."""
    return 42

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

@mcp.tool()
def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Calculate BMI given weight in kg and height in meters"""
    return weight_kg / (height_m**2)

@mcp.prompt()
def echo_prompt(message: str) -> str:
    """Create an echo prompt"""
    return f"Please process this message: {message}"

###


###

async def on_fetch(request, env, ctx):
    app = mcp.streamable_http_app()
    app.add_exception_handler(HTTPException, http_exception)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    ret = await asgi.fetch(app, request, env, ctx)
    return ret
