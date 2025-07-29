#!/usr/bin/env python3
"""
Update Function Protocols from CSV Configuration

This script reads the CSV configuration files and applies protocol changes to
function decorators throughout the codebase. It ensures that the CSV files
drive which functions are exposed via MCP and REST protocols.
"""

import csv
import os
import sys
from pathlib import Path
from typing import Dict, List, Set


def load_csv_config(csv_path: str) -> Dict[str, Dict[str, str]]:
    """
    Load function protocol configuration from CSV file.
    
    Args:
        csv_path: Path to the CSV configuration file
        
    Returns:
        Dict mapping function names to their protocol configuration
    """
    config = {}
    
    if not os.path.exists(csv_path):
        print(f"Warning: CSV file not found: {csv_path}")
        return config
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            func_name = row.get('Function Name', '').strip()
            if func_name:
                config[func_name] = {
                    'mcp': row.get('MCP', '').strip().upper() == 'YES',
                    'rest': row.get('REST', '').strip().upper() == 'YES',
                    'description': row.get('Description', '').strip()
                }
    
    return config


def determine_protocols(mcp_enabled: bool, rest_enabled: bool) -> List[str]:
    """
    Determine the protocol list based on MCP and REST settings.
    
    Args:
        mcp_enabled: Whether MCP protocol is enabled
        rest_enabled: Whether REST protocol is enabled
        
    Returns:
        List of protocol strings
    """
    protocols = []
    
    if mcp_enabled:
        protocols.append("mcp")
    if rest_enabled:
        protocols.append("rest")
        
    # If no protocols are enabled, use "local" (registered but not exposed)
    if not protocols:
        protocols.append("local")
        
    return protocols


def find_function_files(src_dir: str) -> List[Path]:
    """
    Find all Python files in the functions directory.
    
    Args:
        src_dir: Source directory to search
        
    Returns:
        List of Python file paths containing functions
    """
    functions_dir = Path(src_dir) / "functions"
    if not functions_dir.exists():
        print(f"Warning: Functions directory not found: {functions_dir}")
        return []
    
    python_files = []
    for py_file in functions_dir.rglob("*.py"):
        if py_file.name != "__init__.py":
            python_files.append(py_file)
    
    return python_files


def parse_current_decorator(lines: List[str], start_index: int) -> List[str]:
    """
    Parse the current @api_function decorator to extract protocols.
    Handles multi-line decorators.
    
    Args:
        lines: All lines in the file
        start_index: Index of the @api_function line
        
    Returns:
        List of protocol strings currently configured
    """
    import re
    
    # Collect the entire decorator (may span multiple lines)
    decorator_text = ""
    i = start_index
    brace_count = 0
    in_decorator = False
    
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('@api_function'):
            in_decorator = True
            decorator_text += line + " "
            brace_count += line.count('(') - line.count(')')
        elif in_decorator:
            decorator_text += line + " "
            brace_count += line.count('(') - line.count(')')
            
            # End of decorator when braces balance
            if brace_count <= 0:
                break
        
        i += 1
    
    # Handle different decorator formats
    if 'protocols=' not in decorator_text:
        # Default decorator without explicit protocols
        return ["mcp", "rest"]
    
    # Extract protocols list from decorator
    protocols_match = re.search(r'protocols=\[(.*?)\]', decorator_text)
    if not protocols_match:
        return ["mcp", "rest"]  # Default if parsing fails
    
    protocols_str = protocols_match.group(1).strip()
    
    # Handle empty protocols list
    if not protocols_str:
        return ["local"]
    
    # Parse individual protocols
    protocols = []
    for protocol in protocols_str.split(','):
        protocol = protocol.strip().strip('"\'')
        if protocol:
            protocols.append(protocol)
    
    return protocols if protocols else ["local"]


