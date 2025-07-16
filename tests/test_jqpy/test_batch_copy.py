"""
Tests for batch and copy path operations: copy_path, batch_getpaths.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.jqpy import (
    copy_path, copy_path_simple, 
    batch_getpaths,
    get_path, set_path_simple
)


def test_copy_path_basic():
    """Test basic copy_path functionality."""
    src_data = {"name": "john", "age": 30}
    tgt_data = {"city": "NYC"}
    
    # Copy name from source to target
    results = list(copy_path(src_data, tgt_data, "name", "username"))
    assert len(results) == 1
    result = results[0]
    assert result["city"] == "NYC"
    assert result["username"] == "john"
    
    # Original data should be unchanged
    assert "username" not in tgt_data
    assert src_data == {"name": "john", "age": 30}


def test_copy_path_simple():
    """Test copy_path_simple convenience function."""
    src_data = {"user": {"name": "john", "details": {"age": 30}}}
    tgt_data = {"info": {}}
    
    # Copy nested value
    result = copy_path_simple(src_data, tgt_data, "user.details.age", "info.years")
    assert result["info"]["years"] == 30
    assert result["info"] == {"years": 30}


def test_copy_path_with_default():
    """Test copy_path with default value when source path doesn't exist."""
    src_data = {"name": "john"}
    tgt_data = {"city": "NYC"}
    
    # Copy missing path with default
    result = copy_path_simple(src_data, tgt_data, "missing", "fallback", default="unknown")
    assert result["fallback"] == "unknown"
    assert result["city"] == "NYC"


def test_copy_path_missing_no_default():
    """Test copy_path when source path doesn't exist and no default."""
    src_data = {"name": "john"}
    tgt_data = {"city": "NYC"}
    
    # Copy missing path without default - should return original target
    result = copy_path_simple(src_data, tgt_data, "missing", "fallback")
    assert result == {"city": "NYC"}
    assert "fallback" not in result


def test_copy_path_array_operations():
    """Test copy_path with array operations."""
    src_data = {"items": [1, 2, 3, 4]}
    tgt_data = {"results": []}
    
    # Copy array element
    result = copy_path_simple(src_data, tgt_data, "items[1]", "results[0]")
    assert result["results"][0] == 2
    
    # Copy entire array
    result = copy_path_simple(src_data, tgt_data, "items", "all_items")
    assert result["all_items"] == [1, 2, 3, 4]


def test_copy_path_multiple_matches():
    """Test copy_path with only_first_match=False."""
    src_data = {"users": [{"name": "john"}, {"name": "jane"}]}
    tgt_data = {"names": []}
    
    # Copy with only_first_match=True (default)
    result = copy_path_simple(src_data, tgt_data, "users[].name", "first_name", only_first_match=True)
    assert result["first_name"] == "john"
    
    # Copy with only_first_match=False (accumulate all values, last one wins)
    results = list(copy_path(src_data, tgt_data, "users[].name", "final_name", only_first_match=False))
    # Should get exactly one result with the last value (jane overwrites john)
    assert len(results) == 1
    assert results[0]["final_name"] == "jane"  # Last value wins


def test_batch_getpaths():
    """Test batch_getpaths functionality."""
    data = {
        "user": {"name": "john", "age": 30},
        "items": [1, 2, 3],
        "status": "active"
    }
    
    paths = ["user.name", "user.age", "items[1]", "status"]
    results = batch_getpaths(data, paths)
    
    assert results == ["john", 30, 2, "active"]


def test_batch_getpaths_with_missing():
    """Test batch_getpaths with missing paths and defaults."""
    data = {"name": "john", "age": 30}
    
    paths = ["name", "missing", "age"]
    results = batch_getpaths(data, paths, default="N/A")
    
    assert results == ["john", "N/A", 30]


def test_batch_getpaths_empty():
    """Test batch_getpaths with empty path list."""
    data = {"name": "john"}
    
    results = batch_getpaths(data, [])
    assert results == []



def test_copy_path_deep_structures():
    """Test copy operations with deeply nested structures."""
    src_data = {
        "level1": {
            "level2": {
                "level3": {
                    "data": "deep_value"
                }
            }
        }
    }
    tgt_data = {"shallow": "value"}
    
    result = copy_path_simple(
        src_data, tgt_data, 
        "level1.level2.level3.data", 
        "extracted"
    )
    
    assert result["extracted"] == "deep_value"
    assert result["shallow"] == "value"


def test_copy_path_creates_nested_structure():
    """Test that copy_path creates nested target structures as needed."""
    src_data = {"value": 42}
    tgt_data = {}
    
    result = copy_path_simple(src_data, tgt_data, "value", "deep.nested.target")
    
    expected = {
        "deep": {
            "nested": {
                "target": 42
            }
        }
    }
    assert result == expected


def test_copy_with_wildcard_source():
    """Test copy_path with wildcard in source path."""
    src_data = {"users": [{"id": 1}, {"id": 2}, {"id": 3}]}
    tgt_data = {"ids": []}
    
    # Copy first match only (default)
    result = copy_path_simple(src_data, tgt_data, "users[].id", "first_id")
    assert result["first_id"] == 1
    
    # Test multiple matches (accumulative behavior)
    results = list(copy_path(src_data, tgt_data, "users[].id", "current_id", only_first_match=False))
    assert len(results) == 1  # One accumulated result
    assert results[0]["current_id"] == 3  # Last value wins


if __name__ == "__main__":
    pytest.main([__file__])