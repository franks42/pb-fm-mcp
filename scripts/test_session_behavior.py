#!/usr/bin/env python3
"""
Comprehensive test script to validate MCP server session behavior.

Tests:
1. Does server generate new mcp-session-id when none presented?
2. Does server return error when invalid mcp-session-id is presented?
3. Does server accept mcp-session-id across subsequent invocations?
"""

import asyncio
import json
import httpx
import os


async def test_no_session_id():
    """Test 1: Server generates new session ID when none presented."""
    print("\n🧪 TEST 1: Server generates new session ID when none presented")
    print("=" * 60)
    
    mcp_url = "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/mcp"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Send initialize request WITHOUT session ID header
            response = await client.post(
                mcp_url,
                json={
                    "jsonrpc": "2.0",
                    "id": "test-no-session",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {"list": True, "call": True}},
                        "clientInfo": {"name": "test-client", "version": "1.0.0"}
                    }
                },
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📤 HTTP Status: {response.status_code}")
            print(f"📤 Response Headers: {dict(response.headers)}")
            
            # Check if server returned a session ID
            session_id = response.headers.get('Mcp-Session-Id') or response.headers.get('mcp-session-id')
            
            if session_id:
                print(f"✅ SUCCESS: Server generated session ID: {session_id}")
                return session_id
            else:
                print("❌ FAIL: Server did not generate session ID")
                result = response.json()
                print(f"Response body: {json.dumps(result, indent=2)}")
                return None
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None


async def test_invalid_session_id():
    """Test 2: Server error handling for invalid session ID."""
    print("\n🧪 TEST 2: Server error handling for invalid session ID")
    print("=" * 60)
    
    mcp_url = "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/mcp"
    invalid_session = "totally-fake-session-12345"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Send tools/list request with invalid session ID
            response = await client.post(
                mcp_url,
                json={
                    "jsonrpc": "2.0",
                    "id": "test-invalid-session",
                    "method": "tools/list",
                    "params": {}
                },
                headers={
                    "Content-Type": "application/json",
                    "Mcp-Session-Id": invalid_session
                }
            )
            
            print(f"📤 HTTP Status: {response.status_code}")
            print(f"📤 Used Invalid Session ID: {invalid_session}")
            
            result = response.json()
            print(f"📤 Response: {json.dumps(result, indent=2)}")
            
            if "error" in result:
                print(f"✅ SUCCESS: Server returned error for invalid session")
                return True
            elif "result" in result and "tools" in result["result"]:
                print(f"⚠️ UNEXPECTED: Server accepted invalid session (NoOpSessionStore behavior)")
                print(f"   Found {len(result['result']['tools'])} tools")
                return False
            else:
                print(f"❌ UNKNOWN: Unexpected response format")
                return None
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None


async def test_session_persistence_across_invocations():
    """Test 3: Server accepts session ID across multiple invocations."""
    print("\n🧪 TEST 3: Server accepts session ID across multiple invocations")
    print("=" * 60)
    
    mcp_url = "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/mcp"
    
    try:
        # Step 1: Initialize and get session ID
        print("🚀 Step 1: Initialize new session")
        session_id = await test_no_session_id()
        
        if not session_id:
            print("❌ Cannot test persistence without valid session ID")
            return False
            
        # Step 2: Use session ID in subsequent call
        print(f"\n🔄 Step 2: Reuse session ID in tools/list call")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                mcp_url,
                json={
                    "jsonrpc": "2.0",
                    "id": "test-reuse-session",
                    "method": "tools/list",
                    "params": {}
                },
                headers={
                    "Content-Type": "application/json",
                    "Mcp-Session-Id": session_id
                }
            )
            
            print(f"📤 HTTP Status: {response.status_code}")
            print(f"📤 Reused Session ID: {session_id}")
            
            result = response.json()
            
            if "result" in result and "tools" in result["result"]:
                tools_count = len(result["result"]["tools"])
                print(f"✅ SUCCESS: Server accepted reused session ID")
                print(f"   Found {tools_count} tools")
                
                # Step 3: Try one more call to confirm persistence
                print(f"\n🔄 Step 3: Third call with same session ID")
                response2 = await client.post(
                    mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": "test-third-call",
                        "method": "tools/call",
                        "params": {
                            "name": "fetch_current_hash_statistics",
                            "arguments": {}
                        }
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Mcp-Session-Id": session_id
                    }
                )
                
                result2 = response2.json()
                if "result" in result2:
                    print(f"✅ SUCCESS: Session persistent across 3 calls")
                    return True
                else:
                    print(f"❌ FAIL: Third call failed: {result2}")
                    return False
                    
            else:
                print(f"❌ FAIL: Server rejected reused session")
                print(f"   Response: {json.dumps(result, indent=2)}")
                return False
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


