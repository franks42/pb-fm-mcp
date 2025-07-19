#!/usr/bin/env python3
"""
Validation script for pb-fm-mcp setup (no external dependencies required)
"""

import json
import sys
from pathlib import Path

def validate_project_structure():
    """Validate the project structure"""
    required_files = [
        "lambda_handler.py",
        "pyproject.toml", 
        "deploy.py",
        "README.md",
        "src/utils.py",
        "src/hastra.py",
        "src/base64expand.py",
        "src/hastra_types.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    
    print("✓ All required files present")
    return True

def validate_pyproject_toml():
    """Validate pyproject.toml configuration"""
    try:
        import tomllib
    except ImportError:
        # Fallback for Python < 3.11
        try:
            import tomli as tomllib
        except ImportError:
            print("⚠ Cannot validate pyproject.toml (tomllib/tomli not available)")
            return True
    
    try:
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        
        # Check project name
        if config.get("project", {}).get("name") != "pb-fm-mcp":
            print("✗ Project name is not 'pb-fm-mcp'")
            return False
        
        # Check dependencies
        deps = config.get("project", {}).get("dependencies", [])
        required_deps = ["awslabs-mcp-lambda-handler", "httpx", "structlog"]
        missing_deps = [dep for dep in required_deps if not any(dep in d for d in deps)]
        
        if missing_deps:
            print(f"✗ Missing dependencies: {missing_deps}")
            return False
        
        print("✓ pyproject.toml configuration valid")
        return True
        
    except Exception as e:
        print(f"✗ Error reading pyproject.toml: {e}")
        return False

def validate_lambda_handler_syntax():
    """Validate lambda_handler.py syntax without importing dependencies"""
    try:
        with open("lambda_handler.py", "r") as f:
            content = f.read()
        
        # Basic syntax check
        compile(content, "lambda_handler.py", "exec")
        
        # Check for required components
        if "MCPLambdaHandler" not in content:
            print("✗ MCPLambdaHandler not found in lambda_handler.py")
            return False
        
        if "lambda_handler" not in content:
            print("✗ lambda_handler function not found")
            return False
        
        if "@mcp_server.tool()" not in content:
            print("✗ No MCP tools found")
            return False
        
        print("✓ lambda_handler.py syntax and structure valid")
        return True
        
    except SyntaxError as e:
        print(f"✗ Syntax error in lambda_handler.py: {e}")
        return False
    except Exception as e:
        print(f"✗ Error validating lambda_handler.py: {e}")
        return False

def validate_deployment_script():
    """Validate deploy.py"""
    try:
        with open("deploy.py", "r") as f:
            content = f.read()
        
        compile(content, "deploy.py", "exec")
        
        if "create_deployment_package" not in content:
            print("✗ create_deployment_package function not found in deploy.py")
            return False
        
        if "deploy_to_aws" not in content:
            print("✗ deploy_to_aws function not found in deploy.py")
            return False
        
        print("✓ deploy.py structure valid")
        return True
        
    except SyntaxError as e:
        print(f"✗ Syntax error in deploy.py: {e}")
        return False
    except Exception as e:
        print(f"✗ Error validating deploy.py: {e}")
        return False

def count_mcp_tools():
    """Count the number of MCP tools defined"""
    try:
        with open("lambda_handler.py", "r") as f:
            content = f.read()
        
        tool_count = content.count("@mcp_server.tool()")
        print(f"✓ Found {tool_count} MCP tools defined")
        
        # List some of the tools
        tool_names = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "@mcp_server.tool()" in line and i + 1 < len(lines):
                next_line = lines[i + 1]
                if "def " in next_line:
                    func_name = next_line.split("def ")[1].split("(")[0]
                    tool_names.append(func_name)
        
        print(f"  Tools: {', '.join(tool_names[:5])}{'...' if len(tool_names) > 5 else ''}")
        return True
        
    except Exception as e:
        print(f"✗ Error counting MCP tools: {e}")
        return False

def main():
    """Run all validation tests"""
    print("Validating pb-fm-mcp AWS Lambda setup...")
    print("=" * 50)
    
    tests = [
        ("Project structure", validate_project_structure),
        ("pyproject.toml", validate_pyproject_toml),
        ("Lambda handler syntax", validate_lambda_handler_syntax),
        ("Deployment script", validate_deployment_script),
        ("MCP tools count", count_mcp_tools),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Validation Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All validations passed! Ready for AWS Lambda deployment.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install awslabs-mcp-lambda-handler httpx structlog")
        print("2. Test locally (optional)")
        print("3. Deploy: python deploy.py --function-name pb-fm-mcp --role-arn <your-role-arn>")
        return 0
    else:
        print("❌ Some validations failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())