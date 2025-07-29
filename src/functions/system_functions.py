"""
System Functions for pb-fm-mcp

Functions for introspecting the server's capabilities and configuration.
All functions are decorated with @api_function to be automatically
exposed via both MCP and REST protocols.
"""

import time
from typing import Any

import structlog

from registry import api_function, get_registry
from utils import JSONType

# Set up logging
logger = structlog.get_logger()



@api_function(
    protocols=["mcp", "rest"],
    path="/api/get_registry_introspection",
    method="GET",
    tags=["system", "introspection"],
    description="Get detailed information about all registered functions in the server"
)
async def get_registry_introspection() -> JSONType:
    """
    Get comprehensive information about all registered functions in the server,
    including protocol support, paths, and descriptions.
    
    This endpoint provides:
    - Total function counts by protocol
    - List of all functions with their metadata
    - Categorization by module and protocol support
    
    Returns:
        Dictionary containing:
        - summary: Overview statistics of registered functions
        - functions: Detailed list of all functions with metadata
        - by_protocol: Functions grouped by protocol support
        - by_module: Functions grouped by source module
        
    Raises:
        Exception: If registry access fails
    """
    try:
        registry = get_registry()
        all_functions = registry.get_all_functions()
        
        # Initialize counters and categorizations
        summary = {
            "total_functions": len(all_functions),
            "mcp_only": 0,
            "rest_only": 0,
            "dual_protocol": 0,
            "by_tag": {}
        }
        
        functions_list = []
        by_protocol = {
            "mcp_only": [],
            "rest_only": [],
            "dual_protocol": []
        }
        by_module = {}
        
        # Process each function
        for func_name, func_meta in all_functions.items():
            # Extract function details
            func_info = {
                "name": func_name,
                "protocols": [p.value if hasattr(p, 'value') else p for p in func_meta.protocols],
                "path": func_meta.rest_path,
                "method": func_meta.rest_method,
                "tags": func_meta.tags,
                "description": func_meta.description,
                "module": func_meta.func.__module__ if hasattr(func_meta.func, '__module__') else "unknown"
            }
            
            functions_list.append(func_info)
            
            # Categorize by protocol
            protocol_values = [p.value if hasattr(p, 'value') else p for p in func_meta.protocols]
            has_mcp = "mcp" in protocol_values
            has_rest = "rest" in protocol_values
            
            if has_mcp and has_rest:
                summary["dual_protocol"] += 1
                by_protocol["dual_protocol"].append(func_name)
            elif has_mcp:
                summary["mcp_only"] += 1
                by_protocol["mcp_only"].append(func_name)
            elif has_rest:
                summary["rest_only"] += 1
                by_protocol["rest_only"].append(func_name)
            
            # Categorize by module
            module_name = func_info["module"].split('.')[-1] if '.' in func_info["module"] else func_info["module"]
            if module_name not in by_module:
                by_module[module_name] = []
            by_module[module_name].append(func_name)
            
            # Count by tags
            for tag in func_meta.tags:
                if tag not in summary["by_tag"]:
                    summary["by_tag"][tag] = 0
                summary["by_tag"][tag] += 1
        
        # Sort function lists for consistency
        functions_list.sort(key=lambda x: x["name"])
        for key in by_protocol:
            by_protocol[key].sort()
        for module in by_module:
            by_module[module].sort()
        
        return {
            "summary": summary,
            "functions": functions_list,
            "by_protocol": by_protocol,
            "by_module": by_module
        }
        
    except Exception as e:
        logger.error(f"Registry introspection error: {e}")
        return {"MCP-ERROR": f"Registry introspection failed: {e!s}"}


@api_function(
    protocols=["mcp", "rest"],
    path="/api/get_registry_summary",
    method="GET",
    tags=["system", "introspection"],
    description="Get a quick summary of registered functions by protocol"
)
async def get_registry_summary() -> JSONType:
    """
    Get a quick summary of registered functions counts by protocol support.
    
    This is a lightweight version of get_registry_introspection that only
    returns the summary statistics without detailed function information.
    
    Returns:
        Dictionary containing:
        - total_functions: Total number of registered functions
        - mcp_enabled: Number of functions supporting MCP protocol
        - rest_enabled: Number of functions supporting REST protocol
        - dual_protocol: Number of functions supporting both protocols
        - mcp_only: Number of MCP-only functions
        - rest_only: Number of REST-only functions
        
    Raises:
        Exception: If registry access fails
    """
    try:
        registry = get_registry()
        all_functions = registry.get_all_functions()
        
        # Count functions by protocol support
        mcp_enabled = 0
        rest_enabled = 0
        dual_protocol = 0
        mcp_only = 0
        rest_only = 0
        
        for func_name, func_meta in all_functions.items():
            protocol_values = [p.value if hasattr(p, 'value') else p for p in func_meta.protocols]
            has_mcp = "mcp" in protocol_values
            has_rest = "rest" in protocol_values
            
            if has_mcp:
                mcp_enabled += 1
            if has_rest:
                rest_enabled += 1
                
            if has_mcp and has_rest:
                dual_protocol += 1
            elif has_mcp:
                mcp_only += 1
            elif has_rest:
                rest_only += 1
        
        return {
            "total_functions": len(all_functions),
            "mcp_enabled": mcp_enabled,
            "rest_enabled": rest_enabled,
            "dual_protocol": dual_protocol,
            "mcp_only": mcp_only,
            "rest_only": rest_only
        }
        
    except Exception as e:
        logger.error(f"Registry summary error: {e}")
        return {"MCP-ERROR": f"Registry summary failed: {e!s}"}