def update_decorator_in_file(file_path: Path, csv_config: Dict[str, Dict[str, str]]) -> bool:
    """
    Update @api_function decorators in a single file based on CSV configuration.
    Only makes changes when CSV configuration differs from current decorator.
    
    Args:
        file_path: Path to the Python file to update
        csv_config: CSV configuration mapping
        
    Returns:
        True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        modified = False
        changes_made = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for @api_function decorator
            if line.startswith('@api_function'):
                # Find the function definition that follows
                func_name = None
                j = i + 1
                while j < len(lines) and not (lines[j].strip().startswith('def ') or lines[j].strip().startswith('async def ')):
                    j += 1
                
                if j < len(lines):
                    def_line = lines[j].strip()
                    if def_line.startswith('def ') or def_line.startswith('async def '):
                        func_name = def_line.split('(')[0].replace('def ', '').replace('async ', '').strip()
                        
                
                # Update decorator if function is in CSV config
                if func_name and func_name in csv_config:
                    config = csv_config[func_name]
                    desired_protocols = determine_protocols(config['mcp'], config['rest'])
                    current_protocols = parse_current_decorator(lines, i)
                    
                    
                    # Only update if protocols differ
                    if set(desired_protocols) != set(current_protocols):
                        # Generate new decorator line
                        if desired_protocols == ["local"]:
                            new_decorator = '@api_function(protocols=[])'
                        else:
                            protocol_list = ', '.join(f'"{p}"' for p in desired_protocols)
                            new_decorator = f'@api_function(protocols=[{protocol_list}])'
                        
                        # Replace the decorator line (and potentially following lines)
                        # For simplicity, replace with single-line version
                        lines[i] = new_decorator
                        
                        # Remove any continuation lines of the old decorator
                        k = i + 1
                        while k < len(lines) and not lines[k].strip().startswith('def ') and not lines[k].strip().startswith('@'):
                            if lines[k].strip() and not lines[k].strip().startswith('async def '):
                                lines[k] = ""  # Clear the line
                            else:
                                break
                            k += 1
                        
                        modified = True
                        changes_made.append(f"  {func_name}: {current_protocols} → {desired_protocols}")
            
            i += 1
        
        # Write back if modified and show changes
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            for change in changes_made:
                print(change)
            
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main script execution."""
    # Determine CSV file to use based on environment or command line
    csv_file = "function_protocols.csv"  # Default to development
    env_name = "development"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "prod":
            csv_file = "function_protocols_prod.csv"
            env_name = "production"
        elif sys.argv[1] == "dev":
            csv_file = "function_protocols.csv"
            env_name = "development"
        else:
            csv_file = sys.argv[1]
            env_name = "custom"
    
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    csv_path = project_root / csv_file
    src_dir = project_root / "src"
    
    print(f"🔄 Syncing function protocols for {env_name} environment")
    print(f"📄 CSV configuration: {csv_path}")
    print(f"📁 Source directory: {src_dir}")
    
    # Load CSV configuration
    csv_config = load_csv_config(str(csv_path))
    if not csv_config:
        print("❌ No configuration loaded. Exiting.")
        return 1
    
    print(f"✅ Loaded configuration for {len(csv_config)} functions")
    
    # Find function files
    function_files = find_function_files(str(src_dir))
    if not function_files:
        print("❌ No function files found. Exiting.")
        return 1
    
    print(f"📂 Found {len(function_files)} function files to process")
    print()
    
    # Update decorators in each file
    total_modified = 0
    modified_files = []
    
    for file_path in function_files:
        print(f"🔍 Processing: {file_path.name}")
        
        if update_decorator_in_file(file_path, csv_config):
            total_modified += 1
            modified_files.append(file_path.name)
        else:
            print(f"  ✅ No changes needed")
    
    print()
    
    # Results summary
    if total_modified > 0:
        print(f"✅ Sync completed: {total_modified} files modified")
        print(f"📝 Modified files: {', '.join(modified_files)}")
    else:
        print(f"✅ Sync completed: All decorators already match CSV configuration")
    
    # Protocol distribution summary
    protocol_counts = {'mcp': 0, 'rest': 0, 'local': 0, 'both': 0}
    for func_name, config in csv_config.items():
        if config['mcp'] and config['rest']:
            protocol_counts['both'] += 1
        elif config['mcp']:
            protocol_counts['mcp'] += 1
        elif config['rest']:
            protocol_counts['rest'] += 1
        else:
            protocol_counts['local'] += 1
    
    print(f"\n📊 Protocol Distribution ({env_name}):")
    print(f"  🔗 MCP + REST: {protocol_counts['both']}")
    print(f"  🤖 MCP only: {protocol_counts['mcp']}")
    print(f"  🌐 REST only: {protocol_counts['rest']}")
    print(f"  🔒 Local only: {protocol_counts['local']}")
    
    total_mcp = protocol_counts['both'] + protocol_counts['mcp']
    total_rest = protocol_counts['both'] + protocol_counts['rest']
    print(f"\n🎯 Totals: {total_mcp} MCP functions, {total_rest} REST functions")
    
    return 0 if total_modified == 0 else 0  # Success in both cases


if __name__ == "__main__":
    main()