#!/usr/bin/env python3

import logging
logging.basicConfig(level=logging.DEBUG)  # Back to DEBUG to see all details

from src.jqpy import parse_path, get_path

# Test data
data = {
    'users': {
        'alice': {'age': 30, 'active': True},
        'bob': {'age': 25, 'active': False},
        'charlie': {'age': 35, 'active': True}
    }
}

# Also test simpler data
simple_data = {
    'users': {
        'alice': {'age': 30},
        'bob': {'age': 25}
    }
}

print('=== DEBUGGING WILDCARD TRAVERSAL ===\n')

# Step 1: Test parsing
print('Step 1: Parsing "users.*.age"')
try:
    components = parse_path('users.*.age')
    print(f'Parsed components ({len(components)}):')
    for i, comp in enumerate(components):
        print(f'  {i}: {comp.type.value} = "{comp.value}" (raw: "{comp.raw_value}")')
    print()
except Exception as e:
    print(f'Parsing failed: {e}')
    import traceback
    traceback.print_exc()
    exit(1)

# Step 2: Test simple cases first
print('Step 2: Test simple key access')
try:
    simple_result = list(get_path(data, 'users'))
    print(f'users result: {simple_result}')
    print(f'Expected: 1 dict with alice, bob, charlie')
except Exception as e:
    print(f'Simple test failed: {e}')
    import traceback
    traceback.print_exc()

print()

# Step 3: Test nested key access
print('Step 3: Test nested key access')
try:
    nested_result = list(get_path(data, 'users.alice.age'))
    print(f'users.alice.age result: {nested_result}')
    print(f'Expected: [30]')
except Exception as e:
    print(f'Nested test failed: {e}')
    import traceback
    traceback.print_exc()

print()

# Step 4: Test full traversal
print('Step 4: Full traversal with get_path')
try:
    result = list(get_path(data, 'users.*.age'))
    print(f'Result: {result}')
    print(f'Length: {len(result)}')
    if result:
        print(f'Sorted: {sorted(result)}')
        expected = [25, 30, 35]
        actual = sorted(result)
        print(f'Expected: {expected}')
        print(f'Test passes: {actual == expected}')
    else:
        print('EMPTY RESULT - This is the bug!')
except Exception as e:
    print(f'Traversal failed: {e}')
    import traceback
    traceback.print_exc()

print('\n=== END DEBUG ===')