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
        Register all MCP functions from registry as MCP tools.
        
        Args:
            mcp_server: The MCP server instance
            registry: Function registry containing decorated functions
        """
        generator = RegistryGenerator(registry)
        mcp_functions = registry.get_mcp_functions()
        
        for meta in mcp_functions:
            # Generate MCP tool definition
            tool_def = MCPToolGenerator.generate_mcp_tool(meta)
            
            # Create wrapper function for MCP server
            async def mcp_tool_wrapper(arguments: Dict[str, Any] = None) -> Dict[str, Any]:
                arguments = arguments or {}
                
                try:
                    # Call the original function with proper error handling
                    if asyncio.iscoroutinefunction(meta.func):
                        result = await meta.func(**arguments)
                    else:
                        # Run sync function in thread pool
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(None, meta.func, **arguments)
                    
                    # Handle MCP-ERROR responses
                    if isinstance(result, dict) and result.get("MCP-ERROR"):
                        return result
                    
                    return result
                    
                except Exception as e:
                    return {"MCP-ERROR": f"Function execution error: {str(e)}"}
            
            # Register the tool with MCP server
            # Note: We need to create a closure to capture the current meta
            def create_mcp_tool(function_meta: FunctionMeta):
                async def tool_func(arguments: Dict[str, Any] = None) -> Dict[str, Any]:
                    arguments = arguments or {}
                    
                    try:
                        # Call the original function
                        if asyncio.iscoroutinefunction(function_meta.func):
                            result = await function_meta.func(**arguments)
                        else:
                            loop = asyncio.get_event_loop()
                            result = await loop.run_in_executor(None, lambda: function_meta.func(**arguments))
                        
                        # Handle MCP-ERROR responses
                        if isinstance(result, dict) and result.get("MCP-ERROR"):
                            return result
                        
                        return result
                        
                    except Exception as e:
                        return {"MCP-ERROR": f"Function execution error: {str(e)}"}
                
                # Set the tool name and description
                tool_func.__name__ = function_meta.name
                tool_func.__doc__ = function_meta.docstring
                
                # Register with MCP server (no name parameter needed)
                return mcp_server.tool()(tool_func)
            
            # Register the tool
            create_mcp_tool(meta)


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
                        
                        # Call the function
                        if asyncio.iscoroutinefunction(function_meta.func):
                            result = await function_meta.func(**kwargs)
                        else:
                            loop = asyncio.get_event_loop()
                            result = await loop.run_in_executor(None, lambda: function_meta.func(**kwargs))
                        
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