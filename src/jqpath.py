import json
import re
from collections.abc import Callable
from typing import Any

# === ADVANCED JQ-STYLE PATH/SELECTOR LOGIC (MIGRATED FROM setpath.py) ===

Selector = str | int | slice | Callable[[Any, Any, list[Any]], bool]
PathType = list[Selector]

def _normalize_path(path: str | PathType, separator: str = '.') -> PathType:
    if isinstance(path, str):
        parts = path.split(separator)
        norm: list[Selector] = []
        for p in parts:
            if p.isdigit() or (p.startswith('-') and p[1:].isdigit()):
                norm.append(int(p))
            else:
                norm.append(p)
        return norm
    return list(path)

def _is_selector(obj):
    # Treat as selector if it's a callable, a slice, a dict (for dict selector),
    # or a string with '=' (for string selector)
    return (
        callable(obj)
        or isinstance(obj, slice)
        or isinstance(obj, dict)
        or (isinstance(obj, str) and '=' in obj)
    )

def _match_selector(key, value, selector, path_so_far):
    if callable(selector):
        return selector(key, value, path_so_far)
    if isinstance(selector, slice):
        if isinstance(key, int):
            return key in range(*selector.indices(1 << 30))
        return False
    return key == selector

def _find_selector_paths(obj, selectors: PathType, path_so_far=None, only_first=False):
    if path_so_far is None:
        path_so_far: list[Any] = []
    if not selectors:
        yield list(path_so_far)
        return
    sel, *rest = selectors
    if isinstance(obj, dict):
        for k, v in obj.items():
            if _match_selector(k, v, sel, path_so_far):
                yield from _find_selector_paths(
                    v, rest, [*path_so_far, k], only_first
                )
                if only_first:
                    return
    elif isinstance(obj, list):
        # Always match int selectors as direct indices, others as selector functions
        if isinstance(sel, int):
            idx = sel if sel >= 0 else len(obj) + sel
            if 0 <= idx < len(obj):
                v = obj[idx]
                yield from _find_selector_paths(
                    v, rest, [*path_so_far, idx], only_first
                )
                if only_first:
                    return
        else:
            for i, v in enumerate(obj):
                if _match_selector(i, v, sel, path_so_far):
                    yield from _find_selector_paths(
                        v, rest, [*path_so_far, i], only_first
                    )
                    if only_first:
                        return

def _convert_selector(sel):
    # Convert dict selector to a function
    if isinstance(sel, dict):
        def dict_selector(key, value, path_so_far, sel=sel):
            if not isinstance(value, dict):
                return False
            for k, v in sel.items():
                if value.get(k) != v:
                    return False
            return True
        return dict_selector
    # Convert string selector of the form 'key=value' to a function
    if isinstance(sel, str) and '=' in sel:
        key, eq, value = sel.partition('=')
        key = key.strip()
        value = value.strip()
        def str_selector(k, v, path_so_far, key=key, value=value):
            if isinstance(v, dict):
                # Try to match as string or int
                vval = v.get(key)
                if vval is not None and (str(vval) == value or vval == value):
                    return True
            return False
        return str_selector
    return sel

def _convert_selectors_path(selectors):
    # Recursively convert selectors in a path
    out = []
    for s in selectors:
        # If s is a dict, always convert to a selector function
        if isinstance(s, dict):
            out.append(_convert_selector(s))
        else:
            out.append(_convert_selector(s))
    return out

def selectorspaths(obj, selectors: PathType, only_first=False):
    # Always convert selectors, including ints, to ensure selector logic is used for all path types
    selectors = _convert_selectors_path(selectors)
    return list(_find_selector_paths(obj, selectors, only_first=only_first))

