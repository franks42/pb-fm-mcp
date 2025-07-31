import re
import os

def fix_api_function_decorators(file_path):
    """Fix @api_function decorators to use simple format"""
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match @api_function decorators with parameters
    # This matches multi-line decorators with parameters
    pattern = r'@api_function\(\s*protocols=\["mcp",\s*"rest"\][^)]*\)'
    
    # Replace with simple format
    replacement = '@api_function(protocols=["mcp", "rest"])'
    
    # Use DOTALL flag to match across newlines
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Count how many changes were made
    old_count = len(re.findall(r'@api_function\(', content))
    new_count = len(re.findall(r'@api_function\(', new_content))
    
    if content \!= new_content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Fixed decorators in {file_path}")
    else:
        print(f"No changes needed in {file_path}")

if __name__ == "__main__":
    base_path = "src/functions/"
    files_to_fix = [
        "webpage_queue_management.py",
        "webpage_s3_helpers.py", 
        "webpage_orchestration.py"
    ]
    
    for filename in files_to_fix:
        file_path = os.path.join(base_path, filename)
        fix_api_function_decorators(file_path)
