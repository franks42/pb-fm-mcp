"""Tests for delete_path and set_path functionality."""

import pytest
from src.jqpy import delete_path, delete_path_simple, set_path, set_path_simple


class TestDeletePath:
    """Test cases for delete_path functions."""
    
    def test_delete_simple_key(self):
        """Test deleting a simple key."""
        data = {'a': 1, 'b': 2, 'c': 3}
        result = delete_path_simple(data, '.a')
        expected = {'b': 2, 'c': 3}
        assert result == expected
    
    def test_delete_nested_key(self):
        """Test deleting a nested key."""
        data = {'a': {'b': {'c': 1, 'd': 2}}, 'e': 3}
        result = delete_path_simple(data, '.a.b.c')
        expected = {'a': {'b': {'d': 2}}, 'e': 3}
        assert result == expected
    
    def test_delete_array_index(self):
        """Test deleting an array index."""
        data = {'items': [1, 2, 3, 4, 5]}
        result = delete_path_simple(data, '.items[2]')
        expected = {'items': [1, 2, 4, 5]}
        assert result == expected
    
    def test_delete_negative_index(self):
        """Test deleting with negative array index."""
        data = {'items': [1, 2, 3, 4, 5]}
        result = delete_path_simple(data, '.items[-1]')
        expected = {'items': [1, 2, 3, 4]}
        assert result == expected
    
    def test_delete_wildcard_iterator(self):
        """Test iterator with wildcard deletion."""
        data = {'users': [{'name': 'John', 'temp': True}, {'name': 'Jane', 'temp': False}]}
        results = list(delete_path(data, '.users[].temp', all_matches=True))
        
        # Should get two results, each with one temp field removed
        assert len(results) == 2
        assert {'users': [{'name': 'John'}, {'name': 'Jane', 'temp': False}]} in results
        assert {'users': [{'name': 'John', 'temp': True}, {'name': 'Jane'}]} in results
    
    def test_delete_nonexistent_key_error(self):
        """Test that deleting nonexistent key raises KeyError."""
        data = {'a': 1, 'b': 2}
        with pytest.raises(KeyError):
            delete_path_simple(data, '.c')
    
    def test_delete_out_of_bounds_error(self):
        """Test that deleting out of bounds index raises KeyError."""
        data = {'items': [1, 2, 3]}
        with pytest.raises(KeyError):
            delete_path_simple(data, '.items[5]')
    
    def test_delete_root_error(self):
        """Test that deleting root raises ValueError."""
        data = {'a': 1}
        with pytest.raises(ValueError, match="Cannot delete root element"):
            delete_path_simple(data, '')
    
    def test_delete_preserves_original(self):
        """Test that delete operations don't modify the original data."""
        original = {'a': 1, 'b': {'c': 2}}
        data = original.copy()
        delete_path_simple(data, '.a')
        
        # Original should be unchanged
        assert data == original
    
    def test_delete_complex_structure(self):
        """Test deleting from a complex nested structure."""
        data = {
            'users': [
                {'id': 1, 'profile': {'name': 'John', 'email': 'john@example.com'}},
                {'id': 2, 'profile': {'name': 'Jane', 'email': 'jane@example.com'}}
            ],
            'settings': {'theme': 'dark', 'notifications': True}
        }
        
        result = delete_path_simple(data, '.users[0].profile.email')
        expected = {
            'users': [
                {'id': 1, 'profile': {'name': 'John'}},
                {'id': 2, 'profile': {'name': 'Jane', 'email': 'jane@example.com'}}
            ],
            'settings': {'theme': 'dark', 'notifications': True}
        }
        assert result == expected