async def test_client_invocation_persistence():
    """Test 4: Test MCP client session persistence across separate invocations."""
    print("\n🧪 TEST 4: MCP client session persistence across invocations")  
    print("=" * 60)
    
    # Remove any existing session file first
    session_file = ".test_session_persistence"
    if os.path.exists(session_file):
        os.remove(session_file)
        print(f"🗑️ Removed existing session file: {session_file}")
    
    try:
        from mcp_test_client import MCPTestClient
        
        # First invocation - should create new session
        print("🚀 First invocation: Creating new session")
        client1 = MCPTestClient(
            "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/mcp",
            session_file=session_file
        )
        
        if await client1.connect():
            session1 = client1.session_id
            print(f"✅ First session created: {session1}")
            await client1.disconnect()
        else:
            print("❌ First invocation failed")
            return False
            
        # Second invocation - should reuse session
        print(f"\n🔄 Second invocation: Should reuse session")
        client2 = MCPTestClient(
            "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/mcp", 
            session_file=session_file
        )
        
        if await client2.connect():
            session2 = client2.session_id
            print(f"✅ Second session loaded: {session2}")
            await client2.disconnect()
            
            if session1 == session2:
                print(f"✅ SUCCESS: Session persisted across invocations!")
                return True
            else:
                print(f"❌ FAIL: Different sessions - {session1} vs {session2}")
                return False
        else:
            print("❌ Second invocation failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(session_file):
            os.remove(session_file)


async def main():
    """Run all MCP session behavior tests."""
    print("🧪 COMPREHENSIVE MCP SESSION BEHAVIOR TESTS")
    print("=" * 80)
    
    results = {}
    
    # Test 1: Server generates session ID when none presented
    results["new_session_generation"] = await test_no_session_id()
    
    # Test 2: Server error handling for invalid session ID  
    results["invalid_session_handling"] = await test_invalid_session_id()
    
    # Test 3: Server accepts session ID across multiple calls
    results["session_persistence"] = await test_session_persistence_across_invocations()
    
    # Test 4: MCP client session persistence across invocations
    results["client_persistence"] = await test_client_invocation_persistence()
    
    # Summary
    print("\n" + "=" * 80)
    print("🏁 TEST SUMMARY")
    print("=" * 80)
    
    print(f"1. Server generates new session ID: {'✅ YES' if results['new_session_generation'] else '❌ NO'}")
    print(f"2. Server rejects invalid session ID: {'✅ YES' if results['invalid_session_handling'] else '⚠️ NO (NoOpSessionStore)'}")
    print(f"3. Server accepts session across calls: {'✅ YES' if results['session_persistence'] else '❌ NO'}")
    print(f"4. Client persists sessions: {'✅ YES' if results['client_persistence'] else '❌ NO'}")
    
    print(f"\n🎯 CONCLUSION:")
    if results["new_session_generation"] and results["session_persistence"]:
        print("   MCP session system is working correctly!")
        if not results["invalid_session_handling"]:
            print("   Note: Server uses NoOpSessionStore (accepts any session ID)")
    else:
        print("   MCP session system has issues that need investigation")


if __name__ == "__main__":
    asyncio.run(main())