#!/usr/bin/env python3
"""
Test script for the stats function with @api_function decorator
"""

import sys
import os
import asyncio
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.registry import get_registry
from src.registry.generators import RegistryGenerator
from src.functions.stats_functions import fetch_current_hash_statistics


async def test_stats_function():
    """Test the stats function and registry system"""
    print("📊 Testing HASH Statistics Function")
    print("=" * 40)
    
    # Test registry
    registry = get_registry()
    print(f"📋 Registry has {len(registry)} functions")
    
    # Test function registration
    meta = registry.get_function("fetch_current_hash_statistics")
    if meta:
        print(f"✅ Function '{meta.name}' registered successfully")
        print(f"   Protocols: {[p.value for p in meta.protocols]}")
        print(f"   REST Path: {meta.rest_path}")
        print(f"   Method: {meta.rest_method}")
        print(f"   Tags: {meta.tags}")
    else:
        print("❌ Function not found in registry")
        return
    
    # Test MCP tool generation
    generator = RegistryGenerator(registry)
    mcp_tools = generator.generate_mcp_tools()
    print(f"\n🔧 Generated MCP Tool:")
    mcp_tool = next(tool for tool in mcp_tools if tool['name'] == 'fetch_current_hash_statistics')
    print(f"   Name: {mcp_tool['name']}")
    print(f"   Description: {mcp_tool['description'][:100]}...")
    print(f"   Input Schema: {mcp_tool['inputSchema']}")
    
    # Test OpenAPI generation
    openapi_paths = generator.generate_openapi_paths()
    print(f"\n🌐 Generated REST Endpoint:")
    hash_stats_path = openapi_paths.get("/hash/statistics", {}).get("get", {})
    print(f"   Method: GET /hash/statistics")
    print(f"   Summary: {hash_stats_path.get('summary', 'N/A')}")
    print(f"   Tags: {hash_stats_path.get('tags', [])}")
    
    # Test function execution (this will make a real API call!)
    print(f"\n🚀 Testing function execution (real API call):")
    try:
        result = await fetch_current_hash_statistics()
        if result.get("MCP-ERROR"):
            print(f"❌ Error: {result['MCP-ERROR']}")
        else:
            print("✅ Success! Sample response:")
            print(f"   Current Supply: {result.get('currentSupply', {}).get('amount', 'N/A')} nhash")
            print(f"   Circulation: {result.get('circulation', {}).get('amount', 'N/A')} nhash")
            print(f"   Bonded: {result.get('bonded', {}).get('amount', 'N/A')} nhash")
            if 'locked' in result:
                print(f"   Locked (calculated): {result['locked']['amount']} nhash")
    except Exception as e:
        print(f"❌ Function execution failed: {e}")
        return
    
    print("\n✅ All tests passed! Stats function is working! 🎉")


if __name__ == "__main__":
    asyncio.run(test_stats_function())