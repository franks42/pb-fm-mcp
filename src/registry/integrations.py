"""
Integration helpers for MCP and FastAPI

This module provides integration functions to connect the unified function registry
with MCP server and FastAPI applications.
"""

import asyncio
import inspect
from typing import Callable, Dict, Any, List

# Conditional FastAPI import to avoid import errors
try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.routing import APIRoute
    FASTAPI_AVAILABLE = True
except ImportError:
    # Define minimal stubs for type checking
    FastAPI = None
    HTTPException = None 
    Request = None
    APIRoute = None
    FASTAPI_AVAILABLE = False

from .registry import FunctionRegistry, FunctionMeta, Protocol
from .generators import RegistryGenerator, MCPToolGenerator


class MCPIntegration:
    """Integration helper for MCP server"""
    
    @staticmethod
    def register_mcp_tools(mcp_server, registry: FunctionRegistry):
        """
        Register all MCP functions from registry as MCP tools using @async_to_sync_mcp_tool decorator.
        
        Args:
            mcp_server: The MCP server instance
            registry: Function registry containing decorated functions
        """
        # Import the async_to_sync_mcp_tool decorator
        try:
            from async_wrapper import async_to_sync_mcp_tool
        except ImportError:
            try:
                from ..async_wrapper import async_to_sync_mcp_tool
            except ImportError:
                # Fallback - assume it's available in lambda_handler context
                import sys
                async_to_sync_mcp_tool = getattr(sys.modules.get('__main__'), 'async_to_sync_mcp_tool', None)
                if not async_to_sync_mcp_tool:
                    raise ImportError("Cannot import async_to_sync_mcp_tool decorator")
        
        mcp_functions = registry.get_mcp_functions()
        
        for meta in mcp_functions:
            # Use the original function directly with proper decorator
            original_func = meta.func
            
            # Apply the @async_to_sync_mcp_tool decorator to the original function
            # This converts async function to sync for AWS MCP Lambda handler
            decorated_func = async_to_sync_mcp_tool(mcp_server)(original_func)
            
            # The decorator handles registration automatically


