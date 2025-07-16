"""
Path operations for jqpy.

This module provides high-level operations built on top of the core traversal.
"""
from collections.abc import Iterator
from typing import Any

from .parser import PathComponent, PathComponentType, parse_path
from .traverse import traverse


def get_path(
    data: Any, 
    path: str | list[PathComponent],
    only_first_path_match: bool = False,
    max_depth: int = 100
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
        # Check if path contains pipe operator
        if '|' in path:
            yield from _handle_pipe_path(data, path, only_first_path_match, max_depth)
            return
        path_components = parse_path(path)
    else:
        path_components = path
    
    # Handle empty path (return the root)
    if not path_components:
        yield data
        return
    
    # Special case for root selector with no path components
    if len(path_components) == 1 and path_components[0].type == PathComponentType.KEY and path_components[0].value == '.':
        yield data
        return
    
    # Handle regular traversal
    for value in traverse(data, path_components, max_depth=max_depth):
        yield value
        if only_first_path_match:
            return


def _handle_pipe_path(
    data: Any,
    path: str,
    only_first_path_match: bool = False,
    max_depth: int = 100
) -> Iterator[Any]:
    """Handle path expressions with pipe operators.
    
    Args:
        data: The data structure to query
        path: Path expression with pipe operators
        only_first_path_match: If True, return only the first match
        max_depth: Maximum depth to traverse
        
    Yields:
        Values found after applying all pipe operations
    """
    # Split by pipe operator
    pipe_parts = [part.strip() for part in path.split('|')]
    
    # Start with original data
    current_results = [data]
    
    # Apply each pipe segment to the results from the previous segment
    for pipe_part in pipe_parts:
        if not pipe_part:
            continue
            
        next_results = []
        for result in current_results:
            # Apply this pipe segment to each result from the previous segment
            for value in get_path(result, pipe_part, only_first_path_match=False, max_depth=max_depth):
                next_results.append(value)
                if only_first_path_match:
                    yield value
                    return
        
        current_results = next_results
    
    # Yield all final results
    for result in current_results:
        yield result

def batch_get_path(
    data: Any,
    path: str | list[PathComponent],
    default: Any = None,
    only_first_path_match: bool = False
) -> list[Any]:
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
    path: str | list[PathComponent],
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
    path: str | list[PathComponent]
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


def set_path(
    data: Any,
    path: str | list[PathComponent],
    value: Any,
    all_matches: bool = False
) -> Iterator[Any]:
    """Set a value at the specified path in a data structure.
    
    Creates deep copies of the data structure with the value set at matching paths.
    When all_matches=True or wildcards are present, handles multiple path matches.
    
    Args:
        data: The data structure to modify
        path: Path expression or pre-parsed path components  
        value: The value to set at the path
        all_matches: If True, set all matching paths (supports wildcards)
        
    Yields:
        New data structures with values set at the path(s)
        
    Raises:
        ValueError: If the path is invalid or cannot be set
    """
    if isinstance(path, str):
        path_components = parse_path(path)
    else:
        path_components = path
    
    if not path_components:
        yield value
        return
    
    # Check if this is a simple path (no wildcards) for single setting
    has_wildcards = any(
        comp.type == PathComponentType.WILDCARD or 
        (comp.type == PathComponentType.KEY and comp.value == '') or
        comp.value == '[]'
        for comp in path_components
    )
    
    if not all_matches and not has_wildcards:
        # Simple single path setting
        yield _set_single_path(data, path_components, value)
        return
    
    # For wildcard paths or all_matches=True, find all matching paths
    try:
        existing_paths = list(_find_concrete_paths_for_setting(data, path_components))
    except Exception:
        existing_paths = []
    
    if not existing_paths and not all_matches:
        # If no existing paths and not forcing all_matches, try to create the path
        yield _set_single_path(data, path_components, value)
        return
    
    if not existing_paths:
        # No paths found and all_matches=True, nothing to set
        return
    
    # Set each matching path and yield the results
    for concrete_path in existing_paths:
        try:
            yield _set_single_path(data, concrete_path, value)
        except Exception:
            # Skip paths that can't be set
            continue


def _set_single_path(
    data: Any,
    path_components: list[PathComponent],
    value: Any
) -> Any:
    """Set a single concrete path, with smart container creation.
    
    Args:
        data: The data structure to modify
        path_components: Concrete path components (no wildcards)
        value: The value to set
        
    Returns:
        A new data structure with the value set
        
    Raises:
        ValueError: If the path is invalid for setting
    """
    import copy
    
    if not path_components:
        return value
    
    # Create a deep copy to avoid modifying the original
    result = copy.deepcopy(data) if data is not None else {}
    
    # Navigate to the parent of the target location, creating missing elements as needed
    current = result
    for i, component in enumerate(path_components[:-1]):
        next_component = path_components[i + 1] if i + 1 < len(path_components) else None
        
        if component.type == PathComponentType.KEY:
            key = component.value
            if not isinstance(current, dict):
                raise ValueError(f"Cannot access key '{key}' on non-dict type {type(current)}")
            if key not in current:
                # Create the appropriate type based on the next component
                if next_component and next_component.type == PathComponentType.INDEX:
                    current[key] = []  # Next component is an index, so create a list
                else:
                    current[key] = {}  # Default to dict
            current = current[key]
        elif component.type == PathComponentType.INDEX:
            idx = component.value
            if not isinstance(current, list):
                raise ValueError(f"Cannot access index {idx} on non-list type {type(current)}")
            # Extend list if necessary
            while len(current) <= idx:
                current.append(None)
            if current[idx] is None:
                # Create the appropriate type based on the next component
                if next_component and next_component.type == PathComponentType.INDEX:
                    current[idx] = []  # Next component is an index, so create a list
                else:
                    current[idx] = {}  # Default to dict
            current = current[idx]
        else:
            raise ValueError(f"Cannot set path with component type {component.type}")
    
    # Set the final value
    final_component = path_components[-1]
    if final_component.type == PathComponentType.KEY:
        key = final_component.value
        if not isinstance(current, dict):
            raise ValueError(f"Cannot set key '{key}' on non-dict type {type(current)}")
        current[key] = value
    elif final_component.type == PathComponentType.INDEX:
        idx = final_component.value
        if not isinstance(current, list):
            raise ValueError(f"Cannot set index {idx} on non-list type {type(current)}")
        # Extend list if necessary
        while len(current) <= idx:
            current.append(None)
        current[idx] = value
    else:
        raise ValueError(f"Cannot set path with final component type {final_component.type}")
    
    return result


def _find_concrete_paths_for_setting(
    data: Any,
    path_components: list[PathComponent],
    current_path: list[PathComponent] | None = None
) -> Iterator[list[PathComponent]]:
    """Find all concrete paths that exist and match a pattern with wildcards for setting.
    
    This is similar to the deletion version but doesn't require the final path to exist.
    
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
    
    if component.type == PathComponentType.WILDCARD or \
       (component.type == PathComponentType.KEY and component.value == '') or \
       component.value == '[]':
        # Handle wildcard - iterate through all keys/indices
        if isinstance(data, dict):
            for key in data.keys():
                key_component = PathComponent(
                    type=PathComponentType.KEY,
                    value=key,
                    raw_value=str(key)
                )
                yield from _find_concrete_paths_for_setting(
                    data[key], 
                    remaining, 
                    current_path + [key_component]
                )
        elif isinstance(data, list):
            for idx in range(len(data)):
                idx_component = PathComponent(
                    type=PathComponentType.INDEX,
                    value=idx,
                    raw_value=str(idx)
                )
                yield from _find_concrete_paths_for_setting(
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
                yield from _find_concrete_paths_for_setting(data[key], remaining, new_path)
        elif component.type == PathComponentType.INDEX:
            idx = component.value
            if isinstance(data, list):
                if idx < 0:
                    idx = len(data) + idx
                if 0 <= idx < len(data):
                    yield from _find_concrete_paths_for_setting(data[idx], remaining, new_path)


def set_path_simple(
    data: Any,
    path: str | list[PathComponent],
    value: Any
) -> Any:
    """Simple non-iterator version of set_path for backwards compatibility.
    
    Args:
        data: The data structure to modify
        path: Path expression or pre-parsed path components
        value: The value to set
        
    Returns:
        A new data structure with the value set at the path
    """
    results = list(set_path(data, path, value, all_matches=False))
    return results[0] if results else data


# Sentinel object for deletion operations
_DELETE_SENTINEL = object()


def delete_path(
    data: Any,
    path: str | list[PathComponent],
    all_matches: bool = False
) -> Iterator[Any]:
    """Delete values at the specified path in a data structure.
    
    Implemented as a special case of set_path using a deletion sentinel.
    Creates deep copies of the data structure with values deleted at matching paths.
    
    Args:
        data: The data structure to modify
        path: Path expression or pre-parsed path components
        all_matches: If True, delete all matching paths (supports wildcards)
        
    Yields:
        New data structures with values deleted at the path(s)
        
    Raises:
        ValueError: If the path is invalid or cannot be deleted
        KeyError: If the path does not exist (when all_matches=False)
    """
    if isinstance(path, str):
        path_components = parse_path(path)
    else:
        path_components = path
    
    if not path_components:
        raise ValueError("Cannot delete root element")
    
    # Check if paths exist first for non-wildcard, non-all_matches cases
    has_wildcards = any(
        comp.type == PathComponentType.WILDCARD or 
        (comp.type == PathComponentType.KEY and comp.value == '') or
        comp.value == '[]'
        for comp in path_components
    )
    
    # For simple paths, verify the path exists and can be accessed
    if not all_matches and not has_wildcards:
        # Check path step by step to distinguish between missing path and type error
        current = data
        for i, component in enumerate(path_components):
            if component.type == PathComponentType.KEY:
                key = component.value
                if isinstance(current, dict):
                    if key not in current:
                        raise KeyError(f"Path not found: {path}")
                    current = current[key]
                else:
                    raise ValueError(f"Cannot access key '{key}' on non-dict type {type(current).__name__}")
            elif component.type == PathComponentType.INDEX:
                idx = component.value
                if isinstance(current, list):
                    if idx < 0:
                        idx = len(current) + idx
                    if idx < 0 or idx >= len(current):
                        raise KeyError(f"Path not found: {path}")
                    current = current[idx]
                else:
                    raise ValueError(f"Cannot access index {idx} on non-list type {type(current).__name__}")
            else:
                # For other types like wildcards, let set_path handle it
                break
    
    # Use set_path with deletion sentinel, then clean up sentinels
    results_found = False
    try:
        for result_with_sentinel in set_path(data, path, _DELETE_SENTINEL, all_matches=all_matches):
            results_found = True
            try:
                yield _remove_sentinels(result_with_sentinel)
            except ValueError as e:
                if "root sentinel" in str(e).lower():
                    # This shouldn't happen for properly formed paths
                    continue
                raise
    except ValueError as e:
        # Re-raise ValueError from set_path (e.g., type mismatch errors)
        raise e
    
    # If no results found for wildcard/all_matches cases, that's okay
    if not results_found and (all_matches or has_wildcards):
        # For wildcard paths with all_matches=True, no error if no matches found
        pass


def _remove_sentinels(data: Any) -> Any:
    """Remove deletion sentinels from a data structure.
    
    Args:
        data: Data structure that may contain deletion sentinels
        
    Returns:
        Data structure with sentinels removed
        
    Raises:
        ValueError: If trying to remove root sentinel
    """
    if data is _DELETE_SENTINEL:
        raise ValueError("Cannot remove root sentinel")
    
    if isinstance(data, dict):
        return {k: _remove_sentinels(v) for k, v in data.items() if v is not _DELETE_SENTINEL}
    elif isinstance(data, list):
        # For lists, we need to handle sentinel removal carefully
        result = []
        for item in data:
            if item is not _DELETE_SENTINEL:
                result.append(_remove_sentinels(item))
        return result
    else:
        return data


def delete_path_simple(
    data: Any,
    path: str | list[PathComponent]
) -> Any:
    """Simple non-iterator version of delete_path for backwards compatibility.
    
    Args:
        data: The data structure to modify
        path: Path expression or pre-parsed path components
        
    Returns:
        A new data structure with the value deleted at the path
    """
    results = list(delete_path(data, path, all_matches=False))
    return results[0] if results else data
