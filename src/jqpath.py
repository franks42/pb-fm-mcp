# === CONVENIENCE API ===
def getset(
    src: Dict[str, Any],
    src_path: Union[str, List[Union[str, int]]],
    tgt: Dict[str, Any],
    tgt_path: Union[str, List[Union[str, int]]]
) -> Dict[str, Any]:
    """
    Copy a value from a source path in one JSON structure to a target path in another, creating the target path as needed (shallow copy).
    Args:
        src: Source nested data structure (dict/list)
        src_path: Path to value in source (string or list)
        tgt: Target nested data structure (dict/list)
        tgt_path: Path to set value in target (string or list)
    Returns:
        Modified target data structure with value set at tgt_path (shallow copy)
    Examples:
        getset(src, 'user.profile.name', tgt, 'profile.name_copy')
        getset(src, ['a', 0, 'b'], tgt, ['x', 'y'])
    """
    import copy
    value = getpath(src, src_path)
    setpath(tgt, tgt_path, copy.copy(value), create_missing=True)
    return tgt

"""
jqpath: jq-style Path Manipulation Utilities for Python (Cloudflare Workers Compatible)
=====================================================================================

A comprehensive, zero-dependency Python library for manipulating deeply nested dictionaries and lists using jq-style path operations.

This module mimics the path-based manipulation and querying capabilities of the jq command-line tool, providing Pythonic equivalents of jq's getpath, setpath, delpath, delpaths, haspath, findpaths, findvalues, batch_setpath, flatten, unflatten, and merge functions.

Features:
- jq-style getpath, setpath, delpath, delpaths, haspath, findpaths, findvalues, batch_setpath, flatten, unflatten, and merge for dicts/lists
- Path navigation with dot notation or list-of-keys/indices (e.g., 'user.profile.name' or ['user', 0, 'profile', 'name'])
- Robust handling of missing paths (jq semantics: no error on delete if path missing)
- Advanced search with regex and value matching
- Batch and utility operations for complex data transformations
- 100% compatible with Cloudflare Python Workers (uses only Python standard library)

Author: Claude (Anthropic)
Version: 1.0.0
License: MIT
"""

import re
import json
from functools import reduce
from typing import Any, Dict, List, Union, Optional, Tuple, Callable


# === CORE MANIPULATION FUNCTIONS ===

# === DELETION FUNCTIONS (jq-style) ===
def delpath(data: Dict[str, Any], path: Union[str, List[Union[str, int]]]) -> Dict[str, Any]:
    """
    Delete the value at the specified path in a nested data structure.
    If the path does not exist, do nothing (no error).
    Args:
        data: The nested data structure (dict/list) to modify
        path: Path to the target location (string or list)
    Returns:
        Modified data structure with the path deleted (if it existed)
    """
    try:
        setpath(data, path, operation='delete', create_missing=False)
    except (KeyError, IndexError):
        pass
    return data

def delpaths(data: Dict[str, Any], paths: List[Union[str, List[Union[str, int]]]]) -> Dict[str, Any]:
    """
    Delete multiple paths in a nested data structure (jq-style delpaths).
    If a path does not exist, it is ignored (no error).
    Args:
        data: The nested data structure (dict/list) to modify
        paths: List of paths (each path is a string or list)
    Returns:
        Modified data structure with all specified paths deleted (if they existed)
    """
    for path in paths:
        try:
            setpath(data, path, operation='delete', create_missing=False)
        except (KeyError, IndexError):
            pass
    return data