@api_function(protocols=["mcp", "rest"])






async def mcp_warmup_ping() -> JSONType:
    """
    Ultra-fast ping function designed specifically for Lambda warming and MCP timeout recovery.
    
    This function:
    - Returns immediately with minimal processing
    - Warms the Lambda container for subsequent calls
    - Provides connection verification for Claude.ai
    - Can be called multiple times for timeout recovery
    
    Usage Strategy for Claude.ai:
    1. When hitting MCP timeouts, call this function 2-3 times first
    2. This warms the container and tests connectivity
    3. Then proceed with actual business function calls
    4. Much faster than waiting for cold starts on heavy functions
    
    Returns:
        Dictionary containing:
        - status: "warm" to indicate successful ping
        - timestamp: Current Unix timestamp 
        - response_time_ms: Function execution time in milliseconds
        - container_info: Basic Lambda container information
        - message: Instructions for Claude.ai timeout recovery
    """
    start_time = time.time()
    
    # Minimal processing - just return status info
    current_timestamp = int(time.time())
    response_time_ms = (time.time() - start_time) * 1000
    
    return {
        "status": "warm",
        "timestamp": current_timestamp,
        "response_time_ms": round(response_time_ms, 2),
        "container_info": {
            "lambda_ready": True,
            "mcp_handler_active": True,
            "registry_loaded": True
        },
        "message": "Lambda container is now warm. Retry your original function call.",
        "claude_ai_instructions": {
            "on_timeout": "Call mcp_warmup_ping 2-3 times, then retry original function",
            "expected_response_time": "<100ms when warm",
            "purpose": "Container warming and connectivity verification"
        }
    }


