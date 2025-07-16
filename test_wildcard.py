#!/usr/bin/env python3

from src.jqpy import parse_path

# First test parsing
print('Testing parser with users.*.age')
try:
    components = parse_path('users.*.age')
    print(f'Parsed components: {components}')
    for i, comp in enumerate(components):
        print(f'  {i}: {comp}')
    
except Exception as e:
    print(f'Parsing error: {e}')
    import traceback
    traceback.print_exc()

print('\n' + '='*50 + '\n')

# Then test actual traversal
from src.jqpy import get_path

data = {
    'users': {
        'alice': {'age': 30, 'active': True},
        'bob': {'age': 25, 'active': False}, 
        'charlie': {'age': 35, 'active': True}
    }
}

print('Testing users.*.age traversal')
try:
    result = list(get_path(data, 'users.*.age'))
    print(f'Result: {result}')
    print(f'Sorted: {sorted(result)}')
    
    # Test the expected assertion
    expected = [25, 30, 35]
    actual = sorted(result)
    print(f'Expected: {expected}')
    print(f'Actual: {actual}')
    print(f'Test passes: {actual == expected}')
    
except Exception as e:
    print(f'Traversal error: {e}')
    import traceback
    traceback.print_exc()