import json
import re
import time
from collections.abc import Callable, Iterator, MutableMapping, MutableSequence
from typing import Any, Dict, List, Optional, Sequence, Tuple, TypeVar, Union, cast

# === TYPE DEFINITIONS ===

# Type aliases
Selector = Union[str, int, slice, Callable[..., bool]]
PathType = Union[str, int, List[Union[str, int, dict, Callable, slice]]]
T = TypeVar('T')

# Constants
DEFAULT_SEPARATOR = '.'

# Type definitions for HTTP response
class Response:
    """Mock response class for type hints."""
    status_code: int
    text: str
    json: Callable[[], Dict[str, Any]]
    headers: Dict[str, str]
    elapsed: float
    request: Any

# === SELECTOR HELPERS ===

def _make_selector(predicate):
    """Create a selector function that applies the given predicate to the value.
    
    Args:
        predicate: A function that takes a value and returns a boolean
        
    Returns:
        A selector function that applies the predicate to the value
    """
    def selector(key, value):
        return predicate(value)
    return selector

def _make_dict_selector(predicate):
    """Create a selector function that applies the given predicate to a dictionary value.
    
    Args:
        predicate: A function that takes a dictionary and returns a boolean
        
    Returns:
        A selector function that applies the predicate to dictionary values.
        The returned function has the signature (key, value) -> bool.
    """
    def selector(key, value):
        return isinstance(value, dict) and predicate(value)
    return selector

def select_key_exists(key):
    """Create a selector that matches dictionaries containing the specified key."""
    return _make_dict_selector(lambda d: key in d)

def select_key_missing(key):
    """Create a selector that matches dictionaries not containing the specified key."""
    return _make_dict_selector(lambda d: key not in d)

def select_type(type_):
    """Create a selector that matches values of the specified type."""
    return _make_selector(lambda v: isinstance(v, type_))

def select_regex(field, pattern):
    """Create a selector that matches dictionary values where the specified field matches the regex pattern."""
    regex = re.compile(pattern)
    return _make_dict_selector(
        lambda d: field in d and isinstance(d[field], str) and bool(regex.search(d[field]))
    )

def _make_comparison_selector(field, value, op):
    """Helper to create comparison selectors (gt, lt, eq)."""
    return _make_dict_selector(
        lambda d: d.get(field) is not None and op(d[field], value)
    )

def select_gt(field, value):
    """Create a selector that matches dictionary values where the specified field is greater than the value."""
    return _make_comparison_selector(field, value, lambda a, b: a > b)

def select_lt(field, value):
    """Create a selector that matches dictionary values where the specified field is less than the value."""
    return _make_comparison_selector(field, value, lambda a, b: a < b)

def select_eq(field, value):
    """Create a selector that matches dictionary values where the specified field equals the value."""
    return _make_comparison_selector(field, value, lambda a, b: a == b)

def select_contains(field, substring):
    """Create a selector that matches dictionary values where the specified field contains the substring."""
    return _make_dict_selector(
        lambda d: substring in str(d.get(field, ""))
    )

def select_all(key, value):
    """A selector that matches all values."""
    return True


def select_wildcard(key, value):
    """A selector that matches any key/index in a container (dictionary or list).
    
    This selector will match any key in a dictionary or any index in a list.
    It's used to implement the wildcard '*' functionality in paths.
    
    Args:
        key: The key or index being checked
        value: The value being checked (unused in this selector)
        
    Returns:
        bool: Always returns True since this matches any key/index
    """
    return True

# === CORE PATH LOGIC ===

def _normalize_path(path: Union[str, PathType], separator: str = '.') -> PathType:
    if isinstance(path, str):
        return [int(p) if p.isdigit() or (p.startswith('-') and p[1:].isdigit()) else p for p in path.split(separator)]
    return path

def dict_selector(sel: dict) -> Callable[[Any, Any], bool]:
    """
    Create a selector function that matches dictionaries containing all specified key-value pairs.
    
    Args:
        sel: Dictionary of key-value pairs that must be matched
        
    Returns:
        A selector function that returns True if the input is a dict containing all key-value pairs from sel
    """
    def selector(key, value):
        if not isinstance(value, dict):
            return False
        return all(value.get(k) == v for k, v in sel.items())
    return selector

def key_value_selector(key: Any, value: Any) -> Callable[[Any, Any], bool]:
    """
    Create a selector that matches a specific key-value pair.
    
    Args:
        key: The key to match
        value: The value to match
        
    Returns:
        A selector function that returns True if the input is a dict containing the key-value pair
    """
    def selector(k, v):
        return isinstance(v, dict) and v.get(key) == value
    return selector

def _convert_selector(sel: Selector):
    if isinstance(sel, dict):
        return dict_selector(sel)
    elif sel == '*':
        return select_wildcard
    elif isinstance(sel, (str, int, slice)) or callable(sel):
        return sel
    else:
        raise ValueError(f"Unsupported selector type: {type(sel).__name__}")

def _convert_selectors_path(selectors: PathType) -> list:
    if isinstance(selectors, str):
        # Split the path and convert each component
        parts = selectors.split('.')
        result = []
        for part in parts:
            # Try to convert to int if it's a number
            if part.isdigit() or (part.startswith('-') and part[1:].isdigit()):
                result.append(int(part))
            # Convert wildcard to the selector function
            elif part == '*':
                result.append(select_wildcard)
            else:
                result.append(part)
        return result
    elif isinstance(selectors, list):
        # Convert each selector in the list
        result = []
        for s in selectors:
            # If it's a string that looks like a number, convert to int
            if isinstance(s, str) and (s.isdigit() or (s.startswith('-') and s[1:].isdigit())):
                result.append(int(s))
            # Otherwise, convert using _convert_selector if needed
            elif not isinstance(s, (str, int, slice)):
                result.append(_convert_selector(s))
            else:
                result.append(s)
        return result
    else:
        # Single selector
        if isinstance(selectors, str) and (selectors.isdigit() or (selectors.startswith('-') and selectors[1:].isdigit())):
            return [int(selectors)]
        return [_convert_selector(selectors)]

def _is_literal_selector(selector: Any) -> bool:
    """Check if a selector is a literal (string or int) that can be used as a key/index."""
    return isinstance(selector, (str, int)) and not callable(selector) and not (isinstance(selector, str) and selector == '*')

