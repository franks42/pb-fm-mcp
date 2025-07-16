#!/usr/bin/env python3
"""
Verify that the wildcard traversal fix works correctly.
This will attempt to run the same test as test_wildcard_dict_access.
"""

import sys
import os
sys.path.insert(0, '.')

def test_wildcard_fix():
    """Test the wildcard traversal that was failing"""
    print("Testing wildcard traversal fix...")
    
    try:
        from src.jqpy import get_path
        
        # Test data from the failing test
        data = {
            'users': {
                'alice': {'age': 30, 'active': True},
                'bob': {'age': 25, 'active': False},
                'charlie': {'age': 35, 'active': True}
            }
        }
        
        print(f"Data: {data}")
        print("Testing path: users.*.age")
        
        # This was returning [] before the fix
        result = list(get_path(data, 'users.*.age'))
        
        print(f"Result: {result}")
        print(f"Length: {len(result)}")
        print(f"Sorted: {sorted(result) if result else 'Empty'}")
        print(f"Expected: [25, 30, 35]")
        
        # Check if test passes
        expected = [25, 30, 35]
        success = sorted(result) == expected if result else False
        
        print(f"Test result: {'PASS' if success else 'FAIL'}")
        
        if success:
            print("✓ Wildcard traversal is now working correctly!")
        else:
            print("✗ Wildcard traversal is still broken")
            print(f"Expected: {expected}")
            print(f"Got: {sorted(result) if result else 'Empty list'}")
        
        # Also test array wildcard
        print("\nTesting array wildcard...")
        data2 = {'items': [{'name': 'a', 'value': 1}, {'name': 'b', 'value': 2}]}
        result2 = list(get_path(data2, 'items[*].value'))
        print(f"items[*].value: {result2}")
        print(f"Array wildcard: {'PASS' if sorted(result2) == [1, 2] else 'FAIL'}")
        
        return success
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_test_core():
    """Simulate running the core tests that would be in test_core.py"""
    print("\n" + "="*50)
    print("SIMULATING test_core.py TESTS")
    print("="*50)
    
    tests = [
        ("Simple key access", lambda: list(get_path({'a': 1}, 'a')) == [1]),
        ("Nested key access", lambda: list(get_path({'a': {'b': 2}}, 'a.b')) == [2]),
        ("Array index access", lambda: list(get_path({'arr': [10, 20, 30]}, 'arr[1]')) == [20]),
        ("Wildcard dict access", lambda: sorted(list(get_path({'x': {'a': 1, 'b': 2}}, 'x.*'))) == [1, 2]),
        ("Wildcard array access", lambda: list(get_path({'arr': [1, 2, 3]}, 'arr[*]')) == [1, 2, 3]),
    ]
    
    from src.jqpy import get_path
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            result = test_func()
            status = "PASS" if result else "FAIL"
            print(f"{name}: {status}")
            if result:
                passed += 1
        except Exception as e:
            print(f"{name}: ERROR - {e}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    return passed == total

if __name__ == "__main__":
    print("VERIFYING WILDCARD TRAVERSAL FIX")
    print("="*50)
    
    wildcard_success = test_wildcard_fix()
    core_success = simulate_test_core()
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Wildcard fix: {'✓ SUCCESS' if wildcard_success else '✗ FAILED'}")
    print(f"Core tests: {'✓ SUCCESS' if core_success else '✗ FAILED'}")
    
    overall = wildcard_success and core_success
    print(f"Overall: {'✓ ALL TESTS PASS' if overall else '✗ SOME TESTS FAILED'}")
    
    # Write summary to file
    with open('test_summary.txt', 'w') as f:
        f.write(f"Wildcard fix: {'PASS' if wildcard_success else 'FAIL'}\n")
        f.write(f"Core tests: {'PASS' if core_success else 'FAIL'}\n")
        f.write(f"Overall: {'PASS' if overall else 'FAIL'}\n")