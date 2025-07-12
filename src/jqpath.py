import json
import re
from collections.abc import Callable, Iterator
from typing import Any, Union

# === TYPE DEFINITIONS ===
Selector = Union[str, int, slice, Callable[..., bool]]
PathType = list[Selector]

# === SELECTOR HELPERS ===

def select_key_exists(key):
    return lambda k, v: isinstance(v, dict) and key in v

def select_key_missing(key):
    return lambda k, v: isinstance(v, dict) and key not in v

def select_type(type_):
    return lambda k, v: isinstance(v, type_)

def select_regex(field, pattern):
    regex = re.compile(pattern)
    return lambda k, v: isinstance(v, dict) and field in v and isinstance(v[field], str) and regex.search(v[field])

def select_gt(field, value):
    return lambda k, v: isinstance(v, dict) and v.get(field) is not None and v.get(field) > value

def select_lt(field, value):
    return lambda k, v: isinstance(v, dict) and v.get(field) is not None and v.get(field) < value

def select_eq(field, value):
    return lambda k, v: isinstance(v, dict) and v.get(field) == value

def select_contains(field, substring):
    return lambda k, v: isinstance(v, dict) and substring in str(v.get(field, ""))

def select_all(k, v):
    return True

# === CORE PATH LOGIC ===

def _normalize_path(path: Union[str, PathType], separator: str = '.') -> PathType:
    if isinstance(path, str):
        return [int(p) if p.isdigit() or (p.startswith('-') and p[1:].isdigit()) else p for p in path.split(separator)]
    return path

def _convert_selector(sel: Selector) -> Selector:
    if isinstance(sel, dict):
        return lambda item: isinstance(item, dict) and all(item.get(k) == v for k, v in sel.items())
    return sel

def _convert_selectors_path(selectors: PathType) -> list:
    if isinstance(selectors, str):
        return selectors.split('.')
    if isinstance(selectors, list):
        # Correctly handle integers without converting them to strings
        return [s if callable(s) or isinstance(s, (dict, slice, int)) else str(s) for s in selectors]
    # Handle single non-list, non-string selector
    if callable(selectors) or isinstance(selectors, (dict, slice, int)):
        return [selectors]
    return [str(selectors)]

def _match_selector(key_or_index: Any, value: Any, selector: Any) -> bool:
    if callable(selector):
        try:
            return selector(key_or_index, value)
        except Exception:
            return False
    elif isinstance(selector, dict):
        if not isinstance(value, dict):
            return False
        return all(item in value.items() for item in selector.items())
    # For int selectors in lists, we match the index.
    elif isinstance(selector, int):
        return key_or_index == selector
    # For other selectors, we match the key.
    return str(key_or_index) == str(selector)

def _find_selector_paths(obj: Any, selectors: PathType, path_so_far: list, only_first: bool) -> Iterator[PathType]:
    if not selectors:
        yield path_so_far
        return

    sel, *rest = selectors
    if isinstance(obj, list):
        # Correctly handle different selector types for lists
        if isinstance(sel, slice):
            indices = range(*sel.indices(len(obj)))
            for i in indices:
                yield from _find_selector_paths(obj[i], rest, path_so_far + [i], only_first)
                if only_first and rest: return
        elif isinstance(sel, int):
            # Handle negative indices correctly
            idx = sel if sel >= 0 else len(obj) + sel
            if 0 <= idx < len(obj):
                yield from _find_selector_paths(obj[idx], rest, path_so_far + [idx], only_first)
        else: # Handles callable and dict selectors
            for i, item in enumerate(obj):
                if _match_selector(i, item, sel):
                    yield from _find_selector_paths(item, rest, path_so_far + [i], only_first)
                    if only_first: return

    elif isinstance(obj, dict):
        for k, v in obj.items():
            if _match_selector(k, v, sel):
                yield from _find_selector_paths(v, rest, path_so_far + [k], only_first)
                if only_first: return

def selectorspaths(obj: Any, selectors: PathType, only_first: bool = False) -> Iterator[PathType]:
    selectors = _convert_selectors_path(selectors)
    return _find_selector_paths(obj, selectors, [], only_first)

def _getpath(obj: Any, path: PathType):
    for sel in path:
        if isinstance(obj, list):
            if isinstance(sel, int):
                obj = obj[sel]
            else:
                return None
        elif isinstance(obj, dict):
            obj = obj.get(sel)
        else:
            return None
    return obj

def getpath(obj: Any, path: Union[str, PathType], default: Any = None, separator: str = '.', only_first_path_match: bool = True):
    """Gets a value from a nested object using a path, with support for selectors.

    Args:
        obj: The object to get the value from.
        path: The path to the value. Can be a string or a list containing keys, indices, or selectors.
        default: The default value to return if the path doesn't exist.
        separator: The separator to use for string paths.
        only_first_path_match: If False, and selectors match multiple items, returns a list of all values.

    Returns:
        The value at the given path, a list of values, or the default value.
    """
    if isinstance(path, str):
        path = [int(p) if p.isdigit() else p for p in path.split(separator)]

    # Check if the path contains any non-standard selectors that require selectorspaths
    is_complex_path = any(not isinstance(p, (str, int)) for p in path)

    if not is_complex_path:
        # Fast path for simple key/index lookups
        current = obj
        for sel in path:
            if isinstance(current, dict):
                if sel in current:
                    current = current[sel]
                else:
                    return default
            elif isinstance(current, list) and isinstance(sel, int):
                if 0 <= sel < len(current):
                    current = current[sel]
                else:
                    return default
            else:
                return default
        return current

    # Slow path for complex selectors. Always get all paths and decide later whether to return one or all.
    resolved_paths = list(selectorspaths(obj, path, only_first=False))

    if not resolved_paths:
        return default

    values = []
    for p in resolved_paths:
        # We reuse the internal _getpath which is fast and simple
        values.append(_getpath(obj, p))

    if only_first_path_match:
        return values[0] if values else default
    else:
        return values