def _get_literal_value(selector: Any) -> Any:
    """Get the literal value from a selector if it's a literal selector."""
    if _is_literal_selector(selector):
        return selector
    if isinstance(selector, dict) and len(selector) == 1 and 'eq' in selector:
        return selector['eq']
    return None

def _match_selector(key_or_index: Any, value: Any, selector: Any) -> bool:
    """Match a value against a selector.
    
    This function handles all selector types including:
    - Wildcard selectors (* or select_all)
    - Callable selectors (functions that take key and value)
    - Dictionary selectors (must match all key-value pairs)
    - Slice selectors (for list indices)
    - Direct value comparison (for exact matches)
    
    Args:
        key_or_index: The key or index being matched
        value: The value being matched
        selector: The selector to match against
        
    Returns:
        bool: True if the value matches the selector, False otherwise
    """
    # Handle None selector (matches everything)
    if selector is None:
        return True
        
    # Handle wildcard selector (matches anything)
    if selector is Ellipsis or selector == '*':
        return True
        
    # Handle callable selectors
    if callable(selector):
        # Special case for select_all/select_wildcard - only match list indices
        if (selector.__name__ in ('select_all', 'select_wildcard') or 
            selector == select_all or 
            selector == select_wildcard):
            # Only match if we're checking a list index (key_or_index is an integer)
            # and this is being called from within a list context
            return isinstance(key_or_index, int)
            
        # For other callable selectors, try calling with (key, value) first
        try:
            if selector(key_or_index, value):
                return True
        except (TypeError, ValueError):
            # If that fails, try with just the value
            try:
                if selector(value):
                    return True
            except (TypeError, ValueError):
                # If that fails, try with just the key
                try:
                    if selector(key_or_index):
                        return True
                except (TypeError, ValueError):
                    return False
    
    # Handle dictionary selector (must match all key-value pairs)
    if isinstance(selector, dict):
        # Only match if the value is also a dictionary
        if not isinstance(value, dict):
            return False
            
        # Special case: empty dict selector matches any non-empty dict
        if not selector:
            return bool(value)
            
        # Check if all key-value pairs in the selector match
        for k, v in selector.items():
            if k not in value:
                return False
                
            # For nested dictionary selectors, use recursive matching
            if isinstance(v, dict):
                if not _match_selector(k, value[k], v):
                    return False
            # For callable selectors, apply them to the value
            elif callable(v):
                if not v(value[k]):
                    return False
            # For direct value comparison
            elif value[k] != v:
                return False
                
        return True
    
    # Handle slice selector (for list indices)
    if isinstance(selector, slice):
        if not isinstance(key_or_index, (int, str)):
            return False
            
        # Convert key_or_index to int if possible
        try:
            idx = int(key_or_index)
        except (ValueError, TypeError):
            return False
            
        # Check if the index is within the slice
        return ((selector.start is None or idx >= selector.start) and 
                (selector.stop is None or idx < selector.stop) and 
                (selector.step is None or (idx - (selector.start or 0)) % (selector.step or 1) == 0))
    
    # Handle string to int conversion for list indices
    if isinstance(key_or_index, str) and key_or_index.isdigit() and isinstance(selector, int):
        return int(key_or_index) == selector
        
    # Direct value comparison (for exact matches)
    return key_or_index == selector

def _find_selector_paths(
    obj: Any, 
    selectors: PathType, 
    path_so_far: list, 
    only_first: bool = False,
    depth: int = 0
) -> Iterator[PathType]:
    """Recursively find all paths in the object that match the given selectors."""
    if not selectors:
        yield path_so_far
        return
        
    current_selector = selectors[0]
    remaining_selectors = selectors[1:]
    
    def process_value(key: Any, value: Any, new_path: list) -> Iterator[PathType]:
        """Process a single value and continue traversal."""
        if not remaining_selectors:
            yield new_path
        elif hasattr(value, 'items'):
            yield from _find_selector_paths(
                value, remaining_selectors, new_path, only_first, depth + 1
            )
        elif isinstance(value, (list, tuple)):
            for i, v in enumerate(value):
                yield from _find_selector_paths(
                    v, remaining_selectors, new_path + [i], only_first, depth + 1
                )
    
    if isinstance(obj, dict):
        # First try direct key matching
        if current_selector in obj:
            new_path = path_so_far + [current_selector]
            yield from process_value(current_selector, obj[current_selector], new_path)
            if only_first and path_so_far:
                return
                        
        # Then try matching keys/values with the selector
        for key, value in obj.items():
            if _match_selector(key, value, current_selector):
                new_path = path_so_far + [key]
                yield from _find_selector_paths(
                    value,
                    remaining_selectors,
                    new_path,
                    only_first,
                    depth + 1
                )
                if only_first and path_so_far:
                    return
                        
    # Handle lists and tuples
    elif isinstance(obj, (list, tuple)):
        # Handle slice selectors first
        if isinstance(current_selector, slice):
            # Get the slice indices
            start = current_selector.start if current_selector.start is not None else 0
            stop = current_selector.stop if current_selector.stop is not None else len(obj)
            step = current_selector.step if current_selector.step is not None else 1
            
            # Apply the slice to the list indices
            for idx in range(start, stop, step):
                if 0 <= idx < len(obj):
                    new_path = path_so_far + [idx]
                    if not remaining_selectors:
                        yield new_path
                        if only_first:
                            return
                    else:
                        yield from _find_selector_paths(
                            obj[idx],
                            remaining_selectors,
                            new_path,
                            only_first,
                            depth + 1
                        )
                        if only_first and path_so_far:
                            return
            return
            
        # If current_selector is a string that can be an index, try it first
        if isinstance(current_selector, str) and current_selector.isdigit():
            try:
                idx = int(current_selector)
                if 0 <= idx < len(obj):
                    new_path = path_so_far + [idx]
                    yield from _find_selector_paths(
                        obj[idx],
                        remaining_selectors,
                        new_path,
                        only_first,
                        depth + 1
                    )
                    if only_first and path_so_far:
                        return
            except (ValueError, IndexError):
                pass
                
        # If we have a select_all/select_wildcard selector, match all list indices
        if callable(current_selector) and (current_selector.__name__ in ('select_all', 'select_wildcard') or 
                                          current_selector == select_all or 
                                          current_selector == select_wildcard):
            # For select_all, we want to match all list items by index
            # and only yield the indices, not the item properties
            for idx in range(len(obj)):
                # Only yield the path to the list item, not its properties
                if not remaining_selectors:
                    yield path_so_far + [idx]
                    if only_first:
                        return
                else:
                    # If there are remaining selectors, continue traversing
                    new_path = path_so_far + [idx]
                    yield from _find_selector_paths(
                        obj[idx],
                        remaining_selectors,
                        new_path,
                        only_first,
                        depth + 1
                    )
                    if only_first and path_so_far:
                        return
            return
        
        # For other callable selectors, apply the selector to each item in the list
        if callable(current_selector):
            matched = False
            for idx, value in enumerate(obj):
                # First try to match the selector against the list item
                if _match_selector(idx, value, current_selector):
                    new_path = path_so_far + [idx]
                    
                    if not remaining_selectors:
                        # If no more selectors, yield the path to this item
                        yield new_path
                        matched = True
                        if only_first:
                            return
                    else:
                        # Otherwise, continue traversing with remaining selectors
                        yield from _find_selector_paths(
                            value,
                            remaining_selectors,
                            new_path,
                            only_first,
                            depth + 1
                        )
                        if only_first and path_so_far:
                            return
            
            # If we found matches and there are no remaining selectors, we're done
            if matched and not remaining_selectors:
                return
                
        # For non-callable selectors, use the standard matching logic
        # But skip if we already processed callable selectors to avoid duplicates
        if not callable(current_selector):
            for idx, value in enumerate(obj):
                if _match_selector(idx, value, current_selector):
                    new_path = path_so_far + [idx]
                    if not remaining_selectors:
                        yield new_path
                        if only_first:
                            return
                    else:
                        yield from _find_selector_paths(
                            value,
                            remaining_selectors,
                            new_path,
                            only_first,
                            depth + 1
                        )
                        if only_first and path_so_far:
                            return

