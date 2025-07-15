"""
Path operations for jqpy.

This module provides high-level operations built on top of the core traversal.
"""
from typing import Any, Iterator, List, Optional, Union, cast
from .parser import parse_path, PathComponent, PathComponentType
from .traverse import traverse

def get_path(
    data: Any, 
    path: Union[str, List[PathComponent]],
    only_first_path_match: bool = False
) -> Iterator[Any]:
    """Get values from a nested data structure using a path expression.
    
    Args:
        data: The data structure to query
        path: Path expression or pre-parsed path components
        only_first_path_match: If True, return only the first match
        
    Yields:
        Values found at the specified path
    """
    if isinstance(path, str):
        path_components = parse_path(path)
    else:
        path_components = path
    
    for path_taken, value in traverse(data, path_components):
        yield value
        if only_first_path_match:
            return

def batch_get_path(
    data: Any,
    path: Union[str, List[PathComponent]],
    default: Any = None,
    only_first_path_match: bool = False
) -> List[Any]:
    """Get all values from a path as a list.
    
    This is a convenience function that forces evaluation of the iterator
    and returns a list of results.
    
    Args:
        data: The data structure to query
        path: Path expression or pre-parsed path components
        default: Default value to return if no matches are found
        only_first_path_match: If True, return only the first match
        
    Returns:
        List of values found at the specified path, or [default] if none found
    """
    result = list(get_path(data, path, only_first_path_match))
    return result if result else [default] if default is not None else []

def first_path_match(
    data: Any,
    path: Union[str, List[PathComponent]],
    default: Any = None
) -> Any:
    """Get the first matching value or default if none found.
    
    Args:
        data: The data structure to query
        path: Path expression or pre-parsed path components
        default: Default value to return if no matches are found
        
    Returns:
        First matching value, or default if none found
    """
    return next(get_path(data, path, only_first_path_match=True), default)

def has_path(
    data: Any,
    path: Union[str, List[PathComponent]]
) -> bool:
    """Check if a path exists in the data structure.
    
    Args:
        data: The data structure to check
        path: Path expression or pre-parsed path components
        
    Returns:
        True if the path exists, False otherwise
    """
    try:
        next(get_path(data, path, only_first_path_match=True))
        return True
    except StopIteration:
        return False
