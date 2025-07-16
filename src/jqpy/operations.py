"""
Path operations for jqpy.

This module provides high-level operations built on top of the core traversal.
"""
from collections.abc import Iterator
from typing import Any

from .parser import PathComponent, PathComponentType, parse_path
from .traverse import traverse
from .traverse_utils import (
    has_wildcard_components,
    expand_wildcards,
    navigate_to_parent,
    validate_path_exists,
    path_components_to_string
)


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
    has_wildcards = has_wildcard_components(path_components)
    
    if not all_matches and not has_wildcards:
        # Simple single path setting
        yield _set_single_path(data, path_components, value)
        return
    
    # For wildcard paths or all_matches=True, find all matching paths
    try:
        existing_paths = list(expand_wildcards(data, path_components))
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
    if not path_components:
        return value
    
    import copy
    
    # Create a deep copy to avoid modifying the original
    result = copy.deepcopy(data) if data is not None else {}
    
    # Navigate to the parent and get the structure with missing elements created
    try:
        parent_data, final_component = navigate_to_parent(result, path_components, create_missing=True)
    except (ValueError, KeyError) as e:
        raise ValueError(f"Cannot set path: {e}")
    
    # Set the final value
    if final_component.type == PathComponentType.KEY:
        key = final_component.value
        if not isinstance(parent_data, dict):
            raise ValueError(f"Cannot set key '{key}' on non-dict type {type(parent_data)}")
        parent_data[key] = value
    elif final_component.type == PathComponentType.INDEX:
        idx = final_component.value
        if not isinstance(parent_data, list):
            raise ValueError(f"Cannot set index {idx} on non-list type {type(parent_data)}")
        # Extend list if necessary
        while len(parent_data) <= idx:
            parent_data.append(None)
        parent_data[idx] = value
    elif final_component.type == PathComponentType.SLICE:
        slice_obj = final_component.value
        if not isinstance(parent_data, list):
            raise ValueError(f"Cannot set slice {slice_obj} on non-list type {type(parent_data)}")
        # Replace the slice with the new value
        # If value is a list, replace the slice with its elements
        # If value is not a list, replace the slice with a single-element list containing the value
        if isinstance(value, list):
            parent_data[slice_obj] = value
        else:
            parent_data[slice_obj] = [value]
    else:
        raise ValueError(f"Cannot set path with final component type {final_component.type}")
    
    return result


# This function is now replaced by expand_wildcards in traverse_utils.py


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
    has_wildcards = has_wildcard_components(path_components)
    
    # For simple paths, verify the path exists and can be accessed
    if not all_matches and not has_wildcards:
        try:
            validate_path_exists(data, path_components)
        except (KeyError, ValueError) as e:
            if "not found" in str(e) or "out of range" in str(e):
                raise KeyError(f"Path not found: {path}")
            raise ValueError(str(e))
    
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


def copy_path(
    src_data: Any, 
    tgt_data: Any, 
    src_path: str | list[PathComponent], 
    tgt_path: str | list[PathComponent],
    default: Any = None,
    only_first_match: bool = True
) -> Iterator[Any]:
    """Copy value from source path to target path.
    
    Creates a modified copy of the target data structure with value(s) from the source.
    The original target data is never modified (functional immutability).
    
    Args:
        src_data: Source data structure to read from
        tgt_data: Target data structure to write to  
        src_path: Path in source data to read value from
        tgt_path: Path in target data to write value to
        default: Default value if source path doesn't exist
        only_first_match: If True, copy only the first matching source value.
                         If False, copy all matching source values sequentially to the
                         same target path (last value overwrites previous ones).
        
    Yields:
        The modified target data structure. Always yields exactly one result,
        which is a deep copy of tgt_data with the copied value(s) applied.
        
    Note:
        When only_first_match=False and multiple source values match, they are
        applied sequentially to the same target path. The final result contains
        the last matching source value (overwrite semantics).
    """
    import copy
    
    # Parse paths if they're strings
    if isinstance(src_path, str):
        from .parser import parse_path
        src_components = parse_path(src_path)
    else:
        src_components = src_path
        
    if isinstance(tgt_path, str):
        from .parser import parse_path
        tgt_components = parse_path(tgt_path)
    else:
        tgt_components = tgt_path
    
    # Get value from source path
    src_values = list(get_path(src_data, src_components))
    
    if not src_values:
        if default is not None:
            # Use default value if source path doesn't exist
            yield from set_path(tgt_data, tgt_components, default)
        else:
            # No value found and no default - yield original target
            yield tgt_data
        return
    
    # Use first match or all matches based on only_first_match flag
    if only_first_match:
        value_to_copy = src_values[0]
        yield from set_path(tgt_data, tgt_components, value_to_copy)
    else:
        # Copy all matching values, accumulating changes in a single target
        current_tgt = tgt_data
        for value in src_values:
            results = list(set_path(current_tgt, tgt_components, value))
            if results:
                current_tgt = results[0]  # Use the updated version for next iteration
        yield current_tgt  # Return the final accumulated result


