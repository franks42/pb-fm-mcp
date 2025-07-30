#!/usr/bin/env python3
"""
Security check script to find hardcoded wallet addresses in the codebase.

This helps enforce the security policy from CLAUDE.md:
- NEVER save real wallet addresses in files or commit them to git
- Always use environment variables for wallet addresses
"""

import os
import re
import sys
from pathlib import Path

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

def find_wallet_addresses(root_dir: Path):
    """Find all potential wallet addresses in the codebase."""
    # Pattern for Provenance wallet addresses
    # Standard format: pb1 + 39 chars = 42 total
    # Extended format: pb1 + 59 chars = 62 total
    wallet_pattern = re.compile(r'pb1[a-z0-9]{39}\b|pb1[a-z0-9]{59}\b')
    
    # Directories to skip
    skip_dirs = {'.git', '.aws-sam', '__pycache__', 'node_modules', '.venv', 'venv'}
    
    # File extensions to check
    check_extensions = {'.py', '.js', '.json', '.yaml', '.yml', '.md', '.txt', '.sh'}
    
    violations = []
    
    for root, dirs, files in os.walk(root_dir):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            file_path = Path(root) / file
            
            # Skip files without relevant extensions
            if file_path.suffix not in check_extensions:
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Find all wallet addresses
                matches = wallet_pattern.findall(content)
                if matches:
                    # Get line numbers for each match
                    lines = content.split('\n')
                    for match in set(matches):  # Use set to avoid duplicates
                        line_nums = []
                        for i, line in enumerate(lines, 1):
                            if match in line:
                                line_nums.append(i)
                        
                        violations.append({
                            'file': str(file_path.relative_to(root_dir)),
                            'wallet': match,
                            'lines': line_nums
                        })
                        
            except Exception as e:
                # Skip files that can't be read
                pass
    
    return violations

def main():
    """Main function to check for wallet address violations."""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"🔍 Checking for hardcoded wallet addresses in: {project_root}")
    print("=" * 70)
    
    violations = find_wallet_addresses(project_root)
    
    if not violations:
        print(f"{GREEN}✅ No wallet addresses found - codebase is clean!{NC}")
        return 0
    
    # Group violations by file
    files_with_wallets = {}
    for v in violations:
        if v['file'] not in files_with_wallets:
            files_with_wallets[v['file']] = []
        files_with_wallets[v['file']].append(v)
    
    print(f"{RED}🚨 Found {len(violations)} wallet address(es) in {len(files_with_wallets)} file(s):{NC}\n")
    
    for file, file_violations in files_with_wallets.items():
        print(f"{YELLOW}📄 {file}:{NC}")
        for v in file_violations:
            lines_str = ', '.join(map(str, v['lines'][:5]))  # Show first 5 line numbers
            if len(v['lines']) > 5:
                lines_str += f" ... ({len(v['lines']) - 5} more)"
            print(f"   Wallet: {v['wallet']} (lines: {lines_str})")
        print()
    
    print(f"{YELLOW}Per CLAUDE.md security policy:{NC}")
    print("  - NEVER commit real wallet addresses to git")
    print("  - Use environment variables: TEST_WALLET_ADDRESS")
    print("  - Replace with placeholders like 'user_provided_wallet_address'")
    print()
    print("To fix:")
    print("  1. Replace wallet addresses with environment variable usage")
    print("  2. Use os.environ.get('TEST_WALLET_ADDRESS') in Python scripts")
    print("  3. Add validation to ensure the env var is set")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())