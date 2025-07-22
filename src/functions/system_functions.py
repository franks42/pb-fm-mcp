"""
System Functions for pb-fm-mcp

Functions for introspecting the server's capabilities and configuration.
All functions are decorated with @api_function to be automatically
exposed via both MCP and REST protocols.
"""

from typing import Dict, Any, List
import structlog

# Handle import for both relative and absolute path contexts
try:
    from ..registry import api_function, get_registry
except ImportError:
    try:
        from registry import api_function, get_registry
    except ImportError:
        from src.registry import api_function, get_registry

# Set up logging
logger = structlog.get_logger()

# Type alias for JSON response
JSONType = Dict[str, Any]


@api_function(
    protocols=["mcp", "rest"],
    path="/api/registry_introspection",
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
        return {"MCP-ERROR": f"Registry introspection failed: {str(e)}"}


@api_function(
    protocols=["mcp", "rest"],
    path="/api/registry_summary",
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
        return {"MCP-ERROR": f"Registry summary failed: {str(e)}"}