"""
Shared utilities for path traversal and resolution operations.

This module provides common functions used across different path operations
to reduce code duplication and ensure consistent behavior.

It also includes path-aware test data generation utilities for creating
test data structures with embedded path information for better debugging
and test clarity.
"""
from collections.abc import Iterator
from typing import Any, Dict, List, Union

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


# =============================================================================
# Path-Aware Test Data Generation
# =============================================================================

def make_path_aware(obj: Any, current_path: str = ".") -> Any:
    """
    Transform a data structure to include path information for testing.
    
    This function adds a "path" field to every dictionary showing the exact
    jq path to reach that object, and transforms array elements to show their
    path location. This makes test results much easier to understand and debug.
    
    Args:
        obj: The data structure to transform
        current_path: The current jq path to this object
        
    Returns:
        Transformed data structure with embedded path information
        
    Examples:
        >>> data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        >>> path_aware = make_path_aware(data)
        >>> print(path_aware)
        {
          "path": ".",
          "users": [
            {"path": ".users[0]", "name": "Alice"},
            {"path": ".users[1]", "name": "Bob"}
          ]
        }
        
        # Now when you run jq operations, you can see exactly which paths were accessed:
        >>> results = list(get_path(path_aware, '.users[]'))
        >>> for user in results:
        ...     print(f"Found user at path: {user['path']}")
        Found user at path: .users[0]
        Found user at path: .users[1]
    """
    if isinstance(obj, dict):
        # Create a new dict to avoid modifying the original
        result = {}
        
        # Add path to this object
        result["path"] = current_path
        
        for key, value in obj.items():
            # Skip if this is already a path field
            if key == "path":
                continue
                
            # Calculate the path to this field
            if current_path == ".":
                new_path = f".{key}"
            else:
                new_path = f"{current_path}.{key}"
            
            # Recursively process the value
            result[key] = make_path_aware(value, new_path)
            
        return result
        
    elif isinstance(obj, list):
        result = []
        for i, item in enumerate(obj):
            item_path = f"{current_path}[{i}]"
            
            if isinstance(item, (dict, list)):
                # Recursively process complex items
                result.append(make_path_aware(item, item_path))
            else:
                # For primitive values, we can either keep them as-is or make them path-aware
                if isinstance(item, str) and not item.startswith("item-at-"):
                    # For strings, create path-aware representation
                    result.append(f"item-at-{item_path}")
                else:
                    # For numbers, booleans, None, keep as-is for math operations
                    result.append(item)
                    
        return result
    else:
        # For primitive values (numbers, booleans, None), return as-is
        return obj


def create_path_aware_test_data() -> Dict[str, Any]:
    """
    Create comprehensive test datasets with embedded path information.
    
    Returns:
        Dictionary containing various test data structures with paths
        
    Examples:
        >>> test_data = create_path_aware_test_data()
        >>> complex_data = test_data["complex_nested"]
        >>> # Use in tests to see exactly which paths are traversed
    """
    return {
        # Basic structures
        "simple_object": make_path_aware({
            "name": "John",
            "age": 30
        }),
        
        "nested_object": make_path_aware({
            "user": {
                "name": "John", 
                "age": 30,
                "profile": {
                    "email": "john@example.com",
                    "active": True
                }
            }
        }),
        
        "simple_array": make_path_aware({
            "items": [1, 2, 3, 4, 5]
        }),
        
        "array_of_objects": make_path_aware({
            "users": [
                {"name": "John", "age": 30},
                {"name": "Jane", "age": 25}
            ]
        }),
        
        "complex_nested": make_path_aware({
            "company": {
                "departments": [
                    {
                        "name": "Engineering",
                        "teams": [
                            {
                                "name": "Backend",
                                "members": ["Alice", "Bob"]
                            },
                            {
                                "name": "Frontend", 
                                "members": ["Charlie", "Diana"]
                            }
                        ]
                    },
                    {
                        "name": "Sales",
                        "teams": [
                            {
                                "name": "Enterprise",
                                "members": ["Eve", "Frank"]
                            }
                        ]
                    }
                ]
            }
        }),
        
        "mixed_types": make_path_aware({
            "data": {
                "strings": ["hello", "world"],
                "numbers": [1, 2, 3],
                "booleans": [True, False],
                "objects": [
                    {"type": "user", "active": True},
                    {"type": "admin", "active": False}
                ],
                "nested_arrays": [
                    [1, 2],
                    [3, 4, 5]
                ]
            }
        }),
        
        "filtering_data": make_path_aware({
            "products": [
                {"name": "laptop", "price": 1000, "available": True},
                {"name": "mouse", "price": 50, "available": False},
                {"name": "keyboard", "price": 100, "available": True}
            ]
        }),
        
        "deeply_nested_arrays": make_path_aware({
            "matrix": [
                [
                    [1, 2],
                    [3, 4]
                ],
                [
                    [5, 6],
                    [7, 8, 9]
                ]
            ]
        }),
        
        "single_key_objects": make_path_aware([
            {"a": 1},
            {"b": 2},
            {"name": "special"}
        ])
    }


