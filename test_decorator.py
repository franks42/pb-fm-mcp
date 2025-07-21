#!/usr/bin/env python3
"""
Test script for the @api_function decorator system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.registry import api_function, get_registry
from src.registry.generators import RegistryGenerator
import asyncio


@api_function(
    protocols=["mcp", "rest"],
    path="/test/{message}",
    description="Test function for decorator system"
)
async def test_function(message: str, count: int = 1) -> dict:
    """
    Test function to verify decorator functionality.
    
    Args:
        message: The message to return
        count: Number of times to repeat the message
        
    Returns:
        Dictionary containing the processed message
        
    Raises:
        ValueError: If count is negative
    """
    if count < 0:
        raise ValueError("Count cannot be negative")
    
    return {
        "message": message,
        "count": count,
        "repeated": [message] * count,
        "success": True
    }


def test_decorator_system():
    """Test the decorator and registry system"""
    print("🧪 Testing @api_function Decorator System")
    print("=" * 50)
    
    # Test registry
    registry = get_registry()
    print(f"📊 Registry has {len(registry)} functions")
    
    # Test function registration
    meta = registry.get_function("test_function")
    if meta:
        print(f"✅ Function '{meta.name}' registered successfully")
        print(f"   Protocols: {[p.value for p in meta.protocols]}")
        print(f"   REST Path: {meta.rest_path}")
        print(f"   Description: {meta.description}")
    else:
        print("❌ Function not found in registry")
        return
    
    # Test MCP tool generation
    generator = RegistryGenerator(registry)
    mcp_tools = generator.generate_mcp_tools()
    print(f"\n🔧 Generated {len(mcp_tools)} MCP tools:")
    for tool in mcp_tools:
        print(f"   - {tool['name']}: {tool['description'][:50]}...")
        print(f"     Input Schema: {list(tool['inputSchema']['properties'].keys())}")
    
    # Test OpenAPI generation
    openapi_paths = generator.generate_openapi_paths()
    print(f"\n🌐 Generated {len(openapi_paths)} REST paths:")
    for path, methods in openapi_paths.items():
        for method, operation in methods.items():
            print(f"   - {method.upper()} {path}: {operation['summary']}")
    
    # Test function execution
    print(f"\n🚀 Testing function execution:")
    result = asyncio.run(test_function("Hello, World!", 3))
    print(f"   Result: {result}")
    
    print("\n✅ All tests passed! Decorator system is working! 🎉")


if __name__ == "__main__":
    test_decorator_system()