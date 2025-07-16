"""
Shared utilities for path traversal and resolution operations.

This module provides common functions used across different path operations
to reduce code duplication and ensure consistent behavior.
"""
from collections.abc import Iterator
from typing import Any

from .parser import PathComponent, PathComponentType


def has_wildcard_components(path_components: list[PathComponent]) -> bool:
    """Check if path components contain wildcards or dynamic elements.
    
    Args:
        path_components: List of path components to check
        
    Returns:
        True if any component is a wildcard, slice, or similar dynamic element
    """
    return any(
        comp.type == PathComponentType.WILDCARD or 
        comp.type == PathComponentType.OPTIONAL_WILDCARD or
        comp.type == PathComponentType.SLICE or
        (comp.type == PathComponentType.KEY and comp.value == '') or
        comp.value == '[]'
        for comp in path_components
    )


def create_key_component(key: str) -> PathComponent:
    """Create a KEY path component.
    
    Args:
        key: The key value
        
    Returns:
        PathComponent for key access
    """
    return PathComponent(
        type=PathComponentType.KEY,
        value=key,
        raw_value=str(key)
    )


def create_index_component(idx: int) -> PathComponent:
    """Create an INDEX path component.
    
    Args:
        idx: The index value
        
    Returns:
        PathComponent for index access
    """
    return PathComponent(
        type=PathComponentType.INDEX,
        value=idx,
        raw_value=str(idx)
    )


def expand_wildcards(
    data: Any,
    path_components: list[PathComponent],
    current_path: list[PathComponent] = None
) -> Iterator[list[PathComponent]]:
    """Expand wildcard components to concrete paths.
    
    This function traverses data structures and expands wildcard path components
    into concrete paths that actually exist in the data.
    
    Args:
        data: Current data to traverse
        path_components: Path pattern (may contain wildcards)
        current_path: Current concrete path being built
        
    Yields:
        Complete concrete paths that match the pattern
    """
    if current_path is None:
        current_path = []
    
    if not path_components:
        # We've reached the end of the pattern - this is a valid path
        yield current_path
        return
    
    component, *remaining = path_components
    
    if component.type == PathComponentType.SLICE:
        # Handle slice - for setting, we treat slice as a concrete path to the slice itself
        if not remaining:
            # This slice is the final component
            yield current_path + [component]
        else:
            # Continue with the sliced data
            if isinstance(data, list):
                sliced_data = data[component.value]
                yield from expand_wildcards(
                    sliced_data,
                    remaining,
                    current_path + [component]
                )
    elif component.type == PathComponentType.WILDCARD or \
         component.type == PathComponentType.OPTIONAL_WILDCARD or \
         (component.type == PathComponentType.KEY and component.value == '') or \
         component.value == '[]':
        # Handle wildcard - iterate through all keys/indices
        if isinstance(data, dict):
            for key in data.keys():
                key_component = create_key_component(key)
                yield from expand_wildcards(
                    data[key], 
                    remaining, 
                    current_path + [key_component]
                )
        elif isinstance(data, list):
            for idx in range(len(data)):
                idx_component = create_index_component(idx)
                yield from expand_wildcards(
                    data[idx], 
                    remaining, 
                    current_path + [idx_component]
                )
    else:
        # Handle concrete component
        new_path = current_path + [component]
        
        if component.type == PathComponentType.KEY:
            key = component.value
            if isinstance(data, dict) and key in data:
                yield from expand_wildcards(data[key], remaining, new_path)
        elif component.type == PathComponentType.INDEX:
            idx = component.value
            if isinstance(data, list):
                if idx < 0:
                    idx = len(data) + idx
                if 0 <= idx < len(data):
                    yield from expand_wildcards(data[idx], remaining, new_path)


