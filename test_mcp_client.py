#!/usr/bin/env python3
"""
Test client using official MCP Python SDK to test our pb-fm-mcp server
"""

import asyncio
import json
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client  
from mcp.client.streamable_http import streamablehttp_client

async def test_http_client():
    """Test our MCP server using HTTP transport"""
    
    print("🔌 Testing MCP server with official Python SDK HTTP client...")
    print("📍 Server URL: http://localhost:3000/mcp")
    
    try:
        # Create HTTP client session
        async with streamablehttp_client("http://localhost:3000/mcp") as (read, write, get_session_id):
            async with ClientSession(read, write) as session:
                
                print("✅ Connected to MCP server!")
                
                # Initialize the session
                await session.initialize()
                print("✅ Session initialized successfully!")
                
                # List available tools
                tools = await session.list_tools()
                print(f"✅ Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"   - {tool.name}: {tool.description[:80]}...")
                
                # Test a simple tool call
                print("\n🧪 Testing adt tool call...")
                result = await session.call_tool("adt", {"a": 5, "b": 10})
                print(f"✅ adt(5, 10) = {result.content}")
                
                # Test another tool
                print("\n🧪 Testing getSystemContext tool call...")
                result = await session.call_tool("getSystemContext", {})
                print(f"✅ getSystemContext returned {len(str(result.content))} characters")
                
                print("\n🎉 All tests passed! MCP server is working perfectly with official SDK!")
                
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        import traceback
        traceback.print_exc()

async def test_sse_client():
    """Test if SSE transport works (should fail with our HTTP-only server)"""
    
    print("\n🔌 Testing SSE transport (should fail)...")
    
    try:
        async with sse_client("http://localhost:3000/mcp") as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("❌ SSE transport unexpectedly succeeded!")
                
    except Exception as e:
        print(f"✅ SSE transport correctly failed: {e}")

async def main():
    """Run all tests"""
    print("🚀 Testing pb-fm-mcp server with official MCP Python SDK\n")
    
    await test_http_client()
    await test_sse_client()

if __name__ == "__main__":
    asyncio.run(main())