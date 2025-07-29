#!/usr/bin/env python3
"""
Production Configuration Validation Script

This script validates that function decorator assignments match the production CSV configuration.
It ensures only approved functions are exposed via MCP protocol in production deployments.

Usage:
  python scripts/validate_production_config.py           # Validate production CSV
  python scripts/validate_production_config.py dev      # Validate development CSV
  python scripts/validate_production_config.py prod     # Validate production CSV (explicit)

Exit codes:
  0: All validations passed
  1: Validation failures found
"""

import os
import sys
import csv
import re
import glob
from pathlib import Path
from typing import Dict, List, Set, Tuple


def parse_function_decorators(file_path: str) -> List[Tuple[str, List[str]]]:
    """
    Parse Python file to extract function names and their protocol assignments.
    
    Uses regex to handle multi-line decorators and complex patterns.
    
    Args:
        file_path: Path to Python file to parse
        
    Returns:
        List of (function_name, protocols) tuples
    """
    functions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match @api_function decorators with protocols
        # Handles multi-line decorators and various formatting styles
        decorator_pattern = r'@api_function\s*\(\s*.*?protocols\s*=\s*\[([^\]]*)\].*?\)\s*\n\s*(?:async\s+)?def\s+(\w+)'
        
        matches = re.finditer(decorator_pattern, content, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            protocols_str = match.group(1)
            function_name = match.group(2)
            
            # Extract protocol strings from the list
            protocols = []
            if protocols_str.strip():
                # Find all quoted strings in the protocols list
                protocol_matches = re.findall(r'["\']([^"\']*)["\']', protocols_str)
                protocols = [p for p in protocol_matches if p in ['mcp', 'rest', 'local']]
            
            functions.append((function_name, protocols))
    
    except Exception as e:
        print(f"⚠️  Warning: Could not parse {file_path}: {e}")
    
    return functions


def load_csv_config(csv_path: str) -> Dict[str, Dict[str, any]]:
    """
    Load function protocol configuration from CSV file.
    
    Args:
        csv_path: Path to CSV configuration file
        
    Returns:
        Dict mapping function names to their expected configuration
    """
    config = {}
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                function_name = row['Function Name'].strip()
                if function_name:
                    mcp_enabled = row['MCP'].strip().upper() == 'YES'
                    rest_enabled = row['REST'].strip().upper() == 'YES'
                    
                    expected_protocols = []
                    if mcp_enabled:
                        expected_protocols.append('mcp')
                    if rest_enabled:
                        expected_protocols.append('rest')
                    
                    # Empty protocols means local-only
                    if not expected_protocols:
                        expected_protocols.append('local')
                    
                    config[function_name] = {
                        'expected_protocols': sorted(expected_protocols),
                        'mcp': mcp_enabled,
                        'rest': rest_enabled,
                        'description': row.get('Description', '').strip()
                    }
    
    except Exception as e:
        print(f"❌ Error loading CSV configuration: {e}")
        sys.exit(1)
    
    return config


def validate_configuration(csv_path: str, src_dir: str, environment: str) -> bool:
    """
    Validate that current function decorators match CSV configuration.
    
    Args:
        csv_path: Path to CSV configuration file
        src_dir: Source directory containing function files
        environment: Environment name (dev/prod) for reporting
        
    Returns:
        True if all configurations match, False otherwise
    """
    if not os.path.exists(csv_path):
        print(f"❌ CSV configuration file not found: {csv_path}")
        return False
    
    if not os.path.exists(src_dir):
        print(f"❌ Source directory not found: {src_dir}")
        return False
    
    # Load expected configuration
    expected_config = load_csv_config(csv_path)
    print(f"📋 Loaded {environment} configuration for {len(expected_config)} functions")
    
    # Scan all Python files in functions directory
    python_files = list(glob.glob(os.path.join(src_dir, "**", "*.py"), recursive=True))
    python_files = [f for f in python_files if "__pycache__" not in f and "__init__.py" not in f]
    
    print(f"🔍 Scanning {len(python_files)} Python files...")
    
    all_valid = True
    found_functions = set()
    validation_errors = []
    correct_functions = []
    
    for file_path in python_files:
        functions = parse_function_decorators(file_path)
        
        for function_name, actual_protocols in functions:
            found_functions.add(function_name)
            
            if function_name not in expected_config:
                validation_errors.append(
                    f"⚠️  Function '{function_name}' found in code but not in {environment} CSV"
                )
                continue
            
            expected = expected_config[function_name]['expected_protocols']
            
            # Normalize protocol lists for comparison
            actual_normalized = sorted([p for p in actual_protocols if p in ['mcp', 'rest', 'local']])
            
            # Handle empty protocols (should be treated as local)
            if not actual_normalized:
                actual_normalized = ['local']
            
            if actual_normalized != expected:
                all_valid = False
                validation_errors.append(
                    f"❌ Function '{function_name}':"
                    f"\n   Expected: {expected}"
                    f"\n   Actual: {actual_normalized}"
                    f"\n   File: {os.path.relpath(file_path, Path(csv_path).parent)}"
                )
            else:
                correct_functions.append(f"✅ {function_name}: {actual_normalized}")
    
    # Check for missing functions
    missing_functions = set(expected_config.keys()) - found_functions
    for missing in missing_functions:
        validation_errors.append(
            f"⚠️  Function '{missing}' in {environment} CSV but not found in code"
        )
    
    # Print validation results
    print(f"\n📊 Validation Summary ({environment}):")
    print(f"   Functions in CSV: {len(expected_config)}")
    print(f"   Functions found in code: {len(found_functions)}")
    
    # Protocol distribution
    mcp_count = sum(1 for f in expected_config.values() if f['mcp'])
    rest_count = sum(1 for f in expected_config.values() if f['rest'])
    local_count = sum(1 for f in expected_config.values() if not f['mcp'] and not f['rest'])
    
    print(f"   MCP functions: {mcp_count}")
    print(f"   REST functions: {rest_count}")
    print(f"   Local-only functions: {local_count}")
    
    # Show correct configurations (brief)
    if correct_functions:
        print(f"\n✅ Correct configurations: {len(correct_functions)}")
        if len(correct_functions) <= 5:  # Show all if few
            for correct in correct_functions:
                print(f"   {correct}")
        else:  # Show summary if many
            print(f"   (All {len(correct_functions)} functions match expected configuration)")
    
    # Show validation errors (detailed)
    if validation_errors:
        print(f"\n🚨 Validation Issues ({len(validation_errors)}):")
        for error in validation_errors:
            print(f"   {error}")
    
    return all_valid and not validation_errors


def main():
    """Main validation function."""
    # Determine which CSV to validate
    environment = "production"
    csv_file = "function_protocols_prod.csv"
    
    if len(sys.argv) > 1:
        env_arg = sys.argv[1].lower()
        if env_arg == "dev":
            environment = "development" 
            csv_file = "function_protocols.csv"
        elif env_arg == "prod":
            environment = "production"
            csv_file = "function_protocols_prod.csv"
        else:
            print(f"❌ Invalid environment: {sys.argv[1]}. Use 'dev' or 'prod'")
            sys.exit(1)
    
    # Find project paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    csv_path = project_root / csv_file
    src_dir = project_root / "src" / "functions"
    
    print(f"🔍 Validating {environment} function configuration...")
    print(f"📄 CSV file: {csv_path}")
    print(f"📁 Source directory: {src_dir}")
    print("=" * 70)
    
    success = validate_configuration(str(csv_path), str(src_dir), environment)
    
    print("=" * 70)
    if success:
        print(f"🎉 {environment.title()} configuration validation PASSED")
        print(f"✅ All function decorators match {environment} CSV configuration")
        sys.exit(0)
    else:
        print(f"💥 {environment.title()} configuration validation FAILED")
        print(f"❌ Function decorators do not match {environment} CSV configuration")
        print(f"\n💡 To fix issues:")
        print(f"   1. Run: uv run python scripts/update_function_protocols.py {env_arg if len(sys.argv) > 1 else 'prod'}")
        print(f"   2. Or manually update function decorators to match CSV")
        sys.exit(1)


if __name__ == "__main__":
    main()