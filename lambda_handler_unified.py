#!/usr/bin/env python3
"""
Unified AWS Lambda handler with proper dual-path routing.

Architecture:
- MCP requests (/mcp) → Direct AWS MCP Handler (no FastAPI)
- REST requests (/api/*, /docs, etc.) → FastAPI via Web Adapter
"""
import json
import sys
import os
from datetime import UTC, datetime
from pathlib import Path

# Add src directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# AWS Lambda MCP Handler
from awslabs.mcp_lambda_handler import MCPLambdaHandler

# Import registry and function modules
from registry import get_registry
import functions  # This registers all @api_function decorated functions

# Version management
from version import get_version_string


# =============================================================================
# AWS MCP Handler Snake Case Fix (Monkey Patch)
# =============================================================================

def create_snake_case_tool_decorator(original_tool_method):
    """
    Comprehensive monkey patch that preserves original function names instead of converting to camelCase.
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
# MCP Sync Wrapper for AWS MCP Handler
# =============================================================================

import asyncio
from functools import wraps
from typing import Callable, Any

def create_mcp_sync_wrapper(async_func: Callable) -> Callable:
    """
    Clean sync wrapper specifically for AWS MCP Handler.
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


# =============================================================================
# Initialize MCP Server
# =============================================================================

# Initialize the MCP server with dynamic version
mcp_server = MCPLambdaHandler(name="pb-fm-mcp", version=get_version_string())

# Register MCP tools
print("🔧 Registering MCP tools...")
registry = get_registry()
mcp_functions = registry.get_mcp_functions()

for func_meta in mcp_functions:
    # Create sync-wrapped version for MCP
    if asyncio.iscoroutinefunction(func_meta.func):
        sync_func = create_mcp_sync_wrapper(func_meta.func)
    else:
        sync_func = func_meta.func
        
    # Register with MCP server (monkey patch handles snake_case preservation)
    mcp_tool = mcp_server.tool()(sync_func)

print(f"✅ Registered {len(mcp_functions)} MCP tools")


# =============================================================================
# Native REST Handler (No FastAPI)
# =============================================================================

def handle_rest_request(event, context):
    """
    Native REST handler using Lambda events directly.
    No FastAPI, no framework overhead, just clean Lambda integration.
    """
    path = event.get('path', '')
    method = event.get('httpMethod', 'GET')
    
    # Import version for responses
    from version import get_version_string, get_full_version_info
    
    # Handle root endpoint
    if path == '/':
        version_info = get_full_version_info()
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
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
            })
        }
    
    # Handle health check
    elif path == '/health':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                "status": "healthy",
                "version": get_version_string()
            })
        }
    
    # Handle API routes
    elif path.startswith('/api/'):
        return handle_api_function(event, context)
    
    # Unknown path
    return {
        'statusCode': 404,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'error': 'Not Found',
            'message': f'Path {path} not found'
        })
    }


def handle_api_function(event, context):
    """Handle /api/* function calls using the registry"""
    path = event.get('path', '')
    method = event.get('httpMethod', 'GET')
    
    # Find matching function in registry
    for func_meta in registry.get_rest_functions():
        if func_meta.rest_path == path and func_meta.rest_method == method:
            try:
                # Extract parameters
                kwargs = {}
                
                # Path parameters from API Gateway (filter out proxy parameter)
                if event.get('pathParameters'):
                    for param_name, param_value in event['pathParameters'].items():
                        if param_name != 'proxy':  # Filter out API Gateway proxy parameter
                            kwargs[param_name] = param_value
                
                # Query string parameters
                if event.get('queryStringParameters'):
                    for param_name, param_value in event['queryStringParameters'].items():
                        # Type conversion based on function signature
                        param = func_meta.signature.parameters.get(param_name)
                        if param:
                            param_type = func_meta.type_hints.get(param_name, str)
                            kwargs[param_name] = convert_parameter_type(param_value, param_type)
                        else:
                            kwargs[param_name] = param_value
                
                # Body parameters for POST/PUT
                if method in ['POST', 'PUT', 'PATCH'] and event.get('body'):
                    try:
                        body_data = json.loads(event['body'])
                        if isinstance(body_data, dict):
                            for param_name, param_value in body_data.items():
                                param = func_meta.signature.parameters.get(param_name)
                                if param:
                                    param_type = func_meta.type_hints.get(param_name, str)
                                    kwargs[param_name] = convert_parameter_type(param_value, param_type)
                                else:
                                    kwargs[param_name] = param_value
                    except json.JSONDecodeError:
                        return {
                            'statusCode': 400,
                            'headers': {'Content-Type': 'application/json'},
                            'body': json.dumps({
                                'error': 'Bad Request',
                                'message': 'Invalid JSON in request body'
                            })
                        }
                
                # Add default values for missing optional parameters
                for param_name, param in func_meta.signature.parameters.items():
                    if param_name not in kwargs and param.default != param.empty:
                        kwargs[param_name] = param.default
                
                # Call the function
                if asyncio.iscoroutinefunction(func_meta.func):
                    result = asyncio.run(func_meta.func(**kwargs))
                else:
                    result = func_meta.func(**kwargs)
                
                # Handle error responses
                if isinstance(result, dict) and result.get("MCP-ERROR"):
                    return {
                        'statusCode': 500,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({
                            'error': 'Function Error',
                            'message': result["MCP-ERROR"]
                        })
                    }
                
                # Success response
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(result)
                }
                
            except Exception as e:
                print(f"🚨 Error in API function {func_meta.name}: {e}")
                import traceback
                traceback.print_exc()
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'error': 'Internal Server Error',
                        'message': str(e)
                    })
                }
    
    # No matching function found
    return {
        'statusCode': 404,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'error': 'Not Found',
            'message': f'No API function found for {method} {path}'
        })
    }