def add_path_annotations_using_set_path(obj: Any, path_key: str = "_jq_path") -> Any:
    """
    Add path information to an existing data structure using set_path().
    
    This function uses the existing set_path() functionality to add path annotations
    to every object in the data structure. It's more elegant than creating a separate
    traversal function since it reuses tested jqpy functionality.
    
    Args:
        obj: The data structure to annotate
        path_key: The key name to use for path information (default: "_jq_path")
        
    Returns:
        Copy of the data structure with path annotations added to all objects
        
    Examples:
        >>> data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        >>> annotated = add_path_annotations_using_set_path(data)
        >>> print(annotated)
        {
          "_jq_path": ".",
          "users": [
            {"_jq_path": ".users[0]", "name": "Alice"},
            {"_jq_path": ".users[1]", "name": "Bob"}
          ]
        }
    """
    from . import set_path  # Import here to avoid circular imports
    
    # Get all paths in the data structure
    path_map = create_path_map(obj)
    
    # Start with a deep copy of the original data
    import copy
    result = copy.deepcopy(obj)
    
    # Add path annotations using set_path for each object
    for path, value in path_map.items():
        # Only add path info to dictionaries (objects)
        if isinstance(value, dict):
            # Set the path annotation field to the current path
            path_with_annotation = f'{path}.{path_key}' if path != '.' else f'.{path_key}'
            # set_path returns a generator, so we need to get the first (and only) result
            set_path_results = list(set_path(result, path_with_annotation, path))
            if set_path_results:
                result = set_path_results[0]
    
    return result


def add_path_annotations(obj: Any, current_path: str = ".", path_key: str = "_jq_path") -> Any:
    """
    Add path information to an existing data structure without modifying original content.
    
    This function preserves all original data and adds a path annotation field to every
    object. Unlike make_path_aware(), this doesn't transform array elements - it only
    adds path information to dictionaries.
    
    Args:
        obj: The data structure to annotate
        current_path: The current jq path to this object
        path_key: The key name to use for path information (default: "_jq_path")
        
    Returns:
        Copy of the data structure with path annotations added to all objects
        
    Examples:
        >>> # Preserve original data, just add path info
        >>> data = {
        ...     "users": [
        ...         {"name": "Alice", "age": 30},
        ...         {"name": "Bob", "age": 25}
        ...     ],
        ...     "company": "TechCorp"
        ... }
        >>> annotated = add_path_annotations(data)
        >>> print(annotated)
        {
          "_jq_path": ".",
          "users": [
            {"_jq_path": ".users[0]", "name": "Alice", "age": 30},
            {"_jq_path": ".users[1]", "name": "Bob", "age": 25}
          ],
          "company": "TechCorp"
        }
        
        # Now you can see paths when debugging without changing data
        >>> users = list(get_path(annotated, '.users[]'))
        >>> for user in users:
        ...     print(f"User {user['name']} at {user['_jq_path']}")
        User Alice at .users[0]
        User Bob at .users[1]
        
        # Custom path key
        >>> custom = add_path_annotations(data, path_key="debug_path")
        >>> # Objects will have "debug_path" instead of "_jq_path"
    """
    if isinstance(obj, dict):
        # Create a new dict with path annotation
        result = {path_key: current_path}
        
        # Copy all original keys and recursively annotate values
        for key, value in obj.items():
            # Skip if the key is already a path annotation
            if key == path_key:
                continue
                
            # Calculate the path to this field
            if current_path == ".":
                new_path = f".{key}"
            else:
                new_path = f"{current_path}.{key}"
            
            # Recursively process the value
            result[key] = add_path_annotations(value, new_path, path_key)
            
        return result
        
    elif isinstance(obj, list):
        result = []
        for i, item in enumerate(obj):
            item_path = f"{current_path}[{i}]"
            
            # Recursively process items (only dicts get path annotations)
            result.append(add_path_annotations(item, item_path, path_key))
                    
        return result
    else:
        # For primitive values, return as-is (no path annotation possible)
        return obj


