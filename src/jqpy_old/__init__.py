"""
jqpy - A Python implementation of jq-like path expressions for JSON-like data.

This package provides a Pythonic way to query and manipulate nested data structures
using jq-style path expressions.

Example:
    >>> import jqpy
    >>> data = {"a": {"b": [1, 2, 3]}}
    >>> jqpy.get(data, "a.b.1")
    2
"""

__version__ = "0.1.0"

# Import core functionality
from .path import get_path, has_path, set_path, delete_path  # noqa: F401

# Note: We don't provide short aliases to avoid name clashes with built-ins
# and to maintain explicit, clear API