def convert_parameter_type(value: str, param_type: type) -> Any:
    """Convert string parameter to the correct type"""
    if param_type == int:
        return int(value)
    elif param_type == float:
        return float(value)
    elif param_type == bool:
        return value.lower() in ('true', '1', 'yes', 'on')
    else:
        return value


def handle_docs_request(event, context):
    """Simple docs handler - returns basic API information"""
    path = event.get('path', '')
    
    if path == '/docs':
        # Return simple HTML docs page
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html',
                'Access-Control-Allow-Origin': '*'
            },
            'body': """
<!DOCTYPE html>
<html>
<head>
    <title>PB-FM API Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .endpoint { background: #f4f4f4; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .method { color: #007bff; font-weight: bold; }
    </style>
</head>
<body>
    <h1>PB-FM API Documentation</h1>
    <p>Native Lambda REST API for Provenance Blockchain and Figure Markets data.</p>
    <h2>Available Endpoints:</h2>
    <div class="endpoint">
        <span class="method">GET</span> /health - Health check endpoint
    </div>
    <div class="endpoint">
        <span class="method">GET</span> /api/fetch_current_hash_statistics - Get HASH token statistics
    </div>
    <div class="endpoint">
        <span class="method">GET</span> /api/fetch_account_info/{wallet_address} - Get account information
    </div>
    <p>For MCP protocol access, use POST /mcp with JSON-RPC 2.0 format.</p>
</body>
</html>
"""
        }
    
    elif path == '/openapi.json':
        # Return basic OpenAPI spec
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                "openapi": "3.0.0",
                "info": {
                    "title": "PB-FM API",
                    "version": get_version_string(),
                    "description": "Native Lambda REST API"
                },
                "paths": {
                    "/health": {
                        "get": {
                            "summary": "Health check",
                            "responses": {
                                "200": {"description": "Healthy"}
                            }
                        }
                    }
                }
            })
        }


# =============================================================================
# Main Lambda Handler with Dual-Path Routing
# =============================================================================

