"""
Version and System Information Functions

Functions for reporting deployment version, build info, and system status.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from registry import api_function
from utils import JSONType


@api_function(
    protocols=["rest"],
    path="/api/version",
    method="GET",
    tags=["system", "version"],
    description="Get deployment version and build information"
)
async def get_version_info() -> JSONType:
    """
    Get deployment version and build information.
    
    Returns detailed information about the current deployment including
    version numbers, git commit, build timestamp, and environment.
    
    Returns:
        Dictionary containing version and deployment information
    """
    try:
        # Try to load version.json from project root
        version_file = Path(__file__).parent.parent.parent / "version.json"
        
        if version_file.exists():
            with open(version_file, 'r') as f:
                version_data = json.load(f)
        else:
            # Fallback version data if file doesn't exist
            version_data = {
                "major": 0,
                "minor": 1,
                "patch": 0,
                "build_number": 0,
                "description": "Version file not found - using defaults"
            }
        
        # Add runtime information
        version_data.update({
            "server_time": datetime.now().isoformat(),
            "python_version": os.sys.version.split()[0],
            "environment_type": "lambda" if "AWS_LAMBDA_FUNCTION_NAME" in os.environ else "local",
            "function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "unknown"),
            "region": os.environ.get("AWS_REGION", "unknown")
        })
        
        return version_data
        
    except Exception as e:
        return {
            "error": f"Failed to get version info: {str(e)}",
            "fallback_version": "0.1.0",
            "server_time": datetime.now().isoformat()
        }


@api_function(
    protocols=["mcp", "rest"],
    path="/api/system_status",
    method="GET",
    tags=["system", "health"],
    description="Get comprehensive system status and health information"
)
async def get_system_status() -> JSONType:
    """
    Get comprehensive system status and health information.
    
    Includes version info, environment details, and basic health checks.
    
    Returns:
        Dictionary containing system status and health information
    """
    try:
        # Get version information
        version_info = await get_version_info()
        
        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "version_loaded": "version" in version_info or "error" not in version_info,
                "environment_detected": os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None,
                "python_runtime": True  # If we're running, Python is working
            }
        }
        
        # Add environment details
        environment_info = {
            "aws_lambda_function": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "not_set"),
            "aws_region": os.environ.get("AWS_REGION", "not_set"),
            "runtime": os.environ.get("AWS_EXECUTION_ENV", "unknown"),
            "memory_limit": os.environ.get("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", "unknown"),
            "log_group": os.environ.get("AWS_LAMBDA_LOG_GROUP_NAME", "unknown")
        }
        
        return {
            "version": version_info,
            "health": health_status,
            "environment": environment_info,
            "api_info": {
                "protocols_supported": ["MCP", "REST"],
                "csv_sync_enabled": version_info.get("csv_sync_enabled", False),
                "unified_lambda_architecture": True
            }
        }
        
    except Exception as e:
        return {
            "error": f"Failed to get system status: {str(e)}",
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }