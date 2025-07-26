#!/usr/bin/env python3
"""
Test script to see what happens when we send invalid session IDs to the MCP server.
"""

import asyncio
import json
import httpx


async def test_invalid_session_responses():
    """Test what the MCP server returns for invalid session IDs."""
    
    mcp_url = "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/mcp"
    
    test_cases = [
        {
            "name": "Completely Invalid Session ID",
            "session_id": "totally-fake-session-id-123"
        },
        {
            "name": "Empty Session ID",
            "session_id": ""
        },
        {
            "name": "Malformed UUID",
            "session_id": "not-a-uuid-at-all"
        },
        {
            "name": "Valid Format but Non-existent",
            "session_id": "00000000-0000-0000-0000-000000000000"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print(f"📍 Session ID: {test_case['session_id']}")
        print("-" * 50)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Content-Type": "application/json"}
                if test_case['session_id']:
                    headers["Mcp-Session-Id"] = test_case['session_id']
                
                response = await client.post(
                    mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": f"test-{test_case['name'].lower().replace(' ', '-')}",
                        "method": "tools/list",
                        "params": {}
                    },
                    headers=headers
                )
                
                print(f"📤 HTTP Status: {response.status_code}")
                print(f"📤 Headers: {dict(response.headers)}")
                
                if response.headers.get('content-type', '').startswith('application/json'):
                    result = response.json()
                    print(f"📤 Response Body:")
                    print(json.dumps(result, indent=2))
                else:
                    print(f"📤 Response Body: {response.text}")
                    
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    print(f"\n🧪 Testing: No Session ID Header (should work)")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                mcp_url,
                json={
                    "jsonrpc": "2.0",
                    "id": "test-no-session",
                    "method": "tools/list", 
                    "params": {}
                },
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📤 HTTP Status: {response.status_code}")
            result = response.json()
            print(f"📤 Response Body:")
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"❌ Request failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_invalid_session_responses())