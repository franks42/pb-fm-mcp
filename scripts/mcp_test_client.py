#!/usr/bin/env python3
"""
Simple command-line MCP client for testing pb-fm-mcp server.

This script connects to MCP servers and provides interactive testing capabilities
including tool discovery, execution, and comparison with REST endpoints.
"""

import asyncio
import argparse
import json
import sys
from typing import Dict, Any, Optional
import httpx
from urllib.parse import urljoin

MCP_AVAILABLE = True


class MCPTestClient:
    """Simple MCP testing client with command-line interface."""
    
    def __init__(self, mcp_url: str, rest_base_url: Optional[str] = None):
        self.mcp_url = mcp_url
        # If no explicit REST base URL provided, derive it from MCP URL
        # Keep any path prefix (like /v1) when removing /mcp
        if not rest_base_url:
            if '/mcp' in mcp_url:
                # Replace only the last occurrence of /mcp to preserve path prefixes
                parts = mcp_url.rsplit('/mcp', 1)
                self.rest_base_url = parts[0]
            else:
                self.rest_base_url = mcp_url
        else:
            self.rest_base_url = rest_base_url
        
    async def connect(self) -> bool:
        """Connect to the MCP server via HTTP."""
        try:
            print(f"🔌 Testing MCP server: {self.mcp_url}")
            # Test with a simple tools/list call
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.mcp_url,
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
                if "result" in result:
                    print("✅ Connected successfully!")
                    return True
                else:
                    print(f"❌ Unexpected response: {result}")
                    return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        print("🔌 Disconnected from MCP server")
    
    async def list_tools(self) -> list:
        """List all available tools on the MCP server."""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.mcp_url,
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
                
                if "result" in result and "tools" in result["result"]:
                    tools = result["result"]["tools"]
                    print(f"\n📋 Available tools ({len(tools)}):")
                    for i, tool in enumerate(tools, 1):
                        print(f"  {i}. {tool['name']}")
                        print(f"     Description: {tool.get('description', 'No description')}")
                        if 'inputSchema' in tool and tool['inputSchema']:
                            required = tool['inputSchema'].get('properties', {}).keys()
                            print(f"     Parameters: {list(required)}")
                        print()
                    return tools
                else:
                    print(f"❌ Unexpected response: {result}")
                    return []
        except Exception as e:
            print(f"❌ Failed to list tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool with given arguments."""
        try:
            print(f"🔧 Calling tool: {tool_name}")
            print(f"📥 Arguments: {json.dumps(arguments, indent=2)}")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
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
                    tool_result = result["result"]
                    print(f"📤 Result: {json.dumps(tool_result, indent=2)}")
                    return tool_result
                elif "error" in result:
                    error_result = {"error": f"JSON-RPC error: {result['error']}"}
                    print(f"❌ JSON-RPC error: {result['error']}")
                    return error_result
                else:
                    error_result = {"error": f"Unexpected response: {result}"}
                    print(f"❌ Unexpected response: {result}")
                    return error_result
        except Exception as e:
            error_result = {"error": str(e)}
            print(f"❌ Tool call failed: {e}")
            return error_result
    
    async def call_rest_api(self, endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """Call the equivalent REST API endpoint."""
        # Ensure base URL ends with / and endpoint doesn't start with / for proper joining
        base = self.rest_base_url.rstrip('/') + '/'
        endpoint = endpoint.lstrip('/')
        url = urljoin(base, endpoint)
        
        try:
            print(f"🌐 Calling REST API: {method} {url}")
            if kwargs:
                print(f"📥 Parameters: {json.dumps(kwargs, indent=2)}")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=kwargs)
                elif method.upper() == "POST":
                    response = await client.post(url, json=kwargs)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                result = response.json()
                print(f"📤 Result: {json.dumps(result, indent=2)}")
                return result
        except Exception as e:
            error_result = {"error": str(e)}
            print(f"❌ REST API call failed: {e}")
            return error_result
    
    async def compare_mcp_vs_rest(self, tool_name: str, rest_endpoint: str, arguments: Dict[str, Any]):
        """Compare MCP tool call with equivalent REST API call."""
        print(f"\n🔍 Comparing MCP vs REST for: {tool_name}")
        print("=" * 60)
        
        # Call MCP tool
        print("MCP CALL:")
        mcp_result = await self.call_tool(tool_name, arguments)
        
        print("\n" + "-" * 40 + "\n")
        
        # Call REST API
        print("REST CALL:")
        rest_result = await self.call_rest_api(rest_endpoint, **arguments)
        
        print("\n" + "-" * 40 + "\n")
        
        # Compare results
        print("COMPARISON:")
        if mcp_result == rest_result:
            print("✅ Results match perfectly!")
        else:
            print("❌ Results differ:")
            print(f"MCP:  {json.dumps(mcp_result, indent=2)}")
            print(f"REST: {json.dumps(rest_result, indent=2)}")
        
        return mcp_result, rest_result
    
    async def interactive_mode(self):
        """Interactive command-line interface."""
        print("\n🎮 Interactive MCP Test Client")
        print("Commands:")
        print("  list - List available tools")
        print("  call <tool_name> <json_args> - Call a tool")
        print("  rest <endpoint> <json_args> - Call REST API")
        print("  compare <tool_name> <rest_endpoint> <json_args> - Compare MCP vs REST")
        print("  quit - Exit")
        print()
        
        while True:
            try:
                command = input("mcp> ").strip()
                if not command:
                    continue
                
                parts = command.split(' ', 1)
                cmd = parts[0].lower()
                
                if cmd == 'quit':
                    break
                elif cmd == 'list':
                    await self.list_tools()
                elif cmd == 'call' and len(parts) > 1:
                    args = parts[1].split(' ', 1)
                    tool_name = args[0]
                    arguments = json.loads(args[1]) if len(args) > 1 else {}
                    await self.call_tool(tool_name, arguments)
                elif cmd == 'rest' and len(parts) > 1:
                    args = parts[1].split(' ', 1)
                    endpoint = args[0]
                    arguments = json.loads(args[1]) if len(args) > 1 else {}
                    await self.call_rest_api(endpoint, **arguments)
                elif cmd == 'compare' and len(parts) > 1:
                    args = parts[1].split(' ', 2)
                    if len(args) >= 2:
                        tool_name = args[0]
                        rest_endpoint = args[1] 
                        arguments = json.loads(args[2]) if len(args) > 2 else {}
                        await self.compare_mcp_vs_rest(tool_name, rest_endpoint, arguments)
                    else:
                        print("Usage: compare <tool_name> <rest_endpoint> <json_args>")
                else:
                    print(f"Unknown command: {cmd}")
                    
            except (EOFError, KeyboardInterrupt):
                break
            except json.JSONDecodeError as e:
                print(f"❌ JSON error: {e}")
            except Exception as e:
                print(f"❌ Error: {e}")


async def run_predefined_tests(client: MCPTestClient):
    """Run a set of predefined tests using discovered tool names."""
    print("\n🧪 Running predefined tests...")
    
    # First, discover available tools
    tools = await client.list_tools()
    if not tools:
        print("❌ No tools discovered, cannot run tests")
        return
    
    # Create a mapping of tool names for easy lookup
    tool_names = {tool['name'] for tool in tools}
    
    # Get test wallet from environment variable or use default
    import os
    test_wallet = os.environ.get('TEST_WALLET_ADDRESS', "pb1mjtshzl0p9w7xztfawg7z86k7m02d8zznp3t6q7l")
    
    if test_wallet != "pb1mjtshzl0p9w7xztfawg7z86k7m02d8zznp3t6q7l":
        print(f"✅ Using TEST_WALLET_ADDRESS from environment: {test_wallet}")
    else:
        print(f"⚠️  Using default test wallet (set TEST_WALLET_ADDRESS env var for real testing): {test_wallet}")
    
    # Helper function to convert between naming conventions
    def to_snake_case(camel_str: str) -> str:
        """Convert camelCase to snake_case."""
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()
    
    def to_camel_case(snake_str: str) -> str:
        """Convert snake_case to camelCase."""
        components = snake_str.split('_')
        return components[0] + ''.join(word.capitalize() for word in components[1:])
    
    # Dynamically generate test patterns based on discovered tools
    # Look for tools that likely take a wallet_address parameter
    wallet_tools = []
    no_param_tools = []
    
    for tool in tools:
        tool_name = tool['name']
        
        # Check if tool takes wallet_address parameter
        if 'inputSchema' in tool and tool['inputSchema']:
            properties = tool['inputSchema'].get('properties', {})
            if 'wallet_address' in properties:
                wallet_tools.append(tool_name)
        else:
            # Tools with no parameters
            no_param_tools.append(tool_name)
    
    # Run tests for a few wallet-based tools (limit to avoid too many API calls)
    print(f"🔍 Found {len(wallet_tools)} wallet-based tools, testing first 3...")
    for i, tool_name in enumerate(wallet_tools[:3]):
        # Convert tool name to REST path format
        rest_path = f"/api/{tool_name}/{test_wallet}"
        
        print(f"\n📋 Wallet Tool Test #{i+1}: {tool_name}")
        print(f"🔍 Testing tool: {tool_name}")
        await client.compare_mcp_vs_rest(tool_name, rest_path, {"wallet_address": test_wallet})
        print()
    
    # Run tests for a few no-parameter tools
    print(f"🔍 Found {len(no_param_tools)} no-parameter tools, testing first 2...")
    for i, tool_name in enumerate(no_param_tools[:2]):
        # Convert tool name to REST path format  
        rest_path = f"/api/{tool_name}"
        
        print(f"\n📋 No-Parameter Tool Test #{i+1}: {tool_name}")
        print(f"🔍 Testing tool: {tool_name}")
        await client.compare_mcp_vs_rest(tool_name, rest_path, {})
        print()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP Test Client for pb-fm-mcp server")
    parser.add_argument("--mcp-url", default="http://localhost:3000/mcp", 
                       help="MCP server URL")
    parser.add_argument("--rest-url", help="REST API base URL (defaults to MCP URL without /mcp)")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Run in interactive mode")
    parser.add_argument("--test", "-t", action="store_true",
                       help="Run predefined tests")
    
    args = parser.parse_args()
    
    if not MCP_AVAILABLE:
        print("❌ MCP SDK not available. Install with: uv add mcp")
        sys.exit(1)
    
    client = MCPTestClient(args.mcp_url, args.rest_url)
    
    # Connect to server
    if not await client.connect():
        sys.exit(1)
    
    try:
        # List tools
        await client.list_tools()
        
        # Run tests if requested
        if args.test:
            await run_predefined_tests(client)
        
        # Interactive mode if requested
        if args.interactive:
            await client.interactive_mode()
            
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())