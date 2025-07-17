"""
MCP Server for Provenance Blockchain and Figure Markets API Standardization

This module provides a comprehensive transformation engine for standardizing
Provenance Blockchain and Figure Markets APIs into AI-friendly formats.

Key Components:
- Grouped attribute transformations with logical groupings
- Configuration-driven field mappings and transformations  
- Denomination conversion system for all supported assets
- Stateless server optimizations with AI agent caching
- Comprehensive test scenarios and validation tools

Usage:
    from mcpserver import setup_standardized_server
    
    mcp, app = setup_standardized_server()
"""

__version__ = "1.0.0"
__author__ = "Hastra Development Team"

from .src.mcpworker import setup_standardized_server
from .src.grouped_transformer import GroupedAttributeTransformer
from .src.denomination_converter import DenominationConverter
from .src.config_driven_transformer import ConfigDrivenTransformer

__all__ = [
    "setup_standardized_server",
    "GroupedAttributeTransformer", 
    "DenominationConverter",
    "ConfigDrivenTransformer"
]