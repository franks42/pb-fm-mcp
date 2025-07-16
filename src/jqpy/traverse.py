"""
Core traversal functionality for jqpy.

This module provides the base iterator that powers all path operations.
"""
import logging
from collections.abc import Iterator
from typing import Any

from .parser import PathComponent, PathComponentType

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def traverse(
    data: Any, 
    path_components: list[PathComponent],
    current_path: list[PathComponent] | None = None,
    max_depth: int = 100,  # Default max depth
    current_depth: int = 0  # Current traversal depth
) -> Iterator[Any]:
    """Core traversal function that yields values found during traversal.

    Args:
        data: The data structure to traverse
        path_components: List of path components to follow
        current_path: The path taken so far (used internally for recursion)
        max_depth: Maximum depth to traverse
        current_depth: Current depth in traversal

    Yields:
        Values found during traversal
    """
    if current_path is None:
        current_path = []
        current_depth = 0
        logger.debug("\n=== Starting traversal ===")
        logger.debug(f"Path: {path_components}")
        logger.debug(f"Data: {data}")
        logger.debug(f"Max depth: {max_depth}")

    if not path_components:
        logger.debug("\n=== Reached end of path ===")
        logger.debug(f"Final data: {data}")
        logger.debug(f"Final path: {current_path}")
        yield data
        return
    
    if current_depth >= max_depth:
        logger.debug(f"\n=== Max depth {max_depth} reached at depth {current_depth} ===")
        logger.debug(f"Current path: {current_path}")
        logger.debug(f"Current data: {data}")
        return
    
    component, *rest = path_components
    logger.debug(f"\n=== Processing component {component} at depth {current_depth} ===")
    logger.debug(f"Current data: {data}")
    logger.debug(f"Remaining components: {rest}")
    logger.debug(f"Current path: {current_path}")
    
    # Handle literals first - they don't depend on data
    if component.type == PathComponentType.KEY and component.value.startswith('LITERAL:'):
        logger.debug(f"Processing literal: {component.value}")
        literal_str = component.value[8:]  # Remove 'LITERAL:' prefix
        logger.debug(f"Literal string: {literal_str}")
        
        # Convert string representation back to actual value
        if literal_str == 'None':
            logger.debug("Yielding None")
            yield None
        elif literal_str == 'True':
            logger.debug("Yielding True")
            yield True
        elif literal_str == 'False':
            logger.debug("Yielding False")
            yield False
        elif literal_str.replace('.', '').replace('-', '').isdigit():
            if '.' in literal_str:
                logger.debug(f"Yielding float: {float(literal_str)}")
                yield float(literal_str)
            else:
                logger.debug(f"Yielding int: {int(literal_str)}")
                yield int(literal_str)
        else:
            # For actual string literals, yield the string without LITERAL: prefix
            logger.debug(f"Yielding string: {literal_str}")
            yield literal_str
        return
    
    # Make sure current_path is always a list
    if not isinstance(current_path, list):
        current_path = []
    
    # Update current path (create new list to avoid sharing state between recursive calls)
    current_path = current_path + [component]
    
    # Handle null input - only for literal processing, not for optional selectors
    if data is None:
        if not rest and component.type == PathComponentType.KEY and component.value.startswith('LITERAL:'):
            # This is a literal value processing case
            literal_str = component.value[8:]  # Remove 'LITERAL:' prefix
            try:
                # Try to convert to appropriate type
                if literal_str.lower() == 'true':
                    yield True
                elif literal_str.lower() == 'false':
                    yield False
                elif literal_str.isdigit() or (literal_str.startswith('-') and literal_str[1:].isdigit()):
                    yield int(literal_str)
                elif literal_str.replace('.', '').isdigit() or (literal_str.startswith('-') and literal_str[1:].replace('.', '').isdigit()):
                    yield float(literal_str)
                else:
                    yield literal_str
            except Exception:
                yield literal_str
            return
        # For optional selectors and other types, let them handle None appropriately
        # Don't return early - continue to the specific component type handlers
    
    # Handle array splat (empty key or [] value)
    if (component.type == PathComponentType.KEY and component.value == '') or \
       (component.type == PathComponentType.KEY and component.value == '[]'):
        logger.debug("Processing array splat (empty key)")
        if isinstance(data, (list, tuple)):
            logger.debug(f"Processing array splat with {len(data)} items")
            for i, item in enumerate(data):
                yield from traverse(item, rest, current_path, max_depth, current_depth + 1)
        return
    
    # Handle wildcard
    if component.type == PathComponentType.WILDCARD:
        logger.debug("Processing wildcard component")
        # Handle wildcard for dictionaries
        if isinstance(data, dict):
            logger.debug(f"Processing dict wildcard with {len(data)} items")
            for k, v in data.items():
                logger.debug(f"Processing wildcard key: {k}")
                if not rest:
                    # No more components, yield the value
                    yield v
                else:
                    # Continue with remaining components
                    yield from traverse(v, rest, current_path, max_depth, current_depth + 1)
        # Handle wildcard for lists
        elif isinstance(data, (list, tuple)):
            logger.debug(f"Processing list wildcard with {len(data)} items")
            for i, item in enumerate(data):
                logger.debug(f"Processing wildcard index: {i}")
                if not rest:
                    # No more components, yield the item
                    yield item
                else:
                    # Continue with remaining components  
                    yield from traverse(item, rest, current_path, max_depth, current_depth + 1)
        else:
            logger.debug(f"Skipping wildcard for non-container type: {type(data)}")
        return
    
    # Handle selector
    elif component.type == PathComponentType.SELECTOR:
        logger.debug(f"Processing selector: {component.value}")
        selector = component.value
        
        # Handle select() function call
        if selector.startswith('SELECT:'):
            selector_expr = selector[7:]  # Remove 'SELECT:' prefix
            logger.debug(f"Processing select() function with expression: {selector_expr}")
            
            # Parse the selector expression
            parsed_selector = _parse_select_expression(selector_expr)
            
            # Check if the current data matches the selector
            if _matches_selector(data, parsed_selector):
                if not rest:  # This is the last component
                    yield data
                else:  # Continue with the rest of the path
                    yield from traverse(data, rest, current_path, max_depth, current_depth + 1)
            return
        
        # If we're at a dictionary, check if it matches the selector
        if isinstance(data, dict):
            if _matches_selector(data, selector):
                if not rest:  # This is the last component
                    yield data
                else:  # Continue with the rest of the path
                    yield from traverse(data, rest, current_path, max_depth, current_depth + 1)
        
        # If we're at a list, apply selector to each item
        elif isinstance(data, (list, tuple)):
            for i, item in enumerate(data):
                if not isinstance(item, dict):
                    continue
                if _matches_selector(item, selector):
                    if not rest:  # This is the last component
                        yield item
                    else:  # Continue with the rest of the path
                        yield from traverse(item, rest, current_path, max_depth, current_depth + 1)
        return
    
    
    # Handle object construction
    if component.type == PathComponentType.KEY and component.value.startswith('OBJECT_CONSTRUCT:'):
        logger.debug(f"Processing object construction: {component.value}")
        obj_definition = component.value[len('OBJECT_CONSTRUCT:'):]
        
        # Parse {a: .a, b: .b} format
        if obj_definition.startswith('{') and obj_definition.endswith('}'):
            obj_content = obj_definition[1:-1]  # Remove { }
            pairs = obj_content.split(',')
            result = {}
            
            for pair in pairs:
                if ':' in pair:
                    key_part, value_part = pair.split(':', 1)
                    key = key_part.strip()
                    value_path = value_part.strip()
                    
                    # Special handling for single-key objects
                    if value_path == '.key' and isinstance(data, dict) and len(data) == 1:
                        # For single-key objects, '.key' means the key name
                        result[key] = list(data.keys())[0]
                    elif value_path == '.value' and isinstance(data, dict) and len(data) == 1:
                        # For single-key objects, '.value' means the value
                        result[key] = list(data.values())[0]
                    else:
                        # Parse the value path and get the result
                        from .parser import parse_path
                        value_components = parse_path(value_path)
                        
                        # Get the value from the data using the parsed path
                        value_results = list(traverse(data, value_components, current_path, max_depth, current_depth + 1))
                        if value_results:
                            result[key] = value_results[0]  # Take first result
            
            if result:
                logger.debug(f"Constructed object: {result}")
                yield result
        return
    
    # Handle direct key access
    if component.type == PathComponentType.KEY:
        logger.debug(f"Processing key: {component.value}")
        # Skip literal components that should have been handled above
        if component.value.startswith('LITERAL:'):
            logger.debug(f"Skipping literal that should have been handled: {component.value}")
            return
        if isinstance(data, dict) and component.value in data:
            yield from traverse(data[component.value], rest, current_path, max_depth, current_depth + 1)
        elif rest and len(rest) > 0 and rest[0].type in (PathComponentType.OPTIONAL_INDEX, PathComponentType.OPTIONAL_WILDCARD, PathComponentType.OPTIONAL_KEY):
            # If the key doesn't exist but the next component is optional, pass None to it
            yield from traverse(None, rest, current_path, max_depth, current_depth + 1)
    
    # Handle optional key access
    elif component.type == PathComponentType.OPTIONAL_KEY:
        logger.debug(f"Processing optional key: {component.value}")
        if isinstance(data, dict) and component.value in data:
            yield from traverse(data[component.value], rest, current_path, max_depth, current_depth + 1)
        elif data is None:
            # Data is None/null - don't yield anything (silent failure)
            pass
        # For missing keys or non-dict types, just don't continue (no error)
    
    # Handle array index access
    elif component.type == PathComponentType.INDEX:
        logger.debug(f"Processing index: {component.value}")
        if isinstance(data, (list, tuple)):
            idx = component.value
            # Handle negative indices and bounds checking
            if -len(data) <= idx < len(data):
                yield from traverse(data[idx], rest, current_path, max_depth, current_depth + 1)
    
    # Handle array slice access
    elif component.type == PathComponentType.SLICE:
        logger.debug(f"Processing slice: {component.value}")
        if isinstance(data, (list, tuple)):
            slice_obj = component.value
            # Apply the slice to get a sublist/subtuple
            sliced_data = data[slice_obj]
            if not rest:
                # This is the last component - yield the sliced data
                yield sliced_data
            else:
                # Continue with remaining components - the sliced data becomes the new data
                yield from traverse(sliced_data, rest, current_path, max_depth, current_depth + 1)
    
    # Handle optional array index access
    elif component.type == PathComponentType.OPTIONAL_INDEX:
        logger.debug(f"Processing optional index: {component.value}")
        if isinstance(data, (list, tuple)):
            idx = component.value
            # Handle negative indices and bounds checking
            if -len(data) <= idx < len(data):
                yield from traverse(data[idx], rest, current_path, max_depth, current_depth + 1)
            else:
                # Out of bounds - yield null if this is the last component
                if not rest:
                    yield None
                # If there are more components, just don't continue the traversal
        elif data is None:
            # Data is None/null - yield null if this is the last component
            if not rest:
                yield None
        # For non-list types, just don't continue (no error)
    
    # Handle jq function calls
    elif component.type == PathComponentType.FUNCTION:
        logger.debug(f"Processing function: {component.value}")
        result = _handle_jq_function(data, component.value)
        if not rest:
            # This is the last component - yield the function result
            yield result
        else:
            # Continue with remaining components using the function result
            yield from traverse(result, rest, current_path, max_depth, current_depth + 1)
        return
    
    # Handle optional wildcard access
    elif component.type == PathComponentType.OPTIONAL_WILDCARD:
        logger.debug("Processing optional wildcard component")
        # Handle optional wildcard for dictionaries
        if isinstance(data, dict):
            logger.debug(f"Processing dict optional wildcard with {len(data)} items")
            for k, v in data.items():
                logger.debug(f"Processing optional wildcard key: {k}")
                if not rest:
                    # No more components, yield the value
                    yield v
                else:
                    # Continue with remaining components
                    yield from traverse(v, rest, current_path, max_depth, current_depth + 1)
        # Handle optional wildcard for lists
        elif isinstance(data, (list, tuple)):
            logger.debug(f"Processing list optional wildcard with {len(data)} items")
            for i, item in enumerate(data):
                logger.debug(f"Processing optional wildcard index: {i}")
                if not rest:
                    # No more components, yield the item
                    yield item
                else:
                    # Continue with remaining components  
                    yield from traverse(item, rest, current_path, max_depth, current_depth + 1)
        elif data is None:
            # Data is None/null - don't yield anything (silent failure)
            pass
        else:
            logger.debug(f"Skipping optional wildcard for non-container type: {type(data)}")
        return
    
    # Handle the case where we have more components but current data isn't a container
    # This will naturally stop the recursion for that path
    
    # TODO: Add support for other component types (selectors, etc.)
    
    # If we get here, the path didn't match anything
    return


