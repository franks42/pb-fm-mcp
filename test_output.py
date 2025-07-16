#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, '.')

try:
    from src.jqpy.parser import parse_path
    from src.jqpy import get_path
    
    # Test 1: Parse the path
    path = 'users.*.age'
    components = parse_path(path)
    with open('test_output.txt', 'w') as f:
        f.write(f'=== PARSING TEST ===\n')
        f.write(f'Parsing: {path}\n')
        f.write(f'Components: {len(components)}\n')
        for i, comp in enumerate(components):
            f.write(f'  {i}: type={comp.type.value}, value="{comp.value}", raw="{comp.raw_value}"\n')
        
        # Test 2: Simple traversal
        data = {
            'users': {
                'alice': {'age': 30},
                'bob': {'age': 25}
            }
        }
        
        f.write(f'\n=== TRAVERSAL TEST ===\n')
        f.write(f'Data: {data}\n')
        f.write(f'Path: {path}\n')
        
        result = list(get_path(data, path))
        f.write(f'Result: {result}\n')
        f.write(f'Length: {len(result)}\n')
        f.write(f'Expected: [25, 30] or [30, 25]\n')
        f.write(f'Match: {sorted(result) == [25, 30]}\n')
        
        # Test 3: Step by step
        f.write(f'\n=== STEP BY STEP ===\n')
        # Test users access
        users_result = list(get_path(data, 'users'))
        f.write(f'users: {users_result}\n')
        
        # Test users.alice.age
        alice_age = list(get_path(data, 'users.alice.age'))
        f.write(f'users.alice.age: {alice_age}\n')
        
        # Test users.bob.age
        bob_age = list(get_path(data, 'users.bob.age'))
        f.write(f'users.bob.age: {bob_age}\n')
        
        f.write('\nTest completed successfully!\n')
        
except Exception as e:
    with open('test_output.txt', 'w') as f:
        f.write(f'ERROR: {e}\n')
        import traceback
        f.write(traceback.format_exc())