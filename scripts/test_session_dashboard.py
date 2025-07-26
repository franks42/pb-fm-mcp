#!/usr/bin/env python3
"""
Test script to validate MCP session-based dashboard creation.
"""

import asyncio
import json
from mcp_test_client import MCPTestClient


async def test_session_based_dashboard():
    """Test the session-based dashboard creation feature."""
    
    # Initialize session-aware MCP client
    client = MCPTestClient("https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/mcp")
    
    try:
        # Connect with proper session initialization
        print("🚀 Testing Session-Based Dashboard Creation")
        print("=" * 50)
        
        if not await client.connect():
            print("❌ Failed to connect to MCP server")
            return
            
        print(f"✅ Connected with session ID: {client.session_id}")
        print()
        
        # Test dashboard creation with session
        print("🎯 Creating personalized dashboard...")
        result = await client.call_tool("create_personalized_dashboard", {
            "wallet_address": "pb1test123session",
            "dashboard_name": "My Session-Based Dashboard Test"
        })
        
        print("\n📊 Dashboard Creation Result:")
        print(json.dumps(result, indent=2))
        
        # Extract dashboard URL if successful
        if "content" in result and len(result["content"]) > 0:
            content_str = result["content"][0]["text"]
            # Parse the string representation of the dict
            try:
                import ast
                dashboard_data = ast.literal_eval(content_str)
                
                if dashboard_data.get("success"):
                    dashboard_url = dashboard_data.get("dashboard_url")
                    session_type = dashboard_data.get("session_type")
                    mcp_session_id = dashboard_data.get("mcp_session_id")
                    
                    print(f"\n🎉 SUCCESS! Dashboard created:")
                    print(f"📍 URL: {dashboard_url}")
                    print(f"🎯 Session Type: {session_type}")
                    print(f"🔗 MCP Session ID: {mcp_session_id}")
                    print(f"🔄 Client Session ID: {client.session_id}")
                    
                    if mcp_session_id == client.session_id:
                        print("✅ SESSION ID MATCH - Stable URL system working!")
                    else:
                        print("⚠️ Session ID mismatch - investigating...")
                        
                else:
                    print(f"❌ Dashboard creation failed: {dashboard_data.get('error')}")
                    
            except Exception as e:
                print(f"⚠️ Could not parse result: {e}")
                
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_session_based_dashboard())