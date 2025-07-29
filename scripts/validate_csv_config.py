#!/usr/bin/env python3
"""
Validate CSV Configuration Against Codebase

This script validates that the CSV configuration files are consistent with
the actual function definitions in the codebase. It identifies missing
functions, extra entries, and configuration issues.
"""

import csv
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


def load_csv_functions(csv_path: str) -> Dict[str, Dict[str, str]]:
    """Load function names and configurations from CSV file."""
    functions = {}
    
    if not os.path.exists(csv_path):
        print(f"Warning: CSV file not found: {csv_path}")
        return functions
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            func_name = row.get('Function Name', '').strip()
            if func_name:
                functions[func_name] = {
                    'mcp': row.get('MCP', '').strip().upper() == 'YES',
                    'rest': row.get('REST', '').strip().upper() == 'YES',
                    'description': row.get('Description', '').strip()
                }
    
    return functions


def find_decorated_functions(src_dir: str) -> Set[str]:
    """Find all functions with @api_function decorator in the codebase."""
    functions = set()
    functions_dir = Path(src_dir) / "functions"
    
    if not functions_dir.exists():
        print(f"Warning: Functions directory not found: {functions_dir}")
        return functions
    
    # Pattern to match function definitions after @api_function decorator
    decorator_pattern = re.compile(r'@api_function')
    function_pattern = re.compile(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
    
    for py_file in functions_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                # Look for @api_function decorator
                if decorator_pattern.search(line.strip()):
                    # Find the next function definition
                    for j in range(i + 1, min(i + 10, len(lines))):  # Look ahead up to 10 lines
                        func_match = function_pattern.search(lines[j])
                        if func_match:
                            func_name = func_match.group(1)
                            functions.add(func_name)
                            break
        
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    return functions


def validate_configuration(csv_path: str, src_dir: str) -> Tuple[bool, Dict[str, any]]:
    """
    Validate CSV configuration against codebase.
    
    Returns:
        Tuple of (is_valid, validation_results)
    """
    csv_functions = load_csv_functions(csv_path)
    code_functions = find_decorated_functions(src_dir)
    
    # Find differences
    csv_names = set(csv_functions.keys())
    missing_in_csv = code_functions - csv_names
    extra_in_csv = csv_names - code_functions
    
    # Protocol statistics
    protocol_stats = {
        'mcp_only': 0,
        'rest_only': 0,
        'both': 0,
        'neither': 0,
        'total': len(csv_functions)
    }
    
    for func_name, config in csv_functions.items():
        if config['mcp'] and config['rest']:
            protocol_stats['both'] += 1
        elif config['mcp']:
            protocol_stats['mcp_only'] += 1
        elif config['rest']:
            protocol_stats['rest_only'] += 1
        else:
            protocol_stats['neither'] += 1
    
    # Validation results
    results = {
        'csv_functions': csv_functions,
        'code_functions': code_functions,
        'missing_in_csv': missing_in_csv,
        'extra_in_csv': extra_in_csv,
        'protocol_stats': protocol_stats,
        'is_valid': len(missing_in_csv) == 0 and len(extra_in_csv) == 0
    }
    
    return results['is_valid'], results


def print_validation_report(csv_path: str, results: Dict[str, any]):
    """Print detailed validation report."""
    print(f"\n=== Validation Report: {os.path.basename(csv_path)} ===\n")
    
    # Summary
    print(f"Total functions in CSV: {results['protocol_stats']['total']}")
    print(f"Total functions in code: {len(results['code_functions'])}")
    print(f"Validation status: {'✅ VALID' if results['is_valid'] else '❌ INVALID'}")
    
    # Protocol distribution
    stats = results['protocol_stats']
    print(f"\nProtocol Distribution:")
    print(f"  MCP + REST: {stats['both']}")
    print(f"  MCP only: {stats['mcp_only']}")
    print(f"  REST only: {stats['rest_only']}")
    print(f"  Neither (LOCAL): {stats['neither']}")
    
    # Issues
    if results['missing_in_csv']:
        print(f"\n❌ Functions missing in CSV ({len(results['missing_in_csv'])}):")
        for func_name in sorted(results['missing_in_csv']):
            print(f"  - {func_name}")
    
    if results['extra_in_csv']:
        print(f"\n⚠️  Extra entries in CSV ({len(results['extra_in_csv'])}):")
        for func_name in sorted(results['extra_in_csv']):
            print(f"  - {func_name}")
    
    # Production vs Development comparison (if both files exist)
    if "function_protocols.csv" in csv_path:
        # This is the dev config, compare with prod
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        prod_csv = project_root / "function_protocols_prod.csv"
        
        if prod_csv.exists():
            print(f"\n📊 Development vs Production Comparison:")
            prod_functions = load_csv_functions(str(prod_csv))
            
            dev_mcp_count = sum(1 for config in results['csv_functions'].values() if config['mcp'])
            prod_mcp_count = sum(1 for config in prod_functions.values() if config['mcp'])
            
            print(f"  MCP functions in development: {dev_mcp_count}")
            print(f"  MCP functions in production: {prod_mcp_count}")
            print(f"  Reduction: {dev_mcp_count - prod_mcp_count} functions")


def main():
    """Main script execution."""
    # Determine which CSV files to validate
    csv_files = []
    
    if len(sys.argv) > 1:
        # Validate specific file
        csv_files.append(sys.argv[1])
    else:
        # Validate both development and production configs
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        
        dev_csv = project_root / "function_protocols.csv"
        prod_csv = project_root / "function_protocols_prod.csv"
        
        if dev_csv.exists():
            csv_files.append(str(dev_csv))
        if prod_csv.exists():
            csv_files.append(str(prod_csv))
    
    if not csv_files:
        print("No CSV configuration files found to validate.")
        return
    
    # Find source directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    src_dir = project_root / "src"
    
    if not src_dir.exists():
        print(f"Source directory not found: {src_dir}")
        return
    
    # Validate each CSV file
    all_valid = True
    for csv_path in csv_files:
        is_valid, results = validate_configuration(csv_path, str(src_dir))
        print_validation_report(csv_path, results)
        all_valid = all_valid and is_valid
    
    # Exit status
    if all_valid:
        print(f"\n✅ All CSV configurations are valid!")
        sys.exit(0)
    else:
        print(f"\n❌ CSV validation failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()