def selectorspaths(obj: Any, selectors: PathType, only_first: bool = False) -> Iterator[PathType]:
    """Find all paths in the object that match the given selectors.
    
    Args:
        obj: The object to search in
        selectors: List of selectors or direct path components
        only_first: If True, return only the first match
        
    Returns:
        Iterator of paths that match the selectors
    """
    # If selectors is a string, split it into components
    if isinstance(selectors, str):
        selectors = selectors.split('.')
    
    # If selectors is a list, check if it contains any selectors
    if isinstance(selectors, list):
        if any(isinstance(s, (dict, Callable, slice)) for s in selectors):
            # If it contains selectors, convert them
            selectors = _convert_selectors_path(selectors)
        # Otherwise, use the path components as-is
    
    return _find_selector_paths(obj, selectors, [], only_first)

def _traverse_with_selectors(
    obj: Any,
    selectors: list,
    path_so_far: list,
    only_first: bool = False,
    create_missing: bool = False,
    original_path: list = None
) -> Iterator[Tuple[list, Any]]:
    """Traverse an object using a list of selector functions.
    
    This function recursively traverses a nested data structure using a list
    of selectors to find matching paths and values.
    
    Args:
        obj: The current object being traversed
        selectors: List of selectors to match against
        path_so_far: Path taken to reach current object
        only_first: If True, stop after first match
        create_missing: If True, create missing path elements for literal selectors
        original_path: The original path (keys/indices) corresponding to selectors
        
    Yields:
        Tuples of (path, value) for each match found
    """
    if not selectors:
        yield (path_so_far, obj)
        return
        
    current_selector = selectors[0]
    remaining_selectors = selectors[1:]
    current_key = (
        original_path[0] 
        if original_path and len(original_path) > 0 
        else None
    )
    remaining_original_path = original_path[1:] if original_path else None
    
    def process_value(key, value, new_path, new_obj):
        if not remaining_selectors:
            yield (new_path, value)
        else:
            yield from _traverse_with_selectors(
                obj=new_obj, 
                selectors=remaining_selectors, 
                path_so_far=new_path,
                only_first=only_first,
                create_missing=create_missing,
                original_path=remaining_original_path
            )
    
    # Determine if we can create missing path elements. We can only create paths when:
    # 1. create_missing is True
    # 2. All remaining selectors (from current to end) are literals
    # 3. The current selector is a literal
    # This ensures we have unambiguous keys/indices for path creation
    remaining_are_literals = all(
        _is_literal_selector(s) for s in selectors
    )
    can_create_missing = (
        create_missing and 
        remaining_are_literals and 
        _is_literal_selector(current_selector)
    )
    
    # Try to create missing path if possible and needed
    if can_create_missing:
        literal_key = _get_literal_value(current_selector)
        if literal_key is not None:
            if isinstance(obj, dict):
                # For dictionaries, create missing keys with empty dicts 
                # if there are more selectors
                if literal_key not in obj:
                    obj[literal_key] = {}
                yield from process_value(
                    key=literal_key,
                    value=obj[literal_key],
                    new_path=path_so_far + [literal_key],
                    new_obj=obj[literal_key]
                )
                if only_first:
                    return
            elif isinstance(obj, list):
                # For lists, ensure the index is valid and extend if needed
                if not isinstance(literal_key, int):
                    if not str(literal_key).isdigit():
                        raise KeyError(
                            f"Invalid list index: {literal_key}"
                        )
                    literal_key = int(literal_key)
                
                # Extend the list with appropriate empty containers if needed
                # If there are more selectors, use empty dicts, otherwise None
                while len(obj) <= literal_key:
                    obj.append({} if remaining_selectors else None)
                
                yield from process_value(
                    key=literal_key,
                    value=obj[literal_key],
                    new_path=path_so_far + [literal_key],
                    new_obj=obj[literal_key]
                )
    
    # Handle dictionary selectors - special case for matching items in a list
    if isinstance(current_selector, dict) and isinstance(obj, list):
        for idx, item in enumerate(obj):
            if not isinstance(item, dict):
                continue
            
            # Check if all key-value pairs in the selector match the item
            match = all(
                k in item and item[k] == v 
                for k, v in current_selector.items()
            )
            
            if match:
                yield from process_value(
                    key=idx,
                    value=item,
                    new_path=path_so_far + [idx],
                    new_obj=item
                )
                if only_first:
                    return
    # Handle dictionary selectors for dictionary objects
    elif isinstance(current_selector, dict) and isinstance(obj, dict):
        for key, value in obj.items():
            if _match_selector(key, value, current_selector):
                yield from process_value(
                    key=key,
                    value=value,
                    new_path=path_so_far + [key],
                    new_obj=value
                )
                if only_first:
                    return
    
    # Regular traversal for existing elements
    found = False
    if isinstance(obj, dict):
        for key, value in obj.items():
            if _match_selector(key, value, current_selector):
                found = True
                yield from process_value(
                    key=key,
                    value=value,
                    new_path=path_so_far + [key],
                    new_obj=value
                )
                if only_first:
                    return
    elif isinstance(obj, (list, tuple)):
        for idx, value in enumerate(obj):
            if _match_selector(idx, value, current_selector):
                found = True
                yield from process_value(
                    key=idx,
                    value=value,
                    new_path=path_so_far + [idx],
                    new_obj=value
                )
                if only_first:
                    return
    
    # If no matches found and we can't create missing elements, we're done
    if not found and not can_create_missing:
        return