def setpath(data: Dict[str, Any], 
           path: Union[str, List[Union[str, int]]], 
           value: Any = None, 
           operation: str = 'set', 
           create_missing: bool = True) -> Dict[str, Any]:
    """
    jq-style setpath: Add, update, append, extend, or delete values in nested data structures (dicts/lists).

    Args:
        data: The nested data structure (dict/list) to modify
        path: Path to the target location. Can be:
            - String with dot notation: "user.profile.name"
            - List of keys/indices: ["user", "profile", "name"]
            - Mixed: ["user", 0, "profile", "name"] for list indices
            - For list indices, both strings and integers are accepted; string indices are automatically converted to int when accessing lists.
        value: Value to set (ignored for delete operations)
        operation: 'set', 'delete', 'append' (for lists), or 'extend' (for lists)
        create_missing: Whether to create missing intermediate dictionaries

    Returns:
        Modified data structure

    Raises:
        KeyError: When path doesn't exist and create_missing=False
        TypeError: When trying to access invalid types
        ValueError: When operation is invalid

    Examples:
        setpath(data, "user.profile.name", "John Doe")
        setpath(data, "user.tags", "python", "append")
        setpath(data, "old.field", operation="delete")
        setpath(data, ["items", "0", "name"], "Item 1")  # string index for list
        setpath(data, ["items", 0, "name"], "Item 1")     # int index for list
    """
    
    # Convert string path to list
    if isinstance(path, str):
        path = path.split('.')
    
    # Validate operation
    valid_ops = {'set', 'delete', 'append', 'extend'}
    if operation not in valid_ops:
        raise ValueError(f"Operation must be one of: {valid_ops}")
    
    # Handle empty path
    if not path:
        if operation == 'set':
            return value
        else:
            raise ValueError("Cannot delete or append to root")
    
    # Navigate to parent of target
    current = data
    for key in path[:-1]:
        # Handle list indices
        if isinstance(current, list):
            key = int(key)
            if key >= len(current):
                if create_missing:
                    # Extend list to accommodate index
                    current.extend([{}] * (key - len(current) + 1))
                else:
                    raise IndexError(f"List index {key} out of range")
        
        # Handle dictionary keys
        elif isinstance(current, dict):
            if key not in current:
                if create_missing:
                    current[key] = {}
                else:
                    raise KeyError(f"Key '{key}' not found")
        else:
            raise TypeError(f"Cannot navigate through {type(current).__name__}")
        
        current = current[key]
    
    # Perform operation on target
    target_key = path[-1]
    
    if isinstance(current, list):
        target_key = int(target_key)
        
        if operation == 'set':
            # Extend list if necessary
            if target_key >= len(current):
                if create_missing:
                    current.extend([None] * (target_key - len(current) + 1))
                else:
                    raise IndexError(f"List index {target_key} out of range")
            current[target_key] = value
            
        elif operation == 'delete':
            if target_key < len(current):
                del current[target_key]
            else:
                raise IndexError(f"List index {target_key} out of range")
                
        elif operation == 'append':
            current.append(value)
            
        elif operation == 'extend':
            if not hasattr(value, '__iter__'):
                raise TypeError("Value must be iterable for extend operation")
            current.extend(value)
    
    elif isinstance(current, dict):
        if operation == 'set':
            current[target_key] = value
            
        elif operation == 'delete':
            if target_key in current:
                del current[target_key]
            else:
                raise KeyError(f"Key '{target_key}' not found")
                
        elif operation in ['append', 'extend']:
            # Convert dict value to list if needed
            if target_key not in current:
                current[target_key] = []
            elif not isinstance(current[target_key], list):
                current[target_key] = [current[target_key]]
            
            if operation == 'append':
                current[target_key].append(value)
            else:  # extend
                if not hasattr(value, '__iter__'):
                    raise TypeError("Value must be iterable for extend operation")
                current[target_key].extend(value)
    
    else:
        raise TypeError(f"Cannot modify {type(current).__name__}")
    
    return data


def getpath(data: Dict[str, Any], 
           path: Union[str, List[Union[str, int]]], 
           default: Any = None, 
           separator: str = '.') -> Any:
    """
    jq-style getpath: Get a value from a nested data structure (dict/list) by path.

    Args:
        data: The nested data structure (dict/list)
        path: Path to the target. Can be:
            - String with custom separator: "user.profile.name" or "user/profile/name"
            - List of keys/indices: ["user", "profile", "name"]
            - Mixed: ["user", 0, "profile", "name"] for list indices
            - For list indices, both strings and integers are accepted; string indices are automatically converted to int when accessing lists.
        default: Value to return if path doesn't exist
        separator: Custom separator for string paths (default: '.')

    Returns:
        Value at the specified path or default

    Examples:
        getpath(data, 'user.profile.name')
        getpath(data, ['user', 0, 'profile'])
        getpath(data, ['items', '0', 'name'])  # string index for list
        getpath(data, ['items', 0, 'name'])    # int index for list
        getpath(data, 'user/profile/name', separator='/')
        getpath(data, 'missing.key', default='Not found')
        getpath(data, 'items.-1.name')  # Negative indexing
    """
    if isinstance(path, str):
        path = path.split(separator)
    
    if not path:
        return data
    
    current = data
    try:
        for key in path:
            if isinstance(current, list):
                # Handle negative indices
                key = int(key)
                if key < 0:
                    key = len(current) + key
            elif isinstance(current, dict):
                # Keep key as string for dict access
                pass
            else:
                # Can't navigate through this type
                return default
            
            current = current[key]
        return current
    except (KeyError, IndexError, TypeError, ValueError):
        return default