class FastAPIIntegration:
    """Integration helper for FastAPI"""
    
    @staticmethod
    def register_rest_routes(fastapi_app, registry: FunctionRegistry):
        """
        Register all REST functions from registry as FastAPI routes.
        
        Args:
            fastapi_app: The FastAPI application instance
            registry: Function registry containing decorated functions
        """
        if not FASTAPI_AVAILABLE:
            print("⚠️ FastAPI not available, skipping REST route registration")
            return
        rest_functions = registry.get_rest_functions()
        
        for meta in rest_functions:
            if not meta.rest_path:
                continue
                
            # Create route handler
            def create_route_handler(function_meta: FunctionMeta):
                async def route_handler(request: Request):
                    try:
                        # Extract parameters based on function signature
                        sig = function_meta.signature
                        kwargs = {}
                        
                        # Handle path parameters
                        path_params = request.path_params
                        for param_name in path_params:
                            if param_name in sig.parameters:
                                kwargs[param_name] = path_params[param_name]
                        
                        # Handle query parameters
                        query_params = request.query_params
                        for param_name, param in sig.parameters.items():
                            if param_name in ('self', 'cls'):
                                continue
                            
                            if param_name not in kwargs and param_name in query_params:
                                # Type conversion based on annotation
                                param_type = function_meta.type_hints.get(param_name, str)
                                raw_value = query_params[param_name]
                                
                                try:
                                    if param_type == int:
                                        kwargs[param_name] = int(raw_value)
                                    elif param_type == float:
                                        kwargs[param_name] = float(raw_value)
                                    elif param_type == bool:
                                        kwargs[param_name] = raw_value.lower() in ('true', '1', 'yes', 'on')
                                    else:
                                        kwargs[param_name] = raw_value
                                except (ValueError, TypeError):
                                    raise HTTPException(
                                        status_code=400, 
                                        detail=f"Invalid value for parameter {param_name}: {raw_value}"
                                    )
                        
                        # Handle request body for POST/PUT/PATCH
                        if function_meta.rest_method in ['POST', 'PUT', 'PATCH']:
                            if request.headers.get('content-type', '').startswith('application/json'):
                                try:
                                    body = await request.json()
                                    if isinstance(body, dict):
                                        # Merge body parameters
                                        for param_name, param in sig.parameters.items():
                                            if param_name in ('self', 'cls'):
                                                continue
                                            if param_name not in kwargs and param_name in body:
                                                kwargs[param_name] = body[param_name]
                                except Exception as e:
                                    raise HTTPException(status_code=400, detail=f"Invalid JSON body: {str(e)}")
                        
                        # Set defaults for missing optional parameters
                        for param_name, param in sig.parameters.items():
                            if param_name in ('self', 'cls'):
                                continue
                            if param_name not in kwargs and param.default != param.empty:
                                kwargs[param_name] = param.default
                        
                        # Call the function with REST-specific async handling
                        # For REST endpoints, wrap async functions in sync execution to avoid
                        # Lambda + FastAPI + Mangum event loop issues
                        
                        if asyncio.iscoroutinefunction(function_meta.func):
                            # Async function - wrap in sync execution for REST API
                            # This avoids the "no current event loop" issues in Lambda
                            import concurrent.futures
                            
                            def run_async_in_thread():
                                """Run async function in dedicated thread with its own event loop."""
                                try:
                                    # Create new event loop for this thread
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    try:
                                        return loop.run_until_complete(function_meta.func(**kwargs))
                                    finally:
                                        loop.close()
                                except Exception as e:
                                    print(f"🚨 Error in thread execution: {e}")
                                    raise
                            
                            try:
                                # Execute async function in thread pool with dedicated event loop
                                with concurrent.futures.ThreadPoolExecutor() as pool:
                                    future = pool.submit(run_async_in_thread)
                                    result = future.result(timeout=30)  # Add timeout
                            except Exception as e:
                                print(f"🚨 Thread pool execution failed: {e}")
                                # Fallback: try sync wrapper approach
                                try:
                                    result = asyncio.run(function_meta.func(**kwargs))
                                except Exception as fallback_error:
                                    print(f"🚨 Fallback asyncio.run also failed: {fallback_error}")
                                    raise HTTPException(status_code=500, detail=f"Async execution failed: {str(e)}")
                        else:
                            # Sync function - call directly
                            result = function_meta.func(**kwargs)
                        
                        # Handle error responses
                        if isinstance(result, dict) and result.get("MCP-ERROR"):
                            raise HTTPException(status_code=500, detail=result["MCP-ERROR"])
                        
                        return result
                        
                    except HTTPException:
                        raise
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=str(e))
                
                return route_handler
            
            # Register the route
            route_handler = create_route_handler(meta)
            
            # Add route to FastAPI app
            fastapi_app.add_api_route(
                path=meta.rest_path,
                endpoint=route_handler,
                methods=[meta.rest_method],
                summary=meta.description,
                description=meta.docstring,
                tags=meta.tags,
                name=meta.name
            )
    
    @staticmethod
    def update_openapi_schema(fastapi_app: FastAPI, registry: FunctionRegistry):
        """
        Update FastAPI's OpenAPI schema with registry-generated documentation.
        
        Args:
            fastapi_app: The FastAPI application instance
            registry: Function registry containing decorated functions
        """
        generator = RegistryGenerator(registry)
        
        # Get current OpenAPI schema
        openapi_schema = fastapi_app.openapi()
        
        # Update with registry-generated paths
        registry_paths = generator.generate_openapi_paths()
        if 'paths' not in openapi_schema:
            openapi_schema['paths'] = {}
        
        # Merge registry paths with existing paths
        openapi_schema['paths'].update(registry_paths)
        
        # Update the schema
        fastapi_app.openapi_schema = openapi_schema