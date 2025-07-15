"""
Core traversal functionality for jqpy.

This module provides the base iterator that powers all path operations.
"""
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union, cast
from .parser import PathComponent, PathComponentType

def traverse(
    data: Any, 
    path_components: List[PathComponent],
    current_path: Optional[List[PathComponent]] = None
) -> Iterator[Tuple[List[PathComponent], Any]]:
    """Core traversal function that yields (path_taken, value) pairs.
    
    Args:
        data: The data structure to traverse
        path_components: List of path components to follow
        current_path: The path taken so far (used internally for recursion)
        
    Yields:
        Tuples of (path_taken, value) where:
        - path_taken: The actual path taken through the data structure
        - value: The value found at that path
    """
    if current_path is None:
        current_path = []

    if not path_components:
        yield current_path, data
        return

    component, *rest = path_components
    
    # Handle wildcard matching
    if component.type in (PathComponentType.WILDCARD, PathComponentType.KEY and component.value == '*'):
        # Handle dictionary wildcard
        if isinstance(data, dict):
            for k, v in data.items():
                new_component = PathComponent(
                    type=PathComponentType.KEY,
                    value=k,
                    raw_value=str(k)
                )
                new_path = [*current_path, new_component]
                
                # If next component is a selector, apply it to the current value
                if rest and rest[0].type == PathComponentType.SELECTOR:
                    selector = rest[0].value
                    if _matches_selector(v, selector):
                        # If there are components after the selector, continue with those
                        if len(rest) > 1:
                            yield from traverse(v, rest[1:], new_path)
                        else:
                            # If selector is the last component, yield the matching value
                            yield new_path, v
                else:
                    yield from traverse(v, rest, new_path)
        # Handle list/tuple wildcard
        elif isinstance(data, (list, tuple)):
            for i, item in enumerate(data):
                new_component = PathComponent(
                    type=PathComponentType.INDEX,
                    value=i,
                    raw_value=str(i)
                )
                new_path = [*current_path, new_component]
                
                # If next component is a selector, apply it to the current item
                if rest and rest[0].type == PathComponentType.SELECTOR and isinstance(item, dict):
                    selector = rest[0].value
                    if _matches_selector(item, selector):
                        # If there are components after the selector, continue with those
                        if len(rest) > 1:
                            yield from traverse(item, rest[1:], new_path)
                        else:
                            # If selector is the last component, yield the matching item
                            yield new_path, item
                else:
                    yield from traverse(item, rest, new_path)
        # For non-container types, don't yield anything for wildcard
        return
    
    # Handle selector
    elif component.type == PathComponentType.SELECTOR:
        selector = component.value
        
        # If we're at a dictionary, check if it matches the selector
        if isinstance(data, dict):
            if _matches_selector(data, selector):
                if not rest:  # This is the last component
                    yield current_path, data
                else:  # Continue with the rest of the path
                    yield from traverse(data, rest, current_path)
        
        # If we're at a list, apply selector to each item
        elif isinstance(data, (list, tuple)):
            for i, item in enumerate(data):
                if not isinstance(item, dict):
                    continue
                if _matches_selector(item, selector):
                    new_path = current_path + [PathComponent(
                        type=PathComponentType.INDEX,
                        value=i,
                        raw_value=str(i)
                    )]
                    if not rest:  # This is the last component
                        yield new_path, item
                    else:  # Continue with the rest of the path
                        yield from traverse(item, rest, new_path)
        return
    
    # Handle direct key access
    if component.type == PathComponentType.KEY:
        if isinstance(data, dict) and component.value in data:
            yield from traverse(data[component.value], rest, [*current_path, component])
    
    # Handle array index access
    elif component.type == PathComponentType.INDEX:
        if isinstance(data, (list, tuple)):
            idx = component.value
            # Handle negative indices and bounds checking
            if -len(data) <= idx < len(data):
                yield from traverse(data[idx], rest, [*current_path, component])
    
    # Handle the case where we have more components but current data isn't a container
    # This will naturally stop the recursion for that path
    
    # TODO: Add support for other component types (selectors, etc.)
    
    # If we get here, the path didn't match anything
    return


def _matches_selector(value: Any, selector: dict) -> bool:
    """Check if a value matches the given selector condition.
    
    Args:
        value: The value to check (should be a dictionary)
        selector: Selector condition (from _parse_selector)
        
    Returns:
        bool: True if the value matches the selector condition
        
    Raises:
        ValueError: If the selector type is not supported
    """
    if not isinstance(value, dict):
        return False
        
    if selector['type'] == 'compare':
        key = selector['key']
        op = selector['op']
        target = selector['value']
        
        if key not in value:
            return False
            
        current = value[key]
        
        # Only compare if types are compatible
        if not isinstance(current, type(target)) and not (isinstance(current, (int, float)) and isinstance(target, (int, float))):
            return False
            
        if op == '==':
            return current == target
        elif op == '>':
            return current > target
        elif op == '<':
            return current < target
        elif op == '>=':
            return current >= target
        elif op == '<=':
            return current <= target
    
    raise ValueError(f"Unsupported selector type: {selector['type']}")
