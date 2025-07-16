"""
Tests for array slicing functionality in jqpy.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.jqpy import get_path, batch_get_path, first_path_match
from src.jqpy.operations import set_path, delete_path
from src.jqpy.parser import parse_path, PathComponentType


def test_parse_slice_components():
    """Test that slice components are parsed correctly."""
    # Test [1:3] slice
    components = parse_path(".[1:3]")
    assert len(components) == 1
    assert components[0].type == PathComponentType.SLICE
    assert components[0].value == slice(1, 3)
    assert components[0].raw_value == "1:3"
    
    # Test [2:] slice (open end)
    components = parse_path(".[2:]")
    assert len(components) == 1
    assert components[0].type == PathComponentType.SLICE
    assert components[0].value == slice(2, None)
    assert components[0].raw_value == "2:"
    
    # Test [:5] slice (open start)
    components = parse_path(".[:5]")
    assert len(components) == 1
    assert components[0].type == PathComponentType.SLICE
    assert components[0].value == slice(None, 5)
    assert components[0].raw_value == ":5"
    
    # Test [-2:] slice (negative start)
    components = parse_path(".[-2:]")
    assert len(components) == 1
    assert components[0].type == PathComponentType.SLICE
    assert components[0].value == slice(-2, None)
    assert components[0].raw_value == "-2:"


def test_basic_slicing():
    """Test basic array slicing operations."""
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    
    # Test [1:3] - should return [2, 3]
    result = list(get_path(data, ".[1:3]"))
    assert result == [[2, 3]]
    
    # Test [2:] - should return [3, 4, 5, 6, 7, 8]
    result = list(get_path(data, ".[2:]"))
    assert result == [[3, 4, 5, 6, 7, 8]]
    
    # Test [:3] - should return [1, 2, 3]
    result = list(get_path(data, ".[:3]"))
    assert result == [[1, 2, 3]]
    
    # Test [-2:] - should return [7, 8]
    result = list(get_path(data, ".[-2:]"))
    assert result == [[7, 8]]


def test_slicing_with_path_continuation():
    """Test that slicing works correctly when followed by more path components."""
    data = {
        "items": [
            {"name": "item1", "value": 10},
            {"name": "item2", "value": 20},
            {"name": "item3", "value": 30},
            {"name": "item4", "value": 40}
        ]
    }
    
    # Test .items[1:3] - should return middle two items
    result = list(get_path(data, ".items[1:3]"))
    assert result == [[
        {"name": "item2", "value": 20},
        {"name": "item3", "value": 30}
    ]]
    
    # Test .items[1:3][] - should iterate over middle two items  
    result = list(get_path(data, ".items[1:3][]"))
    assert result == [
        {"name": "item2", "value": 20},
        {"name": "item3", "value": 30}
    ]
    
    # Test .items[1:3][].name - should get names of middle two items
    result = list(get_path(data, ".items[1:3][].name"))
    assert result == ["item2", "item3"]


def test_slicing_empty_results():
    """Test slicing behavior with empty or out-of-bounds slices."""
    data = [1, 2, 3]
    
    # Test slice beyond bounds
    result = list(get_path(data, ".[5:10]"))
    assert result == [[]]
    
    # Test slice with start > end
    result = list(get_path(data, ".[3:1]"))
    assert result == [[]]
    
    # Test slice on empty array
    result = list(get_path([], ".[1:3]"))
    assert result == [[]]


def test_slicing_on_non_arrays():
    """Test that slicing on non-array types returns nothing."""
    data = {"key": "value"}
    
    # Slicing on dict should return nothing
    result = list(get_path(data, ".[1:3]"))
    assert result == []
    
    # Slicing on string should return nothing (jq doesn't support string slicing)
    result = list(get_path("hello", ".[1:3]"))
    assert result == []
    
    # Slicing on number should return nothing
    result = list(get_path(42, ".[1:3]"))
    assert result == []


def test_nested_slicing():
    """Test slicing with nested data structures."""
    data = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12]
    ]
    
    # Test .[1:3] - should return middle two sub-arrays
    result = list(get_path(data, ".[1:3]"))
    assert result == [[[5, 6, 7, 8], [9, 10, 11, 12]]]
    
    # Test .[1:3][][1:3] - slice each sub-array
    result = list(get_path(data, ".[1:3][][1:3]"))
    assert result == [[6, 7], [10, 11]]


def test_slicing_with_negative_indices():
    """Test slicing with negative indices."""
    data = [1, 2, 3, 4, 5]
    
    # Test [:-2] - all but last two
    result = list(get_path(data, ".[:-2]"))
    assert result == [[1, 2, 3]]
    
    # Test [-3:-1] - slice from third-to-last to second-to-last
    result = list(get_path(data, ".[-3:-1]"))
    assert result == [[3, 4]]


def test_slice_batch_operations():
    """Test slicing with batch operations."""
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    
    # Test batch_get_path
    result = batch_get_path(data, ".[1:4]")
    assert result == [[2, 3, 4]]
    
    # Test first_path_match
    result = first_path_match(data, ".[2:5]")
    assert result == [3, 4, 5]


def test_complex_slicing_scenarios():
    """Test complex slicing scenarios with real-world data."""
    data = {
        "users": [
            {"id": 1, "name": "Alice", "scores": [85, 90, 88]},
            {"id": 2, "name": "Bob", "scores": [92, 87, 95]},
            {"id": 3, "name": "Charlie", "scores": [78, 82, 85]},
            {"id": 4, "name": "Diana", "scores": [96, 94, 92]}
        ]
    }
    
    # Get middle two users
    result = list(get_path(data, ".users[1:3]"))
    assert len(result) == 1
    assert len(result[0]) == 2
    assert result[0][0]["name"] == "Bob"
    assert result[0][1]["name"] == "Charlie"
    
    # Get names of middle two users
    result = list(get_path(data, ".users[1:3][].name"))
    assert result == ["Bob", "Charlie"]
    
    # Get first two scores of each user
    result = list(get_path(data, ".users[].scores[:2]"))
    assert result == [
        [85, 90],
        [92, 87], 
        [78, 82],
        [96, 94]
    ]
    
    # Get last two users, then their first score
    result = list(get_path(data, ".users[-2:][].scores[0]"))
    assert result == [78, 96]


def test_slice_error_handling():
    """Test error handling for invalid slice syntax."""
    # Invalid slice with too many colons should raise error
    with pytest.raises(ValueError, match="Invalid slice syntax"):
        parse_path(".[1:2:3]")
    
    # Invalid slice with non-numeric values should raise error
    with pytest.raises(ValueError):
        parse_path(".[a:b]")


def test_slice_with_string_data():
    """Test that slicing doesn't work on strings (following jq behavior)."""
    data = "hello world"
    
    # jq doesn't support string slicing, so we shouldn't either
    result = list(get_path(data, ".[1:3]"))
    assert result == []