@api_function(
    protocols=["mcp"],
    path=None,  # MCP-only, no REST endpoint needed
    method="GET",
    tags=["system", "testing", "development"],
    description="Comprehensive MCP server testing tool for development and debugging"
)
async def mcp_test_server(
    function_name: str,                 # Function to test
    target_url: str = "self",           # "self", full URL, or shortcuts "prod"/"dev"
    arguments: dict[str, Any] | None = None,     # Function arguments
    repeat: int = 1,                    # Number of calls to make
    measure_timing: bool = True,        # Collect performance metrics
    test_warmup: bool = False          # Test warmup sequence first
) -> JSONType:
    """
    Comprehensive MCP server testing function for development and cross-server testing.
    
    This powerful testing tool allows:
    - Testing current server ("self") or any remote MCP server
    - Built-in shortcuts for prod/dev servers
    - Performance measurement and timing analysis
    - Multi-call testing for reliability assessment
    - Warmup sequence testing
    - Full MCP protocol compatibility testing
    
    Target URL Options:
    - "self": Test current server (localhost or deployed)
    - "prod": Shortcut for production server
    - "dev": Shortcut for development server  
    - Full URL: Any MCP server endpoint
    
    Use Cases:
    - Development: Quick function testing without custom scripts
    - Cross-server: Test prod from dev, compare implementations
    - Performance: Measure response times and reliability
    - Debugging: Detailed error reporting and diagnostics
    - Discovery: Test unknown MCP servers and explore tools
    
    Args:
        target_url: Server to test ("self", "prod", "dev", or full URL)
        function_name: Name of MCP tool to call
        arguments: Arguments to pass to the function
        repeat: Number of calls to make (default 1)
        measure_timing: Whether to collect timing data (default True)
        test_warmup: Whether to call warmup first (default False)
        
    Returns:
        Dictionary containing:
        - target_info: Information about the target server
        - test_config: Configuration used for testing
        - warmup_results: Warmup sequence results (if requested)
        - test_results: Array of test call results
        - performance_summary: Timing and reliability statistics
        - diagnostics: Error analysis and recommendations
    """
    import asyncio

    import httpx
    
    start_time = time.time()
    
    # Handle default arguments
    if arguments is None:
        arguments = {}
    
    # Resolve target URL shortcuts
    url_shortcuts = {
        "prod": "https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp",
        "dev": "https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod/mcp",
        "self": "self"  # Will be handled specially
    }
    
    resolved_url = url_shortcuts.get(target_url.lower(), target_url)
    is_self_test = resolved_url == "self"
    
    # Prepare test configuration
    test_config = {
        "target_url": target_url,
        "resolved_url": resolved_url,
        "function_name": function_name,
        "arguments": arguments,
        "repeat": repeat,
        "measure_timing": measure_timing,
        "test_warmup": test_warmup,
        "is_self_test": is_self_test
    }
    
    results = {
        "target_info": {
            "url": resolved_url,
            "is_self_test": is_self_test,
            "test_timestamp": int(time.time())
        },
        "test_config": test_config,
        "warmup_results": None,
        "test_results": [],
        "performance_summary": {},
        "diagnostics": {"errors": [], "warnings": [], "recommendations": []}
    }
    
    try:
        # Handle self-testing (direct function call)
        if is_self_test:
            registry = get_registry()
            func_meta = registry.get_function(function_name)
            
            if not func_meta:
                return {
                    "error": f"Function '{function_name}' not found in local registry",
                    "available_functions": list(registry.get_all_functions().keys())
                }
            
            # Perform self-tests
            call_times = []
            for i in range(repeat):
                call_start = time.time()
                try:
                    # Call function directly
                    if asyncio.iscoroutinefunction(func_meta.func):
                        result = await func_meta.func(**arguments)
                    else:
                        result = func_meta.func(**arguments)
                    
                    call_time = (time.time() - call_start) * 1000
                    call_times.append(call_time)
                    
                    results["test_results"].append({
                        "call_number": i + 1,
                        "success": True,
                        "response_time_ms": call_time,
                        "result": result,
                        "error": None
                    })
                    
                except Exception as e:
                    call_time = (time.time() - call_start) * 1000
                    call_times.append(call_time)
                    
                    results["test_results"].append({
                        "call_number": i + 1,
                        "success": False,
                        "response_time_ms": call_time,
                        "result": None,
                        "error": str(e)
                    })
                    
                    results["diagnostics"]["errors"].append(f"Call {i+1}: {e!s}")
        
        else:
            # Handle remote server testing
            if not resolved_url.startswith(('http://', 'https://')):
                results["diagnostics"]["errors"].append("Invalid URL format - must start with http:// or https://")
                return results
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Optional warmup sequence
                if test_warmup:
                    warmup_start = time.time()
                    try:
                        warmup_response = await client.post(
                            resolved_url,
                            json={
                                "jsonrpc": "2.0",
                                "method": "tools/call", 
                                "params": {"name": "mcp_warmup_ping", "arguments": {}},
                                "id": "warmup"
                            }
                        )
                        warmup_time = (time.time() - warmup_start) * 1000
                        results["warmup_results"] = {
                            "success": warmup_response.status_code == 200,
                            "response_time_ms": warmup_time,
                            "status_code": warmup_response.status_code
                        }
                    except Exception as e:
                        results["warmup_results"] = {
                            "success": False,
                            "error": str(e)
                        }
                        results["diagnostics"]["warnings"].append(f"Warmup failed: {e!s}")
                
                # Perform remote tests
                call_times = []
                for i in range(repeat):
                    call_start = time.time()
                    try:
                        response = await client.post(
                            resolved_url,
                            json={
                                "jsonrpc": "2.0",
                                "method": "tools/call",
                                "params": {"name": function_name, "arguments": arguments},
                                "id": f"test_{i}"
                            }
                        )
                        
                        call_time = (time.time() - call_start) * 1000
                        call_times.append(call_time)
                        
                        success = response.status_code == 200
                        result_data = response.json() if success else response.text
                        
                        results["test_results"].append({
                            "call_number": i + 1,
                            "success": success,
                            "response_time_ms": call_time,
                            "status_code": response.status_code,
                            "result": result_data,
                            "error": None if success else f"HTTP {response.status_code}"
                        })
                        
                        if not success:
                            results["diagnostics"]["errors"].append(f"Call {i+1}: HTTP {response.status_code}")
                    
                    except Exception as e:
                        call_time = (time.time() - call_start) * 1000
                        call_times.append(call_time)
                        
                        results["test_results"].append({
                            "call_number": i + 1,
                            "success": False,
                            "response_time_ms": call_time,
                            "result": None,
                            "error": str(e)
                        })
                        
                        results["diagnostics"]["errors"].append(f"Call {i+1}: {e!s}")
        
        # Performance analysis
        if call_times and measure_timing:
            successful_calls = [r for r in results["test_results"] if r["success"]]
            successful_times = [r["response_time_ms"] for r in successful_calls]
            
            results["performance_summary"] = {
                "total_calls": repeat,
                "successful_calls": len(successful_calls),
                "success_rate": len(successful_calls) / repeat * 100,
                "avg_response_time_ms": sum(successful_times) / len(successful_times) if successful_times else 0,
                "min_response_time_ms": min(successful_times) if successful_times else 0,
                "max_response_time_ms": max(successful_times) if successful_times else 0,
                "total_test_duration_ms": (time.time() - start_time) * 1000
            }
            
            # Performance recommendations
            avg_time = results["performance_summary"]["avg_response_time_ms"]
            if avg_time > 5000:
                results["diagnostics"]["recommendations"].append("Response time >5s suggests cold start issues")
            elif avg_time > 1000:
                results["diagnostics"]["recommendations"].append("Response time >1s may cause timeouts in Claude.ai")
            elif avg_time < 100:
                results["diagnostics"]["recommendations"].append("Excellent response time - optimal for Claude.ai")
    
    except Exception as e:
        results["diagnostics"]["errors"].append(f"Test framework error: {e!s}")
        logger.error(f"MCP test server error: {e}")
    
    return results