def extract_paths_from_results(results: List[Any], path_key: str = "_jq_path") -> List[str]:
    """
    Extract path information from annotated results.
    
    Helper function to extract the path annotations from objects returned
    by jq operations on path-annotated data.
    
    Args:
        results: List of results from jq operations
        path_key: The key used for path annotations
        
    Returns:
        List of paths where each result was found
        
    Examples:
        >>> annotated_data = add_path_annotations(your_data)
        >>> results = list(get_path(annotated_data, '.users[]'))
        >>> paths = extract_paths_from_results(results)
        >>> print(paths)
        ['.users[0]', '.users[1]']
    """
    paths = []
    for result in results:
        if isinstance(result, dict) and path_key in result:
            paths.append(result[path_key])
        else:
            paths.append("(no path info)")
    return paths


def create_path_map(obj: Any, current_path: str = ".") -> Dict[str, Any]:
    """
    Create a map of all paths to their values in a data structure.
    
    This creates a flat dictionary mapping jq path expressions to their
    corresponding values, making it easy to see all possible paths.
    
    Args:
        obj: The data structure to map
        current_path: The current path being processed
        
    Returns:
        Dictionary mapping paths to values
        
    Examples:
        >>> data = {"users": [{"name": "Alice"}, {"name": "Bob"}], "count": 2}
        >>> path_map = create_path_map(data)
        >>> for path, value in sorted(path_map.items()):
        ...     print(f"{path}: {value}")
        .: {'users': [{'name': 'Alice'}, {'name': 'Bob'}], 'count': 2}
        .count: 2
        .users: [{'name': 'Alice'}, {'name': 'Bob'}]
        .users[0]: {'name': 'Alice'}
        .users[0].name: Alice
        .users[1]: {'name': 'Bob'}
        .users[1].name: Bob
    """
    path_map = {current_path: obj}
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            if current_path == ".":
                new_path = f".{key}"
            else:
                new_path = f"{current_path}.{key}"
            
            # Recursively map nested paths
            nested_paths = create_path_map(value, new_path)
            path_map.update(nested_paths)
            
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            item_path = f"{current_path}[{i}]"
            
            # Recursively map nested paths
            nested_paths = create_path_map(item, item_path)
            path_map.update(nested_paths)
    
    return path_map


def annotate_objects_with_paths_using_atomic_fn(obj: Any, annotation_key: str = "_jq_path") -> Any:
    """
    Add path annotations using the enhanced resolve_to_atomic_paths() function.
    
    This demonstrates the power of the generic resolve_to_atomic_paths() function
    with type filtering. Now we can use the public API directly to find object paths!
    
    Args:
        obj: The data structure to annotate
        annotation_key: The key name for the path annotation
        
    Returns:
        Copy of the data structure with path annotations added to all objects
        
    Examples:
        >>> data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        >>> annotated = annotate_objects_with_paths_using_atomic_fn(data)
        >>> # Uses the public resolve_to_atomic_paths API with objects filter
    """
    from . import set_path
    from .operations import resolve_to_atomic_paths
    import copy
    
    # Step 1: Use the enhanced public API to get object paths directly!
    object_paths = list(resolve_to_atomic_paths(obj, ".", type_filter="objects"))
    object_paths.append(".")  # Add root path
    
    # Step 2: Start with a deep copy of the original data
    result = copy.deepcopy(obj)
    
    # Step 3: Iterate over object paths to add annotations using set_path
    for object_path in sorted(set(object_paths)):  # Remove duplicates
        # Key name and value derived from the path
        annotation_path = f"{object_path}.{annotation_key}" if object_path != "." else f".{annotation_key}"
        
        # Use set_path to add the annotation
        set_result = list(set_path(result, annotation_path, object_path))
        if set_result:
            result = set_result[0]
    
    return result


