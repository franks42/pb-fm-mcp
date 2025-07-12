#!/usr/bin/env python3
"""
Test Suite for jqpath: jq-style Path Manipulation Utilities for Python
=====================================================================

This test suite validates the correctness and jq-style semantics of the path manipulation functions in jqpath.py.
It covers getpath, setpath, delpath, delpaths, haspath, findpaths, findvalues, batch_setpath, flatten, unflatten, and merge,
ensuring compatibility with Cloudflare Python Workers and robust handling of nested dict/list structures.

Run this file to validate the jqpath module:
python -m pytest tests/test_jqpath.py
"""


import json
import re
from functools import reduce
import time
from collections.abc import Iterator
import pytest

# Import the tested functions from jqpath
from jqpath import (
    setpath,
    getpath,
    haspath,
    findpaths,
    findvalues,
    getpaths,
    getpaths_setpaths,
    selectorspaths,
    delpath,
    delpaths,
    batch_setpath,
    flatten,
    unflatten,
    merge,
    select_key_exists,
    select_key_missing,
    select_type,
    select_regex,
    select_gt,
    select_lt,
    select_eq,
    select_contains,
    select_all,
)

# === TEST DATA ===

@pytest.fixture
def test_data():
    return {
        'user': {
            'profile': {
                'name': 'John Doe',
                'age': 30,
                'email': 'john@example.com',
                'user_id': 12345
            },
            'settings': {
                'theme': 'dark',
                'notifications': True,
                'language': 'en'
            }
        },
        'items': [
            {'id': 1, 'name': 'Item 1', 'tags': ['A', 'B'], 'active': True},
            {'id': 2, 'name': 'Item 2', 'tags': ['C', 'D'], 'active': False},
            {'id': 3, 'name': 'Item 3', 'tags': ['A', 'E'], 'active': True},
            {'id': 4, 'name': 'Another Item', 'tags': ['A', 'E'], 'active': False}
        ],
        'metadata': {
            'source': 'test-suite',
            'version': '1.0.0',
            'timestamp': '2023-10-27T10:00:00Z'
        },
        'status': 'ok',
        'is_validated': True,
        'empty_list': [],
        'null_value': None
    }

# === GETPATH TESTS ===

def test_get_simple_path(test_data):
    assert getpath(test_data, 'user.profile.name') == 'John Doe'

def test_get_with_list_index(test_data):
    assert getpath(test_data, 'items.1.name') == 'Item 2'

def test_get_with_list_path(test_data):
    assert getpath(test_data, ['items', 1, 'name']) == 'Item 2'

def test_get_nonexistent_path(test_data):
    assert getpath(test_data, 'user.profile.address') is None

def test_get_with_default_value(test_data):
    assert getpath(test_data, 'user.profile.address', default='N/A') == 'N/A'

# === GETPATH WITH SELECTOR TESTS ===

def test_getpath_with_selector_single_match(test_data):
    """Test getpath with a selector that finds a single unique item."""
    path = ['items', select_eq('id', 3)]
    result = getpath(test_data, path)
    assert result is not None
    assert result['name'] == 'Item 3'

def test_getpath_with_selector_first_of_many(test_data):
    """Test getpath with a selector that matches multiple items, returning only the first."""
    path = ['items', select_key_exists('active')] # Matches all four items
    result = getpath(test_data, path) # only_first_path_match is True by default
    assert result is not None
    assert result['id'] == 1 # Should return the first item

def test_getpath_with_selector_all_matches(test_data):
    """Test getpath with a selector, returning all matching items."""
    path = ['items', select_type(dict)] # Matches all dicts in the 'items' list
    result = getpath(test_data, path, only_first_path_match=False)
    assert isinstance(result, list)
    assert len(result) == 4
    assert result[0]['id'] == 1
    assert result[3]['id'] == 4

def test_getpath_with_selector_no_match(test_data):
    """Test getpath with a selector that finds no matches."""
    path = ['items', select_eq('id', 999)]
    result = getpath(test_data, path, default='Not Found')
    assert result == 'Not Found'

def test_getpath_with_callable_selector(test_data):
    """Test getpath with a raw callable selector."""
    path = ['items', lambda k, v: isinstance(v, dict) and v.get('id') == 4]
    result = getpath(test_data, path)
    assert result is not None
    assert result['name'] == 'Another Item'

