"""
Unified FastAPI application for AWS Lambda Web Adapter deployment.
Clean implementation supporting both MCP protocol and REST API endpoints.

Architecture:
- MCP Protocol: Uses sync wrappers (AWS MCP Handler requirement)
- REST API: Uses native async (Web Adapter strength)  
- Both protocols share the same function registry
"""
import asyncio
import json
import sys
from functools import wraps
from pathlib import Path
from typing import Callable, Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory for version imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from version import get_version_string, get_full_version_info

# Import registry and function modules
from registry import get_registry
from registry.registry import FunctionRegistry, FunctionMeta
import functions  # This registers all @api_function decorated functions

# Import AWS MCP Handler
from awslabs.mcp_lambda_handler import MCPLambdaHandler


# =============================================================================
# AWS MCP Handler Snake Case Fix (Monkey Patch)
# =============================================================================

def create_snake_case_tool_decorator(original_tool_method):
    """
    Comprehensive monkey patch that preserves original function names instead of converting to camelCase.
    
    AWS Lambda MCP Handler (v0.1.6) automatically converts snake_case to camelCase, which:
    1. Violates MCP community standards (90% use snake_case) 
    2. Creates confusion and inconsistency between function names and tool names
    3. Goes against developer intent and naming conventions
    
    This monkey patch intercepts AWS's conversion and restores the original snake_case names
    by patching BOTH the tools registry (for display) AND tool_implementations (for execution).
    
    Related: GitHub issue awslabs/mcp#757 - AWS investigating this bug for future fix.
    TODO: Remove this patch when AWS provides native snake_case support.
    """
    def patched_tool(self):
        def decorator(func):
            # Store original name before AWS modifies it
            original_name = func.__name__
            
            # Let AWS create the tool with its camelCase conversion
            aws_decorator = original_tool_method(self)
            wrapped_func = aws_decorator(func)
            
            # Find and fix the name in AWS's internal tools registry
            camel_name = ''.join([original_name.split('_')[0]] + 
                               [word.capitalize() for word in original_name.split('_')[1:]])
            
            # Fix the tool registration if AWS changed the name
            if (hasattr(self, 'tools') and camel_name in self.tools and 
                camel_name != original_name):
                # Move tool from camelCase key to original name key
                tool_definition = self.tools.pop(camel_name)
                # Fix the name field in the tool definition
                if isinstance(tool_definition, dict) and 'name' in tool_definition:
                    tool_definition['name'] = original_name
                # Register with correct name
                self.tools[original_name] = tool_definition
                
                # Also fix the tool_implementations mapping - this is critical for execution
                if (hasattr(self, 'tool_implementations') and camel_name in self.tool_implementations):
                    tool_func = self.tool_implementations.pop(camel_name)
                    self.tool_implementations[original_name] = tool_func
            
            return wrapped_func
        return decorator
    return patched_tool

# Apply the monkey patch before creating any MCP server instances
print("🐍 Applying AWS MCP Handler snake_case monkey patch...")
MCPLambdaHandler.tool = create_snake_case_tool_decorator(MCPLambdaHandler.tool)
print("✅ Snake_case monkey patch applied successfully")


# =============================================================================
# MCP Integration - Clean sync wrapper for AWS MCP Handler limitation
# =============================================================================

def create_mcp_sync_wrapper(async_func: Callable) -> Callable:
    """
    Clean sync wrapper specifically for AWS MCP Handler.
    
    AWS MCP Handler calls functions synchronously, so we need to convert
    async functions to sync. This is a clean, minimal implementation.
    """
    @wraps(async_func)
    def sync_wrapper(*args, **kwargs):
        if not asyncio.iscoroutinefunction(async_func):
            return async_func(*args, **kwargs)
            
        # Try asyncio.run first (cleanest approach)
        try:
            return asyncio.run(async_func(*args, **kwargs))
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                # Fallback: create new event loop in thread
                import concurrent.futures
                import threading
                
                def run_in_thread():
                    # Create isolated event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(async_func(*args, **kwargs))
                    finally:
                        loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result(timeout=30)
            else:
                raise
    
    return sync_wrapper


def register_mcp_tools(mcp_server: MCPLambdaHandler, registry: FunctionRegistry):
    """
    Clean MCP tool registration with proper sync wrapping.
    The monkey patch ensures snake_case names are preserved automatically.
    """
    mcp_functions = registry.get_mcp_functions()
    
    for func_meta in mcp_functions:
        # Create sync-wrapped version for MCP
        if asyncio.iscoroutinefunction(func_meta.func):
            sync_func = create_mcp_sync_wrapper(func_meta.func)
        else:
            sync_func = func_meta.func
            
        # Register with MCP server (monkey patch handles snake_case preservation)
        mcp_tool = mcp_server.tool()(sync_func)


# =============================================================================
# REST Integration - Native async for Web Adapter
# =============================================================================