def getpath(obj, path, default=None, separator='.', only_first_path_match=False):
    selectors = _normalize_path(path, separator)
    selectors = _convert_selectors_path(selectors)
    paths = selectorspaths(obj, selectors, only_first=only_first_path_match)
    if paths:
        for p in paths:
            try:
                result = _getpath(obj, p)
                return result
            except Exception:
                continue
        return default
    # If no match, try alternate path form (string <-> list)
    if isinstance(path, list):
        str_path = '.'.join(str(p) for p in path)
        selectors2 = _normalize_path(str_path, separator)
        selectors2 = _convert_selectors_path(selectors2)
        paths2 = selectorspaths(obj, selectors2, only_first=only_first_path_match)
        if paths2:
            for p in paths2:
                try:
                    result = _getpath(obj, p)
                    return result
                except Exception:
                    continue
    elif isinstance(path, str):
        list_path = [
            int(p) if p.isdigit() or (p.startswith('-') and p[1:].isdigit()) else p
            for p in path.split(separator)
        ]
        selectors2 = _normalize_path(list_path, separator)
        selectors2 = _convert_selectors_path(selectors2)
        paths2 = selectorspaths(obj, selectors2, only_first=only_first_path_match)
        if paths2:
            for p in paths2:
                try:
                    result = _getpath(obj, p)
                    return result
                except Exception:
                    continue
    return default


def _find_in_list(
    current,
    sel,
    selectors,
    create_missing=False,
    next_sel=None,
    value=None,
    operation=None,
    path_so_far=None,
):
    """Helper for traversing a list with a selector (function or index)."""
    if path_so_far is None:
        path_so_far = []
    if callable(sel):
        for idx, item in enumerate(current):
            if sel(idx, item, path_so_far):
                return idx, item
        if create_missing:
            # If create_missing, append a new dict or list
            if isinstance(next_sel, int):
                new_item = []
            else:
                new_item = {} if operation != 'set' or value is None else value
            current.append(new_item)
            return len(current) - 1, new_item
        raise KeyError(f"No list element matches selector: {sel}")
    else:
        idx = sel if isinstance(sel, int) else int(sel)
        # Always extend the list if create_missing is True and idx is out of range
        if create_missing:
            while idx >= len(current):
                # If next_sel is an int, create a list, else a dict
                if next_sel is not None and isinstance(next_sel, int):
                    current.append([])
                else:
                    current.append({})
        if idx >= len(current):
            raise IndexError(idx)
        return idx, current[idx]

def _getpath(obj, selectors):
    current = obj
    path_so_far = []
    for sel in selectors:
        if isinstance(current, dict):
            current = current[sel]
            path_so_far.append(sel)
        elif isinstance(current, list):
            idx, current = _find_in_list(current, sel, selectors, path_so_far=path_so_far)
            path_so_far.append(idx)
        else:
            raise KeyError(sel)
    return current

def setpath(
    obj,
    path,
    value=None,
    operation='set',
    create_missing=True,
    only_first_path_match=False,
):
    selectors = _normalize_path(path)
    selectors = _convert_selectors_path(selectors)
    if any(_is_selector(s) for s in selectors):
        paths = selectorspaths(obj, selectors, only_first=only_first_path_match)
        if not paths:
            if not create_missing:
                raise KeyError(f"No matching path for selectors: {selectors}")
            _setpath(obj, selectors, value, operation, create_missing)
            return obj
        for p in paths:
            _setpath(obj, p, value, operation, create_missing)
        return obj
    else:
        return _setpath(obj, selectors, value, operation, create_missing)


