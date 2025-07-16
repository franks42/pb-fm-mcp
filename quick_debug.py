#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, '.')

from src.jqpy.parser import parse_path

# Test parsing
path = 'users.*.age'
print(f'Parsing: {path}')
components = parse_path(path)
print(f'Components: {len(components)}')
for i, comp in enumerate(components):
    print(f'  {i}: type={comp.type.value}, value="{comp.value}", raw="{comp.raw_value}"')

# Test simple data access  
from src.jqpy import get_path

data = {
    'users': {
        'alice': {'age': 30},
        'bob': {'age': 25}
    }
}

print(f'\nData: {data}')
print(f'Testing path: users.*.age')

try:
    result = list(get_path(data, 'users.*.age'))
    print(f'Result: {result}')
    print(f'Expected: [25, 30] or [30, 25]')
    print(f'Match: {sorted(result) == [25, 30]}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()