def haspath(data: Dict[str, Any], path: Union[str, List[Union[str, int]]]) -> bool:
    """
    jq-style haspath: Check if a path exists in a nested data structure (dict/list).

    Args:
        data: The nested data structure
        path: Path to check (string or list)
            - For list indices, both strings and integers are accepted; string indices are automatically converted to int when accessing lists.

    Returns:
        True if path exists, False otherwise

    Examples:
        haspath(data, "user.profile.name")  # True if exists
        haspath(data, ["user", "settings", "theme"])
        haspath(data, ["items", "0", "name"])  # string index for list
        haspath(data, ["items", 0, "name"])     # int index for list
    """
    if isinstance(path, str):
        path = path.split('.')
    
    current = data
    try:
        for key in path:
            if isinstance(current, list):
                key = int(key)
            current = current[key]
        return True
    except (KeyError, IndexError, TypeError, ValueError):
        return False


def getpaths(data: Dict[str, Any], 
            paths: Union[List[str], Dict[str, str]], 
            default: Any = None) -> Union[List[Any], Dict[str, Any]]:
    """
    jq-style getpaths: Get multiple values from nested paths at once.

    Args:
        data: The nested data structure
        paths: List of paths or dict mapping names to paths
            - For list indices in paths, both strings and integers are accepted; string indices are automatically converted to int when accessing lists.
        default: Default value for missing paths

    Returns:
        List of values (if paths is list) or dict of name->value (if paths is dict)

    Examples:
        getpaths(data, ['user.name', 'user.age', 'settings.theme'])
        getpaths(data, [
            ['items', '0', 'name'],  # string index for list
            ['items', 0, 'name']     # int index for list
        ])
        getpaths(data, {
            'name': 'user.profile.name',
            'email': 'user.profile.email',
            'theme': 'settings.theme'
        })
    """
    if isinstance(paths, dict):
        return {name: getpath(data, path, default) for name, path in paths.items()}
    else:
        return [getpath(data, path, default) for path in paths]


# === SEARCH FUNCTIONS ===

