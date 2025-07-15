"""
Core traversal functionality for jqpy.

This module provides the base iterator that powers all path operations.
"""
from typing import Any, Iterator, List, Tuple, Union
from .parser import PathComponent, PathComponentType

def traverse(
    data: Any, 
    path_components: List[PathComponent]
) -> Iterator[Tuple[List[PathComponent], Any]]:
    """Core traversal function that yields (path_taken, value) pairs.
    
    Args:
        data: The data structure to traverse
        path_components: List of path components to follow
        
    Yields:
        Tuples of (path_taken, value) where:
        - path_taken: The actual path taken through the data structure
        - value: The value found at that path
    """
    if not path_components:
        yield [], data
        return
        
    component, *rest = path_components
    
    if component.type == PathComponentType.KEY:
        if component.value == '*':  # Wildcard
            if isinstance(data, dict):
                for k, v in data.items():
                    for subpath, value in traverse(v, rest):
                        yield [component._replace(value=k), *subpath], value
            elif isinstance(data, (list, tuple)):
                for i, item in enumerate(data):
                    for subpath, value in traverse(item, rest):
                        yield [component._replace(value=i), *subpath], value
        else:  # Direct key access
            if isinstance(data, dict) and component.value in data:
                for subpath, value in traverse(data[component.value], rest):
                    yield [component, *subpath], value
    
    elif component.type == PathComponentType.INDEX:
        if isinstance(data, (list, tuple)):
            idx = component.value
            if -len(data) <= idx < len(data):
                for subpath, value in traverse(data[idx], rest):
                    yield [component, *subpath], value
    
    # TODO: Add support for other component types (selectors, etc.)
    
    # If we get here, the path didn't match anything
    return
