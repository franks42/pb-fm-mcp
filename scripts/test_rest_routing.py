#!/usr/bin/env python3
"""
REST API Routing Test Script

Tests REST endpoints with correct HTTP methods (GET vs POST) to identify routing issues.
"""

import asyncio
import httpx
import json
import sys
from typing import Dict, Any

# Test data
TEST_WALLET = "user_provided_wallet_address"
TEST_SESSION = "__TEST_SESSION__"
BASE_URLS = [
    "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1",
    "https://pb-fm-mcp-dev.creativeapptitude.com"
]

# Functions that require POST method
POST_FUNCTIONS = {
    "create_personalized_dashboard": {
        "wallet_address": TEST_WALLET,
        "dashboard_name": "Test Dashboard", 
        "ai_session_id": TEST_SESSION
    },
    "create_hash_price_chart": {
        "time_range": "24h",
        "dashboard_id": "test-dashboard-001"
    },
    "create_portfolio_health": {
        "wallet_address": TEST_WALLET,
        "dashboard_id": "test-dashboard-001",
        "analysis_depth": "basic"
    },
    "take_screenshot": {
        "url": "https://example.com",
        "width": 1200,
        "height": 800,
        "wait_seconds": 2
    },
    "upload_screenshot": {
        "screenshot_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
        "dashboard_id": "test-dashboard-001",
        "context": "test",
        "screenshot_id": "test-001"
    },
    "trigger_browser_screenshot": {
        "dashboard_id": "test-dashboard-001",
        "context": "test",
        "wait_seconds": 2,
        "screenshot_id": "test-001"
    },
    "update_chart_config": {
        "dashboard_id": "test-dashboard-001",
        "chart_element": "test-chart",
        "updates": {"color": "blue"},
        "context": "test"
    },
    "queue_user_message": {
        "message": "Test message",
        "session_id": TEST_SESSION
    },
    "send_response_to_web": {
        "message_id": "test-message-001",
        "response": "Test response",
        "session_id": TEST_SESSION
    },
    "create_new_session": {},
    "cleanup_inactive_sessions": {
        "max_age_hours": 24
    }
}

# Functions that use GET method
GET_FUNCTIONS = [
    "fetch_current_hash_statistics",
    "get_system_context", 
    f"fetch_account_info/{TEST_WALLET}",
    f"fetch_account_is_vesting/{TEST_WALLET}",
    f"fetch_total_delegation_data/{TEST_WALLET}",
    f"fetch_vesting_total_unvested_amount/{TEST_WALLET}",
    f"fetch_available_committed_amount/{TEST_WALLET}",
    "fetch_current_fm_data",
    "fetch_last_crypto_token_price/HASH-USD",
    "fetch_figure_markets_assets_info",
    f"fetch_complete_wallet_summary/{TEST_WALLET}",
    "fetch_market_overview_summary",
    "get_registry_introspection",
    "get_registry_summary",
    f"get_conversation_status?session_id={TEST_SESSION}",
    f"get_dashboard_info/test-dashboard-001?ai_session_id={TEST_SESSION}",
    f"get_dashboard_config/test-dashboard-001",
    f"fetch_session_events?session_id={TEST_SESSION}",
    f"get_browser_connection_order?session_id={TEST_SESSION}"
]

async def test_post_function(base_url: str, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Test a POST function."""
    url = f"{base_url}/api/{function_name}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            return {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.text[:200] if response.status_code != 200 else "OK",
                "data": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            return {
                "status_code": 0,
                "success": False,
                "response": str(e),
                "data": None
            }

async def test_get_function(base_url: str, function_path: str) -> Dict[str, Any]:
    """Test a GET function."""
    url = f"{base_url}/api/{function_path}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            
            return {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.text[:200] if response.status_code != 200 else "OK",
                "data": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            return {
                "status_code": 0,
                "success": False,
                "response": str(e),
                "data": None
            }

async def main():
    print("🔧 REST API Routing Test")
    print("=" * 40)
    
    for base_url in BASE_URLS:
        print(f"\n🌐 Testing: {base_url}")
        print("-" * 60)
        
        # Test POST functions
        print("\n📮 POST Functions:")
        post_passed = 0
        for func_name, payload in POST_FUNCTIONS.items():
            result = await test_post_function(base_url, func_name, payload)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {func_name}: {result['status_code']} - {result['response']}")
            if result["success"]:
                post_passed += 1
        
        print(f"\n📊 POST Results: {post_passed}/{len(POST_FUNCTIONS)} passed ({post_passed/len(POST_FUNCTIONS)*100:.1f}%)")
        
        # Test GET functions  
        print("\n📥 GET Functions:")
        get_passed = 0
        for func_path in GET_FUNCTIONS:
            result = await test_get_function(base_url, func_path)
            status = "✅" if result["success"] else "❌"
            func_name = func_path.split('/')[0].split('?')[0]
            print(f"  {status} {func_name}: {result['status_code']} - {result['response']}")
            if result["success"]:
                get_passed += 1
        
        print(f"\n📊 GET Results: {get_passed}/{len(GET_FUNCTIONS)} passed ({get_passed/len(GET_FUNCTIONS)*100:.1f}%)")
        
        total_passed = post_passed + get_passed
        total_tests = len(POST_FUNCTIONS) + len(GET_FUNCTIONS)
        print(f"\n🎯 Overall: {total_passed}/{total_tests} passed ({total_passed/total_tests*100:.1f}%)")

if __name__ == "__main__":
    asyncio.run(main())