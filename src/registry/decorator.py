"""
@api_function Decorator

The magical decorator that enables single function definitions to be automatically
exposed as both MCP tools and REST API endpoints with unified documentation.
"""

from typing import Callable, List, Optional, Union, Any
from functools import wraps
import asyncio

from .registry import get_registry, Protocol


def api_function(
    protocols: Union[List[str], List[Protocol]] = None,
    description: Optional[str] = None,
    path: Optional[str] = None,
    method: str = "GET",
    tags: Optional[List[str]] = None,
    name: Optional[str] = None
):
    """
    Decorator to register a function for automatic MCP and REST endpoint generation.
    
    This decorator enables a single function definition to be automatically exposed
    via multiple protocols with unified documentation from docstrings and type hints.
    
    Args:
        protocols: List of protocols to expose this function on. Defaults to ["mcp", "rest"]
        description: Custom description (overrides docstring)
        path: REST API path pattern (e.g., "/accounts/{address}/info")
        method: HTTP method for REST endpoint (GET, POST, etc.)
        tags: Tags for grouping functions in documentation
        name: Custom function name (defaults to actual function name)
    
    Example:
        ```python
        @api_function(
            protocols=["mcp", "rest"],
            path="/accounts/{address}/info",
            description="Fetch account information"
        )
        async def fetch_account_info(address: str) -> dict:
            '''
            Fetch account information for given Provenance address.
            
            Args:
                address: Bech32-encoded Provenance blockchain address
                
            Returns:
                Account data including balances and sequence number
            '''
            # Business logic here
            return await get_account_data(address)
        ```
    
    Returns:
        The decorated function with registry metadata attached
    """
    
    def decorator(func: Callable) -> Callable:
        # Default protocols if not specified
        func_protocols = protocols or ["mcp", "rest"]
        
        # Determine REST path if not provided
        rest_path = path
        if rest_path is None and ("rest" in func_protocols or Protocol.REST in func_protocols):
            # Auto-generate REST path from function name
            func_name = name or func.__name__
            # Convert snake_case to kebab-case and add leading slash
            rest_path = "/" + func_name.replace("_", "-")
        
        # Register the function in the global registry
        registry = get_registry()
        meta = registry.register(
            func=func,
            protocols=func_protocols,
            description=description,
            rest_path=rest_path,
            rest_method=method,
            tags=tags,
            name=name
        )
        
        # Create async-compatible wrapper
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            wrapper = async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            wrapper = sync_wrapper
        
        # Attach metadata to the wrapper function for introspection
        wrapper._api_meta = meta
        wrapper._original_func = func
        
        return wrapper
    
    return decorator


def get_function_meta(func: Callable) -> Optional[Any]:
    """
    Get the API metadata attached to a decorated function.
    
    Args:
        func: The decorated function
        
    Returns:
        FunctionMeta object if function is decorated, None otherwise
    """
    return getattr(func, '_api_meta', None)