"""
Tests for string and math operations in jqpy.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.jqpy import get_path, parse_path


class TestStringOperations:
    """Test string manipulation functions."""

    def test_split_function(self):
        """Test split() function with various delimiters."""
        data = "hello,world,test"
        
        # Test basic split
        result = list(get_path(data, "split(\",\")"))[0]
        assert result == ["hello", "world", "test"]
        
        # Test split with single quotes
        result = list(get_path(data, "split(',')"))[0]
        assert result == ["hello", "world", "test"]
        
        # Test split with space
        data = "hello world test"
        result = list(get_path(data, "split(\" \")"))[0]
        assert result == ["hello", "world", "test"]
        
        # Test split on non-string should return None
        result = list(get_path(42, "split(\",\")"))
        assert result == [None]

    def test_join_function(self):
        """Test join() function with various delimiters."""
        data = ["hello", "world", "test"]
        
        # Test basic join
        result = list(get_path(data, "join(\",\")"))[0]
        assert result == "hello,world,test"
        
        # Test join with space
        result = list(get_path(data, "join(\" \")"))[0]
        assert result == "hello world test"
        
        # Test join with empty string
        result = list(get_path(data, "join(\"\")"))[0]
        assert result == "helloworldtest"
        
        # Test join with numbers
        data = [1, 2, 3]
        result = list(get_path(data, "join(\"-\")"))[0]
        assert result == "1-2-3"
        
        # Test join on non-list should return None
        result = list(get_path("test", "join(\",\")"))
        assert result == [None]

    def test_startswith_function(self):
        """Test startswith() function."""
        data = "hello world"
        
        # Test positive case
        result = list(get_path(data, "startswith(\"hello\")"))[0]
        assert result is True
        
        # Test negative case
        result = list(get_path(data, "startswith(\"world\")"))[0]
        assert result is False
        
        # Test with single quotes
        result = list(get_path(data, "startswith('hello')"))[0]
        assert result is True
        
        # Test on non-string
        result = list(get_path(42, "startswith(\"4\")"))[0]
        assert result is False

    def test_endswith_function(self):
        """Test endswith() function."""
        data = "hello world"
        
        # Test positive case
        result = list(get_path(data, "endswith(\"world\")"))[0]
        assert result is True
        
        # Test negative case
        result = list(get_path(data, "endswith(\"hello\")"))[0]
        assert result is False
        
        # Test with single quotes
        result = list(get_path(data, "endswith('world')"))[0]
        assert result is True
        
        # Test on non-string
        result = list(get_path(42, "endswith(\"2\")"))[0]
        assert result is False

    def test_contains_function(self):
        """Test contains() function."""
        # Test string contains
        data = "hello world"
        result = list(get_path(data, "contains(\"llo\")"))[0]
        assert result is True
        
        result = list(get_path(data, "contains(\"xyz\")"))[0]
        assert result is False
        
        # Test array contains
        data = [1, 2, 3, "hello"]
        result = list(get_path(data, "contains(\"hello\")"))[0]
        assert result is True
        
        result = list(get_path(data, "contains(\"xyz\")"))[0]
        assert result is False
        
        # Test dict contains (checks values)
        data = {"a": "hello", "b": "world"}
        result = list(get_path(data, "contains(\"hello\")"))[0]
        assert result is True
        
        result = list(get_path(data, "contains(\"xyz\")"))[0]
        assert result is False

    def test_case_functions(self):
        """Test case conversion functions."""
        data = "Hello World"
        
        # Test lowercase
        result = list(get_path(data, "lowercase"))[0]
        assert result == "hello world"
        
        # Test downcase (alias for lowercase)
        result = list(get_path(data, "downcase"))[0]
        assert result == "hello world"
        
        # Test uppercase
        result = list(get_path(data, "uppercase"))[0]
        assert result == "HELLO WORLD"
        
        # Test upcase (alias for uppercase)
        result = list(get_path(data, "upcase"))[0]
        assert result == "HELLO WORLD"
        
        # Test on non-string
        result = list(get_path(42, "lowercase"))
        assert result == [None]

    def test_trim_function(self):
        """Test trim() function."""
        data = "  hello world  "
        
        result = list(get_path(data, "trim"))[0]
        assert result == "hello world"
        
        # Test with tabs and newlines
        data = "\t\nhello world\n\t"
        result = list(get_path(data, "trim"))[0]
        assert result == "hello world"
        
        # Test on non-string
        result = list(get_path(42, "trim"))
        assert result == [None]


class TestMathOperations:
    """Test mathematical functions."""

    def test_add_function(self):
        """Test add() function."""
        # Test numeric addition
        data = [1, 2, 3, 4, 5]
        result = list(get_path(data, "add"))[0]
        assert result == 15
        
        # Test string concatenation
        data = ["hello", " ", "world"]
        result = list(get_path(data, "add"))[0]
        assert result == "hello world"
        
        # Test array concatenation
        data = [[1, 2], [3, 4], [5]]
        result = list(get_path(data, "add"))[0]
        assert result == [1, 2, 3, 4, 5]
        
        # Test empty array
        result = list(get_path([], "add"))[0]
        assert result is None
        
        # Test mixed types (should return None)
        data = [1, "hello", [2, 3]]
        result = list(get_path(data, "add"))[0]
        assert result is None

    def test_min_max_functions(self):
        """Test min() and max() functions."""
        data = [5, 2, 8, 1, 9]
        
        # Test min
        result = list(get_path(data, "min"))[0]
        assert result == 1
        
        # Test max
        result = list(get_path(data, "max"))[0]
        assert result == 9
        
        # Test with floats
        data = [1.5, 2.7, 0.3, 3.14]
        result = list(get_path(data, "min"))[0]
        assert result == 0.3
        
        result = list(get_path(data, "max"))[0]
        assert result == 3.14
        
        # Test empty array
        result = list(get_path([], "min"))[0]
        assert result is None
        
        # Test array with non-numbers (should extract only numbers)
        data = [1, "hello", 5, 2, "world"]
        result = list(get_path(data, "min"))[0]
        assert result == 1
        
        result = list(get_path(data, "max"))[0]
        assert result == 5

    def test_sort_function(self):
        """Test sort() function."""
        # Test numeric sort
        data = [3, 1, 4, 1, 5, 9, 2, 6]
        result = list(get_path(data, "sort"))[0]
        assert result == [1, 1, 2, 3, 4, 5, 6, 9]
        
        # Test string sort
        data = ["banana", "apple", "cherry"]
        result = list(get_path(data, "sort"))[0]
        assert result == ["apple", "banana", "cherry"]
        
        # Test mixed types (should sort by string representation)
        data = [3, "apple", 1, "banana"]
        result = list(get_path(data, "sort"))[0]
        assert result == [1, 3, "apple", "banana"]
        
        # Test on non-array
        result = list(get_path("test", "sort"))
        assert result == [None]

    def test_reverse_function(self):
        """Test reverse() function."""
        # Test array reverse
        data = [1, 2, 3, 4, 5]
        result = list(get_path(data, "reverse"))[0]
        assert result == [5, 4, 3, 2, 1]
        
        # Test string reverse
        data = "hello"
        result = list(get_path(data, "reverse"))[0]
        assert result == "olleh"
        
        # Test on non-array/string
        result = list(get_path(42, "reverse"))
        assert result == [None]

    def test_unique_function(self):
        """Test unique() function."""
        # Test basic unique
        data = [1, 2, 2, 3, 1, 4, 3, 5]
        result = list(get_path(data, "unique"))[0]
        assert result == [1, 2, 3, 4, 5]
        
        # Test with strings
        data = ["apple", "banana", "apple", "cherry", "banana"]
        result = list(get_path(data, "unique"))[0]
        assert result == ["apple", "banana", "cherry"]
        
        # Test with mixed types
        data = [1, "hello", 1, "world", "hello"]
        result = list(get_path(data, "unique"))[0]
        assert result == [1, "hello", "world"]
        
        # Test on non-array
        result = list(get_path("test", "unique"))
        assert result == [None]

    def test_flatten_function(self):
        """Test flatten() function."""
        # Test basic flatten
        data = [[1, 2], [3, 4], [5, 6]]
        result = list(get_path(data, "flatten"))[0]
        assert result == [1, 2, 3, 4, 5, 6]
        
        # Test mixed flatten
        data = [1, [2, 3], 4, [5]]
        result = list(get_path(data, "flatten"))[0]
        assert result == [1, 2, 3, 4, 5]
        
        # Test with depth
        data = [[[1, 2]], [[3, 4]], [[5, 6]]]
        result = list(get_path(data, "flatten(1)"))[0]
        assert result == [[1, 2], [3, 4], [5, 6]]
        
        # Test deep flatten
        data = [[[1, 2]], [[3, 4]], [[5, 6]]]
        result = list(get_path(data, "flatten(2)"))[0]
        assert result == [1, 2, 3, 4, 5, 6]
        
        # Test on non-array
        result = list(get_path("test", "flatten"))
        assert result == [None]


class TestChainedOperations:
    """Test chaining string and math operations."""

    def test_string_chain(self):
        """Test chaining string operations."""
        data = "  Hello,World,Test  "
        
        # Chain trim and split
        result = list(get_path(data, "trim | split(\",\")"))[0]
        assert result == ["Hello", "World", "Test"]

    def test_math_chain(self):
        """Test chaining math operations."""
        data = [[1, 2], [3, 4], [5, 6]]
        
        # Chain flatten and add
        result = list(get_path(data, "flatten | add"))[0]
        assert result == 21  # 1+2+3+4+5+6

    def test_mixed_chain(self):
        """Test chaining string and math operations."""
        data = ["1", "2", "3", "4", "5"]
        
        # Join as string then split again
        result = list(get_path(data, "join(\",\") | split(\",\")"))[0]
        assert result == ["1", "2", "3", "4", "5"]


if __name__ == "__main__":
    pytest.main([__file__])