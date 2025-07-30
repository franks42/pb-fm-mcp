#!/usr/bin/env python3
"""Quick test to verify live blockchain data handling works correctly."""

import asyncio
import httpx
import json

async def test_live_data_functions():
    """Test a few live blockchain functions to verify they're marked as equivalent."""
    rest_url = "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1"
    mcp_url = "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/mcp"
    test_wallet = "pb1c9rqwfefggk3s3y79rh8quwvp8rf8ayr7qvmk8"
    
    print("🧪 Testing Live Blockchain Data Functions\n")
    
    # Test functions that should be marked as equivalent due to live data
    live_functions = [
        ("fetch_current_hash_statistics", "/api/fetch-current-hash-statistics"),
        ("fetch_current_fm_data", "/api/fetch-current-fm-data"),
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for func_name, rest_path in live_functions:
            print(f"📊 Testing: {func_name}")
            
            # Test MCP
            mcp_response = await client.post(mcp_url, json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": func_name, "arguments": {}},
                "id": 1
            })
            mcp_success = mcp_response.status_code == 200 and "result" in mcp_response.json()
            print(f"  🔧 MCP: {'✅' if mcp_success else '❌'}")
            
            # Test REST  
            rest_response = await client.get(f"{rest_url}{rest_path}")
            rest_success = rest_response.status_code == 200
            print(f"  🌐 REST: {'✅' if rest_success else '❌'}")
            
            if mcp_success and rest_success:
                print(f"  🔄 Data: ✅ LIVE DATA OK (would be marked equivalent)")
            else:
                print(f"  🔄 Data: ❌ One protocol failed")
            print()

if __name__ == "__main__":
    asyncio.run(test_live_data_functions())