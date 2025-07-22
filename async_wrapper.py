#!/usr/bin/env python3
"""
Async wrapper decorator for MCPLambdaHandler compatibility
"""

import asyncio
import inspect
from functools import wraps
from typing import Callable, Any

def sync_wrapper(async_func: Callable) -> Callable:
    """
    Decorator to wrap async functions for MCPLambdaHandler compatibility.
    
    This allows us to keep all async function implementations unchanged
    while making them work with MCPLambdaHandler which doesn't await async functions.
    
    Usage:
        @mcp_server.tool()
        @sync_wrapper
        async def my_async_function(param: str) -> dict:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://api.example.com/{param}")
                return response.json()
    """
    
    @wraps(async_func)
    def wrapper(*args, **kwargs):
        # Check if function is actually async
        if not inspect.iscoroutinefunction(async_func):
            # If it's not async, just call it directly
            return async_func(*args, **kwargs)
        
        # Run the async function and return the result
        try:
            return asyncio.run(async_func(*args, **kwargs))
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                # If we're already in an event loop, use get_running_loop
                try:
                    loop = asyncio.get_running_loop()
                    return loop.run_until_complete(async_func(*args, **kwargs))
                except RuntimeError:
                    # No running loop - create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(async_func(*args, **kwargs))
                    finally:
                        loop.close()
                        asyncio.set_event_loop(None)
            else:
                raise
    
    return wrapper

def async_to_sync_mcp_tool(mcp_server):
    """
    Decorator factory that combines mcp_server.tool() with sync_wrapper.
    
    Usage:
        @async_to_sync_mcp_tool(mcp_server)
        async def my_async_function(param: str) -> dict:
            # async implementation stays the same
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://api.example.com/{param}")
                return response.json()
    """
    def decorator(async_func: Callable) -> Callable:
        # First apply the sync wrapper
        sync_func = sync_wrapper(async_func)
        # Then apply the MCP tool decorator
        return mcp_server.tool()(sync_func)
    
    return decorator