#!/usr/bin/env python3
"""Quick test to identify the remaining 10% failures."""

import asyncio
import httpx
import json

async def identify_failures():
    mcp_url = "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/mcp"
    rest_url = "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1"
    test_wallet = "user_provided_wallet_address"
    
    print("🔍 IDENTIFYING REMAINING FAILURES\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get function protocols
        introspection = await client.get(f"{rest_url}/api/get_registry_introspection")
        functions = introspection.json()['functions']
        
        # Get MCP tools
        mcp_response = await client.post(mcp_url, json={
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        })
        mcp_tools = {tool['name'] for tool in mcp_response.json()['result']['tools']}
        
        # Categorize and test
        mcp_only = [f for f in functions if 'mcp' in f.get('protocols', []) and 'rest' not in f.get('protocols', [])]
        both_protocol = [f for f in functions if 'mcp' in f.get('protocols', []) and 'rest' in f.get('protocols', [])]
        rest_only = [f for f in functions if 'rest' in f.get('protocols', []) and 'mcp' not in f.get('protocols', [])]
        
        print(f"📊 Protocol Distribution:")
        print(f"  MCP-only: {len(mcp_only)} (should not be tested via REST)")
        print(f"  Both protocols: {len(both_protocol)} (test both MCP and REST)")
        print(f"  REST-only: {len(rest_only)} (test REST only)")
        
        # Test both-protocol functions to find failures
        print(f"\n🧪 Testing Both-Protocol Functions:")
        
        mcp_failures = []
        rest_failures = []
        success_count = 0
        
        for func in both_protocol[:10]:  # Test first 10 to avoid timeout
            func_name = func['name']
            func_path = func.get('path', '')
            
            # Test MCP
            mcp_success = func_name in mcp_tools
            if not mcp_success:
                mcp_failures.append(func_name)
            
            # Test REST - try different path patterns and methods
            rest_success = False
            test_paths = []
            http_method = func.get('method', 'GET').upper()
            
            if func_path:
                # Use registered path
                if '{wallet_address}' in func_path:
                    test_path = func_path.replace('{wallet_address}', test_wallet)
                else:
                    test_path = func_path
                test_paths.append(test_path)
            
            # Try common patterns (use snake_case, not kebab-case)
            test_paths.extend([
                f"/api/{func_name}",  # Exact function name (snake_case)
                f"/api/{func_name}?session_id=__TEST_SESSION__",
            ])
            
            for path in test_paths:
                try:
                    url = f"{rest_url}{path}"
                    
                    if http_method == "POST":
                        # Build JSON payload with test data
                        json_data = {}
                        if func_name == "create_hash_price_chart":
                            json_data = {"time_range": "24h"}
                        elif func_name == "create_personalized_dashboard":
                            json_data = {"wallet_address": test_wallet, "dashboard_name": "Test Dashboard"}
                        elif func_name == "create_portfolio_health":
                            json_data = {"wallet_address": test_wallet, "analysis_depth": "basic"}
                        elif func_name == "check_screenshot_requests":
                            json_data = {"dashboard_id": "test-dashboard"}
                        else:
                            json_data = {"session_id": "__TEST_SESSION__"}
                        
                        resp = await client.post(url, json=json_data, headers={"Content-Type": "application/json"})
                    else:
                        resp = await client.get(url)
                    
                    if resp.status_code == 200:
                        rest_success = True
                        break
                except:
                    continue
            
            if not rest_success:
                rest_failures.append((func_name, func_path))
            
            if mcp_success and rest_success:
                success_count += 1
                
            status_mcp = "✅" if mcp_success else "❌"
            status_rest = "✅" if rest_success else "❌"
            print(f"  {func_name}: MCP {status_mcp} REST {status_rest}")
        
        # Show failures
        print(f"\n❌ MCP Failures ({len(mcp_failures)}):")
        for func in mcp_failures[:5]:
            print(f"  - {func}")
        
        print(f"\n❌ REST Failures ({len(rest_failures)}):")
        for func_name, path in rest_failures[:5]:
            print(f"  - {func_name} (path: {path})")
        
        # Calculate rates
        total_tested = min(10, len(both_protocol))
        success_rate = (success_count / total_tested) * 100 if total_tested > 0 else 0
        
        print(f"\n📊 Sample Results:")
        print(f"  Tested: {total_tested} both-protocol functions")
        print(f"  Success: {success_count}")
        print(f"  Success Rate: {success_rate:.1f}%")
        
        # Show what types of issues we're seeing
        print(f"\n🔍 Common Issues:")
        print(f"  1. Functions not appearing in MCP tools list")
        print(f"  2. REST endpoints with non-standard parameter patterns")
        print(f"  3. Functions requiring special setup (browser sessions, etc.)")

if __name__ == "__main__":
    asyncio.run(identify_failures())