def setpath(obj: Any, path: Union[str, PathType], value: Any, create_missing: bool = True, separator: str = '.', operation: str = 'set', only_first_path_match: bool = False):
    # Hybrid approach: First, use selectorspaths to find existing paths for modification.
    # This correctly handles complex selectors (dict, callable, etc.).
    paths_to_modify = list(selectorspaths(obj, path, only_first=only_first_path_match))

    # If no paths are found AND we are allowed to create them, we prepare a simple path for creation.
    # This creation path does not support complex selectors.
    if not paths_to_modify and create_missing:
        if isinstance(path, str):
            # Convert dot-separated string to a list of keys/indices.
            paths_to_modify = [[int(p) if p.isdigit() else p for p in path.split(separator)]]
        elif isinstance(path, list) and all(isinstance(p, (str, int)) for p in path):
            paths_to_modify = [path]  # It's already a simple path.

    if not paths_to_modify:
        return # Nothing to do.

    for p in paths_to_modify:
        current_level = obj
        # Traverse to the second-to-last element to get the parent container.
        for i, sel in enumerate(p[:-1]):
            # --- Traversal and Creation Logic ---
            next_sel = p[i + 1]
            if isinstance(current_level, dict):
                if sel not in current_level and create_missing:
                    current_level[sel] = [] if isinstance(next_sel, int) else {}
                current_level = current_level.get(sel)
            elif isinstance(current_level, list) and isinstance(sel, int):
                if sel >= len(current_level) and create_missing:
                    current_level.extend([None] * (sel - len(current_level) + 1))
                if sel < len(current_level):
                    if current_level[sel] is None and create_missing:
                        current_level[sel] = [] if isinstance(next_sel, int) else {}
                    current_level = current_level[sel]
                else:
                    current_level = None # Path broken
            else:
                current_level = None # Path broken
            
            if current_level is None:
                break # Stop if path is broken
        
        if current_level is None:
            continue # Move to next path if this one was broken

        # --- Perform the final operation on the parent container ---
        last_sel = p[-1]
        if operation == 'set':
            if isinstance(current_level, dict):
                current_level[last_sel] = value
            elif isinstance(current_level, list) and isinstance(last_sel, int):
                if last_sel < len(current_level):
                    current_level[last_sel] = value
                elif last_sel == len(current_level) and create_missing:
                    current_level.append(value)
        elif isinstance(current_level, list) and operation == 'append':
            current_level.append(value)
        elif isinstance(current_level, list) and operation == 'extend' and isinstance(value, list):
            current_level.extend(value)
        elif isinstance(current_level, dict) and last_sel in current_level and isinstance(current_level[last_sel], list):
            target_list = current_level[last_sel]
            if operation == 'append':
                target_list.append(value)
            elif operation == 'extend' and isinstance(value, list):
                target_list.extend(value)

def delpath(obj: Any, path: Union[str, PathType], separator: str = '.'):
    """Deletes an item from the data object at the specified path."""
    paths_to_del = selectorspaths(obj, path)
    # Sort paths in reverse order of indices and length to avoid shifting issues
    # when deleting from lists.
    sorted_paths = sorted(list(paths_to_del), key=lambda p: (str(p), len(p)), reverse=True)

    for p in sorted_paths:
        parent = getpath(obj, p[:-1])
        last_sel = p[-1]
        if parent is not None:
            try:
                if isinstance(parent, (dict, list)):
                    del parent[last_sel]
            except (KeyError, IndexError):
                pass # Item might have been removed by a previous broader selector

def delpaths(obj: Any, paths: list, separator: str = '.'):
    for path in paths:
        delpath(obj, path, separator)

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

def getpaths(obj, paths, default=None):
    return [getpath(obj, p, default) for p in paths]

def getpaths_setpaths(src_obj, tgt_obj, paths_map, default=None):
    for src_path, tgt_path in paths_map:
        value = getpath(src_obj, src_path, default)
        if value is not None:
            setpath(tgt_obj, tgt_path, value)

def haspath(obj: Any, path: Union[str, PathType], separator: str = '.') -> bool:
    try:
        next(selectorspaths(obj, path, only_first=True))
        return True
    except StopIteration:
        return False

# === FLATTEN/UNFLATTEN UTILITIES ===

def flatten(data: dict, separator: str = '.') -> dict[str, Any]:
    flat_dict = {}
    def _flatten_recursive(obj, prefix=''):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_prefix = f"{prefix}{separator}{key}" if prefix else key
                _flatten_recursive(value, new_prefix)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_prefix = f"{prefix}{separator}{i}" if prefix else str(i)
                _flatten_recursive(item, new_prefix)
        else:
            flat_dict[prefix] = obj
    _flatten_recursive(data)
    return flat_dict

def unflatten(data: dict[str, Any], separator: str = '.') -> dict:
    result = {}
    for key, value in data.items():
        setpath(result, key, value, separator=separator)
    return result

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
    