def _setpath(obj, selectors, value, operation, create_missing):
    current = obj
    i = 0
    while i < len(selectors) - 1:
        sel = selectors[i]
        next_sel = selectors[i+1]
        if isinstance(current, dict):
            # If key missing or wrong type, create correct type
            if (
                sel not in current
                or (
                    isinstance(next_sel, int)
                    and not isinstance(current.get(sel), list)
                )
                or (
                    not isinstance(next_sel, int)
                    and not isinstance(current.get(sel), dict)
                )
            ):
                if create_missing:
                    if isinstance(next_sel, int):
                        current[sel] = []
                    else:
                        current[sel] = {}
                else:
                    raise KeyError(sel)
            current = current[sel]
        elif isinstance(current, list):
            # Always extend the list if create_missing is True and idx is out of range
            idx = sel if isinstance(sel, int) else int(sel)
            if create_missing:
                while idx >= len(current):
                    if isinstance(next_sel, int):
                        current.append([])
                    else:
                        current.append({})
            if idx >= len(current):
                raise IndexError(idx)
            current = current[idx]
        else:
            raise TypeError(f"Cannot traverse {type(current)} at {sel}")
        i += 1
    last = selectors[-1]
    if isinstance(current, dict):
        if operation == 'set':
            current[last] = value
        elif operation == 'delete':
            if last in current:
                del current[last]
        elif operation == 'append':
            if last not in current or not isinstance(current[last], list):
                current[last] = []
            current[last].append(value)
        elif operation == 'extend':
            if last not in current or not isinstance(current[last], list):
                current[last] = []
            current[last].extend(value)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    elif isinstance(current, list):
        if callable(last):
            try:
                idx, _ = _find_in_list(
                    current,
                    last,
                    selectors,
                    create_missing=False,
                    value=value,
                    operation=operation,
                )
            except KeyError:
                if create_missing:
                    # Try to synthesize a new element matching the selector
                    new_item = {}
                    key = value_ = None
                    # Dict selector
                    if hasattr(last, '__closure__') and last.__closure__:
                        for cell in last.__closure__:
                            if isinstance(cell.cell_contents, dict):
                                new_item = dict(cell.cell_contents)
                                break
                    # String selector
                    if hasattr(last, '__name__') and last.__name__ == 'str_selector':
                        if hasattr(last, '__closure__') and last.__closure__:
                            closure = last.__closure__
                            if len(closure) >= 2:
                                key = closure[0].cell_contents
                                value_ = closure[1].cell_contents
                                new_item = {key: value_}
                    # If there are more selectors after this, set recursively
                    if len(selectors) > 1:
                        _setpath(new_item, selectors[1:], value, operation, create_missing)
                    else:
                        # Last selector: for set, set the new item directly to value
                        if operation == 'set':
                            new_item = value
                        elif operation == 'append' or operation == 'extend':
                            new_item = value
                    current.append(new_item)
                    idx = len(current) - 1
                else:
                    raise
            if operation == 'set':
                current[idx] = value
            elif operation == 'delete':
                del current[idx]
            elif operation == 'append':
                if not isinstance(current[idx], list):
                    current[idx] = []
                current[idx].append(value)
            elif operation == 'extend':
                if not isinstance(current[idx], list):
                    current[idx] = []
                current[idx].extend(value)
            else:
                raise ValueError(f"Unknown operation: {operation}")
        else:
            idx = last if isinstance(last, int) else int(last)
            if operation == 'set':
                while idx >= len(current):
                    if create_missing:
                        current.append(None)
                    else:
                        raise IndexError(idx)
                current[idx] = value
            elif operation == 'delete':
                if 0 <= idx < len(current):
                    del current[idx]
            elif operation == 'append':
                current.append(value)
            elif operation == 'extend':
                current.extend(value)
            else:
                raise ValueError(f"Unknown operation: {operation}")
    else:
        raise TypeError(f"Cannot set path on {type(current)}")
    return obj

def getpaths(obj, paths, default=None, only_first_path_match=False):
    if isinstance(paths, dict):
        return {
            k: getpath(obj, v, default, only_first_path_match=only_first_path_match)
            for k, v in paths.items()
        }
    else:
        return [
            getpath(obj, p, default, only_first_path_match=only_first_path_match)
            for p in paths
        ]

def haspath(obj, path, separator='.'):
    selectors = _normalize_path(path, separator)
    selectors = _convert_selectors_path(selectors)
    try:
        _getpath(obj, selectors)
        return True
    except Exception:
        return False

# === END ADVANCED JQ-STYLE PATH/SELECTOR LOGIC ===

# === DELETION FUNCTIONS (jq-style) ===


def delpath(
    data: dict[str, Any], path: str | list[str | int]
) -> dict[str, Any]:
    # Delete the value at the specified path in a nested data structure.
    # If the path does not exist, do nothing.
    try:
        setpath(data, path, operation='delete', create_missing=True)
    except (KeyError, IndexError):
        pass
    return data

