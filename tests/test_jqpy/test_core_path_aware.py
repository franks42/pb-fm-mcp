"""
Path-aware tests for the core jqpy functionality.

This is a copy of test_core.py but using test data with embedded path information
to make it easier to understand what operations are being performed and verify
the results. Compare with test_core.py to see the difference in readability.
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.jqpy import get_path, parse_path
from src.jqpy.traverse_utils import make_path_aware, PATH_AWARE_TEST_DATA as PATH_AWARE_DATA


def test_basic_identity_path_aware():
    """Test basic identity filter with path-aware data."""
    # Original data: {'name': 'John', 'age': 30}
    data = make_path_aware({'name': 'John', 'age': 30})
    # Now data = {'path': '.', 'name': 'John', 'age': 30}
    
    result = list(get_path(data, '.'))
    assert result == [data], f"Expected [{data}], got {result}"
    
    # With path-aware data, we can see exactly what object was returned
    print(f"Identity operation returned object at path: {result[0]['path']}")


def test_field_access_path_aware():
    """Test field access with path-aware data."""
    # Original: {'user': {'name': 'John', 'age': 30}}
    data = make_path_aware({
        'user': {
            'name': 'John', 
            'age': 30
        }
    })
    # Now: {'path': '.', 'user': {'path': '.user', 'name': 'John', 'age': 30}}
    
    result = list(get_path(data, '.user.name'))
    assert result == ['John'], f"Expected ['John'], got {result}"
    
    # Test accessing the user object itself to see the path
    user_result = list(get_path(data, '.user'))
    expected_user = {'path': '.user', 'name': 'John', 'age': 30}
    assert user_result == [expected_user], f"Expected [{expected_user}], got {user_result}"
    print(f"User object accessed at path: {user_result[0]['path']}")


def test_array_indexing_path_aware():
    """Test array indexing with path-aware data."""
    # Original: {'items': [1, 2, 3, 4, 5]}
    data = make_path_aware({'items': [1, 2, 3, 4, 5]})
    # Now: {'path': '.', 'items': [1, 2, 3, 4, 5]} (numbers preserved for math)
    
    result = list(get_path(data, '.items[0]'))
    assert result == [1], f"Expected [1], got {result}"
    
    result = list(get_path(data, '.items[-1]'))
    assert result == [5], f"Expected [5], got {result}"
    
    print(f"Array indexing: .items[0] = {result[0]} (from path .items[0])")


def test_wildcard_path_aware():
    """Test wildcard operator with path-aware data."""
    # Original: {'users': [{'name': 'John'}, {'name': 'Jane'}]}
    data = make_path_aware({
        'users': [
            {'name': 'John'}, 
            {'name': 'Jane'}
        ]
    })
    # Now each user object has its own path: .users[0], .users[1]
    
    result = list(get_path(data, '.users[].name'))
    assert sorted(result) == ['Jane', 'John'], f"Expected ['Jane', 'John'], got {result}"
    
    # Test getting the user objects themselves to see paths
    users_result = list(get_path(data, '.users[]'))
    expected_users = [
        {'path': '.users[0]', 'name': 'John'},
        {'path': '.users[1]', 'name': 'Jane'}
    ]
    assert users_result == expected_users, f"Expected {expected_users}, got {users_result}"
    
    for i, user in enumerate(users_result):
        print(f"User {i}: {user['name']} at path {user['path']}")


def test_array_splat_path_aware():
    """Test array splat operator (.[]). with path-aware data."""
    # Original: [1, 2, 3]
    data = [1, 2, 3]  # Keep simple for array splat
    
    result = list(get_path(data, '.[]'))
    assert result == [1, 2, 3], f"Expected [1, 2, 3], got {result}"
    
    # Test with path-aware array of objects
    object_array = make_path_aware([{'value': 'a'}, {'value': 'b'}])
    # Now: [{'path': '.[0]', 'value': 'a'}, {'path': '.[1]', 'value': 'b'}]
    
    splat_result = list(get_path(object_array, '.[]'))
    expected = [
        {'path': '.[0]', 'value': 'a'},
        {'path': '.[1]', 'value': 'b'}
    ]
    assert splat_result == expected, f"Expected {expected}, got {splat_result}"
    
    for obj in splat_result:
        print(f"Array splat returned object at path: {obj['path']}")


def test_array_splat_with_object_path_aware():
    """Test array splat with object construction using path-aware data."""
    # Original: [{'a': 1}, {'b': 2}]
    data = make_path_aware([{'a': 1}, {'b': 2}])
    # Now: [{'path': '.[0]', 'a': 1}, {'path': '.[1]', 'b': 2}]
    
    result = list(get_path(data, '.[] | {key: .key, value: .value}'))
    expected = [{'key': 'a', 'value': 1}, {'key': 'b', 'value': 2}]
    assert result == expected, f"Expected {expected}, got {result}"
    
    print("Object construction from path-aware single-key objects:")
    for i, obj in enumerate(result):
        print(f"  Object {i}: {obj} (constructed from .[{i}])")


def test_comparison_operators_path_aware():
    """Test comparison operators in filters with path-aware data."""
    # Original: [{'age': 25, 'active': True}, {'age': 30, 'active': False}, {'age': 35, 'active': True}]
    data = make_path_aware([
        {'age': 25, 'active': True}, 
        {'age': 30, 'active': False}, 
        {'age': 35, 'active': True}
    ])
    # Now each object has path: .[0], .[1], .[2]
    
    # Test age comparison
    result = list(get_path(data, '.[] | select(.age > 28)'))
    expected = [
        {'path': '.[1]', 'age': 30, 'active': False},
        {'path': '.[2]', 'age': 35, 'active': True}
    ]
    assert result == expected, f"Expected {expected}, got {result}"
    
    print("Age filter (> 28) selected objects at paths:")
    for obj in result:
        print(f"  Path: {obj['path']}, Age: {obj['age']}")
    
    # Test boolean comparison
    active_result = list(get_path(data, '.[] | select(.active == true)'))
    expected_active = [
        {'path': '.[0]', 'age': 25, 'active': True},
        {'path': '.[2]', 'age': 35, 'active': True}
    ]
    assert active_result == expected_active, f"Expected {expected_active}, got {active_result}"
    
    print("Active filter (== true) selected objects at paths:")
    for obj in active_result:
        print(f"  Path: {obj['path']}, Active: {obj['active']}")


def test_nested_access_path_aware():
    """Test deeply nested access with path-aware data."""
    data = PATH_AWARE_DATA["complex_nested"]
    
    # Access deeply nested team names
    result = list(get_path(data, '.company.departments[].teams[].name'))
    expected = ["Backend", "Frontend", "Enterprise"]
    assert sorted(result) == sorted(expected), f"Expected {sorted(expected)}, got {sorted(result)}"
    
    # Access team objects to see their paths
    teams = list(get_path(data, '.company.departments[].teams[]'))
    print("Team objects found at paths:")
    for team in teams:
        print(f"  Path: {team['path']}, Team: {team['name']}")


def test_array_construction_path_aware():
    """Test array construction with path-aware data."""
    data = make_path_aware({
        'numbers': [10, 20, 30],
        'users': [{'name': 'Alice'}, {'name': 'Bob'}]
    })
    
    # Test simple array construction
    result = list(get_path(data, '[.numbers[]]'))
    expected = [[10, 20, 30]]  # Array construction collects results
    assert result == expected, f"Expected {expected}, got {result}"
    
    # Test mixed array construction 
    mixed_result = list(get_path(data, '[.numbers[0], .users[0].name]'))
    expected_mixed = [[10, 'Alice']]
    assert mixed_result == expected_mixed, f"Expected {expected_mixed}, got {mixed_result}"
    
    print("Array construction collected values:")
    print(f"  Numbers: {result[0]}")
    print(f"  Mixed: {mixed_result[0]}")


def test_deeply_nested_arrays_path_aware():
    """Test operations on deeply nested arrays with path-aware data."""
    data = PATH_AWARE_DATA["deeply_nested_arrays"]
    
    # Access all leaf values
    result = list(get_path(data, '.matrix[][][]'))
    expected = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert sorted(result) == sorted(expected), f"Expected {sorted(expected)}, got {sorted(result)}"
    
    # Access specific nested arrays to see structure
    first_matrix = list(get_path(data, '.matrix[0]'))
    print(f"First matrix structure with embedded paths:")
    print(f"  {first_matrix[0]}")
    
    # Test array construction with deeply nested data
    constructed = list(get_path(data, '[.matrix[0][0][]]'))
    expected_constructed = [[1, 2]]
    assert constructed == expected_constructed, f"Expected {expected_constructed}, got {constructed}"


if __name__ == "__main__":
    # Run a few tests to demonstrate the path-aware approach
    print("=== PATH-AWARE TEST DEMONSTRATIONS ===\\n")
    
    test_field_access_path_aware()
    print()
    
    test_wildcard_path_aware() 
    print()
    
    test_comparison_operators_path_aware()
    print()
    
    test_nested_access_path_aware()
    print()
    
    print("=== All path-aware tests demonstrate clear traceability! ===")