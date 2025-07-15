"""
Path handling for jqpy.

This module provides the core functionality for getting, setting, and deleting
values in nested data structures using path expressions.
"""

from typing import Any, List, Union
from .parser import PathComponent, PathComponentType


def get(data: Any, path: Union[str, List[PathComponent]], default: Any = None) -> Any:
    """
    Get a value from a nested data structure using a path expression.

    Args:
        data: The data structure to query.
        path: Path expression or pre-parsed path components.
        default: Default value to return if path doesn't exist.

    Returns:
        The value at the specified path, or default if not found.
    """
    if not path:
        return data
    
    if isinstance(path, str):
        from .parser import parse_path
        path_components = parse_path(path)
    else:
        path_components = path
    
    current = data
    for component in path_components:
        if current is None:
            return default
            
        if component.type == PathComponentType.KEY and isinstance(current, dict):
            current = current.get(component.value, default)
        elif component.type == PathComponentType.INDEX and isinstance(current, (list, tuple)):
            try:
                current = current[component.value]  # type: ignore
            except (IndexError, TypeError):
                return default
        elif component.type == PathComponentType.SELECT_ALL and isinstance(current, (list, tuple)):
            # For now, return the list as is
            return current
        else:
            return default
    
    return current


def set_path(data: Any, path: Union[str, List[PathComponent]], value: Any) -> Any:
    """
    Set a value in a nested data structure using a path expression.
    
    Note: This creates a new copy of the data structure with the value set.
    
    Args:
        data: The data structure to modify.
        path: Path expression or pre-parsed path components.
        value: Value to set at the specified path.
        
    Returns:
        A new data structure with the value set at the specified path.
    """
    raise NotImplementedError("set_path() not implemented yet")


def delete_path(data: Any, path: Union[str, List[PathComponent]]) -> Any:
    """
    Delete a value from a nested data structure using a path expression.
    
    Args:
        data: The data structure to modify.
        path: Path expression or pre-parsed path components.
        
    Returns:
        A new data structure with the value at the specified path removed.
    """
    raise NotImplementedError("delete_path() not implemented yet")


def has_path(data: Any, path: Union[str, List[PathComponent]]) -> bool:
    """
    Check if a path exists in a nested data structure.
    
    Args:
        data: The data structure to check.
        path: Path expression or pre-parsed path components.
        
    Returns:
        True if the path exists, False otherwise.
    """
    if not path:
        return True
        
    if isinstance(path, str):
        from .parser import parse_path
        path_components = parse_path(path)
    else:
        path_components = path
    
    current = data
    for component in path_components:
        if current is None:
            return False
            
        if component.type == PathComponentType.KEY and isinstance(current, dict):
            if component.value not in current:
                return False
            current = current[component.value]
        elif component.type == PathComponentType.INDEX and isinstance(current, (list, tuple)):
            try:
                if not isinstance(component.value, int):
                    return False
                current = current[component.value]  # type: ignore
            except (IndexError, TypeError):
                return False
        else:
            return False
    
    return True
