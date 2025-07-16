#!/usr/bin/env python3

# Direct test without shell dependencies
import sys
import os

# Add current directory to path
current_dir = os.path.abspath(os.path.dirname(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Test imports
try:
    print("Testing imports...")
    from src.jqpy.parser import parse_path, PathComponent, PathComponentType
    print("✓ Parser imports successful")
    
    from src.jqpy.traverse import traverse
    print("✓ Traverse imports successful")
    
    from src.jqpy import get_path
    print("✓ Main module imports successful")
    
    # Test parsing
    print("\nTesting path parsing...")
    path = 'users.*.age'
    components = parse_path(path)
    print(f"Path: {path}")
    print(f"Components: {len(components)}")
    for i, comp in enumerate(components):
        print(f"  {i}: {comp.type.value} = '{comp.value}' (raw: '{comp.raw_value}')")
    
    # Verify component types
    expected_types = ['key', 'wildcard', 'key']
    actual_types = [comp.type.value for comp in components]
    print(f"Expected types: {expected_types}")
    print(f"Actual types: {actual_types}")
    print(f"Types match: {actual_types == expected_types}")
    
    # Test simple data access
    print("\nTesting simple traversal...")
    data = {
        'users': {
            'alice': {'age': 30},
            'bob': {'age': 25},
            'charlie': {'age': 35}
        }
    }
    
    # Test step by step
    print("\n1. Testing 'users' access:")
    users_result = list(get_path(data, 'users'))
    print(f"   Result: {users_result}")
    print(f"   Type: {type(users_result[0]) if users_result else 'None'}")
    
    print("\n2. Testing 'users.alice.age' access:")
    alice_result = list(get_path(data, 'users.alice.age'))
    print(f"   Result: {alice_result}")
    
    print("\n3. Testing 'users.*.age' access:")
    wildcard_result = list(get_path(data, 'users.*.age'))
    print(f"   Result: {wildcard_result}")
    print(f"   Length: {len(wildcard_result)}")
    print(f"   Sorted: {sorted(wildcard_result) if wildcard_result else 'Empty'}")
    print(f"   Expected: [25, 30, 35]")
    print(f"   Match: {sorted(wildcard_result) == [25, 30, 35] if wildcard_result else False}")
    
    print("\n✓ All tests completed")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

print("\nDirect test finished.")