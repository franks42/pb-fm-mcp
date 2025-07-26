#!/usr/bin/env python3
"""
Deployment Test Suite
Comprehensive testing script for pb-fm-mcp deployment verification
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Optional

class DeploymentTester:
    def __init__(self, base_url: str, test_wallet: str = "pb1test"):
        self.base_url = base_url.rstrip('/')
        self.test_wallet = test_wallet
        self.mcp_url = f"{base_url}/mcp"
        self.rest_url = f"{base_url}"
        self.s3_assets_url = "https://pb-fm-mcp-dev-web-assets-289426936662.s3.us-west-1.amazonaws.com"
        self.results = {}
        self.start_time = time.time()
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = {"INFO": "ℹ️", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(level, "📝")
        print(f"[{timestamp}] {icon} {message}")
        
    def test_mcp_basic(self) -> bool:
        """Test basic MCP endpoint connectivity"""
        self.log("Testing MCP basic connectivity...")
        try:
            response = requests.get(self.mcp_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "name" in data and "PB-FM MCP Server" in data["name"]:
                    self.log("MCP endpoint accessible", "PASS")
                    return True
            self.log(f"MCP basic test failed: {response.status_code}", "FAIL")
            return False
        except Exception as e:
            self.log(f"MCP basic test error: {e}", "FAIL")
            return False
            
    def test_mcp_function(self, function_name: str, arguments: dict) -> Dict:
        """Test a specific MCP function"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": "1",
                "params": {
                    "name": function_name,
                    "arguments": arguments
                }
            }
            
            response = requests.post(
                self.mcp_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    return {"success": True, "data": data["result"]}
                elif "error" in data:
                    return {"success": False, "error": data["error"]["message"]}
            
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def test_rest_endpoint(self, endpoint: str, method: str = "GET", data: dict = None) -> Dict:
        """Test a REST API endpoint"""
        try:
            url = f"{self.rest_url}{endpoint}"
            
            if method.upper() == "POST":
                response = requests.post(url, json=data, timeout=15)
            else:
                response = requests.get(url, timeout=15)
                
            return {
                "success": response.status_code in [200, 201],
                "status_code": response.status_code,
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:500]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def test_s3_assets(self) -> Dict:
        """Test S3 assets availability"""
        self.log("Testing S3 assets availability...")
        results = {}
        
        assets = {
            "dashboard.css": f"{self.s3_assets_url}/css/dashboard.css",
            "dashboard.js": f"{self.s3_assets_url}/js/dashboard.js",
            "chat-interface.css": f"{self.s3_assets_url}/css/chat-interface.css",
            "chat-interface.js": f"{self.s3_assets_url}/js/chat-interface.js",
            "error.css": f"{self.s3_assets_url}/css/error.css",
            "fallback.css": f"{self.s3_assets_url}/css/fallback.css"
        }
        
        for asset_name, asset_url in assets.items():
            try:
                response = requests.get(asset_url, timeout=10)
                success = response.status_code == 200 and len(response.text) > 100
                results[asset_name] = {
                    "success": success,
                    "status_code": response.status_code,
                    "size": len(response.text) if success else 0
                }
                
                if success:
                    self.log(f"S3 asset {asset_name}: OK ({len(response.text)} bytes)", "PASS")
                else:
                    self.log(f"S3 asset {asset_name}: FAIL ({response.status_code})", "FAIL")
                    
            except Exception as e:
                results[asset_name] = {"success": False, "error": str(e)}
                self.log(f"S3 asset {asset_name}: ERROR ({e})", "FAIL")
                
        return results
        
    def test_core_mcp_functions(self) -> Dict:
        """Test core MCP functions that are essential for operation"""
        self.log("Testing core MCP functions...")
        results = {}
        
        # Test cases for core functions
        test_cases = {
            "create_hash_price_chart": {
                "time_range": "24h",
                "dashboard_id": "test_dash"
            },
            "create_portfolio_health": {
                "wallet_address": self.test_wallet,
                "dashboard_id": "test_dash",
                "analysis_depth": "comprehensive"
            },
            "fetch_account_info": {
                "wallet_address": self.test_wallet
            },
            "fetch_complete_wallet_summary": {
                "wallet_address": self.test_wallet
            },
            "get_system_context": {}
        }
        
        for func_name, args in test_cases.items():
            self.log(f"Testing MCP function: {func_name}")
            result = self.test_mcp_function(func_name, args)
            results[func_name] = result
            
            if result["success"]:
                self.log(f"MCP {func_name}: PASS", "PASS")
            else:
                self.log(f"MCP {func_name}: FAIL - {result.get('error', 'Unknown error')}", "FAIL")
                
        return results
        
    def test_dashboard_system(self) -> Dict:
        """Test dashboard creation and loading"""
        self.log("Testing dashboard system...")
        
        # Create test dashboard
        dashboard_data = {
            "dashboard_name": f"Test Dashboard {datetime.now().strftime('%H:%M:%S')}",
            "wallet_address": self.test_wallet,
            "ai_session_id": f"test-{int(time.time())}"
        }
        
        create_result = self.test_rest_endpoint(
            "/api/create_personalized_dashboard",
            "POST",
            dashboard_data
        )
        
        if not create_result["success"]:
            self.log("Dashboard creation failed", "FAIL")
            return {"dashboard_creation": create_result}
            
        # Extract dashboard ID
        dashboard_id = create_result["data"].get("dashboard_id")
        if not dashboard_id:
            self.log("No dashboard ID returned", "FAIL")
            return {"dashboard_creation": create_result}
            
        self.log(f"Dashboard created: {dashboard_id}", "PASS")
        
        # Test dashboard loading
        try:
            dashboard_url = f"/dashboard/{dashboard_id}"
            response = requests.get(f"{self.rest_url}{dashboard_url}", timeout=15)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Check for S3 asset references
                has_css_ref = self.s3_assets_url in html_content and "dashboard.css" in html_content
                has_js_ref = self.s3_assets_url in html_content and "dashboard.js" in html_content
                
                dashboard_result = {
                    "success": True,
                    "dashboard_id": dashboard_id,
                    "html_size": len(html_content),
                    "has_s3_css": has_css_ref,
                    "has_s3_js": has_js_ref,
                    "s3_integration": has_css_ref and has_js_ref
                }
                
                if has_css_ref and has_js_ref:
                    self.log("Dashboard S3 integration: PASS", "PASS")
                else:
                    self.log("Dashboard S3 integration: FAIL", "FAIL")
                    
            else:
                dashboard_result = {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
                self.log(f"Dashboard loading failed: {response.status_code}", "FAIL")
                
        except Exception as e:
            dashboard_result = {"success": False, "error": str(e)}
            self.log(f"Dashboard loading error: {e}", "FAIL")
            
        return {
            "dashboard_creation": create_result,
            "dashboard_loading": dashboard_result
        }
        
    def test_key_rest_endpoints(self) -> Dict:
        """Test key REST API endpoints"""
        self.log("Testing key REST endpoints...")
        results = {}
        
        # Test cases for REST endpoints
        test_cases = {
            "root": {"endpoint": "/", "method": "GET"},
            "docs": {"endpoint": "/docs", "method": "GET"},
            "health": {"endpoint": "/health", "method": "GET"},
            "hash_price_chart": {
                "endpoint": "/api/create_hash_price_chart",
                "method": "POST",
                "data": {"time_range": "24h", "dashboard_id": "test"}
            },
            "portfolio_health": {
                "endpoint": "/api/create_portfolio_health", 
                "method": "POST",
                "data": {
                    "wallet_address": self.test_wallet,
                    "dashboard_id": "test",
                    "analysis_depth": "comprehensive"
                }
            }
        }
        
        for test_name, test_config in test_cases.items():
            self.log(f"Testing REST endpoint: {test_name}")
            result = self.test_rest_endpoint(
                test_config["endpoint"],
                test_config["method"],
                test_config.get("data")
            )
            results[test_name] = result
            
            if result["success"]:
                self.log(f"REST {test_name}: PASS", "PASS")
            else:
                error_msg = result.get('error', f"HTTP {result.get('status_code', 'unknown')}")
                self.log(f"REST {test_name}: FAIL - {error_msg}", "FAIL")
                
        return results
        
    def run_full_test_suite(self) -> Dict:
        """Run complete test suite"""
        self.log("🚀 Starting Full Deployment Test Suite")
        self.log(f"Testing deployment: {self.base_url}")
        self.log(f"Test wallet: {self.test_wallet}")
        self.log("=" * 60)
        
        # Run all tests
        test_results = {
            "mcp_basic": self.test_mcp_basic(),
            "s3_assets": self.test_s3_assets(),
            "core_mcp_functions": self.test_core_mcp_functions(),
            "rest_endpoints": self.test_key_rest_endpoints(),
            "dashboard_system": self.test_dashboard_system()
        }
        
        # Calculate summary
        duration = time.time() - self.start_time
        
        # Count successes
        summary = self.calculate_summary(test_results)
        
        # Print final results
        self.log("=" * 60)
        self.log("🎯 TEST SUITE SUMMARY")
        self.log(f"Duration: {duration:.1f} seconds")
        self.log(f"MCP Basic: {'✅ PASS' if test_results['mcp_basic'] else '❌ FAIL'}")
        self.log(f"S3 Assets: {summary['s3_assets']}")
        self.log(f"Core MCP Functions: {summary['mcp_functions']}")
        self.log(f"REST Endpoints: {summary['rest_endpoints']}")
        self.log(f"Dashboard System: {summary['dashboard_system']}")
        
        overall_success = (
            test_results['mcp_basic'] and
            summary['s3_success'] and
            summary['mcp_success'] and
            summary['rest_success'] and
            summary['dashboard_success']
        )
        
        if overall_success:
            self.log("🎉 OVERALL RESULT: ✅ ALL TESTS PASSED", "PASS")
        else:
            self.log("🚨 OVERALL RESULT: ❌ SOME TESTS FAILED", "FAIL")
            
        test_results["summary"] = summary
        test_results["overall_success"] = overall_success
        test_results["duration"] = duration
        
        return test_results
        
    def calculate_summary(self, test_results: Dict) -> Dict:
        """Calculate test summary statistics"""
        # S3 Assets
        s3_results = test_results["s3_assets"]
        s3_passed = sum(1 for r in s3_results.values() if r.get("success", False))
        s3_total = len(s3_results)
        
        # MCP Functions
        mcp_results = test_results["core_mcp_functions"]
        mcp_passed = sum(1 for r in mcp_results.values() if r.get("success", False))
        mcp_total = len(mcp_results)
        
        # REST Endpoints
        rest_results = test_results["rest_endpoints"]
        rest_passed = sum(1 for r in rest_results.values() if r.get("success", False))
        rest_total = len(rest_results)
        
        # Dashboard System
        dashboard_results = test_results["dashboard_system"]
        dashboard_success = (
            dashboard_results.get("dashboard_creation", {}).get("success", False) and
            dashboard_results.get("dashboard_loading", {}).get("success", False) and
            dashboard_results.get("dashboard_loading", {}).get("s3_integration", False)
        )
        
        return {
            "s3_assets": f"✅ {s3_passed}/{s3_total}" if s3_passed == s3_total else f"❌ {s3_passed}/{s3_total}",
            "mcp_functions": f"✅ {mcp_passed}/{mcp_total}" if mcp_passed == mcp_total else f"❌ {mcp_passed}/{mcp_total}",
            "rest_endpoints": f"✅ {rest_passed}/{rest_total}" if rest_passed == rest_total else f"❌ {rest_passed}/{rest_total}",
            "dashboard_system": "✅ PASS" if dashboard_success else "❌ FAIL",
            "s3_success": s3_passed == s3_total,
            "mcp_success": mcp_passed == mcp_total,
            "rest_success": rest_passed == rest_total,
            "dashboard_success": dashboard_success
        }

def main():
    """Main test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PB-FM-MCP Deployment Test Suite")
    parser.add_argument("--url", default="https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1", 
                       help="Base URL for testing")
    parser.add_argument("--wallet", default="pb1test", 
                       help="Test wallet address")
    parser.add_argument("--output", help="JSON output file path")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # Run tests
    tester = DeploymentTester(args.url, args.wallet)
    results = tester.run_full_test_suite()
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        tester.log(f"Results saved to: {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_success"] else 1)

if __name__ == "__main__":
    main()