def test_slice_jq_compatibility():
    """Test that our slicing behavior matches jq exactly."""
    test_cases = [
        ([1, 2, 3, 4, 5], ".[1:3]", [2, 3]),
        ([1, 2, 3, 4, 5], ".[2:]", [3, 4, 5]),
        ([1, 2, 3, 4, 5], ".[:3]", [1, 2, 3]),
        ([1, 2, 3, 4, 5], ".[-2:]", [4, 5]),
        ([1, 2, 3, 4, 5], ".[:-2]", [1, 2, 3]),
        ([1, 2, 3, 4, 5], ".[-3:-1]", [3, 4]),
    ]
    
    for data, path, expected in test_cases:
        result = list(get_path(data, path))
        assert result == [expected], f"Path {path} on {data} should return {expected}, got {result}"


def test_slice_set_operations():
    """Test setting values using slice operations."""
    data = [1, 2, 3, 4, 5]
    
    # Test setting a slice with a list
    result = list(set_path(data, ".[1:3]", [10, 20]))[0]
    assert result == [1, 10, 20, 4, 5]
    
    # Test setting a slice with a single value
    data = [1, 2, 3, 4, 5]
    result = list(set_path(data, ".[1:3]", 99))[0]
    assert result == [1, 99, 4, 5]
    
    # Test setting a slice to empty (deletes elements)
    data = [1, 2, 3, 4, 5]
    result = list(set_path(data, ".[1:3]", []))[0]
    assert result == [1, 4, 5]
    
    # Test setting slice with longer replacement
    data = [1, 2, 3, 4, 5]
    result = list(set_path(data, ".[1:3]", [10, 20, 30, 40]))[0]
    assert result == [1, 10, 20, 30, 40, 4, 5]


def test_slice_delete_operations():
    """Test deleting values using slice operations."""
    data = [1, 2, 3, 4, 5]
    
    # Test deleting a slice
    result = list(delete_path(data, ".[1:3]"))[0]
    assert result == [1, 4, 5]
    
    # Test deleting from start
    data = [1, 2, 3, 4, 5]
    result = list(delete_path(data, ".[:2]"))[0]
    assert result == [3, 4, 5]
    
    # Test deleting from end
    data = [1, 2, 3, 4, 5]
    result = list(delete_path(data, ".[-2:]"))[0]
    assert result == [1, 2, 3]


def test_slice_error_handling_in_operations():
    """Test error handling for slice operations."""
    # Test setting slice on non-list returns empty result (no matching paths)
    data = {"key": "value"}
    result = list(set_path(data, ".[1:3]", [1, 2]))
    assert result == []  # No paths match, so no results
    
    # Test deleting slice on non-list returns empty result
    data = {"key": "value"}
    result = list(delete_path(data, ".[1:3]"))
    assert result == []  # No paths match, so no results


if __name__ == "__main__":
    pytest.main([__file__])