def delpaths(
    data: dict[str, Any], paths: list[str | list[str | int]]
) -> dict[str, Any]:
    # Delete multiple paths in a nested data structure (jq-style delpaths).
    # If a path does not exist, it is ignored.
    for path in paths:
        try:
            setpath(data, path, operation='delete', create_missing=True)
        except (KeyError, IndexError):
            pass
    return data


# === SEARCH FUNCTIONS ===

def findpaths(data: dict[str, Any], 
             pattern: str,
             match_type: str = 'exact',
             case_sensitive: bool = True,
             include_values: bool = False,
             max_depth: int | None = None) -> list[dict[str, Any]]:
    """Search for attributes/keys in a nested data structure and return their paths.
    Example: find_attributes(data, 'name') or find_attributes(data, r'.*_id$', 'regex')
    """
    matches = []
    
    def _search_recursive(obj: Any, current_path: list[str | int] | None = None, depth: int = 0):
        if current_path is None:
            current_path = []

        if max_depth is not None and depth > max_depth:
            return

        if isinstance(obj, dict):
            for key, value in obj.items():
                key_str = str(key)
                new_path = [*current_path, key]

                # Check if key matches
                if _matches_pattern(key_str, pattern, match_type, case_sensitive):
                    matches.append({
                        'path': '.'.join(map(str, new_path)),
                        'path_list': new_path,
                        'key': key,
                        'value': value,
                        'parent_type': 'dict',
                        'match_type': 'key',
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
                            'match_type': 'value',
                        })

                # Recurse into nested structures
                if isinstance(value, dict | list):
                    _search_recursive(value, new_path, depth + 1)

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = [*current_path, i]

                # Check if item value matches (if include_values is True and item is string)
                if include_values and isinstance(item, str):
                    if _matches_pattern(item, pattern, match_type, case_sensitive):
                        matches.append({
                            'path': '.'.join(map(str, new_path)),
                            'path_list': new_path,
                            'key': i,
                            'value': item,
                            'parent_type': 'list',
                            'match_type': 'value',
                        })

                # Recurse into nested structures
                if isinstance(item, dict | list):
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


def findvalues(data: dict[str, Any], 
              pattern: Any,
              match_type: str = 'exact',
              case_sensitive: bool = True,
              value_types: list[type] | None = None,
              max_depth: int | None = None) -> list[dict[str, Any]]:
    """Search for specific values in a nested data structure and return their paths.
    Example: find_values(data, True) or find_values(data, 'john', 'contains', case_sensitive=False)
    """
    matches = []
    
    def _search_recursive(obj: Any, current_path: list[str | int] | None = None, depth: int = 0):
        if current_path is None:
            current_path = []

        if max_depth is not None and depth > max_depth:
            return

        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = [*current_path, key]

                # Check if value matches
                if _value_matches(value, pattern, match_type, case_sensitive, value_types):
                    matches.append({
                        'path': '.'.join(map(str, new_path)),
                        'path_list': new_path,
                        'key': key,
                        'value': value,
                        'parent_type': 'dict',
                    })

                # Recurse into nested structures
                if isinstance(value, dict | list):
                    _search_recursive(value, new_path, depth + 1)

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = [*current_path, i]

                # Check if item matches
                if _value_matches(item, pattern, match_type, case_sensitive, value_types):
                    matches.append({
                        'path': '.'.join(map(str, new_path)),
                        'path_list': new_path,
                        'key': i,
                        'value': item,
                        'parent_type': 'list',
                    })

                # Recurse into nested structures
                if isinstance(item, dict | list):
                    _search_recursive(item, new_path, depth + 1)
    
    def _value_matches(
        value: Any,
        pattern: Any,
        match_type: str,
        case_sensitive: bool,
        value_types: list[type] | None,
    ) -> bool:
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

