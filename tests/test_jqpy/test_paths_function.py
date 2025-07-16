"""
Tests for the paths() function - jq-compatible path introspection.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.jqpy import get_path, batch_get_path, first_path_match
from src.jqpy.parser import parse_path, PathComponentType


def test_parse_paths_function():
    """Test that paths function components are parsed correctly."""
    # Test simple paths function
    components = parse_path("paths")
    assert len(components) == 1
    assert components[0].type == PathComponentType.FUNCTION
    assert components[0].value == "paths"
    
    # Test paths with type filters
    components = parse_path("paths(objects)")
    assert len(components) == 1
    assert components[0].type == PathComponentType.FUNCTION
    assert components[0].value == "paths(objects)"
    
    components = parse_path("paths(arrays)")
    assert len(components) == 1
    assert components[0].type == PathComponentType.FUNCTION
    assert components[0].value == "paths(arrays)"
    
    components = parse_path("paths(scalars)")
    assert len(components) == 1
    assert components[0].type == PathComponentType.FUNCTION
    assert components[0].value == "paths(scalars)"


def test_paths_function_all_paths():
    """Test the paths function without filter (all paths)."""
    data = {
        "a": {
            "b": [1, 2]
        },
        "c": "text"
    }
    
    result = list(get_path(data, "paths"))
    expected = [
        ["a"],
        ["a", "b"],
        ["a", "b", 0],
        ["a", "b", 1],
        ["c"]
    ]
    assert result == [expected]


def test_paths_function_objects():
    """Test paths(objects) - find paths to all objects."""
    data = {
        "a": {
            "b": [1, 2]
        },
        "c": "text",
        "d": {
            "e": "value"
        }
    }
    
    result = list(get_path(data, "paths(objects)"))
    expected = [
        ["a"],
        ["d"]
    ]
    assert result == [expected]


def test_paths_function_arrays():
    """Test paths(arrays) - find paths to all arrays."""
    data = {
        "a": {
            "b": [1, 2],
            "c": [3, 4, 5]
        },
        "d": "text",
        "e": [6, 7]
    }
    
    result = list(get_path(data, "paths(arrays)"))
    expected = [
        ["a", "b"],
        ["a", "c"],
        ["e"]
    ]
    assert result == [expected]


def test_paths_function_scalars():
    """Test paths(scalars) - find paths to all scalar values."""
    data = {
        "a": {
            "b": [1, 2]
        },
        "c": "text",
        "d": True,
        "e": None
    }
    
    result = list(get_path(data, "paths(scalars)"))
    expected = [
        ["a", "b", 0],
        ["a", "b", 1],
        ["c"],
        ["d"],
        ["e"]
    ]
    assert result == [expected]


def test_paths_function_empty_structures():
    """Test paths function with empty data structures."""
    # Empty object
    result = list(get_path({}, "paths"))
    assert result == [[]]
    
    # Empty array
    result = list(get_path([], "paths"))
    assert result == [[]]
    
    # Object with empty containers
    data = {"empty_obj": {}, "empty_arr": [], "value": 42}
    result = list(get_path(data, "paths"))
    expected = [
        ["empty_obj"],
        ["empty_arr"], 
        ["value"]
    ]
    assert result == [expected]


def test_paths_function_nested_structures():
    """Test paths function with deeply nested structures."""
    data = {
        "level1": {
            "level2": {
                "level3": {
                    "data": "deep_value",
                    "numbers": [1, 2, 3]
                },
                "other": "value"
            }
        }
    }
    
    result = list(get_path(data, "paths"))
    expected = [
        ["level1"],
        ["level1", "level2"],
        ["level1", "level2", "level3"],
        ["level1", "level2", "level3", "data"],
        ["level1", "level2", "level3", "numbers"],
        ["level1", "level2", "level3", "numbers", 0],
        ["level1", "level2", "level3", "numbers", 1],
        ["level1", "level2", "level3", "numbers", 2],
        ["level1", "level2", "other"]
    ]
    assert result == [expected]


def test_paths_function_array_of_objects():
    """Test paths function with array of objects."""
    data = {
        "users": [
            {"name": "john", "age": 30},
            {"name": "jane", "age": 25}
        ]
    }
    
    result = list(get_path(data, "paths(objects)"))
    expected = [
        ["users", 0],
        ["users", 1]
    ]
    assert result == [expected]
    
    result = list(get_path(data, "paths(scalars)"))
    expected = [
        ["users", 0, "name"],
        ["users", 0, "age"],
        ["users", 1, "name"],
        ["users", 1, "age"]
    ]
    assert result == [expected]


def test_paths_function_mixed_types():
    """Test paths function with mixed data types."""
    data = {
        "string": "hello",
        "number": 42,
        "boolean": True,
        "null_value": None,
        "array": [1, "two", {"three": 3}],
        "object": {"nested": "value"}
    }
    
    # Test scalars
    result = list(get_path(data, "paths(scalars)"))
    expected = [
        ["string"],
        ["number"],
        ["boolean"],
        ["null_value"],
        ["array", 0],
        ["array", 1],
        ["array", 2, "three"],
        ["object", "nested"]
    ]
    assert result == [expected]
    
    # Test objects
    result = list(get_path(data, "paths(objects)"))
    expected = [
        ["array", 2],
        ["object"]
    ]
    assert result == [expected]


def test_paths_function_chaining():
    """Test chaining paths function with other operations."""
    data = {
        "a": {"b": [1, 2]},
        "c": "text"
    }
    
    # Get number of paths
    result = list(get_path(data, "paths | length"))
    assert result == [5]  # 5 total paths
    
    # Get first path
    result = list(get_path(data, "paths[0]"))
    assert result == [["a"]]


def test_paths_function_primitive_root():
    """Test paths function on primitive values at root."""
    # String root - no sub-paths for scalars
    result = list(get_path("hello", "paths(scalars)"))
    assert result == [[]]  # No sub-paths for primitive scalars
    
    # Number root  
    result = list(get_path(42, "paths"))
    assert result == [[]]  # No sub-paths for primitive values
    
    # Array root
    result = list(get_path([1, 2, 3], "paths"))
    expected = [
        [0],
        [1], 
        [2]
    ]
    assert result == [expected]


def test_paths_function_jq_compatibility():
    """Test that paths function matches jq behavior exactly."""
    # Test case from jq manual
    data = {"a": {"b": [1, 2]}, "c": "text"}
    
    # All paths
    result = list(get_path(data, "paths"))
    expected = [
        ["a"],
        ["a", "b"],
        ["a", "b", 0],
        ["a", "b", 1],
        ["c"]
    ]
    assert result == [expected]
    
    # Objects only
    result = list(get_path(data, "paths(objects)"))
    expected = [["a"]]
    assert result == [expected]
    
    # Arrays only
    result = list(get_path(data, "paths(arrays)"))
    expected = [["a", "b"]]
    assert result == [expected]
    
    # Scalars only
    result = list(get_path(data, "paths(scalars)"))
    expected = [
        ["a", "b", 0],
        ["a", "b", 1],
        ["c"]
    ]
    assert result == [expected]


def test_paths_function_error_cases():
    """Test paths function with invalid type filters."""
    data = {"a": 1}
    
    # Invalid type filter should return empty (no matches)
    result = list(get_path(data, "paths(invalid_type)"))
    assert result == [[]]  # No paths match invalid type
    
    # Empty type filter should work like no filter
    result = list(get_path(data, "paths()"))
    expected = [["a"]]
    assert result == [expected]


if __name__ == "__main__":
    pytest.main([__file__])