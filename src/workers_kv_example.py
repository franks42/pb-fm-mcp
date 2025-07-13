import json
import time
import sys
from typing import Any, Dict, Optional
from jqpath import getpath, setpath, delpath

# Mock Response class for type hints
class Response:
    @staticmethod
    def new(body: str, status: int = 200, headers: Optional[Dict[str, str]] = None) -> 'Response':
        pass

def create_worker_response(data: Any, success: bool = True, error: Optional[str] = None) -> str:
    """Create a standardized JSON response for Cloudflare Workers.
    
    Args:
        data: The response data (if successful)
        success: Whether the operation was successful
        error: Error message (if any)
        
    Returns:
        JSON string with the response
    """
    response_obj = {
        'success': success,
        'data': data if success else None,
        'error': error if not success else None,
        'timestamp': int(time.time())
    }
    return json.dumps(response_obj)

async def example_worker_handler(request: Any, env: Any) -> Response:
    """Handle HTTP requests for a simple key-value store API.
    
    Supported actions:
    - GET /{key}?action=get&path=path.to.value
    - POST /{key}?action=set&path=path.to.value&value=...
    - DELETE /{key}?action=del&path=path.to.value
    
    Args:
        request: The incoming HTTP request
        env: Environment variables and bindings
        
    Returns:
        Response with JSON data or error message
    """
    # Get the key from the URL path
    key = (getattr(request, 'path', '') or '')[1:]
    if not key:
        return Response.new(create_worker_response(
            None, 
            success=False, 
            error="Missing key in URL path"
        ), status=400)

    # Read the existing JSON from KV
    try:
        KV = getattr(env, 'MY_KV_NAMESPACE', None)
        if not KV:
            return Response.new(create_worker_response(
                None,
                success=False,
                error="KV namespace not configured"
            ), status=500)
            
        data_str = await KV.get(key)
        data = json.loads(data_str) if data_str else {}
    except json.JSONDecodeError as e:
        return Response.new(create_worker_response(
            None,
            success=False,
            error=f"Invalid JSON data in KV store: {str(e)}"
        ), status=500)
    except Exception as e:
        return Response.new(create_worker_response(
            None,
            success=False,
            error=f"Error reading from KV store: {str(e)}"
        ), status=500)

    # Get query parameters
    params = getattr(request, 'query', {})
    action = params.get('action')
    path = params.get('path')
    
    # Validate required parameters
    if not action:
        return Response.new(create_worker_response(
            None,
            success=False,
            error="Missing 'action' query parameter"
        ), status=400)
        
    if not path:
        return Response.new(create_worker_response(
            None,
            success=False,
            error="Missing 'path' query parameter"
        ), status=400)

    try:
        if action == 'get':
            value = getpath(data, path)
            response_data = {'key': key, 'path': path, 'value': value}
        
        elif action == 'set':
            value_str = params.get('value')
            if value_str is None:
                return Response.new(create_worker_response(
                    None,
                    success=False,
                    error="Missing 'value' query parameter for 'set' action"
                ), status=400)
            
            try:
                value = json.loads(value_str)
            except json.JSONDecodeError:
                value = value_str  # Treat as plain string if not valid JSON
            
            setpath(data, path, value)
            await KV.put(key, json.dumps(data))
            response_data = {'key': key, 'path': path, 'status': 'set'}

        elif action == 'del':
            delpath(data, path)
            await KV.put(key, json.dumps(data))
            response_data = {'key': key, 'path': path, 'status': 'deleted'}
        
        else:
            return Response.new(create_worker_response(
                None,
                success=False,
                error=f"Invalid action: {action}. Must be one of: get, set, del"
            ), status=400)

        # Return success response
        return Response.new(
            create_worker_response(response_data),
            headers={'Content-Type': 'application/json'}
        )
        
    except Exception as e:
        # Log the full error for debugging
        print(f"Error processing request: {str(e)}", file=sys.stderr)
        
        # Return user-friendly error
        return Response.new(
            create_worker_response(
                None,
                success=False,
                error="An error occurred while processing your request"
            ),
            status=500,
            headers={'Content-Type': 'application/json'}
        )