def getpath_iter(obj: Any, path: Union[str, PathType], separator: str = '.') -> Iterator[Any]:
    """Iterate over values in a nested object using a path, with support for selectors.
    
    Args:
        obj: The object to get values from
        path: The path to traverse (can include selectors)
        separator: Separator for string paths
        
    Yields:
        Values found at the specified path
    """
    if not path and path != 0 and path != '':  # Handle empty path for root
        yield obj
        return
    
    # Convert path to list if it's a string
    if isinstance(path, str):
        # First, handle the case where the entire path might be a float
        try:
            # If the entire path is a float, use it as a single path component
            float(path)
            path_parts = [path]
        except ValueError:
            # Not a float, handle as normal path with separators
            # Handle escaped separators
            path = path.replace(f'\\{separator}', '\0')
            path_parts = path.split(separator)
            path_parts = [p.replace('\0', separator) for p in path_parts]
        path = path_parts
    else:
        path = list(path)  # Make a copy to avoid modifying the input
    
    # Convert path to selectors
    try:
        selectors = _convert_selectors_path(path)
    except ValueError:
        # If we can't convert to selectors, treat as literal path
        selectors = path
    
    # Check if we have a wildcard in the path
    if '*' in path:
        # Use selector-based traversal for paths with wildcards
        found = False
        for p, value in _traverse_with_selectors(obj, path, []):
            found = True
            yield value
        if not found and all(isinstance(p, (str, int)) for p in path):
            # Fall back to direct access if no matches found and path is simple
            try:
                current = obj
                for p in path:
                    if p == '*':
                        if isinstance(current, (list, tuple)):
                            current = list(current)
                        elif isinstance(current, dict):
                            current = list(current.values())
                        else:
                            return
                    elif isinstance(current, dict):
                        current = current[p]
                    elif isinstance(current, (list, tuple)):
                        if not isinstance(p, int):
                            try:
                                p = int(p)
                            except (ValueError, TypeError):
                                return
                        if 0 <= p < len(current):
                            current = current[p]
                        else:
                            return
                    else:
                        return
                if isinstance(current, (list, tuple)):
                    yield from current
                else:
                    yield current
            except (KeyError, IndexError, TypeError, AttributeError):
                pass
        return
    
    # Fast path for simple paths (all strings or integers)
    if all(isinstance(p, (str, int)) for p in path):
        try:
            current = obj
            for p in path:
                if isinstance(current, dict):
                    # Handle non-string keys by trying different type conversions
                    if p not in current:
                        # Try converting the key to different types if direct lookup fails
                        if str(p) in current:
                            p = str(p)
                        else:
                            # Try converting to int, float, or bool if possible
                            try:
                                if p.isdigit():
                                    p_int = int(p)
                                    if p_int in current:
                                        p = p_int
                                elif p.replace('.', '', 1).isdigit() and p.count('.') <= 1:
                                    p_float = float(p)
                                    if p_float in current:
                                        p = p_float
                                elif p.lower() in ('true', 'false'):
                                    p_bool = p.lower() == 'true'
                                    if p_bool in current:
                                        p = p_bool
                            except (ValueError, AttributeError):
                                pass
                    current = current[p]
                elif isinstance(current, (list, tuple)):
                    if not isinstance(p, int):
                        try:
                            p = int(p)
                        except (ValueError, TypeError):
                            # Try negative indices for strings that can't be converted to int
                            if p.startswith('-') and p[1:].isdigit():
                                p = int(p)
                            else:
                                return
                    # Handle negative indices
                    if p < 0:
                        p = len(current) + p
                    if 0 <= p < len(current):
                        current = current[p]
                    else:
                        return
                else:
                    return
            yield current
        except (KeyError, IndexError, TypeError, AttributeError):
            return
    else:
        # Use the selector-based traversal
        found = False
        
        # If we have no selectors, yield the object itself
        if not selectors:
            yield obj
            return
            
        # Get the first selector and remaining selectors
        first_selector = selectors[0]
        remaining_selectors = selectors[1:]
        
        # Handle the first selector
        if first_selector == '*':
            # Wildcard selector - match all keys/indices
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if not remaining_selectors:
                        yield value
                    else:
                        try:
                            yield from getpath_iter(value, remaining_selectors, separator)
                        except Exception:
                            continue
            elif isinstance(obj, (list, tuple)):
                for idx, item in enumerate(obj):
                    if not remaining_selectors:
                        yield item
                    else:
                        try:
                            yield from getpath_iter(item, remaining_selectors, separator)
                        except Exception:
                            continue
            return
        elif isinstance(obj, dict):
            # For dictionaries, check if the key matches the selector
            for key, value in obj.items():
                if _match_selector(key, value, first_selector):
                    found = True
                    # If no more selectors, yield the value
                    if not remaining_selectors:
                        yield value
                    # Otherwise, continue traversal with remaining selectors
                    else:
                        yield from getpath_iter(value, remaining_selectors, separator)
        elif isinstance(obj, (list, tuple)):
            # For lists, check if any item matches the selector
            for idx, item in enumerate(obj):
                if _match_selector(idx, item, first_selector):
                    found = True
                    # If no more selectors, yield the item
                    if not remaining_selectors:
                        yield item
                    # Otherwise, continue traversal with remaining selectors
                    else:
                        yield from getpath_iter(item, remaining_selectors, separator)
        
        # Special case: if the first selector is a dict and we're processing a list of dicts
        if not found and isinstance(first_selector, dict) and isinstance(obj, (list, tuple)):
            for item in obj:
                if not isinstance(item, dict):
                    continue
                if all(k in item and item[k] == v for k, v in first_selector.items()):
                    found = True
                    # If no more selectors, yield the item
                    if not remaining_selectors:
                        yield item
                    # Otherwise, continue traversal with remaining selectors
                    else:
                        yield from getpath_iter(item, remaining_selectors, separator)
        
        # If no matches found and we have a simple path, try direct access as a fallback
        if not found and all(isinstance(s, (str, int)) or (isinstance(s, str) and s.isdigit()) or 
                           (isinstance(s, str) and s.startswith('-') and s[1:].isdigit()) 
                           for s in selectors):
            try:
                current = obj
                for p in selectors:
                    if isinstance(current, dict):
                        # Handle string conversion for dictionary keys
                        if p not in current and str(p) in current:
                            p = str(p)
                        current = current[p]
                    elif isinstance(current, (list, tuple)):
                        if not isinstance(p, int):
                            try:
                                p = int(p)
                            except (ValueError, TypeError):
                                # Try negative indices for strings that can't be converted to int
                                if isinstance(p, str) and p.startswith('-') and p[1:].isdigit():
                                    p = int(p)
                                else:
                                    return
                        # Handle negative indices
                        if p < 0:
                            p = len(current) + p
                        if 0 <= p < len(current):
                            current = current[p]
                        else:
                            return
                    else:
                        return
                yield current
            except (KeyError, IndexError, TypeError, AttributeError):
                pass
                pass

