"""
jqpy - A Python implementation of jq-like path expressions

This module provides a clean, iterator-based implementation of jq's path handling
with support for nested data structures, wildcards, and more.
"""
from collections.abc import Iterator
from typing import Any, List, Optional, Tuple, Union, cast

from .operations import (
    batch_get_path,
    batch_getpaths,
    copy_path,
    copy_path_simple,
    delete_path,
    delete_path_simple,
    first_path_match,
    get_path,
    has_path,
    resolve_to_atomic_paths,
    set_path,
    set_path_simple,
)
from .parser import PathComponent, PathComponentType, parse_path
from .traverse import traverse

# Re-export the most commonly used functions and types
__all__ = [
    'PathComponent',
    'PathComponentType',
    'batch_get_path',
    'batch_getpaths',
    'copy_path',
    'copy_path_simple',
    'delete_path',
    'delete_path_simple',
    'first_path_match',
    'get_path',
    'has_path',
    'parse_path',
    'resolve_to_atomic_paths',
    'set_path',
    'set_path_simple',
    'traverse'
]
