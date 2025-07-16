"""Tests for the core traversal functionality."""
from src.jqpy import get_path, parse_path

def test_simple_key_access():
    """Test basic dictionary key access."""
    data = {'a': 1}
    result = list(get_path(data, 'a'))
    assert result == [1], f"Expected [1], got {result}"


def test_nested_key_access():
    """Test nested dictionary key access."""
    data = {'a': {'b': {'c': 42}}}
    result = list(get_path(data, 'a.b.c'))
    assert result == [42], f"Expected [42], got {result}"


def test_array_index_access():
    """Test array index access."""
    data = {'items': [10, 20, 30]}
    result = list(get_path(data, 'items[1]'))
    assert result == [20], f"Expected [20], got {result}"


def test_wildcard_dict_access():
    """Test wildcard access in dictionaries."""
    data = {
        'users': {
            'alice': {'age': 30, 'active': True},
            'bob': {'age': 25, 'active': False},
            'charlie': {'age': 35, 'active': True}
        }
    }
    # Get all ages
    result = list(get_path(data, 'users.*.age'))
    assert sorted(result) == [25, 30, 35], f"Expected [25, 30, 35], got {result}"
    
    # Test for array wildcard as well
    data2 = {'items': [{'name': 'a', 'value': 1}, {'name': 'b', 'value': 2}]}
    result = list(get_path(data2, 'items[*].value'))
    assert sorted(result) == [1, 2], f"Expected [1, 2], got {result}"
    
# TODO: Uncomment these tests once selector functionality is implemented
    # # Test selector syntax - first check the users.* part
    # users = list(get_path(data, 'users.*'))
    # print(f"Users: {users}")  # Should be list of user dicts
    # 
    # # Now test the selector
    # result = list(get_path(data, 'users.*[?(@.active==true)].age'))
    # print(f"Selector result: {result}")
    # assert sorted(result) == [30, 35], f"Expected [30, 35], got {result}"

    # # Test only_first_path_match with selector
    # result = list(get_path(data, 'users.*[?(@.active==true)].age', only_first_path_match=True))
    # assert len(result) == 1 and result[0] in [30, 35], f"Expected [30] or [35], got {result}"
    # 
    # # Test with numeric comparison
    # result = list(get_path(data, 'users.*[?(@.age>30)].age'))
    # assert result == [35], f"Expected [35], got {result}"
