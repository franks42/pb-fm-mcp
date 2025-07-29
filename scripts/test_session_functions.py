#!/usr/bin/env python3
"""Quick test to verify session setup functions are marked as successful when endpoints are reachable."""

import asyncio
import httpx

async def test_session_setup_functions():
    """Test a few session setup functions to verify endpoint reachability logic."""
    rest_url = "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1"
    
    print("🧪 Testing Session Setup Functions\n")
    
    # Test functions that should be marked as successful if endpoints are reachable
    session_functions = [
        ("queue_user_message", "/api/queue_user_message"),
        ("get_dashboard_config", "/api/get_dashboard_config"),
        ("fetch_session_events", "/api/fetch_session_events"),
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for func_name, rest_path in session_functions:
            print(f"📊 Testing: {func_name}")
            
            # Try to reach the endpoint (expecting 500 parameter error, not 404)
            try:
                response = await client.get(f"{rest_url}{rest_path}")
                
                if response.status_code == 404:
                    print(f"  ❌ Endpoint not found (404)")
                elif response.status_code == 500:
                    print(f"  ✅ Endpoint reachable (500 - parameter error expected)")
                else:
                    print(f"  ✅ Endpoint reachable ({response.status_code})")
                    
            except Exception as e:
                print(f"  ❌ Connection error: {e}")
            print()

if __name__ == "__main__":
    asyncio.run(test_session_setup_functions())