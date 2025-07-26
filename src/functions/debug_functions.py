"""
Debug Functions for Investigating AI Instance Identification

These functions help analyze MCP requests to identify unique identifiers
that could be used for creating stable personal dashboard URLs.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from registry import api_function
from utils import JSONType


@api_function(
    protocols=["mcp"],
    description="Debug function to analyze MCP request context for AI instance identification"
)
async def analyze_mcp_request_context() -> JSONType:
    """
    Analyze the current MCP request context to identify potential
    unique identifiers for AI assistant instances.
    
    This function examines:
    - Lambda event context
    - Request headers
    - Client information
    - Session data
    """
    
    try:
        # Try to access Lambda context if available
        import inspect
        frame = inspect.currentframe()
        context_info = {}
        
        # Look for Lambda event in call stack
        try:
            # This is a hack to try to find the Lambda event
            # In practice, we'd need to pass this through the function call
            context_info = {
                "timestamp": datetime.now().isoformat(),
                "function_name": "analyze_mcp_request_context",
                "investigation": "Looking for AI instance identifiers"
            }
        except Exception as e:
            context_info["error"] = f"Could not access context: {str(e)}"
        
        return {
            "success": True,
            "message": "MCP request context analysis",
            "context_info": context_info,
            "investigation_results": {
                "approach_1": "Lambda event headers - need to modify handler to capture",
                "approach_2": "MCP client User-Agent - need to examine request headers", 
                "approach_3": "Session persistence - could use conversation ID",
                "approach_4": "Request fingerprinting - behavioral patterns"
            },
            "next_steps": [
                "Modify Lambda handler to log all request headers",
                "Examine actual Claude.ai MCP requests", 
                "Look for consistent identifiers across requests",
                "Test with multiple AI instances"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Debug analysis failed: {str(e)}"
        }


@api_function(
    protocols=["mcp"], 
    description="Create a test dashboard with debug information about the requesting AI instance"
)
async def create_debug_dashboard(
    debug_context: str = "investigating_ai_instance_id"
) -> JSONType:
    """
    Create a test dashboard while attempting to capture any available
    information about the AI instance making the request.
    """
    
    try:
        # Generate a unique dashboard ID for this test
        from datetime import datetime
        import uuid
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_id = str(uuid.uuid4())[:8]
        dashboard_id = f"debug_{timestamp}_{debug_id}"
        
        # Try to gather any available context
        investigation_data = {
            "dashboard_id": dashboard_id,
            "created_at": datetime.now().isoformat(),
            "debug_context": debug_context,
            "investigation_notes": {
                "goal": "Identify unique AI instance identifiers",
                "current_limitations": [
                    "No direct access to Lambda event object in function",
                    "Headers not passed through to function parameters",
                    "Need handler-level logging to capture request details"
                ],
                "potential_identifiers": [
                    "User-Agent header from Claude.ai",
                    "X-Request-ID or similar headers",
                    "Client IP (not ideal, can change)",
                    "Session tokens or authentication headers",
                    "Claude conversation ID if available"
                ]
            }
        }
        
        # For now, create a dashboard URL using the debug ID
        dashboard_url = f"https://pb-fm-mcp-dev.creativeapptitude.com/dashboard/{dashboard_id}"
        
        return {
            "success": True,
            "message": "Debug dashboard created for AI instance investigation",
            "dashboard_id": dashboard_id,
            "dashboard_url": dashboard_url,
            "investigation_data": investigation_data,
            "instructions": {
                "for_testing": "Call this function multiple times to see if any consistent patterns emerge",
                "for_development": "Need to modify Lambda handler to capture and pass request headers"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Debug dashboard creation failed: {str(e)}"
        }


@api_function(
    protocols=["mcp"],
    description="Test function to examine if there's any session persistence across MCP calls"
)
async def test_session_persistence(
    test_value: str = "session_test"
) -> JSONType:
    """
    Test whether there's any session persistence that could be used
    to identify the same AI instance across multiple MCP calls.
    """
    
    try:
        # Try to store and retrieve data to see if there's session persistence
        import tempfile
        import os
        
        # Test 1: Environment variables (unlikely to persist)
        env_test_key = "MCP_SESSION_TEST"
        stored_value = os.environ.get(env_test_key)
        os.environ[env_test_key] = test_value
        
        # Test 2: Module-level variables (might persist in warm Lambda)
        global _session_data
        if '_session_data' not in globals():
            _session_data = {}
            
        session_key = "ai_instance_test"
        previous_value = _session_data.get(session_key)
        _session_data[session_key] = {
            "value": test_value,
            "timestamp": datetime.now().isoformat(),
            "call_count": _session_data.get(session_key, {}).get("call_count", 0) + 1
        }
        
        return {
            "success": True,
            "message": "Session persistence test completed",
            "test_results": {
                "environment_variable": {
                    "key": env_test_key,
                    "previous_value": stored_value,
                    "set_value": test_value,
                    "persistence": "unlikely across Lambda invocations"
                },
                "module_variable": {
                    "key": session_key,
                    "previous_value": previous_value,
                    "current_value": _session_data[session_key],
                    "persistence": "possible in warm Lambda containers"
                }
            },
            "conclusions": {
                "environment_vars": "Reset between Lambda invocations",
                "module_vars": "May persist in warm containers but unreliable",
                "recommendation": "Need external storage (DynamoDB) or request-level identifiers"
            },
            "next_test": "Call this function again to see if call_count increments"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Session persistence test failed: {str(e)}"
        }