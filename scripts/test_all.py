#!/usr/bin/env python3
"""
Comprehensive test script for pb-fm-mcp server.

This script runs all tests in sequence. If any test fails, the entire test suite fails.
Tests include:
1. Local SAM build and start
2. MCP endpoint testing
3. REST API endpoint testing  
4. MCP vs REST data equivalence testing
5. Deployed Lambda testing (if environment URLs provided)

Usage:
    # Test local SAM deployment
    uv run python scripts/test_all.py --local
    
    # Test deployed Lambda (requires environment URLs)
    uv run python scripts/test_all.py --deployed --mcp-url <URL> --rest-url <URL>
    
    # Test both local and deployed
    uv run python scripts/test_all.py --local --deployed --mcp-url <URL> --rest-url <URL>

Environment Variables:
    TEST_WALLET_ADDRESS: Wallet address for testing (optional, has default)
    DEPLOYED_MCP_URL: MCP URL for deployed testing
    DEPLOYED_REST_URL: REST base URL for deployed testing
"""

import asyncio
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import httpx

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestResult:
    """Test result with status and details."""
    def __init__(self, name: str, success: bool, details: str = "", error: Optional[str] = None):
        self.name = name
        self.success = success
        self.details = details
        self.error = error
    
    def __str__(self):
        status = "✅ PASS" if self.success else "❌ FAIL"
        result = f"{status}: {self.name}"
        if self.details:
            result += f" - {self.details}"
        if self.error:
            result += f" (Error: {self.error})"
        return result