def _get_value_by_path(obj: Any, path: PathType):
    """Helper function to get a value from an object using a path.
    
    This is similar to getpath but doesn't use selectors and returns None if the path doesn't exist.
    """
    if not path:
        return obj
        
    try:
        current = obj
        for p in path:
            if isinstance(current, dict):
                current = current[p]
            elif isinstance(current, list):
                # Convert string indices to integers if possible
                if isinstance(p, str) and p.isdigit():
                    p = int(p)
                if isinstance(p, int) and 0 <= p < len(current):
                    current = current[p]
                else:
                    return None
            else:
                return None
        return current
    except (KeyError, IndexError, TypeError, AttributeError):
        return None

def delpath(obj: Any, path: Union[str, PathType], separator: str = '.') -> int:
    """Deletes an item from the data object at the specified path.
    
    Args:
        obj: The object to delete from
        path: The path to the item to delete (can include selectors)
        separator: The separator to use for string paths
        
    Returns:
        int: The number of items deleted
    """
    if isinstance(path, str):
        # Don't convert to int here, we'll handle string indices in the helper functions
        path = path.split(separator)
    
    if not path:
        raise ValueError("Path cannot be empty")
    
    deleted_count = 0
    
    # If the last element is a selector, we need to find all matching elements
    last_key = path[-1]
    if isinstance(last_key, (dict, Callable, slice)):
        # Convert selectors to paths and delete each one
        parent_path = path[:-1]
        selector = last_key
        
        # Get all parent objects that might contain matching children
        parent_paths = list(selectorspaths(obj, parent_path))
        
        for p_path in parent_paths:
            parent = _get_value_by_path(obj, p_path)
            if parent is None:
                continue
                
            if isinstance(parent, dict):
                # For dictionaries, find keys that match the selector
                matching_keys = [k for k, v in parent.items() 
                               if _match_selector(k, v, selector)]
                for k in matching_keys:
                    if k in parent:
                        del parent[k]
                        deleted_count += 1
                    
            elif isinstance(parent, list):
                # For lists, find indices that match the selector
                # Need to collect indices first to avoid modifying while iterating
                matching_indices = [i for i, v in enumerate(parent) 
                                  if _match_selector(i, v, selector)]
                # Delete in reverse order to avoid index shifting issues
                for i in sorted(matching_indices, reverse=True):
                    if 0 <= i < len(parent):
                        del parent[i]
                        deleted_count += 1
                        
        return deleted_count
    
    # For regular paths, find the parent and delete the key/index
    parent_path = path[:-1]
    parent = _get_value_by_path(obj, parent_path)
    
    if parent is None:
        return 0  # Path doesn't exist, nothing to delete
        
    key_to_delete = path[-1]
    
    if isinstance(parent, dict):
        if key_to_delete in parent:
            del parent[key_to_delete]
            return 1
    elif isinstance(parent, list):
        # Convert string indices to integers if possible
        if isinstance(key_to_delete, str) and key_to_delete.isdigit():
            key_to_delete = int(key_to_delete)
        
        if isinstance(key_to_delete, int) and 0 <= key_to_delete < len(parent):
            del parent[key_to_delete]
            return 1
    
    return 0  # No deletion occurred

def delpaths(obj: Any, paths: list, separator: str = '.'):
    """Delete multiple paths from the object.
    
    Args:
        obj: The object to delete paths from
        paths: List of paths to delete
        separator: Separator for string paths
    """
    for path in paths:
        delpath(obj, path, separator)

def getpath(obj: Any, path: Union[str, PathType], default: Any = None, separator: str = '.', only_first_path_match: bool = False) -> Any:
    """Gets a value from a nested object using a path, with support for selectors.
    
    Args:
        obj: The object to get the value from.
        path: The path to the value. Can be a string or a list containing keys, indices, or selectors.
        default: The default value to return if the path doesn't exist.
        separator: The separator to use for string paths.
        only_first_path_match: 
            If False (default), always returns a list of all matching values (empty list if no matches found).
            If True, returns the first matching value (or default if none found).
            
    Returns:
        When only_first_path_match==False (default), the return value is always a list of matches, 
            even if there is only one match or no matches (empty list).
        When only_first_path_match==True  - The return value is first matching value, or default if no matches found.
    """
    if not path and path != 0 and path != '':  # Handle empty path for root
        return obj if default is None else default
    
    # Convert path to list if it's a string
    if isinstance(path, str):
        path = path.split(separator) if path else []
    path = list(path) if not isinstance(path, list) else path
    
    # Special case: empty path returns the root object
    if not path:
        return obj if default is None else default
    
    # Handle wildcard selector for lists
    if len(path) == 1 and path[0] == '*':
        if isinstance(obj, (list, tuple)):
            return list(obj) if not only_first_path_match else (obj[0] if obj else default)
        elif isinstance(obj, dict):
            values = list(obj.values())
            return values if not only_first_path_match else (values[0] if values else default)
        return default
    
    # Convert path to selectors
    selectors = _convert_selectors_path(path)
    
    # Use the iterator to get all matching values
    results = []
    try:
        for _, value in _traverse_with_selectors(
            obj, 
            selectors, 
            [], 
            only_first=only_first_path_match,
            create_missing=False,
            original_path=path
        ):
            results.append(value)
            if only_first_path_match:
                break
    except (KeyError, IndexError, TypeError, AttributeError):
        return default
    
    if only_first_path_match:
        return results[0] if results else default
    return results

