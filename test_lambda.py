#!/usr/bin/env python3
"""
Simple test script for the pb-fm-mcp Lambda handler
"""

import json
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import the lambda handler
from lambda_handler import lambda_handler, mcp_server

def test_basic_functionality():
    """Test basic Lambda handler functionality"""
    
    # Test that the MCP server is initialized
    assert mcp_server is not None
    assert mcp_server.name == "pb-fm-mcp"
    assert mcp_server.version == "0.1.0"
    
    print("✓ MCP server initialized correctly")

def test_simple_tool():
    """Test the simple adt tool"""
    
    # Simulate a Lambda event for calling the adt tool
    event = {
        "httpMethod": "POST",
        "path": "/mcp",
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "method": "tools/call",
            "params": {
                "name": "adt",
                "arguments": {"a": 5, "b": 10}
            }
        })
    }
    
    context = {}  # Mock Lambda context
    
    try:
        response = lambda_handler(event, context)
        print("✓ Lambda handler executed without errors")
        print(f"Response: {response}")
        return True
    except Exception as e:
        print(f"✗ Lambda handler failed: {e}")
        return False

def test_imports():
    """Test that all required modules can be imported"""
    
    try:
        import httpx
        print("✓ httpx imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import httpx: {e}")
        return False
    
    try:
        import structlog
        print("✓ structlog imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import structlog: {e}")
        return False
    
    try:
        from awslabs.mcp_lambda_handler import MCPLambdaHandler
        print("✓ awslabs.mcp_lambda_handler imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import awslabs.mcp_lambda_handler: {e}")
        print("Note: This is expected if awslabs-mcp-lambda-handler is not installed")
        return False
    
    return True

def main():
    """Run all tests"""
    print("Testing pb-fm-mcp Lambda handler...")
    print("=" * 50)
    
    tests = [
        ("Import test", test_imports),
        ("Basic functionality", test_basic_functionality),
        ("Simple tool test", test_simple_tool),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                failed += 1
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())