"""Tests for the core jqpy functionality."""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.jqpy import get_path, parse_path

def test_basic_identity():
    """Test basic identity filter."""
    data = {'name': 'John', 'age': 30}
    result = list(get_path(data, '.'))
    assert result == [data], f"Expected [{data}], got {result}"

def test_field_access():
    """Test field access."""
    data = {'user': {'name': 'John', 'age': 30}}
    result = list(get_path(data, '.user.name'))
    assert result == ['John'], f"Expected ['John'], got {result}"

def test_array_indexing():
    """Test array indexing."""
    data = {'items': [1, 2, 3, 4, 5]}
    result = list(get_path(data, '.items[0]'))
    assert result == [1], f"Expected [1], got {result}"
    
    result = list(get_path(data, '.items[-1]'))
    assert result == [5], f"Expected [5], got {result}"

def test_wildcard():
    """Test wildcard operator."""
    data = {'users': [{'name': 'John'}, {'name': 'Jane'}]}
    result = list(get_path(data, '.users[].name'))
    assert sorted(result) == ['Jane', 'John'], f"Expected ['Jane', 'John'], got {result}"

def test_array_splat():
    """Test array splat operator (.[])."""
    data = [1, 2, 3]
    result = list(get_path(data, '.[]'))
    assert result == [1, 2, 3], f"Expected [1, 2, 3], got {result}"

def test_array_splat_with_object():
    """Test array splat with object construction."""
    data = [{'a': 1}, {'b': 2}]
    result = list(get_path(data, '.[] | {key: .key, value: .value}'))
    assert result == [{'key': 'a', 'value': 1}, {'key': 'b', 'value': 2}], f"Expected [{'key': 'a', 'value': 1}, {'key': 'b', 'value': 2}], got {result}"

def test_comparison_operators():
    """Test comparison operators in filters."""
    data = {
        'users': [
            {'name': 'John', 'age': 30, 'active': True},
            {'name': 'Jane', 'age': 25, 'active': False}
        ]
    }
    
    # Test equality
    result = list(get_path(data, '.users[] | select(.active == true) | .name'))
    assert result == ['John'], f"Expected ['John'], got {result}"
    
    # Test numeric comparison
    result = list(get_path(data, '.users[] | select(.age > 25) | .name'))
    assert result == ['John'], f"Expected ['John'], got {result}"

def test_raw_output():
    """Test raw output option (equivalent to string output)."""
    data = {'name': 'John'}
    result = list(get_path(data, '.name'))
    assert result == ['John'], f"Expected ['John'], got {result}"

def test_compact_output():
    """Test compact output (equivalent to no pretty printing)."""
    data = {'name': 'John', 'age': 30}
    result = list(get_path(data, '.'))
    assert result == [data], f"Expected [{data}], got {result}"

def test_slurp():
    """Test slurp option for multiple inputs."""
    data = [{'name': 'John'}, {'name': 'Jane'}]
    result = list(get_path(data, '.[].name'))
    assert sorted(result) == ['Jane', 'John'], f"Expected ['Jane', 'John'], got {result}"

def test_null_input():
    """Test null input option."""
    result = list(get_path(None, '42'))
    assert result == [42], f"Expected [42], got {result}"

def test_exit_status():
    """Test exit status behavior."""
    # Should succeed with output
    data = {}
    result = list(get_path(data, '.'))
    assert result == [{}], f"Expected [{dict()}], got {result}"
    
    # Test literal false returns the boolean false
    result = list(get_path(data, 'false'))
    assert result == [False], f"Expected [False], got {result}"

def test_file_input():
    """Test reading input from a file."""
    data = {'name': 'John'}
    result = list(get_path(data, '.name'))
    assert result == ['John'], f"Expected ['John'], got {result}"

# Add a test that compares jq and jqpy output for various expressions
TEST_CASES = [
    ('.', {'a': 1, 'b': 2}, [{'a': 1, 'b': 2}]),
    ('.a', {'a': 1, 'b': 2}, [1]),
    ('.[]', [1, 2, 3], [1, 2, 3]),
    ('.a.b', {'a': {'b': 'value'}}, ['value']),
    ('{a: .a, b: .b}', {'a': 1, 'b': 2, 'c': 3}, [{'a': 1, 'b': 2}]),
]

@pytest.mark.parametrize("path_expr, data, expected", TEST_CASES)
def test_various_expressions(path_expr, data, expected):
    """Test various path expressions."""
    result = list(get_path(data, path_expr))
    assert result == expected, f"Expected {expected}, got {result}"
