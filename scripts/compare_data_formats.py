#!/usr/bin/env python3
"""
Data Format Comparison Tool

Compares MCP and REST response data by converting both to Python structures
and analyzing the differences. This eliminates JSON formatting issues and 
focuses on actual data content differences.
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union
import httpx
from urllib.parse import urljoin

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class DataFormatComparator:
    """Compares MCP and REST response data structures."""
    
    def __init__(self, mcp_url: str, rest_base_url: str):
        self.mcp_url = mcp_url
        self.rest_base_url = rest_base_url
        
    async def get_mcp_data(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get data from MCP endpoint and extract actual data content."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": arguments
                        }
                    },
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                
                if "result" in result:
                    mcp_result = result["result"]
                    
                    # Extract actual data from MCP protocol wrapper
                    # MCP results might be in different formats:
                    # Format 1: Direct data
                    if isinstance(mcp_result, dict) and not ("content" in mcp_result or "text" in mcp_result):
                        return {"data": mcp_result, "format": "direct_dict"}
                    
                    # Format 2: MCP content array with text
                    elif isinstance(mcp_result, dict) and "content" in mcp_result:
                        content = mcp_result["content"]
                        if isinstance(content, list) and len(content) > 0:
                            first_content = content[0]
                            if isinstance(first_content, dict) and "text" in first_content:
                                text_data = first_content["text"]
                                # Try to parse as JSON if it's a string
                                if isinstance(text_data, str):
                                    try:
                                        parsed_data = json.loads(text_data)
                                        return {"data": parsed_data, "format": "mcp_content_json"}
                                    except json.JSONDecodeError:
                                        # Try to parse as Python literal
                                        try:
                                            import ast
                                            parsed_data = ast.literal_eval(text_data)
                                            return {"data": parsed_data, "format": "mcp_content_literal"}
                                        except (ValueError, SyntaxError):
                                            return {"data": text_data, "format": "mcp_content_string"}
                                else:
                                    return {"data": text_data, "format": "mcp_content_direct"}
                            else:
                                return {"data": first_content, "format": "mcp_content_object"}
                        else:
                            return {"data": content, "format": "mcp_content_empty"}
                    
                    # Format 3: Unknown structure
                    else:
                        return {"data": mcp_result, "format": "mcp_unknown"}
                        
                elif "error" in result:
                    return {"error": f"MCP error: {result['error']}", "format": "error"}
                else:
                    return {"error": f"Unexpected MCP response: {result}", "format": "error"}
                    
        except Exception as e:
            return {"error": f"MCP call failed: {e}", "format": "error"}
    
    async def get_rest_data(self, endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """Get data from REST endpoint."""
        base = self.rest_base_url.rstrip('/') + '/'
        endpoint = endpoint.lstrip('/')
        url = urljoin(base, endpoint)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=kwargs)
                elif method.upper() == "POST":
                    response = await client.post(url, json=kwargs)
                else:
                    return {"error": f"Unsupported method: {method}", "format": "error"}
                
                response.raise_for_status()
                result = response.json()
                return {"data": result, "format": "rest_json"}
                
        except Exception as e:
            return {"error": f"REST call failed: {e}", "format": "error"}
    
    def deep_compare(self, data1: Any, data2: Any, path: str = "") -> Dict[str, Any]:
        """Deep comparison of two data structures."""
        differences = []
        
        def compare_recursive(d1, d2, current_path):
            if type(d1) != type(d2):
                differences.append({
                    "path": current_path,
                    "type": "type_mismatch",
                    "mcp_type": str(type(d1).__name__),
                    "rest_type": str(type(d2).__name__),
                    "mcp_value": str(d1),
                    "rest_value": str(d2)
                })
                return
            
            if isinstance(d1, dict):
                keys1 = set(d1.keys())
                keys2 = set(d2.keys())
                
                # Missing keys
                for key in keys1 - keys2:
                    differences.append({
                        "path": f"{current_path}.{key}" if current_path else key,
                        "type": "missing_in_rest",
                        "mcp_value": str(d1[key])
                    })
                
                for key in keys2 - keys1:
                    differences.append({
                        "path": f"{current_path}.{key}" if current_path else key,
                        "type": "missing_in_mcp", 
                        "rest_value": str(d2[key])
                    })
                
                # Compare common keys
                for key in keys1 & keys2:
                    new_path = f"{current_path}.{key}" if current_path else key
                    compare_recursive(d1[key], d2[key], new_path)
                    
            elif isinstance(d1, list):
                if len(d1) != len(d2):
                    differences.append({
                        "path": current_path,
                        "type": "length_mismatch",
                        "mcp_length": len(d1),
                        "rest_length": len(d2)
                    })
                
                for i, (item1, item2) in enumerate(zip(d1, d2)):
                    new_path = f"{current_path}[{i}]" if current_path else f"[{i}]"
                    compare_recursive(item1, item2, new_path)
                    
            else:
                if d1 != d2:
                    differences.append({
                        "path": current_path,
                        "type": "value_mismatch",
                        "mcp_value": str(d1),
                        "rest_value": str(d2)
                    })
        
        compare_recursive(data1, data2, path)
        
        return {
            "identical": len(differences) == 0,
            "differences": differences,
            "difference_count": len(differences)
        }
    
    async def compare_endpoint(self, tool_name: str, rest_endpoint: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Compare MCP tool call with equivalent REST endpoint."""
        print(f"\n🔍 Comparing {tool_name}")
        print("=" * 50)
        
        # Get data from both endpoints
        mcp_result = await self.get_mcp_data(tool_name, arguments)
        rest_result = await self.get_rest_data(rest_endpoint, **arguments)
        
        print(f"📋 MCP Format: {mcp_result.get('format', 'unknown')}")
        print(f"📋 REST Format: {rest_result.get('format', 'unknown')}")
        
        # Check for errors
        if "error" in mcp_result:
            print(f"❌ MCP Error: {mcp_result['error']}")
            return {"status": "error", "error": mcp_result["error"]}
            
        if "error" in rest_result:
            print(f"❌ REST Error: {rest_result['error']}")
            return {"status": "error", "error": rest_result["error"]}
        
        # Extract data for comparison
        mcp_data = mcp_result["data"]
        rest_data = rest_result["data"]
        
        print(f"\n📤 MCP Data Type: {type(mcp_data).__name__}")
        print(f"📤 REST Data Type: {type(rest_data).__name__}")
        
        # Show raw data (truncated)
        print(f"\n📤 MCP Data Preview: {str(mcp_data)[:200]}...")
        print(f"📤 REST Data Preview: {str(rest_data)[:200]}...")
        
        # Deep comparison
        comparison = self.deep_compare(mcp_data, rest_data)
        
        if comparison["identical"]:
            print("✅ Data structures are identical!")
            status = "identical"
        else:
            print(f"❌ Found {comparison['difference_count']} differences:")
            for diff in comparison["differences"][:5]:  # Show first 5 differences
                print(f"  - {diff['type']} at {diff['path']}")
                if 'mcp_value' in diff and 'rest_value' in diff:
                    print(f"    MCP: {diff['mcp_value']}")
                    print(f"    REST: {diff['rest_value']}")
            
            if comparison['difference_count'] > 5:
                print(f"  ... and {comparison['difference_count'] - 5} more differences")
            status = "different"
        
        return {
            "status": status,
            "mcp_format": mcp_result["format"],
            "rest_format": rest_result["format"],
            "mcp_data_type": type(mcp_data).__name__,
            "rest_data_type": type(rest_data).__name__,
            "comparison": comparison,
            "mcp_data": mcp_data,
            "rest_data": rest_data
        }
    
    async def discover_and_test_tools(self) -> Dict[str, Any]:
        """Discover tools and test a few for data format comparison."""
        print("🔍 Discovering available tools...")
        
        # Get tools list
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list",
                        "params": {}
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                if "result" not in result or "tools" not in result["result"]:
                    return {"error": "Could not discover tools"}
                
                tools = result["result"]["tools"]
                print(f"✅ Found {len(tools)} tools")
                
        except Exception as e:
            return {"error": f"Tool discovery failed: {e}"}
        
        # Test a few tools
        test_results = {}
        test_wallet = os.environ.get('TEST_WALLET_ADDRESS')
        if not test_wallet:
            print("ERROR: TEST_WALLET_ADDRESS environment variable required")
            sys.exit(1)
        
        # Test no-parameter tools
        no_param_tools = [tool for tool in tools if not tool.get('inputSchema')]
        for tool in no_param_tools[:2]:  # Test first 2
            tool_name = tool['name']
            rest_endpoint = f"/api/{tool_name}"
            result = await self.compare_endpoint(tool_name, rest_endpoint, {})
            test_results[tool_name] = result
        
        # Test wallet tools  
        wallet_tools = []
        for tool in tools:
            if 'inputSchema' in tool and tool['inputSchema']:
                properties = tool['inputSchema'].get('properties', {})
                if 'wallet_address' in properties:
                    wallet_tools.append(tool['name'])
        
        for tool_name in wallet_tools[:1]:  # Test first 1
            rest_endpoint = f"/api/{tool_name}/{test_wallet}"
            result = await self.compare_endpoint(tool_name, rest_endpoint, {"wallet_address": test_wallet})
            test_results[tool_name] = result
        
        return {"tools_tested": len(test_results), "results": test_results}