class TestSetPath:
    """Test cases for set_path function."""
    
    def test_set_simple_key(self):
        """Test setting a simple key."""
        data = {'a': 1, 'b': 2}
        result = set_path_simple(data, '.c', 3)
        expected = {'a': 1, 'b': 2, 'c': 3}
        assert result == expected
    
    def test_set_existing_key(self):
        """Test overwriting an existing key."""
        data = {'a': 1, 'b': 2}
        result = set_path_simple(data, '.a', 99)
        expected = {'a': 99, 'b': 2}
        assert result == expected
    
    def test_set_nested_key_create_path(self):
        """Test setting a nested key, creating intermediate objects."""
        data = {'a': 1}
        result = set_path_simple(data, '.b.c.d', 'value')
        expected = {'a': 1, 'b': {'c': {'d': 'value'}}}
        assert result == expected
    
    def test_set_array_index(self):
        """Test setting an array index."""
        data = {'items': [1, 2, 3]}
        result = set_path_simple(data, '.items[1]', 99)
        expected = {'items': [1, 99, 3]}
        assert result == expected
    
    def test_set_array_extend(self):
        """Test setting an array index beyond current length."""
        data = {'items': [1, 2]}
        result = set_path_simple(data, '.items[4]', 'new')
        expected = {'items': [1, 2, None, None, 'new']}
        assert result == expected
    
    def test_set_empty_data(self):
        """Test setting on empty/None data."""
        result = set_path_simple(None, '.a.b', 'value')
        expected = {'a': {'b': 'value'}}
        assert result == expected
    
    def test_set_root_replacement(self):
        """Test setting with empty path replaces root."""
        data = {'a': 1}
        result = set_path_simple(data, '', 'new_root')
        assert result == 'new_root'
    
    def test_set_preserves_original(self):
        """Test that set operations don't modify the original data."""
        original = {'a': 1, 'b': {'c': 2}}
        data = original.copy()
        set_path_simple(data, '.b.d', 3)
        
        # Original should be unchanged  
        assert data == original
    
    def test_set_smart_path_creation_dict_to_array(self):
        """Test smart path creation: dict key followed by array index."""
        data = {}
        result = set_path_simple(data, '.items[2]', 'value')
        expected = {'items': [None, None, 'value']}
        assert result == expected
    
    def test_set_smart_path_creation_array_to_dict(self):
        """Test smart path creation: array index followed by dict key."""
        data = {}
        result = set_path_simple(data, '.users[0].name', 'John')
        expected = {'users': [{'name': 'John'}]}
        assert result == expected
    
    def test_set_smart_path_creation_nested_arrays(self):
        """Test smart path creation: nested arrays."""
        data = {}
        result = set_path_simple(data, '.matrix[1][2]', 42)
        expected = {'matrix': [None, [None, None, 42]]}
        assert result == expected
    
    def test_set_smart_path_creation_complex_mixed(self):
        """Test smart path creation: complex mixed structure."""
        data = {}
        result = set_path_simple(data, '.data[0].items[1].value', 'test')
        expected = {'data': [{'items': [None, {'value': 'test'}]}]}
        assert result == expected
    
    def test_set_wildcard_iterator(self):
        """Test iterator with wildcard setting."""
        data = {'users': [{'name': 'John', 'status': 'old'}, {'name': 'Jane', 'status': 'old'}]}
        results = list(set_path(data, '.users[].status', 'active', all_matches=True))
        
        # Should get two results, each with one status field updated
        assert len(results) == 2
        assert {'users': [{'name': 'John', 'status': 'active'}, {'name': 'Jane', 'status': 'old'}]} in results
        assert {'users': [{'name': 'John', 'status': 'old'}, {'name': 'Jane', 'status': 'active'}]} in results


class TestDeletePathEdgeCases:
    """Test edge cases for delete_path."""
    
    def test_delete_from_empty_dict(self):
        """Test deleting from empty dictionary."""
        data = {}
        with pytest.raises(KeyError):
            delete_path_simple(data, '.a')
    
    def test_delete_from_empty_list(self):
        """Test deleting from empty list."""
        data = {'items': []}
        with pytest.raises(KeyError):
            delete_path_simple(data, '.items[0]')
    
    def test_delete_wildcard_no_matches(self):
        """Test wildcard deletion with no matches."""
        data = {'users': []}
        results = list(delete_path(data, '.users[].name', all_matches=True))
        assert results == []
    
    def test_delete_type_mismatch_error(self):
        """Test type mismatch errors."""
        data = {'a': 'string_not_dict'}
        with pytest.raises(ValueError):
            delete_path_simple(data, '.a.b')