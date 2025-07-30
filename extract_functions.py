import os
import re
import csv

def extract_function_info():
    functions = []
    
    # Search through all Python files in src/functions
    for root, dirs, files in os.walk('src/functions'):
        for file in files:
            if file.endswith('.py') and file \!= '__init__.py':
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Find all @api_function decorators and their function definitions
                    pattern = r'@api_function\(\s*(?:[^)]*?protocols\s*=\s*\[([^\]]*)\][^)]*?)?\)\s*def\s+(\w+)\([^:]*?:\s*"""([^"]*?)"""'
                    matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
                    
                    for protocols_str, func_name, description in matches:
                        # Parse protocols
                        mcp_enabled = 'YES' if 'mcp' in protocols_str else ''
                        rest_enabled = 'YES' if 'rest' in protocols_str else ''
                        
                        # Clean description
                        desc = description.strip().replace('\n', ' ')
                        if len(desc) > 120:
                            desc = desc[:117] + '...'
                        
                        functions.append([func_name, mcp_enabled, rest_enabled, desc])
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    # Sort by function name
    functions.sort(key=lambda x: x[0])
    
    # Write CSV
    with open('function_protocols.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Function Name', 'MCP', 'REST', 'Description'])
        writer.writerows(functions)
    
    print(f"Created CSV with {len(functions)} functions")
    
    # Also print first few for preview
    print("\nFirst 10 functions:")
    for i, func in enumerate(functions[:10]):
        print(f"{func[0]}: MCP={func[1]}, REST={func[2]}")

if __name__ == '__main__':
    extract_function_info()
EOF < /dev/null