def findpaths(data: Dict[str, Any], 
             pattern: str, 
             match_type: str = 'exact', 
             case_sensitive: bool = True, 
             include_values: bool = False, 
             max_depth: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Search for attributes/keys in a nested data structure and return their paths (jq-style findpaths).

    Args:
        data: The nested data structure to search
        pattern: The pattern to search for (string or regex pattern)
        match_type: Type of matching - 'exact', 'contains', 'startswith', 'endswith', 'regex'
        case_sensitive: Whether matching should be case sensitive
        include_values: If True, also search in values (for string values)
        max_depth: Maximum depth to search (None for unlimited)

    Returns:
        List of dictionaries with keys: 'path', 'key', 'value', 'parent_type', 'match_type'

    Examples:
        findpaths(data, 'name')  # Find exact matches for 'name'
        findpaths(data, 'user', 'contains')  # Find keys containing 'user'
        findpaths(data, r'.*_id$', 'regex')  # Find keys ending with '_id'
        findpaths(data, 'john', include_values=True)  # Search in values too
    """
    matches = []
    
    def _search_recursive(obj: Any, current_path: Optional[List[Union[str, int]]] = None, depth: int = 0):
        if current_path is None:
            current_path = []
        
        if max_depth is not None and depth > max_depth:
            return
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                key_str = str(key)
                new_path = current_path + [key]
                
                # Check if key matches
                if _matches_pattern(key_str, pattern, match_type, case_sensitive):
                    matches.append({
                        'path': '.'.join(map(str, new_path)),
                        'path_list': new_path,
                        'key': key,
                        'value': value,
                        'parent_type': 'dict',
                        'match_type': 'key'
                    })
                
                # Check if value matches (if include_values is True and value is string)
                if include_values and isinstance(value, str):
                    if _matches_pattern(value, pattern, match_type, case_sensitive):
                        matches.append({
                            'path': '.'.join(map(str, new_path)),
                            'path_list': new_path,
                            'key': key,
                            'value': value,
                            'parent_type': 'dict',
                            'match_type': 'value'
                        })
                
                # Recurse into nested structures
                if isinstance(value, (dict, list)):
                    _search_recursive(value, new_path, depth + 1)
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = current_path + [i]
                
                # Check if item value matches (if include_values is True and item is string)
                if include_values and isinstance(item, str):
                    if _matches_pattern(item, pattern, match_type, case_sensitive):
                        matches.append({
                            'path': '.'.join(map(str, new_path)),
                            'path_list': new_path,
                            'key': i,
                            'value': item,
                            'parent_type': 'list',
                            'match_type': 'value'
                        })
                
                # Recurse into nested structures
                if isinstance(item, (dict, list)):
                    _search_recursive(item, new_path, depth + 1)
    
    def _matches_pattern(text: str, pattern: str, match_type: str, case_sensitive: bool) -> bool:
        """Check if text matches the pattern based on match_type."""
        if not case_sensitive:
            text = text.lower()
            pattern = pattern.lower()
        
        if match_type == 'exact':
            return text == pattern
        elif match_type == 'contains':
            return pattern in text
        elif match_type == 'startswith':
            return text.startswith(pattern)
        elif match_type == 'endswith':
            return text.endswith(pattern)
        elif match_type == 'regex':
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                return bool(re.search(pattern, text, flags))
            except re.error:
                return False
        else:
            raise ValueError(f"Invalid match_type: {match_type}")
    
    _search_recursive(data)
    return matches


def findvalues(data: Dict[str, Any], 
              pattern: Any, 
              match_type: str = 'exact', 
              case_sensitive: bool = True, 
              value_types: Optional[List[type]] = None, 
              max_depth: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Search for specific values in a nested data structure and return their paths (jq-style findvalues).

    Args:
        data: The nested data structure to search
        pattern: The pattern to search for
        match_type: Type of matching - 'exact', 'contains', 'startswith', 'endswith', 'regex'
        case_sensitive: Whether matching should be case sensitive (for string values)
        value_types: List of types to search in (e.g., [str, int]). None means all types.
        max_depth: Maximum depth to search (None for unlimited)

    Returns:
        List of dictionaries with keys: 'path', 'key', 'value', 'parent_type'

    Examples:
        findvalues(data, True)  # Find all boolean True values
        findvalues(data, 'john', 'contains', case_sensitive=False)
        findvalues(data, 42, value_types=[int])
    """
    matches = []
    
    def _search_recursive(obj: Any, current_path: Optional[List[Union[str, int]]] = None, depth: int = 0):
        if current_path is None:
            current_path = []
        
        if max_depth is not None and depth > max_depth:
            return
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = current_path + [key]
                
                # Check if value matches
                if _value_matches(value, pattern, match_type, case_sensitive, value_types):
                    matches.append({
                        'path': '.'.join(map(str, new_path)),
                        'path_list': new_path,
                        'key': key,
                        'value': value,
                        'parent_type': 'dict'
                    })
                
                # Recurse into nested structures
                if isinstance(value, (dict, list)):
                    _search_recursive(value, new_path, depth + 1)
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = current_path + [i]
                
                # Check if item matches
                if _value_matches(item, pattern, match_type, case_sensitive, value_types):
                    matches.append({
                        'path': '.'.join(map(str, new_path)),
                        'path_list': new_path,
                        'key': i,
                        'value': item,
                        'parent_type': 'list'
                    })
                
                # Recurse into nested structures
                if isinstance(item, (dict, list)):
                    _search_recursive(item, new_path, depth + 1)
    
    def _value_matches(value: Any, pattern: Any, match_type: str, case_sensitive: bool, value_types: Optional[List[type]]) -> bool:
        """Check if value matches the pattern."""
        # Type filtering
        if value_types is not None and type(value) not in value_types:
            return False
        
        # For exact matches with non-string types
        if match_type == 'exact' and not isinstance(value, str):
            return value == pattern
        
        # Convert to string for pattern matching
        if not isinstance(value, str):
            value = str(value)
        
        pattern_str = str(pattern)
        
        if not case_sensitive:
            value = value.lower()
            pattern_str = pattern_str.lower()
        
        if match_type == 'exact':
            return value == pattern_str
        elif match_type == 'contains':
            return pattern_str in value
        elif match_type == 'startswith':
            return value.startswith(pattern_str)
        elif match_type == 'endswith':
            return value.endswith(pattern_str)
        elif match_type == 'regex':
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                return bool(re.search(pattern_str, value, flags))
            except re.error:
                return False
        else:
            return False
    
    _search_recursive(data)
    return matches


# === UTILITY FUNCTIONS ===

def batch_setpath(data: Dict[str, Any], modifications: List[Tuple[str, Any, ...]]) -> Dict[str, Any]:
    """
    jq-style batch_setpath: Apply multiple setpath/append/delete operations to a nested data structure.

    Args:
        data: The data structure to modify
        modifications: List of tuples (path, value, operation)

    Returns:
        Modified data structure

    Examples:
        batch_setpath(data, [
            ('user.name', 'John Doe'),
            ('user.age', 30),
            ('user.tags', 'python', 'append'),
            ('old.field', None, 'delete')
        ])
    """
    for mod in modifications:
        if len(mod) == 2:
            path, value = mod
            operation = 'set'
        else:
            path, value, operation = mod
        # Special case: if operation is 'append' and value is a list of length 1, append the element, not the list
        if operation == 'append' and isinstance(value, list) and len(value) == 1:
            setpath(data, path, value[0], operation)
        else:
            setpath(data, path, value, operation)
    return data


def flatten(data: Dict[str, Any], separator: str = '.', prefix: str = '') -> Dict[str, Any]:
    """
    jq-style flatten: Flatten a nested dictionary into a single-level dictionary with dotted keys.

    Args:
        data: The nested dictionary to flatten
        separator: Separator to use between keys (default: '.')
        prefix: Prefix for all keys (default: '')

    Returns:
        Flattened dictionary

    Examples:
        flatten({'a': {'b': {'c': 1}}})  # {'a.b.c': 1}
        flatten({'users': [{'name': 'John'}]})  # {'users[0].name': 'John'}
    """
    items = []
    
    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key
        
        if isinstance(value, dict):
            items.extend(flatten(value, separator, new_key).items())
        elif isinstance(value, list):
            for i, item in enumerate(value):
                list_key = f"{new_key}[{i}]"
                if isinstance(item, dict):
                    items.extend(flatten(item, separator, list_key).items())
                else:
                    items.append((list_key, item))
        else:
            items.append((new_key, value))
    
    return dict(items)


def unflatten(data: Dict[str, Any], separator: str = '.') -> Dict[str, Any]:
    """
    jq-style unflatten: Unflatten a dictionary with dotted keys into a nested structure.

    Args:
        data: The flattened dictionary to unflatten
        separator: Separator used between keys (default: '.')

    Returns:
        Nested dictionary

    Examples:
        unflatten({'a.b.c': 1})  # {'a': {'b': {'c': 1}}}
    """
    result = {}
    for key, value in data.items():
        # Support list-style keys like 'a.b[0].c' by splitting and parsing indices
        path = []
        for part in key.split(separator):
            # Split out [index] notation
            while '[' in part and part.endswith(']'):
                before, after = part.split('[', 1)
                if before:
                    path.append(before)
                idx = after[:-1]  # remove trailing ]
                try:
                    idx = int(idx)
                except ValueError:
                    pass
                path.append(idx)
                part = ''
            if part:
                path.append(part)
        setpath(result, path, value, create_missing=True)
    return result


def merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    jq-style merge: Deep merge two dictionaries, with dict2 values taking precedence.

    Args:
        dict1: Base dictionary
        dict2: Dictionary to merge into dict1

    Returns:
        New merged dictionary

    Examples:
        merge({'a': {'b': 1}}, {'a': {'c': 2}})  # {'a': {'b': 1, 'c': 2}}
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    
    return result



# === CLOUDFLARE WORKERS INTEGRATION ===

def create_worker_response(data: Dict[str, Any], status: int = 200, headers: Optional[Dict[str, str]] = None) -> str:
    """
    Helper function to create a JSON response for Cloudflare Workers.
    
    Args:
        data: Data to serialize as JSON
        status: HTTP status code
        headers: Optional HTTP headers
    
    Returns:
        JSON string suitable for Response.new()
        
    Examples:
        json_response = create_worker_response({'success': True, 'data': result})
    """
    try:
        return json.dumps(data, separators=(',', ':'))  # Compact JSON
    except (TypeError, ValueError) as e:
        # Fallback for non-serializable data
        return json.dumps({
            "error": f"JSON serialization failed: {str(e)}",
            "status": "error"
        })


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string with fallback.
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON data or default value
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default


# === EXAMPLE CLOUDFLARE WORKER HANDLER ===

async def example_worker_handler(request, env):
    """
    Example Worker handler showing how to use the nested utilities.
    This demonstrates usage patterns for Cloudflare Workers.
    """
    try:
        # Import at function level for Cloudflare Workers
        from js import Response
        
        # Parse request body
        request_data = await request.json()
        
        # Extract user information safely
        user_info = getpaths(request_data, {
            'name': 'user.profile.name',
            'email': 'user.profile.email',
            'theme': 'user.settings.theme',
            'notifications': 'user.settings.notifications'
        }, default=None)
        
        # Add processing metadata
        setpath(request_data, 'metadata.processed_at', '2025-01-01T00:00:00Z')
        setpath(request_data, 'metadata.server', 'cloudflare-workers')
        setpath(request_data, 'metadata.version', '1.0.0')
        
        # Search for sensitive data fields
        sensitive_fields = findpaths(
            request_data, 
            r'(password|secret|key|token)', 
            'regex', 
            case_sensitive=False
        )
        
        # Batch update user preferences
        if haspath(request_data, 'user.settings'):
            batch_setpath(request_data, [
                ('user.settings.last_login', '2025-01-01T00:00:00Z'),
                ('user.settings.login_count', 1, 'append'),
                ('user.flags.processed', True)
            ])
        
        # Create response
        response_data = {
            'success': True,
            'user_info': user_info,
            'sensitive_fields_detected': len(sensitive_fields),
            'processed': True,
            'timestamp': '2025-01-01T00:00:00Z'
        }
        
        # Return JSON response
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
    # Core functions
    'modify_nested',
    'get_nested', 
    'has_nested',
    'get_multiple_nested',
    
    # Search functions
    'find_attributes',
    'find_values',
    
    # Utility functions
    'batch_modify',
    'flatten_dict',
    'unflatten_dict', 
    'deep_merge',
    
    # Worker helpers
    'create_worker_response',
    'safe_json_loads',
    'example_worker_handler'
]


