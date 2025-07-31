#\!/usr/bin/env python3
"""Fix syntax errors in webpage files"""

import re
from pathlib import Path

def fix_missing_braces(file_path: Path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix pattern: 'SK': {'S': 'METADATA'}\n\nif 'Item'
    content = re.sub(
        r"'SK': \{'S': 'METADATA'\}\s*\n\s*(?=if 'Item')",
        "'SK': {'S': 'METADATA'}\n            }\n        )\n        ",
        content
    )
    
    # Fix pattern: 'SK': {'S': 'CLIENT#'}\n\nparticipants
    content = re.sub(
        r"'SK': \{'S': 'CLIENT#'\}\s*\n\s*(?=participants)",
        "'SK': {'S': 'CLIENT#'}\n            }\n        )\n        ",
        content
    )
    
    # Fix pattern: 'SK': {'S': f'CLIENT#{new_master_id}'}\n\nif 'Item'
    content = re.sub(
        r"'SK': \{'S': f'CLIENT#\{[^}]+\}'\}\s*\n\s*(?=if 'Item')",
        lambda m: m.group(0).replace('\n\n        if', '\n            }\n        )\n        if'),
        content
    )
    
    # Fix similar patterns for other cases
    content = re.sub(
        r"'SK': \{'S': '[^']+'\}\s*\n\s*(?=deleted_items\.append)",
        "'SK': {'S': 'METADATA'}\n            }\n        )\n        ",
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed syntax in {file_path.name}")

# Fix webpage files
src_dir = Path("src/functions")
for file_path in src_dir.glob("webpage_*.py"):
    fix_missing_braces(file_path)