# === SETPATH TESTS ===

def test_set_simple_path():
    data = {}
    setpath(data, 'a.b.c', 100)
    assert data == {'a': {'b': {'c': 100}}}

def test_set_with_list_creation():
    data = {}
    setpath(data, 'a.0.b', 'test')
    assert data == {'a': [{'b': 'test'}]}

def test_set_existing_path():
    data = {'a': {'b': 1}}
    setpath(data, 'a.b', 2)
    assert data['a']['b'] == 2

def test_set_with_append():
    data = {'a': [1]}
    setpath(data, 'a', 2, operation='append')
    assert data['a'] == [1, 2]

def test_set_with_extend():
    data = {'a': [1, 2]}
    setpath(data, 'a', [3, 4], operation='extend')
    assert data == {'a': [1, 2, 3, 4]}

def test_setpath_append_operation():
    data = {"items": [{"id": 1, "tags": ["a"]}]}
    setpath(data, "items.0.tags", "b", operation="append")
    assert data["items"][0]["tags"] == ["a", "b"]

# === DELPATH/DELPATHS TESTS ===

def test_delpath_simple():
    data = {'a': {'b': 1, 'c': 2}}
    delpath(data, 'a.b')
    assert data == {'a': {'c': 2}}

def test_delpath_list_item():
    data = {'a': [1, 2, 3]}
    delpath(data, 'a.1')
    assert data == {'a': [1, 3]}

def test_delpaths_multiple():
    data = {'a': 1, 'b': 2, 'c': 3}
    delpaths(data, ['a', 'c'])
    assert data == {'b': 2}

def test_delpath_nonexistent():
    data = {'a': {'b': 1}}
    original_data = data.copy()
    # Should not raise an error
    delpath(data, 'a.c')
    assert data == original_data

# === HASPATH TESTS ===

def test_haspath_existing(test_data):
    assert haspath(test_data, 'user.profile.name') is True

def test_haspath_nonexistent(test_data):
    assert haspath(test_data, 'user.profile.address') is False

# === FINDPATHS/FINDVALUES TESTS ===

def test_findpaths_key_contains(test_data):
    paths = list(findpaths(test_data, 'name', 'contains'))
    assert len(paths) == 5

def test_findvalues(test_data):
    # Explicitly search for values only, not keys, to get the correct count.
    values = list(findvalues(test_data, True, 'exact'))
    assert len(values) == 4

# === BATCH_SETPATH TESTS ===

def test_batch_setpath_mixed_ops():
    data = {'user': {'name': 'Old Name'}, 'items': [1]}
    modifications = [
        ('user.name', 'New Name', 'set'),
        ('items', 2, 'append'),
        ('user.status', 'active', 'set')
    ]
    batch_setpath(data, modifications)
    assert data['user']['name'] == 'New Name'
    assert data['items'] == [1, 2]
    assert data['user']['status'] == 'active'

# === FLATTEN/UNFLATTEN TESTS ===

def test_flatten_unflatten_cycle():
    original = {'a': {'b': 1}, 'c': [2, 3]}
    flattened = flatten(original)
    unflattened = unflatten(flattened)
    assert original == unflattened

def test_flatten_unflatten_empty_dict():
    original = {}
    flattened = flatten(original)
    assert flattened == {}
    unflattened = unflatten(flattened)
    assert unflattened == {}

def test_flatten_unflatten_nested_lists():
    original = {'a': [1, [2, 3]], 'b': [{'c': 4}, {'d': 5}]}
    flattened = flatten(original)
    expected_flattened = {'a.0': 1, 'a.1.0': 2, 'a.1.1': 3, 'b.0.c': 4, 'b.1.d': 5}
    assert flattened == expected_flattened
    unflattened = unflatten(flattened)
    assert unflattened == original

# === MERGE TESTS ===

def test_merge_simple():
    d1 = {'a': 1, 'b': {'c': 2}}
    d2 = {'b': {'d': 3}, 'e': 4}
    merged = merge(d1, d2)
    assert merged == {'a': 1, 'b': {'c': 2, 'd': 3}, 'e': 4}

# === ADVANCED SELECTOR TESTS ===

def test_callable_selector(test_data):
    # Select items where the name contains 'Item'
    path = ['items', lambda k, v: isinstance(v, dict) and 'Item' in v.get('name', '')]
    paths = list(selectorspaths(test_data, path))
    assert len(paths) == 4

