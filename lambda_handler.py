"""
Provenance Blockchain + Figure Markets MCP Server for AWS Lambda
"""
import sys
import asyncio
import json
from datetime import UTC, datetime
from typing import Dict, Any, Union
from pathlib import Path

# Add src directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import utils
from base64expand import base64expand
from hastra_types import JSONType
from async_wrapper import sync_wrapper, async_to_sync_mcp_tool

# AWS Lambda MCP Handler
from awslabs.mcp_lambda_handler import MCPLambdaHandler
import httpx

# FastAPI and Lambda adapter
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from mangum import Mangum

# Unified Function Registry  
from registry import get_registry, MCPIntegration, FastAPIIntegration
import functions  # This will register all @api_function decorated functions

#########################################################################################
# helper functions
#########################################################################################

def datetime_to_ms(dt):
    """Convert datetime to milliseconds since epoch"""
    if dt.tzinfo is None:
        # Assume UTC if no timezone specified
        dt = dt.replace(tzinfo=UTC)
    return int(dt.timestamp() * 1000)

def ms_to_datetime(ms_timestamp, tz=UTC):
    """Convert milliseconds since epoch to datetime"""
    return datetime.fromtimestamp(ms_timestamp / 1000, tz=tz)

def current_ms():
    """Get current time in milliseconds since epoch"""
    return int(datetime.now(UTC).timestamp() * 1000)

# helper function to standardize async http-get of json return
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