def setpath(obj: Any, path: Union[str, PathType], value: Any, create_missing: bool = True, separator: str = '.', operation: str = 'set', only_first_path_match: bool = False):
    """Set a value at a path in a nested structure.
    
    Args:
        obj: The object to modify
        path: Path to the value to set (string or list of keys/indices)
        value: Value to set
        create_missing: If True, create missing path components
        separator: Separator for string paths (default: '.')
        operation: Operation to perform ('set', 'append', 'extend')
        only_first_path_match: If True, only modify the first matching path
    """
    # Convert path to selectors if it's a string or list
    if isinstance(path, str):
        path_parts = path.split(separator)
        # For string paths, treat as direct path by default
        selectors = path_parts
        original_path = path_parts
    else:
        # For list paths, check if it contains any selectors
        if any(isinstance(p, (dict, Callable, slice)) for p in path):
            # If it contains selectors, convert them
            selectors = _convert_selectors_path(path)
        else:
            # Otherwise, treat as direct path
            selectors = list(path)
        original_path = path
    


    # First, try to find existing paths that match the selectors
    paths_to_modify = []
    
    # First, try direct path traversal for simple paths
    if all(isinstance(p, (str, int)) for p in selectors):
        try:
            current = obj
            valid_path = True
            for part in selectors[:-1]:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                elif isinstance(current, list) and isinstance(part, (int, str)):
                    try:
                        idx = int(part) if isinstance(part, str) and part.isdigit() else part
                        if 0 <= idx < len(current):
                            current = current[idx]
                        else:
                            valid_path = False
                            break
                    except (ValueError, IndexError):
                        valid_path = False
                        break
                else:
                    valid_path = False
                    break
            
            if valid_path:
                # If we got here, the direct path is valid
                paths_to_modify = [selectors]
        except Exception as e:
            pass
    
    # If no direct path found, try using selectors
    if not paths_to_modify:
        paths_to_modify = list(selectorspaths(obj, selectors, only_first=only_first_path_match))
    
    # If we found matching paths, update them
    if paths_to_modify:
        for p in paths_to_modify:
            current = obj
            # Traverse to the parent of the target
            path = []
            for key in p[:-1]:
                path.append(key)

                if isinstance(current, dict) and key in current:

                    current = current[key]
                elif isinstance(current, list) and isinstance(key, (int, str)):
                    try:
                        idx = int(key) if isinstance(key, str) and key.isdigit() else key
                        if 0 <= idx < len(current):

                            current = current[idx]
                        else:

                            current = None
                            break
                    except (ValueError, IndexError) as e:

                        current = None
                        break
                else:

                    current = None
                    break
            
            if current is not None:
                last_key = p[-1]

                
                if operation == 'set':
                    if isinstance(current, dict):

                        current[last_key] = value
                    elif isinstance(current, list) and isinstance(last_key, int):
                        if 0 <= last_key < len(current):

                            current[last_key] = value
                        elif last_key == len(current) and create_missing:

                            current.append(value)
                elif operation == 'append':
                    
                    # Get the target value
                    target = None
                    if isinstance(current, dict):
                        if last_key in current:
                            target = current[last_key]
                            if isinstance(target, list):
                                target.append(value)
                            else:
                                current[last_key] = [target, value] if target is not None else [value]
                        else:
                            current[last_key] = [value]
                    elif isinstance(current, list) and isinstance(last_key, int):
                        if 0 <= last_key < len(current):
                            target = current[last_key]
                            if isinstance(target, list):
                                target.append(value)
                            else:
                                current[last_key] = [target, value] if target is not None else [value]
                        elif last_key == len(current):
                            current.append(value)
                elif operation == 'extend' and isinstance(value, list):
                    if last_key in current and isinstance(current[last_key], list):
                        current[last_key].extend(value)
                    elif last_key not in current and isinstance(current, dict):
                        current[last_key] = value.copy()
    
    # If no paths matched and we can create missing ones, build the path
    elif create_missing and all(_is_literal_selector(s) for s in selectors):
        current = obj
        path_parts = []
        
        # Convert all selectors to their literal values
        for s in selectors:
            part = _get_literal_value(s)
            if part is None:
                return  # Can't create path with non-literal selector
            path_parts.append(part)
        
        # Traverse and create missing path elements
        for i, part in enumerate(path_parts[:-1]):
            next_part = path_parts[i + 1] if i + 1 < len(path_parts) else None
            
            # Handle dictionary case
            if isinstance(current, dict):
                # If part doesn't exist, create appropriate container based on next part
                if part not in current:
                    if next_part is not None:
                        # If next part is an integer or a string that can be an integer, create a list
                        if isinstance(next_part, int) or (isinstance(next_part, str) and next_part.isdigit()):
                            current[part] = []
                        else:
                            current[part] = {}
                    else:
                        current[part] = {}
                current = current[part]
            # Handle list case
            elif isinstance(current, list):
                # Convert part to int if it's a string representation of a number
                if isinstance(part, str) and part.isdigit():
                    part = int(part)
                elif not isinstance(part, int):
                    return  # Invalid list index
                
                # Ensure the list is large enough
                while len(current) <= part:
                    # If next part is an integer or a string that can be an integer, create a list
                    if next_part is not None and (isinstance(next_part, int) or (isinstance(next_part, str) and next_part.isdigit())):
                        current.append([])
                    else:
                        current.append({})
                current = current[part]
            else:
                # Can't traverse through non-container types
                return
        
        # Set the final value
        if path_parts:
            last_part = path_parts[-1]
            if isinstance(current, dict):
                current[last_part] = value
            elif isinstance(current, list):
                # Convert last_part to int if it's a string representation of a number
                if isinstance(last_part, str) and last_part.isdigit():
                    last_part = int(last_part)
                
                if isinstance(last_part, int):
                    if 0 <= last_part < len(current):
                        current[last_part] = value
                    elif last_part == len(current):
                        current.append(value)
                    elif last_part > len(current):
                        # Pad the list with None values up to the index
                        while len(current) < last_part:
                            current.append(None)
                        current.append(value)