# === getpaths_setpaths ===
def getpaths_setpaths(src, tgt, pairs, default=None):
    """
    Copy values from src to tgt by path pairs. Each pair is (src_path, tgt_path).
    Supports list of pairs or a single pair.
    """
    # If pairs is a tuple or list of length 2 and both elements are not themselves pairs,
    # treat as a single pair
    if (
        isinstance(pairs, tuple | list)
        and len(pairs) == 2
        and not (isinstance(pairs[0], tuple | list) and len(pairs[0]) == 2)
    ):
        pairs = [pairs]
    if not pairs:
        return tgt
    for pair in pairs:
        if not isinstance(pair, tuple | list) or len(pair) != 2:
            continue
        src_path, tgt_path = pair
        if isinstance(src_path, tuple):
            src_path = list(src_path)
        if isinstance(tgt_path, tuple):
            tgt_path = list(tgt_path)
        value = getpath(src, src_path, default)
        if value is None and default is None:
            if isinstance(src_path, list):
                str_path = '.'.join(str(p) for p in src_path)
                value = getpath(src, str_path, default)
            elif isinstance(src_path, str):
                list_path = [
                    int(p) if p.isdigit() or (p.startswith('-') and p[1:].isdigit()) else p
                    for p in src_path.split('.')
                ]
                value = getpath(src, list_path, default)
        if isinstance(value, list):
            value = value.copy()
        elif isinstance(value, dict):
            value = value.copy()
        setpath(tgt, tgt_path, value)
    return tgt

def batch_setpath(
    data: dict[str, Any], modifications: list[tuple[Any, ...]]
) -> dict[str, Any]:
    """
    Apply multiple modifications to a nested data structure.
    Example:
        batch_modify(
            data,
            [
                ('user.name', 'John Doe'),
                ('user.age', 30),
                ('user.tags', 'python', 'append'),
                ('old.field', None, 'delete'),
            ],
        )
    """
    for mod in modifications:
        if len(mod) == 2:
            path, value = mod
            operation = 'set'
        else:
            path, value, operation = mod
        # Special case: if operation == 'append' and value is a list of length 1,
        # append the element, not the list
        if operation == 'append' and isinstance(value, list) and len(value) == 1:
            setpath(data, path, value[0], operation)
        else:
            setpath(data, path, value, operation)
    return data


def flatten(data: dict[str, Any], separator: str = '.', prefix: str = '') -> dict[str, Any]:
    """Flatten a nested dictionary into a single-level dictionary with dotted keys."""
    items: list[tuple[str, Any]] = []
    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key
        if isinstance(value, dict):
            items += list(flatten(value, separator, new_key).items())
        elif isinstance(value, list):
            for i, item in enumerate(value):
                list_key = f"{new_key}[{i}]"
                if isinstance(item, dict):
                    items += list(flatten(item, separator, list_key).items())
                else:
                    items.append((list_key, item))
        else:
            items.append((new_key, value))
    return dict(items)


def unflatten(data: dict[str, Any], separator: str = '.') -> dict[str, Any]:
    """Unflatten a dictionary with dotted keys into a nested structure."""
    result: dict[str, Any] = {}
    import re
    index_pattern = re.compile(r"([^[\]]+)|\[(\d+)\]")
    for key, value in data.items():
        path: list[str | int] = []
        parts = key.split(separator)
        for part in parts:
            for match in index_pattern.finditer(part):
                if match.group(1) is not None:
                    seg = match.group(1)
                    if seg != '':
                        path.append(seg)
                elif match.group(2) is not None:
                    path.append(int(match.group(2)))
        setpath(result, path, value, create_missing=True)
    return result


def merge(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries, with dict2 values taking precedence."""
    result: dict[str, Any] = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


# === CLOUDFLARE WORKERS INTEGRATION ===

def create_worker_response(
    data: dict[str, Any],
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> str:
    """Helper function to create a JSON response for Cloudflare Workers."""
    try:
        return json.dumps(data, separators=(',', ':'))  # Compact JSON
    except (TypeError, ValueError) as e:
        # Fallback for non-serializable data
        return json.dumps({
            "error": f"JSON serialization failed: {e!s}",
            "status": "error"
        })


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string with fallback."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default


# === EXAMPLE CLOUDFLARE WORKER HANDLER ===

async def example_worker_handler(request, env):
    """Example Worker handler showing how to use the nested utilities."""
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
    'setpath',
    'unflatten',
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
    