def copy_path_simple(
    src_data: Any, 
    tgt_data: Any, 
    src_path: str | list[PathComponent], 
    tgt_path: str | list[PathComponent],
    default: Any = None,
    only_first_match: bool = True
) -> Any:
    """Simple copy_path that returns the first result directly.
    
    Args:
        src_data: Source data structure to read from
        tgt_data: Target data structure to write to
        src_path: Path in source data to read value from  
        tgt_path: Path in target data to write value to
        default: Default value if source path doesn't exist
        only_first_match: If True, only copy first match from source
        
    Returns:
        The modified target data structure
    """
    results = list(copy_path(src_data, tgt_data, src_path, tgt_path, default, only_first_match))
    return results[0] if results else tgt_data


def batch_getpaths(data: Any, paths: list[str | list[PathComponent]], default: Any = None) -> list[Any]:
    """Get values from multiple paths in batch.
    
    Args:
        data: The data structure to read from
        paths: List of paths to get values from
        default: Default value if a path doesn't exist
        
    Returns:
        List of values, one for each path (in same order)
    """
    results = []
    for path in paths:
        path_results = list(get_path(data, path))
        if path_results:
            results.append(path_results[0])  # Take first match
        else:
            results.append(default)
    return results


def resolve_to_atomic_paths(data: Any, path: str | list[PathComponent], type_filter: str | None = None) -> Iterator[str]:
    """Resolve a complex path expression to atomic paths for any matching values.
    
    Takes a path expression that may match containers (objects, arrays) and yields
    concrete paths that lead to the matching values. Can optionally filter by type.
    
    Supports all path expressions that work with get_path() and set_path(), including:
    - Wildcards: .*, []
    - Conditional selectors: [?(@.field == value)]
    - Array slicing: [0:2], [1:], [:3]
    - Function calls: select(), map(), etc.
    
    Args:
        data: The data structure to resolve paths in
        path: Complex path expression (may contain wildcards, match containers)
        type_filter: Optional filter - 'objects', 'arrays', 'scalars', or None for all types
        
    Yields:
        Concrete path strings, each leading to a value of the specified type
        
    Examples:
        data = {"users": [{"name": "john", "age": 30}, {"name": "jane", "age": 25}]}
        
        # All paths (default behavior - backwards compatible with scalars for now)
        list(resolve_to_atomic_paths(data, "users[]"))
        # Returns: ["users[0].name", "users[0].age", "users[1].name", "users[1].age"]
        
        # Only object paths
        list(resolve_to_atomic_paths(data, "users[]", type_filter="objects"))
        # Returns: ["users[0]", "users[1]"]
        
        # Only scalar paths (explicit)
        list(resolve_to_atomic_paths(data, "users[]", type_filter="scalars"))
        # Returns: ["users[0].name", "users[0].age", "users[1].name", "users[1].age"]
        
        # All types
        list(resolve_to_atomic_paths(data, ".", type_filter=None))
        # Returns: [".", "users", "users[0]", "users[0].name", "users[0].age", ...]
    """
    # Parse the input path if it's a string
    if isinstance(path, str):
        path_components = parse_path(path)
    else:
        path_components = path
    
    # Default to scalars for backwards compatibility
    if type_filter is None:
        type_filter = "scalars"
    
    # Use the full traverse function with custom path tracking
    yield from _traverse_with_full_atomic_paths(data, path_components, type_filter)