def test_callable_selector_with_currying(test_data):
    """Tests using a factory to create a selector with a captured variable."""
    def create_id_gt_selector(min_id):
        # This factory returns the actual selector function
        def selector(key, value):
            return isinstance(value, dict) and value.get('id', 0) > min_id
        return selector

    # Create a selector for items with id > 2
    id_gt_2_selector = create_id_gt_selector(2)

    path = ['items', id_gt_2_selector]
    paths = list(selectorspaths(test_data, path))
    
    assert len(paths) == 2
    assert paths[0] == ['items', 2] # Corresponds to Item 3 (id=3)
    assert paths[1] == ['items', 3] # Corresponds to Another Item (id=4)

def test_dict_selector(test_data):
    path = ['items', {'id': 3, 'active': True}]
    assert getpath(test_data, path)['name'] == 'Item 3'

def test_get_with_slice_selector(test_data):
    # Select the first two items from the list using a slice selector
    path_with_selector = ['items', slice(0, 2)]
    
    # selectorspaths should resolve the slice into concrete paths
    concrete_paths = list(selectorspaths(test_data, path_with_selector))
    assert concrete_paths == [['items', 0], ['items', 1]]

    # Now, get the values for these paths
    values = [getpath(test_data, p) for p in concrete_paths]
    assert len(values) == 2
    assert values[0]['name'] == 'Item 1'
    assert values[1]['name'] == 'Item 2'

def test_selectorspaths_multiple_matches(test_data):
    paths = list(selectorspaths(test_data, ['items', {'active': True}]))
    assert len(paths) == 2
    assert paths[0] == ['items', 0]
    assert paths[1] == ['items', 2]

def test_setpath_with_selector(test_data):
    data = json.loads(json.dumps(test_data))
    setpath(data, ['items', {'id': 2}], {'id': 2, 'name': 'Item 2 Updated', 'tags': ['C', 'D'], 'active': False})
    assert getpath(data, 'items.1.name') == 'Item 2 Updated'

def test_delpath_with_selector(test_data):
    data = json.loads(json.dumps(test_data))
    delpath(data, ['items', {'id': 2}])
    assert len(data['items']) == 3
    assert getpath(data, 'items.1.name') == 'Item 3'

# === PORTED SELECTOR TESTS ===

def test_select_regex(test_data):
    # Find the user profile where the email ends with @example.com
    path = ['user', select_regex('email', r'.+@example\.com')]
    result = getpath(test_data, path)
    assert result is not None
    assert result['name'] == 'John Doe'

    # Test for a non-matching pattern
    path_no_match = ['user', select_regex('email', r'.+@another-domain\.com')]
    result_no_match = getpath(test_data, path_no_match)
    assert result_no_match is None

def test_ported_selectors(test_data):
    path = ['items', select_eq('id', 2)]
    assert getpath(test_data, path)['name'] == 'Item 2'
    path = ['items', select_gt('id', 2)]
    assert getpath(test_data, path)['name'] == 'Item 3'
    path = ['items', select_lt('id', 2)]
    assert getpath(test_data, path)['name'] == 'Item 1'
    path = ['items', select_key_exists('active')]
    assert getpath(test_data, path)['id'] == 1
    all_items = list(selectorspaths(test_data, ['items', select_all]))
    assert len(all_items) == 4
    assert all_items[0] == ['items', 0]

# === ITERATOR TESTS ===

def test_iterator_behavior(test_data):
    paths_gen = findpaths(test_data, 'name', 'contains')
    assert isinstance(paths_gen, Iterator)
    paths_list = list(paths_gen)
    assert len(paths_list) == 5

# === UTILITY FUNCTION TESTS ===

def test_getpaths_setpaths():
    src = {
        'user': {'name': 'John', 'details': {'age': 30}},
        'product': {'id': 123, 'price': 99.99}
    }
    tgt = {}
    paths_map = [
        ('user.name', 'customer.name'),
        ('user.details.age', 'customer.age'),
        ('product.id', 'item.product_id')
    ]
    getpaths_setpaths(src, tgt, paths_map)
    expected = {
        'customer': {'name': 'John', 'age': 30},
        'item': {'product_id': 123}
    }
    assert tgt == expected
