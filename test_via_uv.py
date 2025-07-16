#!/usr/bin/env python3

import subprocess
import os
import sys

# Change to the project directory
os.chdir('/Users/franksiebenlist/Documents/GitHub/hastra-fm-mcp')

try:
    # Run the test using uv
    result = subprocess.run([
        'uv', 'run', 'pytest', 
        'tests/test_jqpy/test_traversal.py::test_wildcard_dict_access', 
        '-v'
    ], capture_output=True, text=True, timeout=30)
    
    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    print(f"\nReturn code: {result.returncode}")
    
except subprocess.TimeoutExpired:
    print("Test timed out after 30 seconds")
except FileNotFoundError:
    print("uv command not found")
except Exception as e:
    print(f"Error running test: {e}")

# Also try a simple import test
print("\n" + "="*50)
print("TESTING IMPORTS")
print("="*50)

try:
    sys.path.insert(0, '.')
    from src.jqpy import get_path
    
    data = {
        'users': {
            'alice': {'age': 30},
            'bob': {'age': 25},
            'charlie': {'age': 35}
        }
    }
    
    result = list(get_path(data, 'users.*.age'))
    print(f"Direct test result: {result}")
    print(f"Expected: [25, 30, 35]")
    print(f"Sorted result: {sorted(result) if result else 'Empty'}")
    print(f"Test passes: {sorted(result) == [25, 30, 35] if result else False}")
    
except Exception as e:
    print(f"Import test failed: {e}")
    import traceback
    traceback.print_exc()