import asyncio
import copy
import json
import httpx
import sys
from decimal import Decimal
from hastra_types import JSONType


class JsonDecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


def parse_amount(val: object) -> int | Decimal:
    """Parse a value as int if integer-like, else as Decimal for high-precision decimals."""
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        if val.isdigit() or (val.startswith('-') and val[1:].isdigit()):
            return int(val)
        try:
            dec = Decimal(val)
            if dec == dec.to_integral_value():
                return int(dec)
            return dec
        except Exception:
            pass
    # fallback: try Decimal
    return Decimal(str(val))

from datetime import datetime, timezone
from typing import Tuple, Any, Dict, List, Union


#########################################################################################
## helper functions
#########################################################################################

def datetime_to_ms(dt):
    """Convert datetime to milliseconds since epoch"""
    if dt.tzinfo is None:
        # Assume UTC if no timezone specified
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)

def ms_to_datetime(ms_timestamp, tz=timezone.utc):
    """Convert milliseconds since epoch to datetime"""
    return datetime.fromtimestamp(ms_timestamp / 1000, tz=tz)

def current_ms():
    """Get current time in milliseconds since epoch"""
    return int(datetime.now(timezone.utc).timestamp() * 1000)



from typing import TypedDict

class AmountDenomT(TypedDict):
    amount: int | Decimal
    denom: str


def is_amount_denom_type(a_d: dict) -> bool:
    return (
        (isinstance(a_d.get('amount', None), (int, Decimal))) and
        isinstance(a_d.get('denom', None), str)
    )


def is_same_denom(amt, *amts) -> bool:
    if not is_amount_denom_type(amt) : return False
    for an_amt in amts:
        if not (is_amount_denom_type(an_amt) and
                amt['denom'] == an_amt['denom']):
            return False
    return True


def amount_denom_add(amt: AmountDenomT, *amts: AmountDenomT) -> AmountDenomT:
    r_amt = copy.deepcopy(amt)
    r_amt['amount'] = parse_amount(r_amt['amount'])
    for an_amt in amts:
        if is_same_denom(r_amt, an_amt):
            r_amt['amount'] = parse_amount(r_amt['amount']) + parse_amount(an_amt['amount'])
        else:
            raise Exception("ERROR - Cannot add amounts of different denom's.")
    return r_amt

###

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


class WorkerLogger:
    """Simple logger that works in Cloudflare Workers environment.
    
    This logger is designed to work in environments where the standard Python logging
    module might not be available, such as Cloudflare Workers running Python via Pyodide.
    It provides basic logging methods that output to standard output with print.
    """
    
    @staticmethod
    def debug(msg, *args, **kwargs):
        """Log a debug message."""
        print(f"DEBUG: {msg % args if args else msg}")
    
    @staticmethod
    def info(msg, *args, **kwargs):
        """Log an info message."""
        print(f"INFO: {msg % args if args else msg}")
    
    @staticmethod
    def warning(msg, *args, **kwargs):
        """Log a warning message."""
        print(f"WARNING: {msg % args if args else msg}")
    
    @staticmethod
    def error(msg, *args, **kwargs):
        """Log an error message."""
        print(f"ERROR: {msg % args if args else msg}")
    
    @staticmethod
    def critical(msg, *args, **kwargs):
        """Log a critical message."""
        print(f"CRITICAL: {msg % args if args else msg}")

# Create a default logger instance
default_logger = WorkerLogger()
