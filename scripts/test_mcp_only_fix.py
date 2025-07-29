#!/usr/bin/env python3
"""Quick test to verify MCP-only function handling."""

import asyncio
import httpx
import json

async def test_protocol_awareness():
    mcp_url = "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/mcp"
    rest_url = "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1"
    
    # Get protocol information
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch introspection data
        response = await client.get(f"{rest_url}/api/get_registry_introspection")
        introspection = response.json()
        
        # Categorize functions
        mcp_only = []
        rest_only = []
        both = []
        
        for func in introspection['functions']:
            protocols = func.get('protocols', [])
            if 'mcp' in protocols and 'rest' not in protocols:
                mcp_only.append(func['name'])
            elif 'rest' in protocols and 'mcp' not in protocols:
                rest_only.append(func['name'])
            elif 'mcp' in protocols and 'rest' in protocols:
                both.append(func['name'])
        
        print(f"📊 Protocol Distribution:")
        print(f"  MCP-only: {len(mcp_only)}")
        print(f"  REST-only: {len(rest_only)}")
        print(f"  Both: {len(both)}")
        print(f"  Total: {len(mcp_only) + len(rest_only) + len(both)}")
        
        # Test a few examples
        print(f"\n🧪 Testing examples:")
        
        # Test an MCP-only function
        if mcp_only:
            func_name = mcp_only[0]
            print(f"\n1. MCP-only function: {func_name}")
            
            # Try REST (should fail)
            try:
                rest_resp = await client.get(f"{rest_url}/api/{func_name}")
                print(f"   REST: {rest_resp.status_code} - {'UNEXPECTED SUCCESS' if rest_resp.status_code == 200 else 'Expected failure'}")
            except Exception as e:
                print(f"   REST: Failed as expected - {e}")
            
            # Try MCP (should work)
            mcp_resp = await client.post(mcp_url, json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            })
            tools = mcp_resp.json()['result']['tools']
            has_tool = any(t['name'] == func_name for t in tools)
            print(f"   MCP: {'✅ Found in tools list' if has_tool else '❌ Not found'}")
        
        # Test a both-protocols function
        if both:
            func_name = "fetch_current_hash_statistics"  # Known to support both
            print(f"\n2. Both-protocols function: {func_name}")
            
            # Try REST
            rest_resp = await client.get(f"{rest_url}/api/{func_name}")
            print(f"   REST: {rest_resp.status_code} - {'✅ Success' if rest_resp.status_code == 200 else '❌ Failed'}")
            
            # Try MCP
            mcp_resp = await client.post(mcp_url, json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 2,
                "params": {
                    "name": func_name,
                    "arguments": {}
                }
            })
            mcp_success = 'result' in mcp_resp.json()
            print(f"   MCP: {'✅ Success' if mcp_success else '❌ Failed'}")
        
        # Show some specific examples
        print(f"\n📋 Example MCP-only functions:")
        for func in mcp_only[:5]:
            print(f"  - {func}")
        
        print(f"\n📋 Example both-protocol functions:")
        for func in both[:5]:
            print(f"  - {func}")

if __name__ == "__main__":
    asyncio.run(test_protocol_awareness())