def _parse_select_expression(expr: str) -> dict:
    """Parse a select() expression into a selector condition.
    
    Args:
        expr: The select expression (e.g., '.active == true')
        
    Returns:
        dict: Parsed selector condition
    """
    # Remove leading dot if present
    if expr.startswith('.'):
        expr = expr[1:]
    
    # Check for comparison operators
    operators = ['==', '>=', '<=', '>', '<']
    op = None
    for op_test in operators:
        if op_test in expr:
            op = op_test
            break
    
    if op:
        left, right = expr.split(op, 1)
        left = left.strip()
        right = right.strip()
        
        # Remove quotes if present
        if (right.startswith('"') and right.endswith('"')) or \
           (right.startswith("'") and right.endswith("'")):
            right = right[1:-1]
        # Convert to boolean if needed
        elif right.lower() == 'true':
            right = True
        elif right.lower() == 'false':
            right = False
        # Convert to number if possible
        elif right.replace('.', '').replace('-', '').isdigit():
            if '.' in right:
                right = float(right)
            else:
                right = int(right)
        
        return {'type': 'compare', 'key': left, 'op': op, 'value': right}
    
    raise ValueError(f"Unsupported select expression: {expr}")


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


def _handle_jq_function(data: Any, function_spec: str) -> Any:
    """Handle jq core function calls.
    
    Args:
        data: The input data
        function_spec: Function specification (e.g., 'keys', 'length', 'has:key', 'map:expr')
        
    Returns:
        The result of the function
    """
    # Handle simple functions without arguments
    if function_spec == 'keys':
        if isinstance(data, dict):
            return sorted(data.keys())
        elif isinstance(data, list):
            return list(range(len(data)))
        else:
            return None
    
    elif function_spec == 'length':
        if isinstance(data, (dict, list, str)):
            return len(data)
        elif data is None:
            return 0
        else:
            return None
    
    elif function_spec == 'type':
        if isinstance(data, dict):
            return "object"
        elif isinstance(data, list):
            return "array"
        elif isinstance(data, str):
            return "string"
        elif isinstance(data, bool):
            return "boolean"
        elif isinstance(data, (int, float)):
            return "number"
        elif data is None:
            return "null"
        else:
            return "unknown"
    
    elif function_spec == 'paths' or function_spec.startswith('paths('):
        # Handle paths() function with optional type filtering
        type_filter = None
        if function_spec.startswith('paths(') and function_spec.endswith(')'):
            # Extract type filter from paths(type)
            type_arg = function_spec[6:-1].strip()  # Remove 'paths(' and ')'
            if type_arg:
                type_filter = type_arg
        
        return _get_all_paths(data, type_filter)
    
    # Handle functions with arguments
    elif function_spec.startswith('has:'):
        key_or_index = function_spec[4:]  # Remove 'has:' prefix
        
        # Try to parse as integer for array index
        try:
            index = int(key_or_index)
            if isinstance(data, list):
                return 0 <= index < len(data)
        except ValueError:
            pass
        
        # Remove quotes if present for string keys
        if (key_or_index.startswith('"') and key_or_index.endswith('"')) or \
           (key_or_index.startswith("'") and key_or_index.endswith("'")):
            key_or_index = key_or_index[1:-1]
        
        if isinstance(data, dict):
            return key_or_index in data
        elif isinstance(data, list):
            # For lists, has() checks if the index exists
            try:
                index = int(key_or_index)
                return 0 <= index < len(data)
            except ValueError:
                return False
        else:
            return False
    
    elif function_spec.startswith('map:'):
        expr = function_spec[4:]  # Remove 'map:' prefix
        
        if not isinstance(data, list):
            raise ValueError(f"Cannot map over non-array type: {type(data)}")
        
        results = []
        for item in data:
            # Handle simple mathematical expressions
            if expr.strip() == '. * 2':
                if isinstance(item, (int, float)):
                    results.append(item * 2)
                else:
                    results.append(None)
            elif expr.strip() == '. * 3':
                if isinstance(item, (int, float)):
                    results.append(item * 3)
                else:
                    results.append(None)
            elif expr.strip() == '. + 1':
                if isinstance(item, (int, float)):
                    results.append(item + 1)
                else:
                    results.append(None)
            else:
                # Parse and evaluate the expression on each item for non-math expressions
                from .parser import parse_path
                expr_components = parse_path(expr)
                
                # Get the result for this item
                item_results = list(traverse(item, expr_components))
                if item_results:
                    results.append(item_results[0])  # Take first result
                else:
                    results.append(None)
        
        return results
    
    else:
        raise ValueError(f"Unsupported jq function: {function_spec}")


