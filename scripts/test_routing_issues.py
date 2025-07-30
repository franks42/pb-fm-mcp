#!/usr/bin/env python3
"""Test specific routing issues for functions that should support REST."""

import asyncio
import httpx
import json

async def test_routing_issues():
    rest_url = "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1"
    
    print("🔍 Testing Known Routing Issues\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: get_dashboard_config - query vs path params
        print("1. get_dashboard_config:")
        
        # Wrong way (path param)
        resp1 = await client.get(f"{rest_url}/api/get_dashboard_config/test-dashboard-001")
        print(f"   Path param: {resp1.status_code} - {'❌ Wrong' if resp1.status_code == 404 else 'Unexpected'}")
        
        # Right way (query params)
        resp2 = await client.get(f"{rest_url}/api/get_dashboard_config?dashboard_id=test-dashboard-001&version=1")
        print(f"   Query params: {resp2.status_code} - {'✅ Correct' if resp2.status_code == 200 else '❌ Failed'}")
        
        # Test 2: get_conversation_status - path vs query params
        print("\n2. get_conversation_status:")
        
        # Wrong way (query param)
        resp3 = await client.get(f"{rest_url}/api/get_conversation_status?session_id=__TEST_SESSION__")
        print(f"   Query param: {resp3.status_code} - {'❌ Wrong' if resp3.status_code == 404 else 'Unexpected'}")
        
        # Right way (path param)
        resp4 = await client.get(f"{rest_url}/api/get_conversation_status/__TEST_SESSION__")
        print(f"   Path param: {resp4.status_code} - {'✅ Correct' if resp4.status_code == 200 else '❌ Failed'}")
        
        # Test 3: Check functions with wrong path prefix
        print("\n3. Functions with wrong/missing REST paths:")
        
        # Get introspection to find these
        introspection = await client.get(f"{rest_url}/api/get_registry_introspection")
        functions = introspection.json()['functions']
        
        # Find functions that claim REST support but might have issues
        potential_issues = []
        for func in functions:
            if 'rest' in func.get('protocols', []):
                path = func.get('path', '')
                if path and not path.startswith('/api/'):
                    potential_issues.append((func['name'], path))
        
        if potential_issues:
            print("   Found functions with non-standard REST paths:")
            for name, path in potential_issues[:5]:
                print(f"   - {name}: {path} (should start with /api/)")
        else:
            print("   ✅ All REST functions have proper /api/ prefix")
        
        # Test 4: Check OpenAPI consistency
        print("\n4. OpenAPI endpoint consistency:")
        openapi_resp = await client.get(f"{rest_url}/openapi.json")
        if openapi_resp.status_code == 200:
            openapi = openapi_resp.json()
            paths = openapi.get('paths', {})
            api_paths = [p for p in paths if p.startswith('/api/')]
            print(f"   Total paths: {len(paths)}")
            print(f"   API paths: {len(api_paths)}")
            print(f"   Non-API paths: {len(paths) - len(api_paths)}")
            
            # Show some non-API paths
            non_api = [p for p in paths if not p.startswith('/api/') and p != '/']
            if non_api:
                print("\n   Non-standard paths found:")
                for path in non_api[:5]:
                    print(f"   - {path}")

if __name__ == "__main__":
    asyncio.run(test_routing_issues())