def lambda_handler(event, context):
    """
    Unified AWS Lambda handler with proper dual-path routing.
    
    Architecture:
    - MCP requests (/mcp) → Direct AWS MCP Handler 
    - REST requests (/api/*, /docs, etc.) → FastAPI via Web Adapter
    """
    
    try:
        # Extract request details
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '/mcp')
        headers = event.get('headers', {})
        
        print(f"🔍 Lambda handler: {http_method} {path}")
        
        # Path-based routing: determine which handler to use
        if path.startswith('/api/') or path in ['/', '/health']:
            # Route to native REST handler (no FastAPI!)
            print(f"🌐 Routing {http_method} {path} to native REST handler")
            return handle_rest_request(event, context)
            
        elif path == '/docs' or path == '/openapi.json':
            # Simple docs response for now
            print(f"📖 Routing {http_method} {path} to docs handler")
            return handle_docs_request(event, context)
        
        else:
            # Route to MCP handler (default for /mcp and unknown paths)
            print(f"🔧 Routing {http_method} {path} to MCP handler")
            
            # Handle MCP requests directly
            return handle_mcp_request(event, context)
            
    except Exception as e:
        print(f"🚨 EXCEPTION in lambda_handler: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def handle_mcp_request(event, context):
    """Handle MCP requests using direct AWS MCP Handler"""
    
    try:
        # Extract request details for debugging
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '/mcp')
        headers = event.get('headers', {})
        query_params = event.get('queryStringParameters') or {}
        body = event.get('body') or ''
        
        # Enhanced debug logging to capture AI instance identifiers
        print("🔍 === MCP REQUEST DEBUG (AI INSTANCE INVESTIGATION) ===")
        print(f"📍 Timestamp: {datetime.now(UTC).isoformat()}")
        print(f"📍 Method: {http_method}")
        print(f"📍 Path: {path}")
        print(f"📍 Lambda Request ID: {context.aws_request_id if hasattr(context, 'aws_request_id') else 'N/A'}")
        
        # Log ALL headers for AI instance identification
        print("📍 ALL HEADERS:")
        for key, value in headers.items():
            print(f"    {key}: {value}")
        
        # Look for specific headers that might identify AI instances
        potential_identifiers = {
            'user-agent': headers.get('User-Agent') or headers.get('user-agent'),
            'mcp-session-id': headers.get('MCP-Session-Id') or headers.get('mcp-session-id'),
            'x-request-id': headers.get('X-Request-ID') or headers.get('x-request-id'),
            'x-amzn-trace-id': headers.get('X-Amzn-Trace-Id') or headers.get('x-amzn-trace-id'),
            'authorization': headers.get('Authorization') or headers.get('authorization'),
            'x-forwarded-for': headers.get('X-Forwarded-For') or headers.get('x-forwarded-for')
        }
        
        print("📍 POTENTIAL AI IDENTIFIERS:")
        for key, value in potential_identifiers.items():
            if value:
                print(f"    {key}: {value}")
            else:
                print(f"    {key}: NOT PRESENT")
        
        print(f"📍 Body: {body[:200]}{'...' if len(body) > 200 else ''}")
        
        # Check Accept header for proper MCP client detection
        accept_header = ''
        for key, value in headers.items():
            if key.lower() == 'accept':
                accept_header = value.lower()
                break
        
        print(f"📍 Accept header: {accept_header}")
        
        # Handle different request types
        if http_method == 'GET':
            # Handle GET requests (Claude.ai connection testing)
            if 'text/event-stream' in accept_header:
                print("❌ Client requesting SSE - returning 405")
                return {
                    'statusCode': 405,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                        'Access-Control-Allow-Headers': '*'
                    },
                    'body': json.dumps({
                        'error': 'Method Not Allowed',
                        'message': 'SSE not supported, use HTTP POST'
                    })
                }
            else:
                # Regular GET - return server info
                print("✅ Handling GET request - returning server info")
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                        'Access-Control-Allow-Headers': '*'
                    },
                    'body': json.dumps({
                        "name": "PB-FM MCP Server",
                        "version": get_version_string(),
                        "description": "MCP server for Provenance Blockchain and Figure Markets data",
                        "protocol": "Model Context Protocol",
                        "methods": ["POST"],
                        "message": "Send POST requests with JSON-RPC 2.0 format to interact with MCP tools"
                    })
                }
        
        elif http_method == 'POST':
            # Handle POST requests (actual MCP protocol)
            # Check if client accepts both application/json and text/event-stream
            if 'application/json' in accept_header and 'text/event-stream' in accept_header:
                print("✅ Proper MCP client detected - using direct MCP handler")
            else:
                print("⚠️ Non-standard accept header - using MCP handler anyway")
            
            # Use direct AWS MCP handler - this is the key!
            print("🔧 Calling mcp_server.handle_request() directly")
            response = mcp_server.handle_request(event, context)
            
            # Debug response
            print("📤 === MCP RESPONSE DEBUG ===")
            print(f"📍 Status Code: {response.get('statusCode')}")
            response_body = response.get('body', '')
            print(f"📍 Response Body: {response_body[:200]}{'...' if len(response_body) > 200 else ''}")
            print("🔍 === END DEBUG ===\n")
            
            return response
        
        elif http_method == 'OPTIONS':
            print("🔎 Processing OPTIONS (CORS preflight) request")
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Max-Age': '3600'
                },
                'body': ''
            }
        
        else:
            print(f"🔎 Unsupported method {http_method}")
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Method Not Allowed',
                    'message': f'Method {http_method} not supported'
                })
            }
            
    except Exception as e:
        print(f"🚨 EXCEPTION in handle_mcp_request: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }