import re
import sys

def fix_api_function_decorators(file_path):
    """Fix @api_function decorators to use simple format"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match complex @api_function decorators
    pattern = r'@api_function\(\s*protocols=\["mcp",\s*"rest"\],\s*description="[^"]*",\s*parameters=\{[^}]*\}\s*\)'
    
    # Replace with simple format
    replacement = '@api_function(protocols=["mcp", "rest"])'
    
    # Count replacements
    new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
    
    if count > 0:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Fixed {count} decorators in {file_path}")
    else:
        print(f"No decorators to fix in {file_path}")

if __name__ == "__main__":
    files_to_fix = [
        "src/functions/webpage_queue_management.py",
        "src/functions/webpage_s3_helpers.py",
        "src/functions/webpage_orchestration.py"
    ]
    
    for file_path in files_to_fix:
        fix_api_function_decorators(file_path)
