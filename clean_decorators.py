#\!/usr/bin/env python3
"""Clean up malformed decorators"""

import re
from pathlib import Path

def clean_file(file_path: Path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove malformed decorator patterns
    # Pattern 1: @api_function(protocols=["mcp", "rest"])"},
    content = re.sub(r'@api_function\(protocols=\["mcp",\s*"rest"\]\)"\}', '@api_function(protocols=["mcp", "rest"])', content)
    
    # Pattern 2: @api_function(protocols=["mcp", "rest"])",
    content = re.sub(r'@api_function\(protocols=\["mcp",\s*"rest"\]\)",', '@api_function(protocols=["mcp", "rest"])', content)
    
    # Remove orphaned parameters blocks
    content = re.sub(r'^\s*parameters=\{[^}]*\}\s*\)\s*$', '', content, flags=re.MULTILINE)
    
    # Remove orphaned closing braces and parens
    content = re.sub(r'^\s*\}\s*\)\s*$', '', content, flags=re.MULTILINE)
    
    # Clean up duplicate blank lines
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Cleaned {file_path.name}")

# Clean all webpage files
src_dir = Path("src/functions")
for file_path in src_dir.glob("webpage_*.py"):
    clean_file(file_path)
