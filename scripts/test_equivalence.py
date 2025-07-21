#!/usr/bin/env python3
"""
MCP vs REST API Equivalence Test Runner

Simple script to run equivalence tests and verify that MCP tools and REST endpoints
return identical results. This can be used in CI/CD pipelines or manual testing.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
import httpx
from typing import Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.registry import get_registry
# Import function modules to trigger decorator registration
import src.functions

# Test configuration
TEST_WALLET_ADDRESS = "pb1c9rqwfefggk3s3y79rh8quwvp8rf8ayr7qvmk8"  # Real test address with actual data
DEV_BASE_URL = "https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod"
TIMEOUT = 30.0

class MCPTestClient:
    """Mock MCP client that calls functions directly for testing equivalence"""
    
    async def call_tool(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a registered function directly to simulate MCP tool call"""
        registry = get_registry()
        
        # Find the function by name in the registry
        functions = registry.get_all_functions()
        if function_name in functions:
            func_meta = functions[function_name]
            # Call the function directly with arguments
            if arguments:
                result = await func_meta.func(**arguments)
            else:
                result = await func_meta.func()
            return result
        
        raise ValueError(f"Function {function_name} not found in registry. Available: {list(functions.keys())}")

class RESTTestClient:
    """REST client for testing API endpoints"""
    
    def __init__(self, base_url: str = DEV_BASE_URL):
        self.base_url = base_url
    
    async def call_endpoint(self, path: str, method: str = "GET") -> Dict[str, Any]:
        """Call a REST API endpoint"""
        url = f"{self.base_url}{path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()

def normalize_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize response data for comparison by sorting and handling floating point precision"""
    if isinstance(data, dict):
        # Sort dictionary keys and normalize nested structures
        return {k: normalize_response(v) for k, v in sorted(data.items())}
    elif isinstance(data, list):
        # Sort lists if they contain dictionaries, otherwise preserve order
        if data and isinstance(data[0], dict):
            return [normalize_response(item) for item in sorted(data, key=str)]
        return [normalize_response(item) for item in data]
    elif isinstance(data, float):
        # Round floats to avoid precision differences
        return round(data, 10)
    else:
        return data

def assert_responses_equivalent(mcp_result: Dict[str, Any], rest_result: Dict[str, Any], context: str, allow_live_data_drift: bool = True):
    """Assert that MCP and REST responses are equivalent"""
    # Normalize both responses for comparison
    normalized_mcp = normalize_response(mcp_result)
    normalized_rest = normalize_response(rest_result)
    
    # Check for errors in either response
    mcp_error = mcp_result.get("MCP-ERROR")
    rest_error = rest_result.get("MCP-ERROR") or rest_result.get("error")
    
    if mcp_error or rest_error:
        raise Exception(f"{context}: Error in response - MCP: {mcp_error}, REST: {rest_error}")
    
    # For live blockchain data, allow small differences due to real-time updates
    if allow_live_data_drift and are_responses_close_enough(normalized_mcp, normalized_rest):
        print(f"✅ {context}: MCP and REST responses are equivalent (within acceptable live data tolerance)")
        return
    
    # Compare normalized responses
    if normalized_mcp != normalized_rest:
        mcp_json = json.dumps(normalized_mcp, indent=2, sort_keys=True)
        rest_json = json.dumps(normalized_rest, indent=2, sort_keys=True)
        raise Exception(f"{context}: Responses differ.\nMCP Result:\n{mcp_json}\nREST Result:\n{rest_json}")
    
    print(f"✅ {context}: MCP and REST responses are equivalent")

def are_responses_close_enough(mcp_data: Dict[str, Any], rest_data: Dict[str, Any]) -> bool:
    """Check if responses are close enough for live blockchain data, allowing for minor real-time differences"""
    # Special handling for known dynamic blockchain data fields that change in real-time
    dynamic_fields = ['circulation', 'locked', 'communityPool', 'bonded']
    
    # Check structure first
    if set(mcp_data.keys()) != set(rest_data.keys()):
        return False
    
    # Check each top-level field
    for key in mcp_data.keys():
        mcp_val = mcp_data[key]
        rest_val = rest_data[key]
        
        # For dynamic fields, allow small percentage differences
        if key in dynamic_fields and isinstance(mcp_val, dict) and isinstance(rest_val, dict):
            if set(mcp_val.keys()) != set(rest_val.keys()):
                return False
                
            # Check amounts with tolerance
            if 'amount' in mcp_val and 'amount' in rest_val:
                mcp_amount = int(mcp_val['amount']) if isinstance(mcp_val['amount'], str) else mcp_val['amount']
                rest_amount = int(rest_val['amount']) if isinstance(rest_val['amount'], str) else rest_val['amount']
                
                if mcp_amount == 0 and rest_amount == 0:
                    continue
                
                percent_diff = abs(mcp_amount - rest_amount) / max(abs(mcp_amount), abs(rest_amount))
                print(f"    📊 {key}: {percent_diff:.6f}% difference ({mcp_amount} vs {rest_amount})")
                
                if percent_diff > 0.001:  # Allow up to 0.1% difference
                    return False
            
            # Check denom matches exactly
            if mcp_val.get('denom') != rest_val.get('denom'):
                return False
        else:
            # For non-dynamic fields, require exact match
            if mcp_val != rest_val:
                return False
    
    return True

async def test_full_equivalence_suite():
    """Run full equivalence test suite for all dual-protocol functions"""
    mcp_client = MCPTestClient()
    rest_client = RESTTestClient()
    
    test_cases = [
        ("HASH Statistics", "fetch_current_hash_statistics", {}, "/api/current_hash_statistics"),
        ("Account Info", "fetch_account_info", {"wallet_address": TEST_WALLET_ADDRESS}, f"/api/account_info/{TEST_WALLET_ADDRESS}"),
        ("Account Vesting", "fetch_account_is_vesting", {"wallet_address": TEST_WALLET_ADDRESS}, f"/api/account_is_vesting/{TEST_WALLET_ADDRESS}"),
        ("Total Delegation", "fetch_total_delegation_data", {"wallet_address": TEST_WALLET_ADDRESS}, f"/api/total_delegation_data/{TEST_WALLET_ADDRESS}"),
    ]
    
    print("🧪 Running full MCP vs REST equivalence test suite...")
    
    for test_name, mcp_function, mcp_args, rest_path in test_cases:
        try:
            # Call MCP function
            mcp_result = await mcp_client.call_tool(mcp_function, mcp_args)
            
            # Call REST endpoint  
            rest_result = await rest_client.call_endpoint(rest_path)
            
            # Assert equivalence
            assert_responses_equivalent(mcp_result, rest_result, test_name)
            
        except Exception as e:
            raise Exception(f"❌ {test_name} equivalence test failed: {str(e)}")
    
    print("🎉 All MCP vs REST equivalence tests passed!")

async def main():
    """Run the equivalence test suite"""
    print("🚀 Starting MCP vs REST API Equivalence Tests")
    print("=" * 60)
    
    try:
        await test_full_equivalence_suite()
        print("=" * 60)
        print("✅ All equivalence tests PASSED!")
        return 0
    except Exception as e:
        print("=" * 60)
        print(f"❌ Equivalence tests FAILED: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)