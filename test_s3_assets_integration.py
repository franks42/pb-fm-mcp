#!/usr/bin/env python3
"""
S3 Assets Integration Test

This script tests that the dashboard correctly loads CSS and JavaScript from S3
and that the assets are properly accessible.
"""

import requests
import json
import time
from datetime import datetime

def test_s3_assets_integration():
    """Test complete S3 assets integration"""
    print("🚀 Testing S3 Assets Integration")
    print("=" * 50)
    
    # Configuration
    base_url = "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1"
    s3_base_url = "https://pb-fm-mcp-dev-web-assets-289426936662.s3.us-west-1.amazonaws.com"
    
    results = {
        "s3_css_accessible": False,
        "s3_js_accessible": False,
        "dashboard_references_s3": False,
        "dashboard_loads": False,
        "overall_success": False
    }
    
    # Test 1: S3 CSS file accessible
    print("1. Testing S3 CSS accessibility...")
    try:
        css_response = requests.get(f"{s3_base_url}/css/dashboard.css", timeout=10)
        if css_response.status_code == 200 and "PB-FM MCP Dashboard Styles" in css_response.text:
            print("   ✅ CSS file accessible and contains expected content")
            results["s3_css_accessible"] = True
        else:
            print(f"   ❌ CSS file error: {css_response.status_code}")
    except Exception as e:
        print(f"   ❌ CSS file error: {e}")
    
    # Test 2: S3 JavaScript file accessible  
    print("2. Testing S3 JavaScript accessibility...")
    try:
        js_response = requests.get(f"{s3_base_url}/js/dashboard.js", timeout=10)
        if js_response.status_code == 200 and "PB-FM MCP Dashboard JavaScript" in js_response.text:
            print("   ✅ JavaScript file accessible and contains expected content")
            results["s3_js_accessible"] = True
        else:
            print(f"   ❌ JavaScript file error: {js_response.status_code}")
    except Exception as e:
        print(f"   ❌ JavaScript file error: {e}")
    
    # Test 3: Create test dashboard
    print("3. Creating test dashboard...")
    try:
        dashboard_data = {
            "dashboard_name": f"S3 Test Dashboard {datetime.now().strftime('%H:%M:%S')}",
            "wallet_address": "pb1s3test",
            "ai_session_id": f"s3-test-{int(time.time())}"
        }
        
        create_response = requests.post(
            f"{base_url}/api/create_personalized_dashboard",
            json=dashboard_data,
            timeout=15
        )
        
        if create_response.status_code == 200:
            dashboard_info = create_response.json()
            dashboard_id = dashboard_info["dashboard_id"]
            print(f"   ✅ Dashboard created: {dashboard_id}")
            
            # Test 4: Dashboard HTML references S3 assets
            print("4. Testing dashboard HTML includes S3 references...")
            dashboard_response = requests.get(f"{base_url}/dashboard/{dashboard_id}", timeout=15)
            
            if dashboard_response.status_code == 200:
                html_content = dashboard_response.text
                
                # Check for S3 CSS reference
                css_ref = f"{s3_base_url}/css/dashboard.css"
                js_ref = f"{s3_base_url}/js/dashboard.js"
                
                if css_ref in html_content and js_ref in html_content:
                    print("   ✅ Dashboard HTML correctly references S3 assets")
                    results["dashboard_references_s3"] = True
                    results["dashboard_loads"] = True
                else:
                    print("   ❌ Dashboard HTML missing S3 asset references")
                    print(f"     CSS ref found: {css_ref in html_content}")
                    print(f"     JS ref found: {js_ref in html_content}")
            else:
                print(f"   ❌ Dashboard load error: {dashboard_response.status_code}")
        else:
            print(f"   ❌ Dashboard creation error: {create_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Dashboard test error: {e}")
    
    # Calculate overall success
    results["overall_success"] = all([
        results["s3_css_accessible"],
        results["s3_js_accessible"], 
        results["dashboard_references_s3"],
        results["dashboard_loads"]
    ])
    
    # Print results
    print("\n📊 Test Results:")
    print("=" * 50)
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎯 Overall Result: {'✅ SUCCESS' if results['overall_success'] else '❌ FAILURE'}")
    
    if results["overall_success"]:
        print("\n🎉 S3 Assets Integration is working perfectly!")
        print("Benefits achieved:")
        print("  • CSS/JS updates now happen instantly without Lambda redeployment")
        print("  • Figma assets can be uploaded directly to S3")
        print("  • Better browser caching and performance")
        print("  • Cleaner separation of concerns")
        print(f"\nTest Dashboard URL: {base_url}/dashboard/{dashboard_id}")
    else:
        print("\n⚠️ S3 Assets Integration needs attention")
        print("Check the failed tests above for details")
    
    return results

if __name__ == "__main__":
    test_s3_assets_integration()