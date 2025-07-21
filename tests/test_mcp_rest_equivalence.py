"""
Test MCP vs REST API Equivalence

This module contains tests that verify MCP tools and their equivalent REST API endpoints
return identical results. This ensures protocol consistency and data integrity.
"""

import asyncio
import json
import pytest
import httpx
from typing import Dict, Any, Optional

from src.registry import get_registry
from src.functions.stats_functions import fetch_current_hash_statistics
from src.functions.blockchain_functions import (
    fetch_account_info,
    fetch_account_is_vesting,
    fetch_total_delegation_data
)

# Test configuration
TEST_WALLET_ADDRESS = "pb1c9rqwfefggk3s3y79rh8quwvp8rf8ayr7qvmk8"  # Real test address with actual data
LOCAL_BASE_URL = "http://localhost:3000"
DEV_BASE_URL = "https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod"
TIMEOUT = 30.0

class MCPTestClient:
    """Mock MCP client that calls functions directly for testing equivalence"""
    
    async def call_tool(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a registered function directly to simulate MCP tool call"""
        registry = get_registry()
        
        # Find the function by name in the registry
        for func_meta in registry.get_all_functions():
            if func_meta.name == function_name:
                # Call the function directly with arguments
                if arguments:
                    result = await func_meta.func(**arguments)
                else:
                    result = await func_meta.func()
                return result
        
        raise ValueError(f"Function {function_name} not found in registry")


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


@pytest.fixture
def mcp_client():
    """Provide MCP test client"""
    return MCPTestClient()


@pytest.fixture
def rest_client():
    """Provide REST test client"""
    return RESTTestClient()


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


def assert_responses_equivalent(mcp_result: Dict[str, Any], rest_result: Dict[str, Any], context: str):
    """Assert that MCP and REST responses are equivalent"""
    # Normalize both responses for comparison
    normalized_mcp = normalize_response(mcp_result)
    normalized_rest = normalize_response(rest_result)
    
    # Check for errors in either response
    mcp_error = mcp_result.get("MCP-ERROR")
    rest_error = rest_result.get("MCP-ERROR") or rest_result.get("error")
    
    if mcp_error or rest_error:
        pytest.fail(f"{context}: Error in response - MCP: {mcp_error}, REST: {rest_error}")
    
    # Compare normalized responses
    if normalized_mcp != normalized_rest:
        mcp_json = json.dumps(normalized_mcp, indent=2, sort_keys=True)
        rest_json = json.dumps(normalized_rest, indent=2, sort_keys=True)
        pytest.fail(f"{context}: Responses differ.\nMCP Result:\n{mcp_json}\nREST Result:\n{rest_json}")
    
    print(f"✅ {context}: MCP and REST responses are equivalent")


@pytest.mark.asyncio
class TestMCPRestEquivalence:
    """Test cases for MCP vs REST API equivalence"""
    
    async def test_hash_statistics_equivalence(self, mcp_client, rest_client):
        """Test that HASH statistics are identical between MCP and REST"""
        # Call MCP function directly
        mcp_result = await mcp_client.call_tool("fetch_current_hash_statistics", {})
        
        # Call REST API endpoint
        rest_result = await rest_client.call_endpoint("/api/hash/statistics")
        
        # Assert equivalence
        assert_responses_equivalent(
            mcp_result, 
            rest_result, 
            "HASH Statistics (MCP vs REST)"
        )
    
    async def test_account_info_equivalence(self, mcp_client, rest_client):
        """Test that account info is identical between MCP and REST"""
        # Call MCP function directly
        mcp_result = await mcp_client.call_tool("fetch_account_info", {"wallet_address": TEST_WALLET_ADDRESS})
        
        # Call REST API endpoint
        rest_result = await rest_client.call_endpoint(f"/api/account/info/{TEST_WALLET_ADDRESS}")
        
        # Assert equivalence
        assert_responses_equivalent(
            mcp_result,
            rest_result,
            f"Account Info for {TEST_WALLET_ADDRESS} (MCP vs REST)"
        )
    
    async def test_account_vesting_equivalence(self, mcp_client, rest_client):
        """Test that account vesting status is identical between MCP and REST"""
        # Call MCP function directly
        mcp_result = await mcp_client.call_tool("fetch_account_is_vesting", {"wallet_address": TEST_WALLET_ADDRESS})
        
        # Call REST API endpoint
        rest_result = await rest_client.call_endpoint(f"/api/account/vesting-status/{TEST_WALLET_ADDRESS}")
        
        # Assert equivalence
        assert_responses_equivalent(
            mcp_result,
            rest_result,
            f"Account Vesting Status for {TEST_WALLET_ADDRESS} (MCP vs REST)"
        )
    
    async def test_total_delegation_equivalence(self, mcp_client, rest_client):
        """Test that total delegation data is identical between MCP and REST"""
        # Call MCP function directly
        mcp_result = await mcp_client.call_tool("fetch_total_delegation_data", {"wallet_address": TEST_WALLET_ADDRESS})
        
        # Call REST API endpoint
        rest_result = await rest_client.call_endpoint(f"/api/delegation/total/{TEST_WALLET_ADDRESS}")
        
        # Assert equivalence
        assert_responses_equivalent(
            mcp_result,
            rest_result,
            f"Total Delegation Data for {TEST_WALLET_ADDRESS} (MCP vs REST)"
        )
    
    async def test_registry_function_coverage(self):
        """Test that all dual-protocol functions have proper equivalence tests"""
        registry = get_registry()
        dual_protocol_functions = []
        
        # Find all functions that support both MCP and REST
        for func_meta in registry.get_all_functions():
            protocols = [p.value if hasattr(p, 'value') else str(p) for p in func_meta.protocols]
            if "mcp" in protocols and "rest" in protocols:
                dual_protocol_functions.append(func_meta.name)
        
        print(f"Found {len(dual_protocol_functions)} dual-protocol functions:")
        for func_name in dual_protocol_functions:
            print(f"  - {func_name}")
        
        # Check that we have tests for each dual-protocol function
        expected_test_functions = {
            "fetch_current_hash_statistics",
            "fetch_account_info", 
            "fetch_account_is_vesting",
            "fetch_total_delegation_data"
        }
        
        missing_tests = set(dual_protocol_functions) - expected_test_functions
        if missing_tests:
            pytest.fail(f"Missing equivalence tests for dual-protocol functions: {missing_tests}")
        
        print(f"✅ All {len(expected_test_functions)} dual-protocol functions have equivalence tests")


@pytest.mark.asyncio
async def test_full_equivalence_suite():
    """Run full equivalence test suite for all dual-protocol functions"""
    mcp_client = MCPTestClient()
    rest_client = RESTTestClient()
    
    test_cases = [
        ("HASH Statistics", "fetch_current_hash_statistics", {}, "/api/hash/statistics"),
        ("Account Info", "fetch_account_info", {"wallet_address": TEST_WALLET_ADDRESS}, f"/api/account/info/{TEST_WALLET_ADDRESS}"),
        ("Account Vesting", "fetch_account_is_vesting", {"wallet_address": TEST_WALLET_ADDRESS}, f"/api/account/vesting-status/{TEST_WALLET_ADDRESS}"),
        ("Total Delegation", "fetch_total_delegation_data", {"wallet_address": TEST_WALLET_ADDRESS}, f"/api/delegation/total/{TEST_WALLET_ADDRESS}"),
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
            pytest.fail(f"❌ {test_name} equivalence test failed: {str(e)}")
    
    print("🎉 All MCP vs REST equivalence tests passed!")


if __name__ == "__main__":
    # Allow running tests directly
    asyncio.run(test_full_equivalence_suite())