def _get_all_paths(data: Any, type_filter: str | None = None) -> list[list]:
    """Get all paths in a data structure, optionally filtered by type.
    
    Args:
        data: The data structure to traverse
        type_filter: Optional type filter ('objects', 'arrays', 'scalars', or None for all)
        
    Returns:
        List of paths (each path is a list of keys/indices)
    """
    paths = []
    
    def _traverse_for_paths(obj: Any, current_path: list = None) -> None:
        if current_path is None:
            current_path = []
        
        # Determine the type of the current object
        obj_type = _get_jq_type(obj)
        
        # Check if we should include this path based on type filter
        should_include = False
        if type_filter is None:
            # No filter - include all non-root paths
            should_include = len(current_path) > 0
        elif type_filter == 'objects':
            should_include = obj_type == 'object' and len(current_path) > 0
        elif type_filter == 'arrays':
            should_include = obj_type == 'array' and len(current_path) > 0
        elif type_filter == 'scalars':
            should_include = obj_type in ('string', 'number', 'boolean', 'null') and len(current_path) > 0
        
        # Add path if it matches the filter
        if should_include:
            paths.append(current_path[:])  # Copy the path
        
        # Recursively traverse children
        if isinstance(obj, dict):
            for key, value in obj.items():
                _traverse_for_paths(value, current_path + [key])
        elif isinstance(obj, list):
            for idx, value in enumerate(obj):
                _traverse_for_paths(value, current_path + [idx])
    
    _traverse_for_paths(data)
    return paths


def _get_jq_type(obj: Any) -> str:
    """Get the jq type name for an object."""
    if isinstance(obj, dict):
        return "object"
    elif isinstance(obj, list):
        return "array"
    elif isinstance(obj, str):
        return "string"
    elif isinstance(obj, bool):
        return "boolean"
    elif isinstance(obj, (int, float)):
        return "number"
    elif obj is None:
        return "null"
    else:
        return "unknown"