# === SEARCH FUNCTIONS ===

def findpaths(obj: Any, pattern: Any, search_type: str = 'exact', case_sensitive: bool = True, search_keys: bool = True, search_values: bool = True) -> Iterator[PathType]:
    if search_type not in ['exact', 'contains', 'regex']:
        raise ValueError("search_type must be 'exact', 'contains', or 'regex'")

    if search_type == 'regex':
        try:
            compiled_regex = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    else:
        if not case_sensitive:
            pattern = pattern.lower() if isinstance(pattern, str) else pattern

    def _match(target):
        if target is None:
            return False
        
        original_target = target
        if not case_sensitive and isinstance(target, str):
            target = target.lower()

        if search_type == 'exact':
            # Strict type and value checking for exact matches
            return target == pattern and type(target) is type(pattern)
        elif search_type == 'contains':
            if isinstance(target, str):
                return pattern in target
            elif isinstance(target, list):
                return pattern in target
            return False
        elif search_type == 'regex':
            return isinstance(original_target, str) and compiled_regex.search(original_target)
        return False

    def recurse(current_obj, current_path):
        if isinstance(current_obj, dict):
            for k, v in current_obj.items():
                new_path = current_path + [k]
                if search_keys and _match(k):
                    yield new_path
                if search_values:
                    if _match(v):
                        yield new_path
                    else:
                        yield from recurse(v, new_path)
        elif isinstance(current_obj, list):
            for i, item in enumerate(current_obj):
                yield from recurse(item, current_path + [i])

    yield from recurse(obj, [])

def findvalues(obj: Any, pattern: Any, search_type: str = 'exact', case_sensitive: bool = True):
    paths = findpaths(obj, pattern, search_type, case_sensitive)
    for path in paths:
        yield getpath(obj, path)

# === BATCH AND UTILITY FUNCTIONS ===

def batch_setpath(data: Any, modifications: list[tuple]):
    """Applies a batch of modifications to the data object."""
    for mod in modifications:
        path, value, *op = mod
        operation = op[0] if op else 'set'
        # Delegate to the main setpath function for each modification.
        setpath(data, path, value, create_missing=True, operation=operation)

def getpaths(obj, paths, default=None, only_first_path_match: bool = False):
    return [getpath(obj, p, default, only_first_path_match) for p in paths]

def getpaths_setpaths(src_obj, tgt_obj, paths_map, default=None, only_first_path_match=False):
    """Copy values from source to target object using path mappings.
    
    Args:
        src_obj: Source object to read values from
        tgt_obj: Target object to write values to
        paths_map: List of (source_path, target_path) tuples
        default: Default value if source path doesn't exist
        only_first_path_match: If True, only use first match when source path has multiple matches
    """
    for src_path, tgt_path in paths_map:
        value = getpath(src_obj, src_path, default, only_first_path_match=only_first_path_match)
        if value is not None and value != []:  # Don't set if empty list (no matches)
            setpath(tgt_obj, tgt_path, value, only_first_path_match=only_first_path_match)

def haspath(obj: Any, path: Union[str, PathType], separator: str = '.') -> bool:
    """Check if a path exists in the object.
    
    Args:
        obj: The object to check
        path: The path to check, which can be a string with separators or a list of path components
        separator: The separator to use if path is a string
        
    Returns:
        bool: True if the path exists, False otherwise
    """
    # First, normalize the path
    path_components = _normalize_path(path, separator)
    
    # If no path components, the path exists by definition
    if not path_components:
        return True
        
    # Traverse the object to check if the path exists
    current = obj
    for component in path_components:
        if isinstance(current, dict):
            if component not in current:
                return False
            current = current[component]
        elif isinstance(current, (list, tuple)):
            if not isinstance(component, int):
                return False
            if component < 0 or component >= len(current):
                return False
            current = current[component]
        else:
            return False
            
    return True

# === FLATTEN/UNFLATTEN UTILITIES ===

def flatten(data: Any, separator: str = '.', _path: str = '') -> dict[str, Any]:
    """Flatten a nested dictionary/JSON structure into a single level with dotted keys.
    
    Args:
        data: The dictionary to flatten
        separator: The separator to use between keys (default: '.')
        _path: Internal use only - current path being processed
        
    Returns:
        A flattened dictionary with dot-notation keys
    """
    items: dict[str, Any] = {}
    
    if isinstance(data, dict):
        if not data and _path:  # Only add empty dict if it's not the root
            items[_path] = {}
        else:
            for k, v in data.items():
                new_key = f"{_path}{separator}{k}" if _path else k
                items.update(flatten(v, separator, new_key))
    elif isinstance(data, (list, tuple)):
        if not data and _path:  # Only add empty list if it's not the root
            items[_path] = []
        else:
            for i, v in enumerate(data):
                new_key = f"{_path}{separator}{i}" if _path else str(i)
                items.update(flatten(v, separator, new_key))
    else:
        if _path:  # Only add non-empty paths
            items[_path] = data
    
    return items

def unflatten(data: dict[str, Any], separator: str = '.') -> Any:
    """Unflatten a dictionary with dot-notation keys into a nested structure.
    
    Args:
        data: The flattened dictionary to unflatten
        separator: The separator used in the keys (default: '.')
        
    Returns:
        A nested dictionary/list structure
    """
    def _is_list_key(key: str) -> bool:
        # Check if the key represents a list index
        return key.isdigit() or (key.startswith('-') and key[1:].isdigit())
    
    def _get_list_index(key: str) -> int:
        # Convert string to list index, handling negative indices
        return int(key)
    
    # First, build a tree structure with nested dictionaries
    tree = {}
    
    for key, value in data.items():
        if not key:  # Skip empty keys
            continue
            
        parts = key.split(separator)
        current = tree
        
        # Process all parts except the last one
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the value for the last part
        last_part = parts[-1]
        if last_part:  # Only process non-empty last parts
            current[last_part] = value
    
    # Now convert the tree to the final structure with proper lists
    def _convert_node(node):
        if not isinstance(node, dict):
            return node
            
        # Check if all keys are list indices
        keys = [k for k in node.keys() if k != '']
        if keys and all(_is_list_key(k) for k in keys):
            # It's a list
            indices = [_get_list_index(k) for k in keys]
            max_idx = max(indices) if indices else -1
            lst = [None] * (max_idx + 1)
            
            for k, v in node.items():
                if not k:  # Skip empty keys
                    continue
                idx = _get_list_index(k)
                if 0 <= idx < len(lst):
                    lst[idx] = _convert_node(v)
            return lst
        else:
            # It's a dict
            result = {}
            for k, v in node.items():
                if k:  # Skip empty keys
                    result[k] = _convert_node(v)
            return result
    
    return _convert_node(tree)