async def main():
    parser = argparse.ArgumentParser(description="Compare MCP and REST data formats")
    parser.add_argument("--mcp-url", required=True, help="MCP endpoint URL")
    parser.add_argument("--rest-url", required=True, help="REST API base URL")
    parser.add_argument("--tool", help="Specific tool to test")
    parser.add_argument("--endpoint", help="REST endpoint path for specific tool")
    parser.add_argument("--args", help="JSON arguments for tool call", default="{}")
    
    args = parser.parse_args()
    
    comparator = DataFormatComparator(args.mcp_url, args.rest_url)
    
    if args.tool and args.endpoint:
        # Test specific tool
        arguments = json.loads(args.args)
        result = await comparator.compare_endpoint(args.tool, args.endpoint, arguments)
        print(f"\nResult: {result['status']}")
    else:
        # Discover and test multiple tools
        results = await comparator.discover_and_test_tools()
        if "error" in results:
            print(f"❌ Error: {results['error']}")
            sys.exit(1)
        
        print(f"\n📊 SUMMARY")
        print("=" * 30)
        print(f"Tools tested: {results['tools_tested']}")
        
        identical_count = sum(1 for r in results['results'].values() if r.get('status') == 'identical')
        different_count = sum(1 for r in results['results'].values() if r.get('status') == 'different')
        error_count = sum(1 for r in results['results'].values() if r.get('status') == 'error')
        
        print(f"✅ Identical: {identical_count}")
        print(f"❌ Different: {different_count}")
        print(f"🚨 Errors: {error_count}")
        
        if different_count > 0:
            print(f"\n🔍 TOOLS WITH DATA DIFFERENCES:")
            for tool_name, result in results['results'].items():
                if result.get('status') == 'different':
                    print(f"  - {tool_name}: {result.get('mcp_format')} vs {result.get('rest_format')}")


if __name__ == "__main__":
    asyncio.run(main())