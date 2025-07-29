#!/usr/bin/env python3
"""
Production Configuration Validation Script

This script validates that function decorator assignments match the production spreadsheet.
It ensures only approved functions are exposed via MCP protocol in production.
"""

import os
import sys
import csv
import ast
import glob
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def parse_function_decorators(file_path: str) -> List[Tuple[str, List[str]]]:
    """
    Parse Python file to extract function names and their protocol assignments.
    
    Returns:
        List of (function_name, protocols) tuples
    """
    functions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use regex to find @api_function decorators and following function definitions
        # This pattern handles both filled and empty protocol lists
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
                protocols = protocol_matches
            
            functions.append((function_name, protocols))
    
    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")
    
    return functions

def load_production_csv(csv_path: str) -> Dict[str, Dict[str, str]]:
    """
    Load production configuration from CSV file.
    
    Returns:
        Dict mapping function names to their expected protocol configuration
    """
    config = {}
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                function_name = row['Function Name']
                mcp_enabled = row['MCP'].strip().upper() == 'YES'
                rest_enabled = row['REST'].strip().upper() == 'YES'
                
                expected_protocols = []
                if mcp_enabled:
                    expected_protocols.append('mcp')
                if rest_enabled:
                    expected_protocols.append('rest')
                
                config[function_name] = {
                    'expected_protocols': expected_protocols,
                    'mcp': mcp_enabled,
                    'rest': rest_enabled,
                    'description': row.get('Description', '')
                }
    
    except Exception as e:
        print(f"Error loading production CSV: {e}")
        sys.exit(1)
    
    return config

def validate_configuration() -> bool:
    """
    Validate that current function decorators match production CSV.
    
    Returns:
        True if all configurations match, False otherwise
    """
    script_dir = Path(__file__).parent.parent
    csv_path = script_dir / "function_protocols_prod.csv"
    src_dir = script_dir / "src" / "functions"
    
    if not csv_path.exists():
        print(f"❌ Production CSV not found: {csv_path}")
        return False
    
    # Load expected configuration
    expected_config = load_production_csv(str(csv_path))
    print(f"📋 Loaded production config for {len(expected_config)} functions")
    
    # Scan all Python files in functions directory
    python_files = list(glob.glob(str(src_dir / "**" / "*.py"), recursive=True))
    print(f"🔍 Scanning {len(python_files)} Python files...")
    
    all_valid = True
    found_functions = set()
    validation_errors = []
    
    for file_path in python_files:
        if "__pycache__" in file_path or "__init__.py" in file_path:
            continue
            
        functions = parse_function_decorators(file_path)
        
        for function_name, actual_protocols in functions:
            found_functions.add(function_name)
            
            if function_name not in expected_config:
                validation_errors.append(
                    f"⚠️  Function '{function_name}' found in code but not in production CSV"
                )
                continue
            
            expected = expected_config[function_name]['expected_protocols']
            
            # Normalize protocol lists for comparison
            actual_normalized = sorted([p for p in actual_protocols if p in ['mcp', 'rest']])
            expected_normalized = sorted(expected)
            
            if actual_normalized != expected_normalized:
                all_valid = False
                validation_errors.append(
                    f"❌ Function '{function_name}':\n"
                    f"   Expected protocols: {expected_normalized}\n" 
                    f"   Actual protocols: {actual_normalized}\n"
                    f"   File: {os.path.relpath(file_path, script_dir)}"
                )
            else:
                print(f"✅ {function_name}: {actual_normalized}")
    
    # Check for missing functions
    missing_functions = set(expected_config.keys()) - found_functions
    for missing in missing_functions:
        validation_errors.append(
            f"⚠️  Function '{missing}' in production CSV but not found in code"
        )
    
    # Print validation results
    print(f"\n📊 Validation Summary:")
    print(f"   Functions in CSV: {len(expected_config)}")
    print(f"   Functions found in code: {len(found_functions)}")
    print(f"   Functions with MCP enabled: {sum(1 for f in expected_config.values() if f['mcp'])}")
    print(f"   Functions with REST enabled: {sum(1 for f in expected_config.values() if f['rest'])}")
    print(f"   Functions completely disabled: {sum(1 for f in expected_config.values() if not f['mcp'] and not f['rest'])}")
    
    if validation_errors:
        print(f"\n🚨 Validation Issues ({len(validation_errors)}):")
        for error in validation_errors:
            print(f"   {error}")
    
    if all_valid and not validation_errors:
        print(f"\n🎉 All function decorators match production configuration!")
        return True
    else:
        print(f"\n❌ Validation failed - decorators do not match production CSV")
        return False

def main():
    """Main validation function."""
    print("🔍 Validating production function configuration...")
    print("=" * 60)
    
    success = validate_configuration()
    
    print("=" * 60)
    if success:
        print("✅ Production configuration validation PASSED")
        sys.exit(0)
    else:
        print("❌ Production configuration validation FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()