"""
Tests for resolve_to_atomic_paths() function - resolving complex paths to atomic components.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.jqpy import resolve_to_atomic_paths, get_path


def test_resolve_simple_object():
    """Test resolving paths on a simple object."""
    data = {"name": "john", "age": 30, "active": True}
    
    # Resolve root object
    result = list(resolve_to_atomic_paths(data, "."))
    expected = ["name", "age", "active"]
    assert sorted(result) == sorted(expected)


def test_resolve_nested_object():
    """Test resolving paths on nested objects."""
    data = {
        "user": {
            "name": "john",
            "details": {
                "age": 30,
                "city": "NYC"
            }
        }
    }
    
    # Resolve nested object
    result = list(resolve_to_atomic_paths(data, "user"))
    expected = ["user.name", "user.details.age", "user.details.city"]
    assert sorted(result) == sorted(expected)


def test_resolve_array_wildcard():
    """Test resolving paths with array wildcard."""
    data = {
        "users": [
            {"name": "john", "age": 30},
            {"name": "jane", "age": 25}
        ]
    }
    
    # Resolve array wildcard
    result = list(resolve_to_atomic_paths(data, "users[]"))
    expected = [
        "users[0].name", "users[0].age",
        "users[1].name", "users[1].age"
    ]
    assert sorted(result) == sorted(expected)


def test_resolve_mixed_containers():
    """Test resolving paths with mixed containers."""
    data = {
        "items": [
            {"name": "item1", "tags": ["tag1", "tag2"]},
            {"name": "item2", "tags": ["tag3"]}
        ]
    }
    
    # Resolve array wildcard
    result = list(resolve_to_atomic_paths(data, "items[]"))
    expected = [
        "items[0].name", "items[0].tags[0]", "items[0].tags[1]",
        "items[1].name", "items[1].tags[0]"
    ]
    assert sorted(result) == sorted(expected)


def test_resolve_already_atomic():
    """Test resolving when path already leads to atomic values."""
    data = {"name": "john", "age": 30}
    
    # Path that already leads to atomic value
    result = list(resolve_to_atomic_paths(data, "name"))
    assert result == ["name"]
    
    # Path that already leads to atomic value
    result = list(resolve_to_atomic_paths(data, "age"))
    assert result == ["age"]


def test_resolve_primitive_array():
    """Test resolving paths on primitive arrays."""
    data = {"numbers": [1, 2, 3, 4, 5]}
    
    # Resolve array wildcard on primitives
    result = list(resolve_to_atomic_paths(data, "numbers[]"))
    expected = ["numbers[0]", "numbers[1]", "numbers[2]", "numbers[3]", "numbers[4]"]
    assert result == expected


def test_resolve_empty_containers():
    """Test resolving paths on empty containers."""
    data = {"empty_obj": {}, "empty_arr": []}
    
    # Resolve empty object
    result = list(resolve_to_atomic_paths(data, "empty_obj"))
    assert result == []
    
    # Resolve empty array
    result = list(resolve_to_atomic_paths(data, "empty_arr"))
    assert result == []


def test_resolve_deep_nesting():
    """Test resolving paths with deep nesting."""
    data = {
        "level1": {
            "level2": {
                "level3": {
                    "value": "deep",
                    "array": [1, 2, 3]
                }
            }
        }
    }
    
    result = list(resolve_to_atomic_paths(data, "level1.level2"))
    expected = [
        "level1.level2.level3.value",
        "level1.level2.level3.array[0]",
        "level1.level2.level3.array[1]",
        "level1.level2.level3.array[2]"
    ]
    assert sorted(result) == sorted(expected)


def test_resolve_specific_index():
    """Test resolving paths with specific array indices."""
    data = {
        "users": [
            {"name": "john", "age": 30},
            {"name": "jane", "age": 25}
        ]
    }
    
    # Resolve specific index
    result = list(resolve_to_atomic_paths(data, "users[0]"))
    expected = ["users[0].name", "users[0].age"]
    assert sorted(result) == sorted(expected)


def test_resolve_object_wildcard():
    """Test resolving paths with object wildcard."""
    data = {
        "users": {
            "john": {"age": 30, "city": "NYC"},
            "jane": {"age": 25, "city": "LA"}
        }
    }
    
    # Resolve object wildcard  
    result = list(resolve_to_atomic_paths(data, "users.*"))
    expected = [
        "users.john.age", "users.john.city",
        "users.jane.age", "users.jane.city"
    ]
    assert sorted(result) == sorted(expected)


def test_resolve_mixed_types():
    """Test resolving paths with mixed data types."""
    data = {
        "string": "hello",
        "number": 42,
        "boolean": True,
        "null_value": None,
        "array": [1, "two", {"three": 3}],
        "object": {"nested": "value"}
    }
    
    result = list(resolve_to_atomic_paths(data, "."))
    expected = [
        "string", "number", "boolean", "null_value",
        "array[0]", "array[1]", "array[2].three",
        "object.nested"
    ]
    assert sorted(result) == sorted(expected)


def test_resolve_nonexistent_path():
    """Test resolving nonexistent paths."""
    data = {"name": "john"}
    
    # Nonexistent key
    result = list(resolve_to_atomic_paths(data, "missing"))
    assert result == []
    
    # Nonexistent array index
    result = list(resolve_to_atomic_paths(data, "name[0]"))
    assert result == []


def test_resolve_complex_example():
    """Test resolving paths on a complex realistic example."""
    data = {
        "company": {
            "name": "TechCorp",
            "employees": [
                {
                    "name": "john",
                    "roles": ["developer", "manager"],
                    "details": {"age": 30, "salary": 75000}
                },
                {
                    "name": "jane", 
                    "roles": ["designer"],
                    "details": {"age": 25, "salary": 65000}
                }
            ]
        }
    }
    
    result = list(resolve_to_atomic_paths(data, "company.employees[]"))
    expected = [
        "company.employees[0].name",
        "company.employees[0].roles[0]",
        "company.employees[0].roles[1]", 
        "company.employees[0].details.age",
        "company.employees[0].details.salary",
        "company.employees[1].name",
        "company.employees[1].roles[0]",
        "company.employees[1].details.age",
        "company.employees[1].details.salary"
    ]
    assert sorted(result) == sorted(expected)


def test_resolve_array_slicing():
    """Test resolving paths with array slicing support."""
    data = {
        "items": [
            {"name": "item1", "value": 10},
            {"name": "item2", "value": 20},
            {"name": "item3", "value": 30},
            {"name": "item4", "value": 40}
        ]
    }
    
    # Test basic slicing
    result = list(resolve_to_atomic_paths(data, "items[1:3]"))
    expected = [
        "items[1].name", "items[1].value",
        "items[2].name", "items[2].value"
    ]
    assert sorted(result) == sorted(expected)
    
    # Test open-ended slicing  
    result = list(resolve_to_atomic_paths(data, "items[2:]"))
    expected = [
        "items[2].name", "items[2].value",
        "items[3].name", "items[3].value"
    ]
    assert sorted(result) == sorted(expected)
    
    # Test from beginning
    result = list(resolve_to_atomic_paths(data, "items[:2]"))
    expected = [
        "items[0].name", "items[0].value",
        "items[1].name", "items[1].value"
    ]
    assert sorted(result) == sorted(expected)


def test_resolve_enhanced_path_support():
    """Test that resolve_to_atomic_paths supports same paths as get_path."""
    data = {
        "users": [
            {"name": "john", "age": 30, "active": True},
            {"name": "jane", "age": 25, "active": False}
        ]
    }
    
    # Test that paths work the same in both functions
    test_paths = [
        "users[]",
        "users[0]", 
        "users[0:1]",
        "users[1:]",
        "users[].name"
    ]
    
    for path in test_paths:
        # Both should work without error
        get_path_results = list(get_path(data, path))
        atomic_path_results = list(resolve_to_atomic_paths(data, path))
        
        # resolve_to_atomic_paths should return paths, not values
        assert all(isinstance(result, str) for result in atomic_path_results)
        print(f"Path '{path}' -> {len(atomic_path_results)} atomic paths")


if __name__ == "__main__":
    pytest.main([__file__])