def navigate_to_parent(
    data: Any,
    path_components: list[PathComponent],
    create_missing: bool = False
) -> tuple[Any, PathComponent]:
    """Navigate to the parent of the target location.
    
    Args:
        data: The data structure to navigate
        path_components: Path components to follow
        create_missing: Whether to create missing intermediate containers
        
    Returns:
        Tuple of (parent_container, final_component)
        
    Raises:
        ValueError: If path cannot be navigated or types don't match
        KeyError: If path doesn't exist and create_missing is False
    """
    if not path_components:
        raise ValueError("Cannot navigate to parent of empty path")
    
    # Navigate to the parent of the target location
    current = data
    for i, component in enumerate(path_components[:-1]):
        next_component = path_components[i + 1] if i + 1 < len(path_components) else None
        
        if component.type == PathComponentType.KEY:
            key = component.value
            if not isinstance(current, dict):
                raise ValueError(f"Cannot access key '{key}' on non-dict type {type(current)}")
            
            if key not in current:
                if create_missing:
                    # Create the appropriate type based on the next component
                    if next_component and next_component.type == PathComponentType.INDEX:
                        current[key] = []  # Next component is an index, so create a list
                    else:
                        current[key] = {}  # Default to dict
                else:
                    raise KeyError(f"Key '{key}' not found in path")
            
            current = current[key]
            
        elif component.type == PathComponentType.INDEX:
            idx = component.value
            if not isinstance(current, list):
                raise ValueError(f"Cannot access index {idx} on non-list type {type(current)}")
            
            if idx < 0:
                idx = len(current) + idx
            
            if create_missing:
                # Extend list if necessary
                while len(current) <= idx:
                    current.append(None)
                
                if current[idx] is None:
                    # Create the appropriate type based on the next component
                    if next_component and next_component.type == PathComponentType.INDEX:
                        current[idx] = []  # Next component is an index, so create a list
                    else:
                        current[idx] = {}  # Default to dict
            else:
                if idx < 0 or idx >= len(current):
                    raise KeyError(f"Index {idx} not found in path")
            
            current = current[idx]
            
        else:
            raise ValueError(f"Cannot navigate with component type {component.type}")
    
    final_component = path_components[-1]
    return current, final_component


def validate_path_exists(data: Any, path_components: list[PathComponent]) -> None:
    """Validate that a path exists in the data structure.
    
    Args:
        data: The data structure to check
        path_components: Path components to validate
        
    Raises:
        KeyError: If the path doesn't exist
        ValueError: If there's a type mismatch in the path
    """
    current = data
    for component in path_components:
        if component.type == PathComponentType.KEY:
            key = component.value
            if isinstance(current, dict):
                if key not in current:
                    raise KeyError(f"Key '{key}' not found")
                current = current[key]
            else:
                raise ValueError(f"Cannot access key '{key}' on non-dict type {type(current).__name__}")
        elif component.type == PathComponentType.INDEX:
            idx = component.value
            if isinstance(current, list):
                if idx < 0:
                    idx = len(current) + idx
                if idx < 0 or idx >= len(current):
                    raise KeyError(f"Index {idx} out of range")
                current = current[idx]
            else:
                raise ValueError(f"Cannot access index {idx} on non-list type {type(current).__name__}")
        else:
            # For other types like wildcards, we can't validate statically
            break


def path_components_to_string(path_components: list[PathComponent | str | int]) -> str:
    """Convert a list of path components to a string representation.
    
    Args:
        path_components: List of path components, keys, or indices
        
    Returns:
        String representation of the path
    """
    if not path_components:
        return "."
    
    result = ""
    for component in path_components:
        if isinstance(component, PathComponent):
            if component.type == PathComponentType.KEY:
                if result and not result.endswith('.'):
                    result += "."
                result += component.value
            elif component.type == PathComponentType.INDEX:
                result += f"[{component.value}]"
            else:
                # For other types, use raw_value
                if result and not result.endswith('.'):
                    result += "."
                result += component.raw_value
        elif isinstance(component, str):
            # Handle string keys
            if result and not result.endswith('.'):
                result += "."
            result += component
        elif isinstance(component, int):
            # Handle numeric indices
            result += f"[{component}]"
        else:
            # Handle raw values
            if result and not result.endswith('.'):
                result += "."
            result += str(component)
    
    return result