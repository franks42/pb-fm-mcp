import sys
import os
sys.path.insert(0, os.path.abspath('.'))

try:
    from src.jqpy import get_path
    
    data = {
        'users': {
            'alice': {'age': 30},
            'bob': {'age': 25}
        }
    }
    
    print("Testing users.*.age...")
    result = list(get_path(data, 'users.*.age'))
    print(f"Result: {result}")
    print(f"Expected: [30, 25] or [25, 30]")
    print(f"Success: {sorted(result) == [25, 30]}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()