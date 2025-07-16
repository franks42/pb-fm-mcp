#!/usr/bin/env python3
"""
Test script to verify the wildcard traversal fix.
This replicates the failing test to show the output.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.abspath('.'))

def run_test():
    """Run the equivalent of test_wildcard_dict_access"""
    print("="*60)
    print("TESTING WILDCARD TRAVERSAL FIX")
    print("="*60)
    
    try:
        # Import the fixed module
        print("1. Testing imports...")
        from src.jqpy import get_path, parse_path
        print("   ✓ Imports successful")
        
        # Test data from the failing test
        data = {
            'users': {
                'alice': {'age': 30, 'active': True},
                'bob': {'age': 25, 'active': False},
                'charlie': {'age': 35, 'active': True}
            }
        }
        
        print("\n2. Testing path parsing...")
        components = parse_path('users.*.age')
        print(f"   Path: users.*.age")
        print(f"   Components: {len(components)}")
        for i, comp in enumerate(components):
            print(f"     {i}: {comp.type.value} = '{comp.value}' (raw: '{comp.raw_value}')")
        
        print("\n3. Testing step-by-step access...")
        
        # Test basic access
        users_result = list(get_path(data, 'users'))
        print(f"   users: {len(users_result)} result(s)")
        if users_result:
            print(f"          Keys: {list(users_result[0].keys())}")
        
        # Test individual user access
        alice_age = list(get_path(data, 'users.alice.age'))
        print(f"   users.alice.age: {alice_age}")
        
        bob_age = list(get_path(data, 'users.bob.age'))
        print(f"   users.bob.age: {bob_age}")
        
        charlie_age = list(get_path(data, 'users.charlie.age'))
        print(f"   users.charlie.age: {charlie_age}")
        
        print("\n4. MAIN TEST: Testing wildcard access...")
        print("   Path: users.*.age")
        
        # This is the test that was failing
        result = list(get_path(data, 'users.*.age'))
        
        print(f"   Result: {result}")
        print(f"   Length: {len(result)}")
        print(f"   Sorted: {sorted(result) if result else 'Empty'}")
        print(f"   Expected: [25, 30, 35]")
        
        # Check if test passes
        expected = [25, 30, 35]
        test_passes = sorted(result) == expected if result else False
        
        print(f"\n   TEST RESULT: {'✓ PASS' if test_passes else '✗ FAIL'}")
        
        if not test_passes:
            print(f"   Expected: {expected}")
            print(f"   Got:      {sorted(result) if result else 'Empty list'}")
        
        print("\n5. Testing array wildcard as well...")
        data2 = {'items': [{'name': 'a', 'value': 1}, {'name': 'b', 'value': 2}]}
        result2 = list(get_path(data2, 'items[*].value'))
        print(f"   items[*].value: {result2}")
        print(f"   Expected: [1, 2]")
        print(f"   Array test: {'✓ PASS' if sorted(result2) == [1, 2] else '✗ FAIL'}")
        
        return test_passes
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nFull traceback:")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test()
    print("\n" + "="*60)
    print(f"OVERALL RESULT: {'✓ SUCCESS' if success else '✗ FAILURE'}")
    print("="*60)
    
    # Write results to file for reading
    with open('test_results.txt', 'w') as f:
        f.write(f"Test result: {'PASS' if success else 'FAIL'}\n")
        f.write("See console output above for details.\n")