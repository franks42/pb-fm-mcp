#!/usr/bin/env python3
"""
Simple decorator fixer - removes invalid parameters from @api_function decorators
"""

import re
import sys
from pathlib import Path

def fix_decorators_in_file(file_path: Path) -> bool:
    """Fix @api_function decorators in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match @api_function decorators with extra parameters
        # This matches the entire multi-line decorator including all parameters
        pattern = r'@api_function\([^)]*parameters\s*=\s*\{[^}]*\}[^)]*\)'
        
        # Replace with simple format
        replacement = '@api_function(protocols=["mcp", "rest"])'
        
        # Use DOTALL flag to match across newlines
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        if content != new_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Fixed decorators in {file_path.name}")
            return True
        else:
            print(f"  No changes needed in {file_path.name}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main script execution."""
    if len(sys.argv) > 1:
        # Fix specific file
        file_path = Path(sys.argv[1])
        if file_path.exists():
            fix_decorators_in_file(file_path)
        else:
            print(f"File not found: {file_path}")
    else:
        # Fix all webpage files
        src_dir = Path("src/functions")
        webpage_files = list(src_dir.glob("webpage_*.py"))
        test_files = list(src_dir.glob("test_*.py"))
        
        all_files = webpage_files + test_files
        
        if not all_files:
            print("No webpage or test files found")
            return
        
        print(f"Found {len(all_files)} files to process")
        
        fixed_count = 0
        for file_path in all_files:
            if fix_decorators_in_file(file_path):
                fixed_count += 1
        
        print(f"\n✅ Fixed {fixed_count} files")

if __name__ == "__main__":
    main()