def register_rest_routes(app: FastAPI, registry: FunctionRegistry):
    """
    Clean REST route registration with native async support.
    Web Adapter provides proper event loop, no wrappers needed.
    """
    rest_functions = registry.get_rest_functions()
    
    for func_meta in rest_functions:
        if not func_meta.rest_path:
            continue
            
        def create_route_handler(meta: FunctionMeta):
            async def route_handler(request: Request):
                try:
                    # Extract parameters from request
                    kwargs = {}
                    
                    # Path parameters
                    for param_name, param_value in request.path_params.items():
                        kwargs[param_name] = param_value
                    
                    # Query parameters with type conversion
                    for param_name, param in meta.signature.parameters.items():
                        if param_name in ('self', 'cls') or param_name in kwargs:
                            continue
                            
                        if param_name in request.query_params:
                            raw_value = request.query_params[param_name]
                            param_type = meta.type_hints.get(param_name, str)
                            
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
                    
                    # Set defaults for missing optional parameters
                    for param_name, param in meta.signature.parameters.items():
                        if (param_name not in ('self', 'cls') and 
                            param_name not in kwargs and 
                            param.default != param.empty):
                            kwargs[param_name] = param.default
                    
                    # Execute function - native async support in Web Adapter!
                    if asyncio.iscoroutinefunction(meta.func):
                        result = await meta.func(**kwargs)  # Clean async execution
                    else:
                        result = meta.func(**kwargs)
                    
                    # Handle error responses
                    if isinstance(result, dict) and result.get("MCP-ERROR"):
                        raise HTTPException(status_code=500, detail=result["MCP-ERROR"])
                    
                    return result
                    
                except HTTPException:
                    raise
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))
            
            return route_handler
        
        # Register route
        handler = create_route_handler(func_meta)
        app.add_api_route(
            path=func_meta.rest_path,
            endpoint=handler,
            methods=[func_meta.rest_method],
            summary=func_meta.description,
            description=func_meta.docstring,
            tags=func_meta.tags,
            name=func_meta.name
        )


# =============================================================================
# Mock Lambda Context for Container Environment
# =============================================================================

class MockLambdaContext:
    """Minimal mock context for AWS MCP Handler in container environment."""
    def __init__(self):
        self.function_name = "pb-fm-mcp-container"
        self.function_version = "$LATEST"  
        self.invoked_function_arn = "arn:aws:lambda:us-west-1:123456789012:function:pb-fm-mcp-container"
        self.memory_limit_in_mb = "512"
        self.remaining_time_in_millis = lambda: 30000
        self.aws_request_id = "container-request-id"


# =============================================================================
# Unified FastAPI Application
# =============================================================================

# Initialize MCP server
print("🔧 Initializing MCP server...")
mcp_server = MCPLambdaHandler(name="pb-fm-mcp", version=get_version_string())

# Create FastAPI app
# Handle API Gateway stage path for proper documentation URLs
import os

# Get the stage path from environment or use empty string for local development
stage_path = os.environ.get("API_GATEWAY_STAGE_PATH", "")

app = FastAPI(
    title="PB-FM Unified API",
    description="Unified MCP + REST API for Provenance Blockchain and Figure Markets data",
    version=get_version_string(),
    docs_url="/docs",
    openapi_url="/openapi.json",
    root_path=stage_path,  # This ensures Swagger UI uses correct paths
    servers=[
        {"url": stage_path, "description": "Current deployment"},
        {"url": "/", "description": "Local development"}
    ] if stage_path else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for container readiness."""
    return {"status": "healthy", "version": get_version_string()}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with unified API information."""
    version_info = get_full_version_info()
    registry = get_registry()
    return {
        "name": "PB-FM Unified API",
        "version": version_info["version"],
        "build_number": version_info["build_number"],
        "build_datetime": version_info["build_datetime"],
        "environment": version_info["deployment_environment"],
        "description": "Unified MCP + REST API for Provenance Blockchain and Figure Markets data",
        "protocols": {
            "mcp": {
                "endpoint": "/mcp",
                "method": "POST",
                "tools": len(registry.get_mcp_functions())
            },
            "rest": {
                "endpoints": len(registry.get_rest_functions()),
                "docs": "/docs",
                "openapi": "/openapi.json"
            }
        },
        "endpoints": {
            "mcp": "/mcp",
            "docs": "/docs",
            "openapi": "/openapi.json", 
            "health": "/health"
        }
    }

# MCP connection test endpoint for Claude.ai
@app.get("/mcp")
async def mcp_connection_test():
    """Handle MCP connection test requests from Claude.ai"""
    return {
        "name": "PB-FM MCP Server",
        "version": get_version_string(), 
        "description": "MCP server for Provenance Blockchain and Figure Markets data",
        "protocol": "Model Context Protocol",
        "methods": ["POST"],
        "message": "Send POST requests with JSON-RPC 2.0 format to interact with MCP tools"
    }

# MCP endpoint - AWS MCP Handler expects sync execution
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Handle MCP protocol requests."""
    try:
        body = await request.json()
        context = MockLambdaContext()
        
        # AWS MCP Handler expects sync execution, so run in thread
        import concurrent.futures
        
        def sync_mcp_handler():
            # AWS MCP Handler expects Lambda event format, not direct JSON
            lambda_event = {
                "httpMethod": "POST",
                "headers": dict(request.headers),
                "body": json.dumps(body),
                "path": "/mcp",
                "pathParameters": None,
                "queryStringParameters": None,
                "requestContext": {
                    "requestId": "container-request-id"
                }
            }
            return mcp_server.handle_request(lambda_event, context)
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(sync_mcp_handler)
            aws_response = future.result(timeout=30)
        
        # AWS MCP Handler returns Lambda response format, extract the actual MCP response
        if isinstance(aws_response, dict) and 'body' in aws_response:
            # Parse the JSON body from AWS Lambda response format
            mcp_response = json.loads(aws_response['body'])
            return mcp_response
        else:
            # Direct response (shouldn't happen but handle gracefully)
            return aws_response
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        print(f"🚨 MCP handler error: {e}")
        raise HTTPException(status_code=500, detail=f"MCP processing error: {str(e)}")

# Register both protocols
print("🔧 Registering API functions...")
registry = get_registry()

print("🔧 Registering MCP tools...")
register_mcp_tools(mcp_server, registry)
print(f"✅ Registered {len(registry.get_mcp_functions())} MCP tools")

print("🔧 Registering REST routes...")
register_rest_routes(app, registry)
print(f"✅ Registered {len(registry.get_rest_functions())} REST endpoints")

print("📝 Unified MCP + REST server ready")