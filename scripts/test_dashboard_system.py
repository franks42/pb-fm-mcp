#!/usr/bin/env python3
"""
Test script for the personalized dashboard system.

This script tests:
1. Creating a personalized dashboard via MCP function
2. Retrieving dashboard info
3. Creating a HASH price chart
4. Accessing the dashboard web interface
"""

import requests
import json
import sys
from urllib.parse import urlparse

# Development environment URL
BASE_URL = "https://pb-fm-mcp-dev.creativeapptitude.com"

def test_create_dashboard():
    """Test creating a personalized dashboard."""
    print("🔧 Testing dashboard creation...")
    
    url = f"{BASE_URL}/api/create_personalized_dashboard"
    payload = {
        "wallet_address": "pb1test_wallet_12345",
        "dashboard_name": "AI Test Dashboard",
        "ai_session_id": "test_session_001"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Dashboard created successfully!")
                print(f"   Dashboard ID: {data['dashboard_id']}")
                print(f"   Dashboard URL: {data['dashboard_url']}")
                print(f"   AI Instructions: {data['ai_instructions']}")
                return data['dashboard_id'], data['dashboard_url']
            else:
                print(f"❌ Dashboard creation failed: {data.get('error', 'Unknown error')}")
                return None, None
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Dashboard creation error: {e}")
        return None, None

def test_get_dashboard_info(dashboard_id):
    """Test retrieving dashboard info."""
    print(f"🔧 Testing dashboard info retrieval...")
    
    url = f"{BASE_URL}/api/get_dashboard_info/{dashboard_id}"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Dashboard info retrieved successfully!")
                print(f"   Dashboard Name: {data['dashboard_name']}")
                print(f"   Wallet Address: {data.get('wallet_address', 'Not specified')}")
                print(f"   Created: {data['created_at']}")
                print(f"   AI Message: {data['ai_message']}")
                return True
            else:
                print(f"❌ Dashboard info retrieval failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard info retrieval error: {e}")
        return False

def test_create_hash_chart(dashboard_id):
    """Test creating a HASH price chart."""
    print(f"🔧 Testing HASH price chart creation...")
    
    url = f"{BASE_URL}/api/create_hash_price_chart"
    payload = {
        "time_range": "24h",
        "dashboard_id": dashboard_id
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ HASH price chart created successfully!")
                print(f"   Chart Type: {data['chart_type']}")
                print(f"   Data Points: {data['data_points']}")
                print(f"   Current Price: ${data['current_price']:.4f}")
                print(f"   Price Change: {data['price_change_percent']:.2f}%")
                print(f"   AI Insights: {data['ai_insights']}")
                return True
            else:
                print(f"❌ HASH chart creation failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ HASH chart creation error: {e}")
        return False

def test_dashboard_web_access(dashboard_url):
    """Test accessing the dashboard web interface."""
    print(f"🔧 Testing dashboard web interface access...")
    
    try:
        response = requests.get(dashboard_url, timeout=30)
        
        if response.status_code == 200:
            content = response.text
            if "dashboard-title" in content and "Plotly" in content:
                print(f"✅ Dashboard web interface accessible!")
                print(f"   URL: {dashboard_url}")
                print(f"   Content Length: {len(content)} bytes")
                print(f"   Contains Plotly.js: {'✅' if 'plotly-latest.min.js' in content else '❌'}")
                return True
            else:
                print(f"❌ Dashboard web interface missing expected content")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard web access error: {e}")
        return False

def main():
    """Run all dashboard tests."""
    print("🚀 Starting Personalized Dashboard System Tests")
    print("=" * 60)
    
    # Test 1: Create dashboard
    dashboard_id, dashboard_url = test_create_dashboard()
    if not dashboard_id:
        print("❌ Cannot continue tests - dashboard creation failed")
        sys.exit(1)
    
    print()
    
    # Test 2: Get dashboard info
    info_success = test_get_dashboard_info(dashboard_id)
    
    print()
    
    # Test 3: Create HASH chart
    chart_success = test_create_hash_chart(dashboard_id)
    
    print()
    
    # Test 4: Access web interface
    web_success = test_dashboard_web_access(dashboard_url)
    
    print()
    print("=" * 60)
    print("🏁 Test Results Summary:")
    print(f"   Dashboard Creation: {'✅' if dashboard_id else '❌'}")
    print(f"   Dashboard Info:     {'✅' if info_success else '❌'}")
    print(f"   HASH Chart:         {'✅' if chart_success else '❌'}")
    print(f"   Web Interface:      {'✅' if web_success else '❌'}")
    
    if all([dashboard_id, info_success, chart_success, web_success]):
        print("\n🎉 ALL TESTS PASSED! Personalized dashboard system is working!")
        print(f"\n🔗 Your test dashboard: {dashboard_url}")
    else:
        print("\n⚠️  Some tests failed - check the output above for details")
        sys.exit(1)

if __name__ == "__main__":
    main()