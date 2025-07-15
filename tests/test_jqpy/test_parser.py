"""Tests for the jqpy parser module."""

import pytest
from jqpy.parser import parse_path, PathComponent, PathComponentType


def test_parse_simple_dot_notation():
    """Test parsing simple dot notation paths."""
    components = parse_path("a.b.c")
    assert components == [
        PathComponent(PathComponentType.KEY, "a", "a"),
        PathComponent(PathComponentType.KEY, "b", "b"),
        PathComponent(PathComponentType.KEY, "c", "c"),
    ]


def test_parse_bracket_notation():
    """Test parsing bracket notation with string keys."""
    components = parse_path('["a"]["b"]["c"]')
    assert components == [
        PathComponent(PathComponentType.KEY, "a", '"a"'),
        PathComponent(PathComponentType.KEY, "b", '"b"'),
        PathComponent(PathComponentType.KEY, "c", '"c"'),
    ]


def test_parse_array_indices():
    """Test parsing array indices."""
    components = parse_path("array[0][-1]")
    assert components == [
        PathComponent(PathComponentType.KEY, "array", "array"),
        PathComponent(PathComponentType.INDEX, 0, '0'),
        PathComponent(PathComponentType.INDEX, -1, '-1'),
    ]


def test_parse_mixed_notation():
    """Test parsing mixed dot and bracket notation."""
    path = 'a.b["c.d"][0]'
    print(f"\nTesting path: {path}")
    components = parse_path(path)
    
    print("\nParsed components:")
    for i, comp in enumerate(components):
        print(f"  {i}: type={comp.type.name}, value={comp.value!r}, raw_value={comp.raw_value!r}")
    
    expected = [
        PathComponent(PathComponentType.KEY, "a", "a"),
        PathComponent(PathComponentType.KEY, "b", "b"),
        # For quoted keys in brackets, raw_value includes the quotes
        PathComponent(PathComponentType.KEY, "c.d", '"c.d"'),
        PathComponent(PathComponentType.INDEX, 0, '0'),
    ]
    
    print("\nExpected components:")
    for i, comp in enumerate(expected):
        print(f"  {i}: type={comp.type.name}, value={comp.value!r}, raw_value={comp.raw_value!r}")
    
    assert components == expected


def test_parse_escaped_dots():
    """Test parsing keys with escaped dots."""
    components = parse_path(r'a\.b\[0\]')
    assert components == [
        PathComponent(PathComponentType.KEY, "a.b[0]", "a.b[0]"),
    ]


def test_parse_selector():
    """Test parsing array selector []."""
    components = parse_path("items[]")
    assert components == [
        PathComponent(PathComponentType.KEY, "items", "items"),
        PathComponent(PathComponentType.SELECT_ALL, None, None),
    ]


if __name__ == "__main__":
    pytest.main()