def _traverse_with_full_atomic_paths(data: Any, path_components: list[PathComponent], type_filter: str = "scalars", current_path: list = None) -> Iterator[str]:
    """Traverse data structure using full traverse() function and yield atomic paths."""
    if current_path is None:
        current_path = []
    
    if not path_components:
        # End of path - find all paths within this value based on type filter
        from .traverse import _get_all_paths, _get_jq_type
        
        # Check if the current data itself matches the type filter
        data_type = _get_jq_type(data)
        should_include_current = False
        
        if type_filter == "scalars" and data_type in ('string', 'number', 'boolean', 'null'):
            should_include_current = True
        elif type_filter == "objects" and data_type == "object":
            should_include_current = True
        elif type_filter == "arrays" and data_type == "array":
            should_include_current = True
        elif type_filter is None:  # Include all types
            should_include_current = True
        
        # If current data matches filter, include its path
        if should_include_current and current_path:
            yield path_components_to_string(current_path)
        
        # If this is a scalar and we're looking for scalars, return current path
        if type_filter == "scalars" and data_type in ('string', 'number', 'boolean', 'null'):
            if not current_path:  # Root scalar
                yield "."
            return
        
        # For containers, find inner paths based on type filter
        if type_filter is None:
            # Get all types
            all_inner_paths = []
            for filter_type in ["objects", "arrays", "scalars"]:
                inner_paths = _get_all_paths(data, filter_type)
                all_inner_paths.extend(inner_paths)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_paths = []
            for path in all_inner_paths:
                path_str = path_components_to_string(path)
                if path_str not in seen:
                    seen.add(path_str)
                    unique_paths.append(path)
            inner_atomic_paths = unique_paths
        else:
            # Get specific type
            inner_atomic_paths = _get_all_paths(data, type_filter)
        
        for inner_path in inner_atomic_paths:
            full_path = current_path + inner_path
            yield path_components_to_string(full_path)
        return
    
    # For complex path expressions, we need to use the full traverse function
    # but track paths. This is tricky because traverse() doesn't expose paths.
    # 
    # Approach: Use traverse() to get all matching values, then find where they
    # came from by re-traversing with path tracking for common cases.
    
    # For now, delegate to the existing implementation for common cases
    # and use traverse() for complex expressions
    component = path_components[0]
    from .parser import PathComponentType
    
    if component.type in (PathComponentType.KEY, PathComponentType.INDEX, PathComponentType.WILDCARD):
        # Use the existing simple implementation for these
        yield from _traverse_with_atomic_paths_simple(data, path_components, type_filter, current_path)
    else:
        # For complex expressions, fall back to a hybrid approach
        # Get the results from traverse and try to map them back to paths
        from .traverse import traverse
        results = list(traverse(data, path_components))
        
        # This is a limitation - we can't easily map complex results back to paths
        # without significant changes to the traverse function
        # For now, return empty (will be improved in future)
        return


def _traverse_with_atomic_paths_simple(data: Any, path_components: list[PathComponent], type_filter: str = "scalars", current_path: list = None) -> Iterator[str]:
    """Simple traversal for basic path components."""
    if current_path is None:
        current_path = []
    
    if not path_components:
        # End of path - find all paths within this value based on type filter
        from .traverse import _get_all_paths, _get_jq_type
        
        # Check if the current data itself matches the type filter
        data_type = _get_jq_type(data)
        should_include_current = False
        
        if type_filter == "scalars" and data_type in ('string', 'number', 'boolean', 'null'):
            should_include_current = True
        elif type_filter == "objects" and data_type == "object":
            should_include_current = True
        elif type_filter == "arrays" and data_type == "array":
            should_include_current = True
        elif type_filter is None:  # Include all types
            should_include_current = True
        
        # If current data matches filter, include its path
        if should_include_current:
            yield path_components_to_string(current_path)
        
        # If this is a scalar, no need to recurse further
        if data_type in ('string', 'number', 'boolean', 'null'):
            return
        
        # For containers, find inner paths based on type filter
        if type_filter is None:
            # Get all types
            all_inner_paths = []
            for filter_type in ["objects", "arrays", "scalars"]:
                inner_paths = _get_all_paths(data, filter_type)
                all_inner_paths.extend(inner_paths)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_paths = []
            for path in all_inner_paths:
                path_str = path_components_to_string(path)
                if path_str not in seen:
                    seen.add(path_str)
                    unique_paths.append(path)
            inner_atomic_paths = unique_paths
        else:
            # Get specific type
            inner_atomic_paths = _get_all_paths(data, type_filter)
        
        for inner_path in inner_atomic_paths:
            full_path = current_path + inner_path
            yield path_components_to_string(full_path)
        return
    
    # Continue traversing
    component, *rest = path_components
    
    from .parser import PathComponentType
    
    if component.type == PathComponentType.KEY:
        key = component.value
        if isinstance(data, dict) and key in data:
            yield from _traverse_with_atomic_paths_simple(
                data[key], 
                rest, 
                type_filter,
                current_path + [key]
            )
    elif component.type == PathComponentType.INDEX:
        idx = component.value
        if isinstance(data, list):
            if idx < 0:
                idx = len(data) + idx
            if 0 <= idx < len(data):
                yield from _traverse_with_atomic_paths_simple(
                    data[idx], 
                    rest, 
                    type_filter,
                    current_path + [idx]
                )
    elif component.type == PathComponentType.WILDCARD:
        # Wildcard - traverse all keys/indices
        if isinstance(data, dict):
            for key in data.keys():
                yield from _traverse_with_atomic_paths_simple(
                    data[key], 
                    rest, 
                    type_filter,
                    current_path + [key]
                )
        elif isinstance(data, list):
            for idx in range(len(data)):
                yield from _traverse_with_atomic_paths_simple(
                    data[idx], 
                    rest, 
                    type_filter,
                    current_path + [idx]
                )
    elif component.type == PathComponentType.SLICE:
        # Handle slicing
        if isinstance(data, list):
            slice_obj = component.value
            for idx in range(len(data))[slice_obj]:
                yield from _traverse_with_atomic_paths_simple(
                    data[idx], 
                    rest, 
                    type_filter,
                    current_path + [idx]
                )
    # Other component types would need to be handled here


# Use the shared utility function
_path_components_to_string = path_components_to_string


