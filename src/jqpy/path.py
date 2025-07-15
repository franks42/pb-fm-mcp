"""
Path handling for jqpy.

This module provides the core functionality for getting, setting, and deleting
values in nested data structures using path expressions.
"""

from typing import Any, List, Union
from .parser import PathComponent, PathComponentType


def get_path(data: Any, path: Union[str, List[PathComponent]], default: Any = None) -> Any:
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
        
    Raises:
        IndexError: If array index is out of bounds.
        KeyError: If trying to set a non-existent key and parent is not a dict.
        TypeError: If trying to use an index on a non-sequence or a key on a non-mapping.
    """
    if isinstance(path, str):
        from .parser import parse_path
        path_components = parse_path(path)
    else:
        path_components = path
    
    if not path_components:
        return value
    
    # Create a deep copy of the data to avoid modifying the original
    import copy
    current = copy.deepcopy(data)
    
    # Navigate to the parent of the target
    parent = None
    target = current
    target_component = None
    
    for i, component in enumerate(path_components[:-1]):
        # If target is None and we need to create a container
        if target is None and parent is not None:
            if component.type == PathComponentType.KEY:
                target = {}
            elif component.type == PathComponentType.INDEX:
                target = []
            else:  # SELECT_ALL
                raise ValueError("Cannot set value with wildcard selector in path")
                
            # Attach the new container to its parent
            if isinstance(parent, dict) and i > 0:
                parent[path_components[i-1].value] = target
            elif isinstance(parent, list) and i > 0:
                parent[path_components[i-1].value] = target
        
        # Move to the next component
        parent = target
        target_component = component
        
        if component.type == PathComponentType.KEY:
            if not isinstance(target, dict):
                if target is None and i == 0:
                    # If we're at the root, create a dict
                    target = {}
                    current = target
                else:
                    raise TypeError(f"Cannot use key access on {type(target).__name__}")
            
            # Get the next target, or None if it doesn't exist
            next_target = None
            if component.value in target:
                next_target = target[component.value]
            
            # If we're at the last component, we'll create the new value in the next step
            if i < len(path_components) - 2:  # Not the last component
                if next_target is None:
                    # Create missing intermediate dict
                    next_target = {}
                    target[component.value] = next_target
            
            target = next_target
            
        elif component.type == PathComponentType.INDEX:
            if not isinstance(target, (list, tuple)):
                if target is None and i == 0:
                    # If we're at the root, create a list
                    target = []
                    current = target
                else:
                    raise TypeError(f"Cannot use index access on {type(target).__name__}")
            try:
                target = target[component.value]
            except IndexError as e:
                raise IndexError(f"Index {component.value} out of bounds") from e
                
        elif component.type == PathComponentType.SELECT_ALL:
            raise ValueError("Cannot set value with wildcard selector in path")
    
    # Set the value at the target path
    if not path_components:
        return value
        
    last_component = path_components[-1]
    
    if last_component.type == PathComponentType.KEY:
        if target is None:
            # If target is None, create a new dict
            target = {}
            if parent is not None and len(path_components) > 1:
                # If we have a parent, update it with the new dict
                if isinstance(parent, dict):
                    parent[path_components[-2].value] = target
                elif isinstance(parent, list):
                    parent[path_components[-2].value] = target
            
        if not isinstance(target, dict):
            raise TypeError(f"Cannot set key on {type(target).__name__}")
                    
        # Check if we need to merge with an existing value (for escaped keys)
        existing_key = None
        if hasattr(last_component, 'raw_value'):
            # For escaped keys, try to find an exact match with the raw value
            for key in target.keys():
                if key == last_component.raw_value or key == last_component.value:
                    existing_key = key
                    break
            
        if existing_key is not None:
            target[existing_key] = value
        else:
            target[last_component.value] = value
        
    elif last_component.type == PathComponentType.INDEX:
        if not isinstance(target, list):
            raise TypeError(f"Cannot set index on {type(target).__name__}")
        try:
            target[last_component.value] = value
        except IndexError as e:
            raise IndexError(f"Index {last_component.value} out of bounds") from e
            
    elif last_component.type == PathComponentType.SELECT_ALL:
        raise ValueError("Cannot set value with wildcard selector")
    
    return current


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