# helper function to standardize sync http-get of json return
def http_get_json(
    url: str,
    params: dict | None = None,
    timeout: float = 10.0,
    connect_timeout: float = 5.0
) -> JSONType:
    """Make a sync HTTP GET request and return JSON response.

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

    with httpx.Client(timeout=timeout_config) as client:
        try:
            response = client.get(url, params=params, headers=headers)
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

#########################################################################################
# Initialize MCP Server for AWS Lambda
#########################################################################################

# Initialize the MCP server with a name and version
mcp_server = MCPLambdaHandler(name="pb-fm-mcp", version="0.1.0")

# Initialize FastAPI app for REST endpoints
fastapi_app = FastAPI(
    title="PB-FM API",
    description="REST API for Provenance Blockchain and Figure Markets data",
    version="0.1.0",
    docs_url=None,  # Disable built-in docs to avoid async issues
    openapi_url="/openapi.json",
    # Configure for API Gateway path
    root_path="/Prod",
    servers=[
        {
            "url": "https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod",
            "description": "Development environment"
        },
        {
            "url": "https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod", 
            "description": "Production environment"
        },
        {
            "url": "http://localhost:3000",
            "description": "Local development server"
        }
    ]
)

# Add CORS middleware to enable external Swagger UI access
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for OpenAPI spec access
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

#########################################################################################
# Unified Function Registry Integration
#########################################################################################

# Get the global function registry
registry = get_registry()

# Auto-register all @api_function decorated functions with MCP server
MCPIntegration.register_mcp_tools(mcp_server, registry)
print(f"🔧 Registered {len(registry.get_mcp_functions())} MCP tools from function registry")

# Auto-register all @api_function decorated functions with FastAPI
FastAPIIntegration.register_rest_routes(fastapi_app, registry)
print(f"🌐 Registered {len(registry.get_rest_functions())} REST routes from function registry")

# Update OpenAPI schema with proper parameter definitions
FastAPIIntegration.update_openapi_schema(fastapi_app, registry)
print("📝 Updated OpenAPI schema with registry-generated documentation")

# Create Mangum handler for FastAPI with proper async support
fastapi_handler = Mangum(fastapi_app, lifespan="off")

#########################################################################################
# MCP Tool Functions
#########################################################################################

# Removed manual test MCP tool - replaced with auto-generated tools from unified registry

# Removed legacy MCP tool get_system_context - migrated to unified registry

# Removed manual MCP tool - replaced with auto-generated fetch_last_crypto_token_price from unified registry

# Removed manual MCP tool - replaced with auto-generated fetch_current_fm_data from unified registry

# Removed duplicate legacy MCP tools:
# - fetch_current_fm_account_balance_data: Replaced with unified registry fetch_current_fm_account_balance_data
# - fetch_available_total_amount: Similar functionality available in unified registry fetch_account_balance

# Removed legacy MCP tool fetch_vesting_total_unvested_amount - migrated to unified registry

# Removed legacy MCP tool fetch_available_committed_amount - migrated to unified registry

# Removed legacy MCP tool fetch_figure_markets_assets_info - migrated to unified registry


#########################################################################################
# FastAPI REST Endpoints
#########################################################################################

@fastapi_app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "PB-FM API",
        "version": "0.1.0",
        "description": "REST API for Provenance Blockchain and Figure Markets data",
        "endpoints": {
            "docs": "/docs",
            "openapi": "/openapi.json",
            "mcp": "/mcp"
        }
    }

# Removed manual /api/markets endpoint - replaced with auto-generated /api/figure_markets_data from unified registry

# Removed manual /api/account/{wallet_address}/balance endpoint - replaced with auto-generated /api/fm_account_balance/{wallet_address} from unified registry

# Removed manual /api/account/{wallet_address}/info endpoint - replaced with auto-generated /api/fm_account_info/{wallet_address} from unified registry

def _generate_docs_html(base_url: str):
    """Generate the documentation HTML content (sync function for thread pool execution)"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PB-FM API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui.css" />
        <style>
            body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
            .header {{ background: #1f8aed; color: white; padding: 20px; margin: -20px -20px 20px -20px; }}
            .quick-links {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
            .endpoint {{ background: white; border: 1px solid #e0e0e0; border-radius: 6px; padding: 15px; margin: 10px 0; }}
            .method {{ font-weight: bold; color: #1f8aed; }}
            a {{ color: #1f8aed; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 PB-FM API Documentation</h1>
            <p>REST API for Provenance Blockchain and Figure Markets data</p>
        </div>
        
        <div class="quick-links">
            <h3>📋 Quick Links</h3>
            <p><strong>OpenAPI Spec:</strong> <a href="/Prod/openapi.json" target="_blank">/Prod/openapi.json</a></p>
            <p><strong>Interactive Swagger UI Options:</strong></p>
            <ul style="margin-left: 20px;">
                <li><a href="https://generator3.swagger.io/index.html?url={base_url}/openapi.json" target="_blank">Swagger UI</a></li>
                <li><a href="https://editor.swagger.io/" target="_blank">Swagger Editor</a> (manual: File → Import URL → paste OpenAPI URL)</li>
                <li><a href="https://redoc.ly/redoc/?url={base_url}/openapi.json" target="_blank">ReDoc Documentation</a></li>
            </ul>
        </div>

        <h3>🔗 Available Endpoints</h3>
        
        <div class="endpoint">
            <div class="method">GET /api/markets</div>
            <p>Get current Figure Markets trading pairs and prices</p>
            <p><a href="/Prod/api/markets" target="_blank">Try it →</a></p>
        </div>

        <div class="endpoint">
            <div class="method">GET /api/account/{{wallet_address}}/balance</div>
            <p>Get account balance data for a wallet address</p>
            <p><a href="/Prod/api/account/pb1c9rqwfefggk3s3y79rh8quwvp8rf8ayr7qvmk8/balance" target="_blank">Try example →</a></p>
        </div>

        <div class="endpoint">
            <div class="method">GET /api/account/{{wallet_address}}/info</div>
            <p>Get account info and vesting status for a wallet address</p>
            <p><a href="/Prod/api/account/pb1c9rqwfefggk3s3y79rh8quwvp8rf8ayr7qvmk8/info" target="_blank">Try example →</a></p>
        </div>

        <div class="endpoint">
            <div class="method">POST /mcp</div>
            <p>MCP (Model Context Protocol) endpoint for AI agents</p>
            <p>Accepts JSON-RPC 2.0 formatted requests with MCP protocol</p>
        </div>

        <h3>💡 Usage Examples</h3>
        <pre style="background: #f8f9fa; padding: 15px; border-radius: 6px; overflow-x: auto;">
# Get all trading pairs
curl "{base_url}/api/markets"

# Get account balance  
curl "{base_url}/api/account/pb1c9rqwfefggk3s3y79rh8quwvp8rf8ayr7qvmk8/balance"

# MCP protocol example
curl -X POST "{base_url}/mcp" \\
  -H "Content-Type: application/json" \\
  -d '{{"method": "tools/list", "params": {{}}, "jsonrpc": "2.0", "id": 1}}'
        </pre>
    </body>
    </html>
    """
    return html_content

@fastapi_app.get("/docs", response_class=HTMLResponse)
async def custom_docs(request: Request):
    """Custom documentation page that works with Lambda async context"""
    # Determine the base URL from the request
    host = request.headers.get("host", "localhost:3000")
    scheme = "https" if "execute-api" in host else "http"
    base_url = f"{scheme}://{host}/Prod"
    
    # Use thread pool to avoid event loop issues in Lambda
    loop = asyncio.get_event_loop()
    html_content = await loop.run_in_executor(None, _generate_docs_html, base_url)
    return HTMLResponse(content=html_content)

#########################################################################################
# AWS Lambda Handler
#########################################################################################

def lambda_handler(event, context):
    """Dual-protocol AWS Lambda handler: MCP + REST API with path-based routing"""
    
    try:
        # Extract request details
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '/mcp')
        
        # Path-based routing: determine which handler to use
        if path.startswith('/api/') or path in ['/', '/docs', '/openapi.json']:
            # Route to FastAPI for REST endpoints and documentation
            print(f"🌐 Routing {http_method} {path} to FastAPI handler")
            return fastapi_handler(event, context)
        else:
            # Route to MCP handler (default for /mcp and unknown paths)
            print(f"🔧 Routing {http_method} {path} to MCP handler")
            # Continue with existing MCP debug logic
            headers = event.get('headers', {})
            query_params = event.get('queryStringParameters') or {}
            body = event.get('body') or ''
        
        # Debug logging
        print("🔍 === MCP REQUEST DEBUG ===")
        print(f"📍 Timestamp: {datetime.now(UTC).isoformat()}")
        print(f"📍 Method: {http_method}")
        print(f"📍 Path: {path}")
        print(f"📍 Query Params: {query_params}")
        print(f"📍 Request Source IP: {event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')}")
        print(f"📍 Request ID: {event.get('requestContext', {}).get('requestId', 'unknown')}")
        print(f"📍 Raw Event: {json.dumps(event, indent=2, default=str)}")
        print(f"📍 Headers:")
        for key, value in headers.items():
            print(f"   {key}: {value}")
        print(f"📍 Body: {body[:200]}{'...' if len(body) > 200 else ''}")
        print(f"📍 Body Length: {len(body)}")
        print(f"📍 Context: {context}")
        
        # Get Accept header (case-insensitive)
        accept_header = ''
        content_type = ''
        origin = ''
        user_agent = ''
        authorization = ''
        connection = ''
        upgrade = ''
        
        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower == 'accept':
                accept_header = value
            elif key_lower == 'content-type':
                content_type = value
            elif key_lower == 'origin':
                origin = value
            elif key_lower == 'user-agent':
                user_agent = value
            elif key_lower == 'authorization':
                authorization = value
            elif key_lower == 'connection':
                connection = value
            elif key_lower == 'upgrade':
                upgrade = value
        
        print(f"📍 Parsed Accept: {accept_header}")
        print(f"📍 Parsed Content-Type: {content_type}")
        print(f"📍 Parsed Origin: {origin}")
        print(f"📍 Parsed User-Agent: {user_agent}")
        print(f"📍 Parsed Authorization: {'[PRESENT]' if authorization else '[NONE]'}")
        print(f"📍 Parsed Connection: {connection}")
        print(f"📍 Parsed Upgrade: {upgrade}")
        
        # Check if this looks like a capability check or connection probe
        if not body and http_method == 'POST':
            print("⚠️ WARNING: Empty body POST request - potential capability check")
        
        if 'upgrade' in connection.lower() or upgrade:
            print("⚠️ WARNING: Client attempting protocol upgrade")
            
        # Check for WebSocket or SSE connection attempts
        if 'websocket' in upgrade.lower():
            print("❌ DETECTED: WebSocket upgrade attempt - unsupported")
            return {
                'statusCode': 426,
                'headers': {
                    'Content-Type': 'text/plain',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept'
                },
                'body': 'Upgrade Required - WebSocket not supported, use HTTP POST'
            }
        
        if 'text/event-stream' in accept_header and http_method != 'GET':
            print("⚠️ WARNING: SSE Accept header on non-GET request")
        
        if http_method == 'GET':
            print("🔎 Processing GET request")
            # MCP Streamable HTTP spec: GET requests for SSE
            if 'text/event-stream' in accept_header:
                print("❌ Client requesting SSE - returning 405")
                # Client wants SSE - we don't support it, return 405
                response = {
                    'statusCode': 405,
                    'headers': {
                        'Content-Type': 'text/plain',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept',
                        'Allow': 'POST, OPTIONS'
                    },
                    'body': 'Method Not Allowed - SSE not supported, use HTTP POST'
                }
            else:
                print("✅ Returning server info for GET request")
                # Regular GET request - return server info
                response = {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept'
                    },
                    'body': json.dumps({
                        'name': 'pb-fm-mcp',
                        'version': '0.1.0',
                        'transport': 'http',  # HTTP-only transport
                        'capabilities': {
                            'tools': True,
                            'streaming': False
                        }
                    })
                }
        
        elif http_method == 'POST':
            print("🔎 Processing POST request")
            
            # Try to parse JSON body if present
            json_body = None
            if body:
                try:
                    json_body = json.loads(body)
                    print(f"📍 Parsed JSON Body: {json.dumps(json_body, indent=2)}")
                except json.JSONDecodeError as e:
                    print(f"⚠️ Failed to parse JSON body: {e}")
            
            # Check if client accepts both application/json and text/event-stream
            if 'application/json' in accept_header and 'text/event-stream' in accept_header:
                print("✅ Proper MCP client detected - using MCP handler")
                # Proper MCP client - use MCP handler
                response = mcp_server.handle_request(event, context)
            else:
                print("⚠️ Non-standard accept header - using MCP handler anyway")
                # Regular POST request - use MCP handler
                response = mcp_server.handle_request(event, context)
        
        elif http_method == 'OPTIONS':
            print("🔎 Processing OPTIONS (CORS preflight) request")
            response = mcp_server.handle_request(event, context)
        
        else:
            print(f"🔎 Processing {http_method} request through MCP handler")
            # Handle other requests through MCP handler
            response = mcp_server.handle_request(event, context)
        
        # Debug response
        print("📤 === MCP RESPONSE DEBUG ===")
        print(f"📍 Status Code: {response.get('statusCode')}")
        print(f"📍 Response Headers:")
        for key, value in response.get('headers', {}).items():
            print(f"   {key}: {value}")
        response_body = response.get('body', '')
        print(f"📍 Response Body: {response_body[:200]}{'...' if len(response_body) > 200 else ''}")
        print(f"📍 Response Body Length: {len(response_body)}")
        print("🔍 === END DEBUG ===\n")
        
        return response
        
    except Exception as e:
        print(f"🚨 EXCEPTION in lambda_handler: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept'
            },
            'body': json.dumps({'error': 'Internal server error', 'message': str(e)})
        }