if __name__ == "__main__":
    # Example usage and testing
    print("🐍 Nested Data Structure Utilities for Cloudflare Python Workers")
    print(f"Version: {__version__}")
    print("=" * 60)
    
    # Sample data
    sample_data = {
        'user': {
            'profile': {
                'name': 'John Doe',
                'age': 30,
                'email': 'john@example.com'
            },
            'settings': {
                'theme': 'dark',
                'notifications': True,
                'preferences': ['email', 'sms']
            }
        },
        'metadata': {
            'version': '1.0',
            'created': '2024-01-01'
        }
    }
    
    print("Original data:")
    print(json.dumps(sample_data, indent=2))
    
    # Demonstrate core functionality
    print("\n🔧 Core Operations:")
    
    # Get operations
    name = getpath(sample_data, 'user.profile.name')
    print(f"User name: {name}")
    
    # Modify operations
    setpath(sample_data, 'user.profile.age', 31)
    setpath(sample_data, 'user.profile.city', 'New York')
    setpath(sample_data, 'user.settings.preferences', 'push', 'append')
    
    # Search operations
    name_fields = findpaths(sample_data, 'name')
    print(f"Found {len(name_fields)} 'name' fields")
    
    # Batch operations
    user_info = getpaths(sample_data, {
        'name': 'user.profile.name',
        'age': 'user.profile.age',
        'theme': 'user.settings.theme'
    })
    print(f"User info: {user_info}")
    
    print("\nModified data:")
    print(json.dumps(sample_data, indent=2))
    
    print(f"\n✅ All functions ready for Cloudflare Python Workers!")
    print(f"📦 Uses only standard library: {', '.join(__dependencies__)}")