def annotate_objects_with_paths(obj: Any, annotation_key: str = "_jq_path") -> Any:
    """
    Add path annotations to all objects in a data structure.
    
    This function:
    1. Gets the paths for all objects in the data
    2. Iterates over those paths to add key-value pairs  
    3. Where the key name and value are derived from the paths that matched individual objects
    
    Args:
        obj: The data structure to annotate
        annotation_key: The key name for the path annotation
        
    Returns:
        Copy of the data structure with path annotations added to all objects
        
    Examples:
        >>> data = {"users": [{"name": "Alice"}, {"name": "Bob"}], "config": {"theme": "dark"}}
        >>> annotated = annotate_objects_with_paths(data)
        >>> # Result: all objects now have "_jq_path" showing their location
        
        >>> # Custom annotation key
        >>> custom = annotate_objects_with_paths(data, annotation_key="debug_path") 
        >>> # Result: all objects have "debug_path" instead
    """
    from . import set_path  # Import here to avoid circular imports
    import copy
    
    # Step 1: Get paths for all objects in the data
    all_paths = create_path_map(obj)
    
    # Step 2: Start with a deep copy of the original data
    result = copy.deepcopy(obj)
    
    # Step 3: Iterate over those paths to add key-value pairs
    for path, value in all_paths.items():
        # Only annotate dictionaries (objects)
        if isinstance(value, dict):
            # Key name derived from annotation_key parameter
            # Value derived from the path that matched this individual object
            if path == ".":
                annotation_path = f".{annotation_key}"
            else:
                annotation_path = f"{path}.{annotation_key}"
            
            # Use set_path to add the annotation
            set_result = list(set_path(result, annotation_path, path))
            if set_result:
                result = set_result[0]
    
    return result


def annotate_with_custom_values(obj: Any, value_function, annotation_key: str = "_annotation") -> Any:
    """
    Add custom annotations to all objects based on their paths.
    
    This is a more flexible version that allows custom value generation
    based on the path information.
    
    Args:
        obj: The data structure to annotate
        value_function: Function that takes a path and returns the annotation value
        annotation_key: The key name for the annotation
        
    Returns:
        Copy of the data structure with custom annotations
        
    Examples:
        >>> # Add depth information
        >>> def depth_calculator(path):
        ...     return path.count('.') + path.count('[')
        >>> annotated = annotate_with_custom_values(data, depth_calculator, "_depth")
        
        >>> # Add path type information  
        >>> def path_type(path):
        ...     if '[' in path:
        ...         return "array_element" 
        ...     elif path == ".":
        ...         return "root"
        ...     else:
        ...         return "object_field"
        >>> typed = annotate_with_custom_values(data, path_type, "_path_type")
    """
    from . import set_path
    import copy
    
    # Get all object paths
    all_paths = create_path_map(obj)
    result = copy.deepcopy(obj)
    
    # Iterate over paths and add custom annotations
    for path, value in all_paths.items():
        if isinstance(value, dict):
            # Generate custom value using the provided function
            custom_value = value_function(path)
            
            # Create annotation path
            if path == ".":
                annotation_path = f".{annotation_key}"
            else:
                annotation_path = f"{path}.{annotation_key}"
            
            # Add the custom annotation
            set_result = list(set_path(result, annotation_path, custom_value))
            if set_result:
                result = set_result[0]
    
    return result


# Pre-generated test datasets for common use cases
PATH_AWARE_TEST_DATA = create_path_aware_test_data()