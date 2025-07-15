""Tests for the core traversal functionality."""
import pytest
from src.jqpy import get_path, batch_get_path, has_path, first_path_match

def test_get_path_basic():
    data = {
        'a': {
            'b': [
                {'c': 1},
                {'c': 2},
                {'d': 3}
            ]
        }
    }
    
    # Test basic path
    assert list(get_path(data, 'a.b')) == [data['a']['b']]
    
    # Test wildcard
    assert list(get_path(data, 'a.b.*.c')) == [1, 2]
    
    # Test only first match
    assert list(get_path(data, 'a.b.*.c', only_first_path_match=True)) == [1]

def test_batch_get_path():
    data = {'a': [{'b': 1}, {'b': 2}]}
    
    # Test getting all matches
    assert batch_get_path(data, 'a.*.b') == [1, 2]
    
    # Test default value
    assert batch_get_path(data, 'x.y.z', default='not found') == ['not found']
    
    # Test only first match
    assert batch_get_path(data, 'a.*.b', only_first_path_match=True) == [1]

def test_has_path():
    data = {'a': {'b': 1}}
    
    assert has_path(data, 'a.b') is True
    assert has_path(data, 'a.c') is False
    assert has_path(data, 'a.*') is True  # Wildcard match

def test_first_path_match():
    data = {'items': [{'id': 1}, {'id': 2}]}
    
    assert first_path_match(data, 'items.*.id') == 1
    assert first_path_match(data, 'nonexistent', default=0) == 0
