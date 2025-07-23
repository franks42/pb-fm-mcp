"""
Simplified integration helpers for FastAPI with direct async support.
For use with AWS Lambda Web Adapter + Uvicorn deployment.
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
    FastAPI = None
    HTTPException = None 
    Request = None
    APIRoute = None
    FASTAPI_AVAILABLE = False

from .registry import FunctionRegistry, FunctionMeta, Protocol
from .generators import RegistryGenerator, MCPToolGenerator


class FastAPIIntegration:
    """Simplified integration helper for FastAPI with direct async support"""
    
    @staticmethod
    def register_rest_routes(fastapi_app, registry: FunctionRegistry):
        """
        Register all REST functions from registry as FastAPI routes.
        Simplified version for Lambda Web Adapter deployment.
        
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
                
            # Create route handler with direct async support
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
                        
                        # SIMPLIFIED: Direct async execution - no thread wrapper needed!
                        if asyncio.iscoroutinefunction(function_meta.func):
                            result = await function_meta.func(**kwargs)  # ✅ Direct await!
                        else:
                            result = function_meta.func(**kwargs)
                        
                        # Handle error responses
                        if isinstance(result, dict) and result.get("MCP-ERROR"):
                            raise HTTPException(status_code=500, detail=result["MCP-ERROR"])
                        
                        return result
                        
                    except HTTPException:
                        raise
                    except Exception as e:
                        print(f"🚨 Error in route handler: {e}")
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