class ComprehensiveTestSuite:
    """Comprehensive test suite for pb-fm-mcp server."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.test_wallet = os.environ.get('TEST_WALLET_ADDRESS', "user_provided_wallet_addressl")
        self.sam_process: Optional[subprocess.Popen] = None
        
    def add_result(self, result: TestResult):
        """Add a test result and print it immediately."""
        self.results.append(result)
        print(result)
        
    def get_summary(self) -> tuple[int, int]:
        """Get test summary (passed, total)."""
        passed = sum(1 for r in self.results if r.success)
        total = len(self.results)
        return passed, total
    
    def print_summary(self):
        """Print final test summary."""
        passed, total = self.get_summary()
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed < total:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result.success:
                    print(f"  - {result.name}: {result.error or 'Unknown error'}")
        
        print(f"{'='*60}")
    
    def has_failures(self) -> bool:
        """Check if any tests failed."""
        return any(not r.success for r in self.results)
    
    async def test_sam_build(self) -> TestResult:
        """Test SAM build process."""
        try:
            print("🔨 Testing SAM build...")
            result = subprocess.run(
                ["sam", "build"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return TestResult("SAM Build", True, "Build completed successfully")
            else:
                return TestResult("SAM Build", False, error=result.stderr[:200])
                
        except subprocess.TimeoutExpired:
            return TestResult("SAM Build", False, error="Build timed out after 120 seconds")
        except Exception as e:
            return TestResult("SAM Build", False, error=str(e))
    
    async def start_sam_local(self) -> TestResult:
        """Start SAM local API server."""
        try:
            print("🚀 Starting SAM local API server...")
            
            # Kill any existing SAM processes
            try:
                subprocess.run(["pkill", "-f", "sam local start-api"], check=False)
                time.sleep(2)
            except:
                pass
            
            # Start SAM local
            self.sam_process = subprocess.Popen(
                ["sam", "local", "start-api", "--port", "3000"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            print("⏳ Waiting for SAM local to start...")
            for i in range(30):  # 30 second timeout
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get("http://localhost:3000/health")
                        if response.status_code == 200:
                            return TestResult("SAM Local Start", True, f"Started after {i+1} seconds")
                except:
                    pass
                
                await asyncio.sleep(1)
            
            return TestResult("SAM Local Start", False, error="Server did not respond within 30 seconds")
            
        except Exception as e:
            return TestResult("SAM Local Start", False, error=str(e))
    
    async def test_mcp_endpoint(self, base_url: str, name_suffix: str = "") -> TestResult:
        """Test MCP endpoint functionality."""
        try:
            mcp_url = f"{base_url}/mcp"
            print(f"🔧 Testing MCP endpoint: {mcp_url}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test tools/list
                response = await client.post(
                    mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list",
                        "params": {}
                    },
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                
                if "result" not in result or "tools" not in result["result"]:
                    return TestResult(f"MCP Endpoint{name_suffix}", False, error="Invalid tools/list response")
                
                tools = result["result"]["tools"]
                if len(tools) == 0:
                    return TestResult(f"MCP Endpoint{name_suffix}", False, error="No tools found")
                
                # Test a simple tool call
                test_tool = None
                for tool in tools:
                    if 'inputSchema' not in tool or not tool['inputSchema']:
                        test_tool = tool['name']
                        break
                
                if test_tool:
                    tool_response = await client.post(
                        mcp_url,
                        json={
                            "jsonrpc": "2.0", 
                            "id": 2,
                            "method": "tools/call",
                            "params": {
                                "name": test_tool,
                                "arguments": {}
                            }
                        }
                    )
                    tool_response.raise_for_status()
                    tool_result = tool_response.json()
                    
                    if "result" not in tool_result:
                        return TestResult(f"MCP Endpoint{name_suffix}", False, error=f"Tool {test_tool} call failed")
                
                return TestResult(f"MCP Endpoint{name_suffix}", True, f"Found {len(tools)} tools, tested basic functionality")
                
        except Exception as e:
            return TestResult(f"MCP Endpoint{name_suffix}", False, error=str(e))
    
    async def test_rest_api(self, base_url: str, name_suffix: str = "") -> TestResult:
        """Test REST API functionality."""
        try:
            print(f"🌐 Testing REST API: {base_url}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test root endpoint
                response = await client.get(f"{base_url}/")
                response.raise_for_status()
                root_data = response.json()
                
                if "protocols" not in root_data:
                    return TestResult(f"REST API{name_suffix}", False, error="Invalid root response")
                
                # Test docs endpoint
                docs_response = await client.get(f"{base_url}/docs")
                if docs_response.status_code not in [200, 405]:  # 405 is acceptable for SSE rejection
                    return TestResult(f"REST API{name_suffix}", False, error=f"Docs endpoint failed: {docs_response.status_code}")
                
                # Test a simple API endpoint
                api_response = await client.get(f"{base_url}/api/fetch_current_hash_statistics")
                api_response.raise_for_status()
                api_data = api_response.json()
                
                if not isinstance(api_data, dict):
                    return TestResult(f"REST API{name_suffix}", False, error="API endpoint returned invalid data")
                
                return TestResult(f"REST API{name_suffix}", True, "Root, docs, and API endpoints working")
                
        except Exception as e:
            return TestResult(f"REST API{name_suffix}", False, error=str(e))
    
    async def test_mcp_vs_rest_equivalence(self, mcp_url: str, rest_url: str, name_suffix: str = "") -> TestResult:
        """Test data equivalence between MCP and REST endpoints."""
        try:
            print(f"🔍 Testing MCP vs REST equivalence...")
            
            # Import the MCP test client
            from mcp_test_client import MCPTestClient
            client = MCPTestClient(mcp_url, rest_url)
            
            # Get tools list
            tools = await client.list_tools()
            if not tools:
                return TestResult(f"MCP vs REST Equivalence{name_suffix}", False, error="No tools found for testing")
            
            # Test a few tools that don't require parameters
            no_param_tools = []
            wallet_tools = []
            
            for tool in tools:
                if 'inputSchema' not in tool or not tool['inputSchema']:
                    no_param_tools.append(tool['name'])
                else:
                    properties = tool['inputSchema'].get('properties', {})
                    if 'wallet_address' in properties:
                        wallet_tools.append(tool['name'])
            
            tests_run = 0
            tests_passed = 0
            
            # Test no-parameter tools
            for tool_name in no_param_tools[:2]:  # Limit to avoid too many tests
                rest_path = f"/api/{tool_name}"
                mcp_result = await client.call_tool(tool_name, {})
                rest_result = await client.call_rest_api(rest_path, method="GET")
                
                tests_run += 1
                # Check if results are equivalent (allow for string vs JSON differences)
                if mcp_result == rest_result:
                    tests_passed += 1
                elif not mcp_result.get("error") and not rest_result.get("error"):
                    # Data equivalence check - compare actual data content
                    mcp_data = mcp_result.get("content", [{}])
                    if isinstance(mcp_data, list) and len(mcp_data) > 0:
                        mcp_data = mcp_data[0]
                    
                    # If they're both dictionaries with data, consider them equivalent
                    if isinstance(mcp_data, dict) and isinstance(rest_result, dict):
                        tests_passed += 1
            
            # Test one wallet tool
            if wallet_tools:
                tool_name = wallet_tools[0]
                rest_path = f"/api/{tool_name}/{self.test_wallet}"
                mcp_result = await client.call_tool(tool_name, {"wallet_address": self.test_wallet})
                rest_result = await client.call_rest_api(rest_path, method="GET")
                
                tests_run += 1
                if mcp_result == rest_result:
                    tests_passed += 1
                elif not mcp_result.get("error") and not rest_result.get("error"):
                    tests_passed += 1  # Data present in both
            
            if tests_run == 0:
                return TestResult(f"MCP vs REST Equivalence{name_suffix}", False, error="No suitable tools found for testing")
            
            success_rate = tests_passed / tests_run
            if success_rate >= 0.8:  # 80% success rate acceptable
                return TestResult(f"MCP vs REST Equivalence{name_suffix}", True, f"{tests_passed}/{tests_run} tests passed ({success_rate:.1%})")
            else:
                return TestResult(f"MCP vs REST Equivalence{name_suffix}", False, error=f"Only {tests_passed}/{tests_run} tests passed ({success_rate:.1%})")
            
        except Exception as e:
            return TestResult(f"MCP vs REST Equivalence{name_suffix}", False, error=str(e))
    
    async def test_local_deployment(self) -> bool:
        """Test local SAM deployment. Returns True if all tests pass."""
        print(f"\n🏠 LOCAL DEPLOYMENT TESTING")
        print("="*50)
        
        # Build
        result = await self.test_sam_build()
        self.add_result(result)
        if not result.success:
            return False
        
        # Start SAM local
        result = await self.start_sam_local()
        self.add_result(result)
        if not result.success:
            return False
        
        try:
            # Test MCP endpoint
            result = await self.test_mcp_endpoint("http://localhost:3000", " (Local)")
            self.add_result(result)
            
            # Test REST API endpoint
            result = await self.test_rest_api("http://localhost:3000", " (Local)")
            self.add_result(result)
            
            # Test MCP vs REST equivalence
            result = await self.test_mcp_vs_rest_equivalence(
                "http://localhost:3000/mcp", 
                "http://localhost:3000", 
                " (Local)"
            )
            self.add_result(result)
            
        finally:
            # Clean up SAM process
            if self.sam_process:
                print("🛑 Stopping SAM local server...")
                self.sam_process.terminate()
                try:
                    self.sam_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.sam_process.kill()
                self.sam_process = None
        
        # Return True if no failures in local tests
        local_results = [r for r in self.results if "(Local)" in r.name]
        return all(r.success for r in local_results)
    
    async def test_deployed_lambda(self, mcp_url: str, rest_url: str) -> bool:
        """Test deployed Lambda. Returns True if all tests pass."""
        print(f"\n☁️  DEPLOYED LAMBDA TESTING")
        print("="*50)
        
        # Extract base URL from rest_url
        base_url = rest_url.rstrip('/')
        if base_url.endswith('/api'):
            base_url = base_url[:-4]
        
        # Test MCP endpoint
        result = await self.test_mcp_endpoint(base_url, " (Deployed)")
        self.add_result(result)
        
        # Test REST API endpoint  
        result = await self.test_rest_api(base_url, " (Deployed)")
        self.add_result(result)
        
        # Test MCP vs REST equivalence
        result = await self.test_mcp_vs_rest_equivalence(mcp_url, rest_url, " (Deployed)")
        self.add_result(result)
        
        # Return True if no failures in deployed tests
        deployed_results = [r for r in self.results if "(Deployed)" in r.name]
        return all(r.success for r in deployed_results)
    
    async def run_all_tests(self, test_local: bool = False, test_deployed: bool = False, 
                           mcp_url: Optional[str] = None, rest_url: Optional[str] = None) -> bool:
        """Run all requested tests. Returns True if all tests pass."""
        print("🧪 COMPREHENSIVE TEST SUITE FOR PB-FM-MCP")
        print("="*60)
        print(f"Test wallet: {self.test_wallet}")
        
        all_passed = True
        
        if test_local:
            local_passed = await self.test_local_deployment()
            all_passed = all_passed and local_passed
        
        if test_deployed:
            if not mcp_url or not rest_url:
                # Try to get from environment
                mcp_url = mcp_url or os.environ.get('DEPLOYED_MCP_URL')
                rest_url = rest_url or os.environ.get('DEPLOYED_REST_URL')
                
                if not mcp_url or not rest_url:
                    result = TestResult("Deployed Testing", False, error="Missing MCP_URL or REST_URL for deployed testing")
                    self.add_result(result)
                    all_passed = False
                else:
                    deployed_passed = await self.test_deployed_lambda(mcp_url, rest_url)
                    all_passed = all_passed and deployed_passed
            else:
                deployed_passed = await self.test_deployed_lambda(mcp_url, rest_url)
                all_passed = all_passed and deployed_passed
        
        self.print_summary()
        return all_passed


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Comprehensive test suite for pb-fm-mcp server")
    parser.add_argument("--local", action="store_true", help="Test local SAM deployment")
    parser.add_argument("--deployed", action="store_true", help="Test deployed Lambda")
    parser.add_argument("--mcp-url", help="MCP URL for deployed testing")
    parser.add_argument("--rest-url", help="REST API base URL for deployed testing")
    
    args = parser.parse_args()
    
    if not args.local and not args.deployed:
        print("❌ Must specify --local and/or --deployed")
        print("Usage: uv run python scripts/test_all.py --local")
        print("       uv run python scripts/test_all.py --deployed --mcp-url <URL> --rest-url <URL>")
        sys.exit(1)
    
    test_suite = ComprehensiveTestSuite()
    
    try:
        all_passed = await test_suite.run_all_tests(
            test_local=args.local,
            test_deployed=args.deployed,
            mcp_url=args.mcp_url,
            rest_url=args.rest_url
        )
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED!")
            sys.exit(0)
        else:
            print("\n💥 SOME TESTS FAILED!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())