"""
Tests for core jq functions: keys, length, type, has, map.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.jqpy import get_path, batch_get_path, first_path_match
from src.jqpy.parser import parse_path, PathComponentType


def test_parse_function_components():
    """Test that function components are parsed correctly."""
    # Test simple functions
    components = parse_path("keys")
    assert len(components) == 1
    assert components[0].type == PathComponentType.FUNCTION
    assert components[0].value == "keys"
    
    components = parse_path("length")
    assert len(components) == 1
    assert components[0].type == PathComponentType.FUNCTION
    assert components[0].value == "length"
    
    components = parse_path("type")
    assert len(components) == 1
    assert components[0].type == PathComponentType.FUNCTION
    assert components[0].value == "type"
    
    # Test functions with arguments
    components = parse_path('has("name")')
    assert len(components) == 1
    assert components[0].type == PathComponentType.FUNCTION
    assert components[0].value == 'has:"name"'
    
    components = parse_path('map(. * 2)')
    assert len(components) == 1
    assert components[0].type == PathComponentType.FUNCTION
    assert components[0].value == 'map:. * 2'


def test_keys_function():
    """Test the keys function."""
    # Test on object
    data = {"name": "john", "age": 30, "city": "NYC"}
    result = list(get_path(data, "keys"))
    assert result == [["age", "city", "name"]]  # Keys should be sorted
    
    # Test on array
    data = [1, 2, 3, 4]
    result = list(get_path(data, "keys"))
    assert result == [[0, 1, 2, 3]]
    
    # Test on empty object
    data = {}
    result = list(get_path(data, "keys"))
    assert result == [[]]
    
    # Test on empty array
    data = []
    result = list(get_path(data, "keys"))
    assert result == [[]]
    
    # Test on non-object/array
    data = "hello"
    result = list(get_path(data, "keys"))
    assert result == [None]


def test_length_function():
    """Test the length function."""
    # Test on object
    data = {"name": "john", "age": 30}
    result = list(get_path(data, "length"))
    assert result == [2]
    
    # Test on array
    data = [1, 2, 3, 4, 5]
    result = list(get_path(data, "length"))
    assert result == [5]
    
    # Test on string
    data = "hello"
    result = list(get_path(data, "length"))
    assert result == [5]
    
    # Test on empty containers
    result = list(get_path({}, "length"))
    assert result == [0]
    
    result = list(get_path([], "length"))
    assert result == [0]
    
    result = list(get_path("", "length"))
    assert result == [0]
    
    # Test on null
    result = list(get_path(None, "length"))
    assert result == [0]
    
    # Test on number
    result = list(get_path(42, "length"))
    assert result == [None]


def test_type_function():
    """Test the type function."""
    test_cases = [
        ({"key": "value"}, "object"),
        ([1, 2, 3], "array"),
        ("hello", "string"),
        (42, "number"),
        (3.14, "number"),
        (True, "boolean"),
        (False, "boolean"),
        (None, "null"),
    ]
    
    for data, expected_type in test_cases:
        result = list(get_path(data, "type"))
        assert result == [expected_type], f"Type of {data} should be {expected_type}, got {result}"


def test_has_function():
    """Test the has function."""
    # Test on object with string keys
    data = {"name": "john", "age": 30}
    
    result = list(get_path(data, 'has("name")'))
    assert result == [True]
    
    result = list(get_path(data, 'has("missing")'))
    assert result == [False]
    
    # Test on array with indices
    data = [1, 2, 3, 4]
    
    result = list(get_path(data, 'has(1)'))
    assert result == [True]
    
    result = list(get_path(data, 'has(0)'))
    assert result == [True]
    
    result = list(get_path(data, 'has(10)'))
    assert result == [False]
    
    result = list(get_path(data, 'has(-1)'))
    assert result == [False]  # jq doesn't support negative indices in has()
    
    # Test on non-object/array
    result = list(get_path("hello", 'has("x")'))
    assert result == [False]


def test_map_function():
    """Test the map function."""
    # Test simple mapping
    data = [1, 2, 3, 4]
    result = list(get_path(data, 'map(. * 2)'))
    assert result == [[2, 4, 6, 8]]
    
    # Test mapping with field access
    data = [{"a": 1}, {"a": 2}, {"a": 3}]
    result = list(get_path(data, 'map(.a)'))
    assert result == [[1, 2, 3]]
    
    # Test mapping with more complex expressions
    data = [{"name": "john", "age": 30}, {"name": "jane", "age": 25}]
    result = list(get_path(data, 'map(.name)'))
    assert result == [["john", "jane"]]
    
    # Test mapping on empty array
    data = []
    result = list(get_path(data, 'map(. * 2)'))
    assert result == [[]]
    
    # Test error on non-array
    data = {"not": "array"}
    with pytest.raises(ValueError, match="Cannot map over non-array type"):
        list(get_path(data, 'map(. * 2)'))


def test_function_chaining():
    """Test chaining functions with other operations."""
    # Test chaining with field access
    data = {"items": [1, 2, 3, 4]}
    result = list(get_path(data, ".items | length"))
    assert result == [4]
    
    # Test chaining with keys
    data = {"user": {"name": "john", "age": 30}}
    result = list(get_path(data, ".user | keys"))
    assert result == [["age", "name"]]
    
    # Test chaining with map (using field access for now)
    data = {"items": [{"a": 1}, {"a": 2}, {"a": 3}]}
    result = list(get_path(data, '.items | map(.a)'))
    assert result == [[1, 2, 3]]


def test_function_with_path_continuation():
    """Test functions followed by more path components."""
    # keys followed by array access
    data = {"b": 1, "a": 2, "c": 3}
    result = list(get_path(data, "keys[0]"))
    assert result == ["a"]  # First key alphabetically
    
    # Test keys followed by length
    data = {"b": 1, "a": 2, "c": 3}
    result = list(get_path(data, "keys | length"))
    assert result == [3]  # Number of keys
    
    # TODO: Support map(.name)[0] syntax - requires better parsing of function arguments


def test_nested_function_calls():
    """Test complex nested function scenarios."""
    data = {
        "users": [
            {"name": "john", "scores": [85, 90, 88]},
            {"name": "jane", "scores": [92, 87]}
        ]
    }
    
    # Get user names
    result = list(get_path(data, '.users | map(.name)'))
    assert result == [["john", "jane"]]
    
    # Get first score of each user
    result = list(get_path(data, '.users | map(.scores[0])'))
    assert result == [[85, 92]]
    
    # Check if users have scores
    result = list(get_path(data, '.users | map(has("scores"))'))
    assert result == [[True, True]]


def test_jq_compatibility():
    """Test that our function implementations match jq behavior exactly."""
    test_cases = [
        # (data, path, expected_result)
        ({"name": "john", "age": 30}, "keys", ["age", "name"]),
        ([1, 2, 3], "keys", [0, 1, 2]),
        ({"a": 1, "b": 2}, "length", 2),
        ([1, 2, 3, 4], "length", 4),
        ("hello", "length", 5),
        ({"name": "john"}, "type", "object"),
        ([1, 2, 3], "type", "array"),
        ("hello", "type", "string"),
        (42, "type", "number"),
        (True, "type", "boolean"),
        (None, "type", "null"),
        ({"name": "john"}, 'has("name")', True),
        ({"name": "john"}, 'has("age")', False),
        ([1, 2, 3], 'has(1)', True),
        ([1, 2, 3], 'has(5)', False),
        # Mathematical expressions in map() - basic support for common cases
        ([1, 2, 3], 'map(. * 2)', [2, 4, 6]),
        # Field access in map() - fully supported
        ([{"a": 1}, {"a": 2}], 'map(.a)', [1, 2]),
    ]
    
    for data, path, expected in test_cases:
        result = list(get_path(data, path))
        assert result == [expected], f"Path {path} on {data} should return {expected}, got {result}"


if __name__ == "__main__":
    pytest.main([__file__])