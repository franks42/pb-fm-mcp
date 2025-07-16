"""Tests for optional selector functionality ([]? and [index]?)."""

import pytest
from src.jqpy import get_path


class TestOptionalSelector:
    """Test cases for optional selector functionality."""
    
    def test_optional_wildcard_existing_array(self):
        """Test []? with existing array."""
        data = {'items': [1, 2, 3]}
        result = list(get_path(data, '.items[]?'))
        assert result == [1, 2, 3]
    
    def test_optional_wildcard_missing_field(self):
        """Test []? with missing field."""
        data = {'notitems': 123}
        result = list(get_path(data, '.items[]?'))
        assert result == []
    
    def test_optional_wildcard_null_value(self):
        """Test []? with null value."""
        data = {'items': None}
        result = list(get_path(data, '.items[]?'))
        assert result == []
    
    def test_optional_wildcard_non_array(self):
        """Test []? with non-array value."""
        data = {'items': 'not_an_array'}
        result = list(get_path(data, '.items[]?'))
        assert result == []
    
    def test_optional_index_existing_element(self):
        """Test [index]? with existing element."""
        data = {'items': [1, 2, 3]}
        result = list(get_path(data, '.items[0]?'))
        assert result == [1]
    
    def test_optional_index_out_of_bounds(self):
        """Test [index]? with out of bounds index."""
        data = {'items': [1, 2, 3]}
        result = list(get_path(data, '.items[5]?'))
        assert result == [None]
    
    def test_optional_index_negative_out_of_bounds(self):
        """Test [index]? with negative out of bounds index."""
        data = {'items': [1, 2, 3]}
        result = list(get_path(data, '.items[-5]?'))
        assert result == [None]
    
    def test_optional_index_missing_field(self):
        """Test [index]? with missing field."""
        data = {'notitems': 123}
        result = list(get_path(data, '.items[0]?'))
        assert result == [None]
    
    def test_optional_index_null_value(self):
        """Test [index]? with null value."""
        data = {'items': None}
        result = list(get_path(data, '.items[0]?'))
        assert result == [None]
    
    def test_optional_index_non_array(self):
        """Test [index]? with non-array value."""
        data = {'items': 'not_an_array'}
        result = list(get_path(data, '.items[0]?'))
        assert result == []
    
    def test_optional_wildcard_dict(self):
        """Test []? with dictionary."""
        data = {'items': {'a': 1, 'b': 2}}
        result = list(get_path(data, '.items[]?'))
        assert sorted(result) == [1, 2]
    
    def test_optional_index_negative_valid(self):
        """Test [index]? with valid negative index."""
        data = {'items': [1, 2, 3]}
        result = list(get_path(data, '.items[-1]?'))
        assert result == [3]
    
    def test_optional_chained_access(self):
        """Test chaining optional selectors."""
        data = {'users': [{'profile': {'name': 'John'}}, {'profile': None}]}
        result = list(get_path(data, '.users[]?.profile.name'))
        assert result == ['John']
    
    def test_optional_vs_regular_selector_error_handling(self):
        """Test that optional selectors don't raise errors while regular ones do."""
        data = {'items': 'not_an_array'}
        
        # Regular selector should produce no results but not error
        regular_result = list(get_path(data, '.items[]'))
        assert regular_result == []
        
        # Optional selector should also produce no results
        optional_result = list(get_path(data, '.items[]?'))
        assert optional_result == []
    
    def test_optional_index_with_continuation(self):
        """Test optional index with more path components."""
        data = {'items': [{'name': 'John'}, {'name': 'Jane'}]}
        
        # Valid index with continuation
        result1 = list(get_path(data, '.items[0]?.name'))
        assert result1 == ['John']
        
        # Out of bounds index with continuation
        result2 = list(get_path(data, '.items[5]?.name'))
        assert result2 == []  # No continuation since we got null
    
    def test_optional_empty_array(self):
        """Test optional selectors with empty array."""
        data = {'items': []}
        
        # []? on empty array
        result1 = list(get_path(data, '.items[]?'))
        assert result1 == []
        
        # [0]? on empty array  
        result2 = list(get_path(data, '.items[0]?'))
        assert result2 == [None]


class TestOptionalSelectorEdgeCases:
    """Test edge cases for optional selectors."""
    
    def test_multiple_optional_selectors(self):
        """Test multiple optional selectors in one path."""
        data = {'a': {'b': [{'c': 1}, {'c': 2}]}}
        result = list(get_path(data, '.a?.b[]?.c'))
        assert sorted(result) == [1, 2]
    
    def test_optional_with_missing_intermediate(self):
        """Test optional selector with missing intermediate path."""
        data = {'a': None}
        result = list(get_path(data, '.a?.b[]?'))
        assert result == []
    
    def test_root_optional_access(self):
        """Test optional access at root level."""
        data = [1, 2, 3]
        result = list(get_path(data, '[]?'))
        assert result == [1, 2, 3]
    
    def test_root_optional_index(self):
        """Test optional index at root level."""
        data = [1, 2, 3]
        result = list(get_path(data, '[0]?'))
        assert result == [1]
        
        result2 = list(get_path(data, '[5]?'))
        assert result2 == [None]