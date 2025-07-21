"""
Unified Function Registry for pb-fm-mcp

This module provides the decorator-based function registry system that enables
single function definitions to be automatically exposed as both MCP tools and
REST API endpoints.
"""

from .decorator import api_function
from .registry import FunctionRegistry, get_registry
from .generators import RegistryGenerator
from .integrations import MCPIntegration, FastAPIIntegration

__all__ = [
    "api_function", 
    "FunctionRegistry", 
    "get_registry",
    "RegistryGenerator",
    "MCPIntegration",
    "FastAPIIntegration"
]