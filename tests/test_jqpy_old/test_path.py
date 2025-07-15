"""Tests for jqpy.path module."""

import pytest
from jqpy.path import get_path, set_path, has_path


def test_set_path_simple_dict():
    data = {"a": 1, "b": 2}
    result = set_path(data, "a", 10)
    assert result == {"a": 10, "b": 2}
    # Original should not be modified
    assert data == {"a": 1, "b": 2}


def test_set_path_nested_dict():
    data = {"a": {"b": 1, "c": 2}}
    result = set_path(data, "a.b", 10)
    assert result == {"a": {"b": 10, "c": 2}}


def test_set_path_create_missing():
    data = {}
    result = set_path(data, "a.b.c", 10)
    assert result == {"a": {"b": {"c": 10}}}


def test_set_path_array_index():
    data = {"a": [1, 2, 3]}
    result = set_path(data, "a[1]", 20)
    assert result == {"a": [1, 20, 3]}


def test_set_path_array_negative_index():
    data = {"a": [1, 2, 3]}
    result = set_path(data, "a[-1]", 30)
    assert result == {"a": [1, 2, 30]}


def test_set_path_array_out_of_bounds():
    data = {"a": [1, 2, 3]}
    with pytest.raises(IndexError):
        set_path(data, "a[5]", 10)


def test_set_path_mixed_notation():
    data = {"a": [{"b": 1}, {"b": 2}]}
    result = set_path(data, "a[1].b", 20)
    assert result == {"a": [{"b": 1}, {"b": 20}]}


def test_set_path_with_escaped_chars():
    # The path parser doesn't support escaped characters in the path string directly
    # Instead, we need to use bracket notation for keys with special characters
    data = {"a.b": {"c[d]": 1}}
    result = set_path(data, '["a.b"]["c[d]"]', 10)
    assert result == {"a.b": {"c[d]": 10}}


def test_set_path_with_selector():
    data = {"items": [{"id": 1, "value": 10}, {"id": 2, "value": 20}]}
    # Selector support is not implemented yet, so we expect a ValueError
    with pytest.raises(ValueError, match="Cannot set value with wildcard selector"):
        set_path(data, "items[].value", 100)
