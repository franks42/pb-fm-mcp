#\!/usr/bin/env python3
"""Comprehensive syntax fixer"""

import ast
import re
from pathlib import Path

def fix_file_syntax(file_path: Path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix all missing closing braces/parens in DynamoDB calls
    # Pattern: function_call(\n    key=value\n\nother_code -> function_call(\n    key=value\n)\n\nother_code
    
    # Fix ExpressionAttributeValues patterns
    content = re.sub(
        r"(ExpressionAttributeValues=\{[^}]*}\s*)\n\s*(?=\w)",
        r"\1\n        )\n        ",
        content,
        flags=re.MULTILINE
    )
    
    # Fix Key patterns  
    content = re.sub(
        r"(Key=\{[^}]*}\s*)\n\s*(?=\w)",
        r"\1\n        )\n        ",
        content,
        flags=re.MULTILINE
    )
    
    # Fix ExpressionAttributeNames patterns
    content = re.sub(
        r"(ExpressionAttributeNames=\{[^}]*}\s*)\n\s*(?=\w)",
        r"\1\n        )\n        ",
        content,
        flags=re.MULTILINE
    )
    
    # Fix nested dictionary patterns that end with just a closing brace
    content = re.sub(
        r"(\s+}\s*)\n\s*(?=[a-zA-Z_])",
        r"\1\n        )\n        ",
        content,
        flags=re.MULTILINE
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    # Test if syntax is valid
    try:
        ast.parse(content)
        print(f"✅ Fixed {file_path.name}")
        return True
    except SyntaxError as e:
        print(f"❌ Still has syntax errors in {file_path.name}: {e}")
        return False

# Fix all webpage files
src_dir = Path("src/functions")
fixed_count = 0
for file_path in src_dir.glob("webpage_*.py"):
    if fix_file_syntax(file_path):
        fixed_count += 1

print(f"\n✅ Successfully fixed {fixed_count} files")