# === MERGE UTILITY ===

def merge(dict1: dict, dict2: dict) -> dict:
    merged = dict1.copy()
    for key, value in dict2.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge(merged[key], value)
        else:
            merged[key] = value
    return merged


# === MISC UTILITIES ===

def safe_json_loads(s: str, default: Any = None) -> Any:
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return default

# === WORKER-SPECIFIC HELPERS ===

# This is a generic response creator for Cloudflare Workers.
# It ensures a consistent JSON response format.
def create_worker_response(data: Any, success: bool = True, error: str = None) -> str:
    response_obj = {
        'success': success,
        'data': data if success else None,
        'error': error if not success else None,
        'timestamp': int(time.time())
    }
    return json.dumps(response_obj)

# This is an example of a full Cloudflare Worker handler using these utilities.
# It demonstrates a simple API that can get, set, or delete values in a JSON object
# stored in a KV namespace.
async def example_worker_handler(request, env):
    # Assumes a KV binding named 'MY_KV_NAMESPACE'
    KV = env.MY_KV_NAMESPACE
    
    # Get the key from the URL path, e.g., /my-json-document
    key = request.path[1:]
    if not key:
        return Response.new("Not Found", status=404)

    # Read the existing JSON from KV
    try:
        data_str = await KV.get(key)
        data = json.loads(data_str) if data_str else {}
    except Exception as e:
        return Response.new(f"Error reading from KV: {e}", status=500)

    # Determine action from query parameters
    params = request.query
    action = params.get('action')
    path = params.get('path')
    
    if not action or not path:
        return Response.new("Missing 'action' or 'path' query parameter", status=400)

    try:
        if action == 'get':
            value = getpath(data, path)
            response_data = {'key': key, 'path': path, 'value': value}
        
        elif action == 'set':
            value_str = params.get('value')
            if value_str is None:
                return Response.new("Missing 'value' query parameter for 'set' action", status=400)
            
            try:
                value = json.loads(value_str)
            except json.JSONDecodeError:
                value = value_str # Treat as a plain string if not valid JSON
            
            setpath(data, path, value)
            await KV.put(key, json.dumps(data))
            response_data = {'key': key, 'path': path, 'status': 'set'}

        elif action == 'del':
            delpath(data, path)
            await KV.put(key, json.dumps(data))
            response_data = {'key': key, 'path': path, 'status': 'deleted'}
        
        else:
            return Response.new(f"Invalid action: {action}", status=400)

        # Create a standardized JSON response
        json_response = create_worker_response(response_data)
        return Response.new(json_response, {
            'headers': {'Content-Type': 'application/json'},
            'status': 200
        })
        
    except Exception as e:
        # Error handling
        error_response = create_worker_response({
            'success': False,
            'error': str(e),
            'timestamp': '2025-01-01T00:00:00Z'
        })
        return Response.new(error_response, {
            'status': 500,
            'headers': {'Content-Type': 'application/json'}
        })


# === VERSION AND COMPATIBILITY INFO ===

__version__ = "1.0.0"
__author__ = "Claude (Anthropic)"
__license__ = "MIT"

# Modules used (all available in Cloudflare Python Workers)
__dependencies__ = [
    "re",          # Regular expressions
    "json",        # JSON parsing/serialization  
    "functools",   # reduce function
    "typing"       # Type hints (optional)
]

# Functions exported by this module
__all__ = [
    'batch_setpath',
    'create_worker_response',
    'delpath',
    'delpaths',
    'example_worker_handler',
    'findpaths',
    'findvalues',
    'flatten',
    'getpath',
    'getpaths',
    'getpaths_setpaths',
    'haspath',
    'merge',
    'safe_json_loads',
    'selectorspaths',
    'setpath',
    'unflatten',
    # Selectors
    'select_all',
    'select_contains',
    'select_eq',
    'select_gt',
    'select_key_exists',
    'select_key_missing',
    'select_lt',
    'select_regex',
    'select_type',
]


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="jqpath: jq-style path/query tool for JSON/YAML data (Python)"
    )
    parser.add_argument(
        "-f", "--file", type=str, default=None, help="Input file (JSON, or YAML if PyYAML installed). If omitted, reads from stdin."
    )
    parser.add_argument(
        "-p", "--path", type=str, required=True, help="jq-style path expression (e.g. 'user.profile.name' or 'items[0].id')"
    )
    parser.add_argument(
        "-s", "--set", type=str, default=None, help="Set the value at the path (JSON-encoded string)"
    )
    parser.add_argument(
        "--delete", action="store_true", help="Delete the value at the path")
    parser.add_argument(
        "--flatten", action="store_true", help="Flatten the input object")
    parser.add_argument(
        "--unflatten", action="store_true", help="Unflatten the input object")
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print output JSON")
    args = parser.parse_args()

    # Read input
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            input_str = f.read()
    else:
        input_str = sys.stdin.read()

    # Try JSON, fallback to YAML if available
    try:
        data = json.loads(input_str)
    except Exception:
        try:
            import yaml
            data = yaml.safe_load(input_str)
        except Exception:
            print("Error: Input is not valid JSON (or YAML if PyYAML installed).", file=sys.stderr)
            sys.exit(1)

    # Flatten/unflatten
    if args.flatten:
        result = flatten(data)
        print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
        sys.exit(0)
    if args.unflatten:
        result = unflatten(data)
        print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
        sys.exit(0)

    # Set or delete
    if args.set is not None:
        try:
            value = json.loads(args.set)
        except Exception:
            value = args.set
        setpath(data, args.path, value)
        print(json.dumps(data, indent=2 if args.pretty else None, ensure_ascii=False))
        sys.exit(0)
    if args.delete:
        delpath(data, args.path)
        print(json.dumps(data, indent=2 if args.pretty else None, ensure_ascii=False))
        sys.exit(0)

    # Get value at path
    value = getpath(data, args.path)
    print(json.dumps(value, indent=2 if args.pretty else None, ensure_ascii=False))
    
