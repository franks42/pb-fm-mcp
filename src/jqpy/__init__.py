""
jqpy - A Python implementation of jq-like path expressions

This module provides a clean, iterator-based implementation of jq's path handling
with support for nested data structures, wildcards, and more.
"""
from .parser import parse_path, PathComponent, PathComponentType
from .operations import get_path, batch_get_path, has_path, first_path_match

# Re-export the most commonly used functions and types
__all__ = [
    'parse_path',
    'PathComponent',
    'PathComponentType',
    'get_path',
    'batch_get_path',
    'has_path',
    'first_path_match',
]
