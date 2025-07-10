import re
from typing import Any, Dict, List, Union, Optional, Callable, Iterator


# --- Common selectors ---
def select_key_exists(key):
    """
    Select dicts where the given key exists.
    Example: select_key_exists('foo') matches any dict with a 'foo' key.
    """
    return lambda item: isinstance(item, dict) and key in item

def select_key_missing(key):
    """
    Select dicts where the given key does NOT exist.
    Example: select_key_missing('foo') matches any dict without a 'foo' key.
    """
    return lambda item: isinstance(item, dict) and key not in item

def select_type(type_):
    """
    Select items of a given type (e.g., dict, list, str, int, etc).
    Example: select_type(dict) matches all dicts; select_type(str) matches all strings.
    """
    return lambda item: isinstance(item, type_)

def select_regex(field, pattern):
    """
    Select dicts where the value of 'field' matches the given regex pattern (as a string).
    Example: select_regex('name', r'^foo.*') matches dicts with a 'name' key whose value starts with 'foo'.
    """
    regex = re.compile(pattern)
    return lambda item: isinstance(item, dict) and field in item and isinstance(item[field], str) and regex.search(item[field])

def select_gt(field, value):
    """
    Select dicts where the value of 'field' is greater than the given value.
    Example: select_gt('age', 18) matches dicts with 'age' > 18.
    """
    return lambda item: isinstance(item, dict) and item.get(field) is not None and item.get(field) > value

def select_lt(field, value):
    """
    Select dicts where the value of 'field' is less than the given value.
    Example: select_lt('score', 100) matches dicts with 'score' < 100.
    """
    return lambda item: isinstance(item, dict) and item.get(field) is not None and item.get(field) < value

def select_eq(field, value):
    """
    Select dicts where field == value.
    Example: select_eq('id', 5) matches dicts with {'id': 5}.
    """
    return lambda item: isinstance(item, dict) and item.get(field) == value

def select_contains(field, substring):
    """
    Select dicts where substring in str(field value).
    Example: select_contains('name', 'foo') matches dicts with a 'name' containing 'foo'.
    """
    return lambda item: isinstance(item, dict) and substring in str(item.get(field, ""))

def select_all(item):
    """
    Select all items (wildcard).
    Example: select_all matches every item in a list (useful for bulk operations).
    """
    return True

# --- Public: selectorspaths ---
def selectorspaths(data: Any, path: List[Union[str, int, Callable]], current_path=None) -> Iterator[List[Any]]:
    """
    Yield all matching paths in data for a path of selectors (jq-style).
    Each path element can be:
      - str/int: dict key or list index
      - callable: select function for list items (applies to all matches)
    Yields lists of keys/indices representing the full path to each match.
    """
    if current_path is None:
        current_path = []
    if not path:
        yield current_path
        return
    key, *rest = path
    if isinstance(data, dict):
        if isinstance(key, (str, int)):
            if key in data:
                yield from selectorspaths(data[key], rest, current_path + [key])
        else:
            raise TypeError(f"Dict selector must be str/int, got {type(key)}")
    elif isinstance(data, list):
        if callable(key):
            for idx, item in enumerate(data):
                try:
                    if key(item):
                        yield from selectorspaths(item, rest, current_path + [idx])
                except Exception:
                    continue
        elif key == '*':  # Allow string wildcard for convenience
            for idx, item in enumerate(data):
                yield from selectorspaths(item, rest, current_path + [idx])
        elif isinstance(key, int):
            if 0 <= key < len(data):
                yield from selectorspaths(data[key], rest, current_path + [key])
        else:
            raise TypeError(f"List selector must be int or callable, got {type(key)}")
    else:
        # End of path, but not traversable
        return


# --- Helper functions ---


# --- getpath with selector support ---

def getpath(
    data: Any,
    path: Union[str, List[Union[str, int, Callable]]],
    default: Any = None,
    separator: str = '.',
    set_only_first_path_match: bool = False
) -> Any:
    """
    jq-style getpath: Get a value from a nested data structure (dict/list) by path, supporting selectors/callables.

    Args:
        data: The nested data structure (dict/list)
        path: Path to the target. Can be:
            - String with custom separator: "user.profile.name" or "user/profile/name"
            - List of keys/indices/selectors: ["user", select_eq("id", 2), "balance"]
            - Mixed: ["user", 0, "profile", "name"] for list indices
            - For list indices, both strings and integers are accepted; string indices are automatically converted to int when accessing lists.
            - jq-style selectors for lists:
                * Callable selector: select_eq, select_contains, select_all, etc.
                * Dict selector: {"field": value} (for backward compatibility)
                * String selector: "field=value" (for backward compatibility)
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
        getpath(data, ['wallets', select_eq('id', 2), 'balance'])
        getpath(data, ['wallets', select_all, 'balance'])
    """
    if isinstance(path, str):
        path = path.split(separator)
    if not path:
        return data
    # If no selector/callable in path, use original logic
    if not any(callable(p) for p in path):
        current = data
        try:
            for key in path:
                if isinstance(current, dict):
                    current = current[key]
                elif isinstance(current, list):
                    idx = int(key)
                    if idx < 0:
                        idx = len(current) + idx
                    current = current[idx]
                else:
                    return default
            return current
        except (KeyError, IndexError, TypeError, ValueError):
            return default
    # If selector/callable in path, use selectorspaths to find all matches
    matches = []
    for match_path in selectorspaths(data, path):
        # Traverse to the value at match_path
        current = data
        try:
            for k in match_path:
                if isinstance(current, dict):
                    current = current[k]
                elif isinstance(current, list):
                    current = current[k]
                else:
                    raise KeyError
            matches.append(current)
            if set_only_first_path_match:
                break
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    if not matches:
        return default
    if set_only_first_path_match:
        return matches[0]
    return matches
# --- Internal: apply operation ---
def _apply_op(current, target_key, value, operation, create_missing):
    if isinstance(current, list):
        idx = int(target_key)
        if operation == 'set':
            if idx >= len(current):
                if create_missing:
                    current.extend([None] * (idx - len(current) + 1))
                else:
                    raise IndexError(f"List index {idx} out of range")
            current[idx] = value
        elif operation == 'delete':
            if idx < len(current):
                del current[idx]
            else:
                raise IndexError(f"List index {idx} out of range")
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

# batch getpaths

def getpaths(data: Any, selector_paths: List[List[Union[str, int, Callable]]], default: Any = None, set_only_first_path_match: bool = False) -> List[Any]:
    """
    Batch getpath: Retrieve values for all selector paths using the new selector/callable logic.

    Args:
        data: The nested data structure (dict/list)
        selector_paths: List of selector paths (each a list of keys/indices/callables)
        default: Value to return if a path doesn't exist
        set_only_first_path_match: If True, only the first match per path is returned (default False: all matches)

    Returns:
        List of values, one per selector path (each value is a list of matches or a single value if set_only_first_path_match)

    Example:
        getpaths(data, [["wallets", select_all, "balance"]])
    """
    return [getpath(data, path, default=default, set_only_first_path_match=set_only_first_path_match) for path in selector_paths]

# --- setpath using selectorspaths ---

def setpath(
    data: Dict[str, Any],
    path: Union[str, List[Union[str, int]]],
    value: Any = None,
    operation: str = 'set',
    create_missing: bool = True,
    set_only_first_path_match: bool = False
) -> Dict[str, Any]:
    """
    jq-style setpath: Add, update, append, extend, or delete values in nested data structures (dicts/lists).

    Args:
        data: The nested data structure to modify
        path: The path to the target element (dot-separated string or list of keys/indices)
        value: The value to set (for 'set' operation) or iterable (for 'append'/'extend' operations)
        operation: The operation to perform - 'set', 'delete', 'append', 'extend'
        create_missing: If True, create missing keys/indices in the path
        set_only_first_path_match: If True, only the first matching path will be set/modified. If False (default), all matching paths will be set/modified.

    Returns:
        The modified data structure

    Raises:
        KeyError, IndexError, TypeError, ValueError

    Examples:
        setpath(data, 'a.b.c', 42)  # Set value
        setpath(data, 'a.b.c', operation='delete')  # Delete key
        setpath(data, 'a.b.c', [1, 2, 3], operation='set')  # Set list value
        setpath(data, 'a.b.c', 4, operation='append')  # Append to list
        setpath(data, 'a.b.c', [5, 6], operation='extend')  # Extend list
        setpath(data, ['wallets', select_eq('id', 2), 'balance'], 99, set_only_first_path_match=True)  # Only first match
    """

    if isinstance(path, str):
        path = path.split('.')
    valid_ops = {'set', 'delete', 'append', 'extend'}
    if operation not in valid_ops:
        raise ValueError(f"Operation must be one of: {valid_ops}")
    if not path:
        if operation == 'set':
            return value
        else:
            raise ValueError("Cannot delete or append to root")
    # Find all matching parent paths and keys, and apply operation
    parent_paths_iter = selectorspaths(data, path[:-1])
    target_key = path[-1]
    did_first = False
    for parent_path in parent_paths_iter:
        if set_only_first_path_match and did_first:
            break
        # Traverse to parent
        current = data
        for k in parent_path:
            if isinstance(current, dict):
                if k not in current:
                    if create_missing:
                        current[k] = {}
                    else:
                        raise KeyError(f"Key '{k}' not found")
                current = current[k]
            elif isinstance(current, list):
                if not (0 <= k < len(current)):
                    if create_missing:
                        current.extend([{}] * (k - len(current) + 1))
                    else:
                        raise IndexError(f"List index {k} out of range")
                current = current[k]
            else:
                raise TypeError(f"Cannot navigate through {type(current).__name__}")
        # Now current is the parent, target_key is the final key/index/selector
        _apply_op(current, target_key, value, operation, create_missing)
        did_first = True
    return data


def findpaths(data: Dict[str, Any], 
             pattern: str, 
             match_type: str = 'exact', 
             case_sensitive: bool = True, 
             include_values: bool = False, 
             max_depth: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Search for attributes/keys in a nested data structure and return their paths (jq-style findpaths).

    This function is best used for *discovery* and *reporting*:
    - Finds all keys (and optionally values) matching a pattern, anywhere in the structure, regardless of path.
    - Supports pattern-based search (exact, contains, startswith, endswith, regex) for both keys and values.
    - Returns all matches with metadata: path, key, value, parent type, and match type (key or value).
    - Useful when you do not know the structure in advance, or want to audit all occurrences of a key/value.

    This is different from selectors (used with selectorspaths/setpath), which are for traversing or modifying
    specific (possibly dynamic) paths, and require you to specify the path structure or selection logic at each step.

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

# Simple test/demo
if __name__ == "__main__":
    # --- getpath tests ---
    print("\ngetpath tests:")
    d3 = {"wallets": [
        {"id": 1, "balance": 10, "tags": ["a", "b"]},
        {"id": 2, "balance": 20, "tags": ["b", "c"]},
        {"id": 3, "balance": 30, "tags": ["c", "d"]}
    ]}
    # Direct key
    print(getpath(d3, ["wallets", 1, "balance"]))  # 20
    # Callable selector
    print(getpath(d3, ["wallets", select_eq("id", 2), "balance"]))  # 20
    # select_all returns first match (should be id=1)
    print(getpath(d3, ["wallets", select_all, "balance"]))  # 10
    # select_contains
    print(getpath(d3, ["wallets", select_contains("tags", "d"), "balance"]))  # 30
    # Dict selector (legacy)
    print(getpath(d3, ["wallets", {"id": 3}, "balance"]))  # 30
    # String selector (legacy)
    print(getpath(d3, ["wallets", "id=1", "balance"]))  # 10
    # Negative index
    print(getpath(d3, ["wallets", -1, "balance"]))  # 30
    # Not found
    print(getpath(d3, ["wallets", select_eq("id", 99), "balance"]))  # None
    # Not found with default
    print(getpath(d3, ["wallets", select_eq("id", 99), "balance"], default="notfound"))  # notfound

    # --- set_only_first_path_match tests for getpath ---
    print("\ngetpath set_only_first_path_match tests:")
    # Multiple matches: get all balances
    all_balances = getpath(d3, ["wallets", select_all, "balance"])
    print("All balances:", all_balances)  # [10, 20, 30]
    # Only first match
    first_balance = getpath(d3, ["wallets", select_all, "balance"], set_only_first_path_match=True)
    print("First balance (set_only_first_path_match=True):", first_balance)  # 10
    # Multiple matches: get all tags containing 'b'
    all_b_tags = getpath(d3, ["wallets", select_contains("tags", "b"), "balance"])
    print("All balances with tag 'b':", all_b_tags)  # [10, 20]
    # Only first match for tag 'b'
    first_b_tag = getpath(d3, ["wallets", select_contains("tags", "b"), "balance"], set_only_first_path_match=True)
    print("First balance with tag 'b' (set_only_first_path_match=True):", first_b_tag)  # 10
    # No matches: should return default
    no_match = getpath(d3, ["wallets", select_eq("id", 99), "balance"], set_only_first_path_match=True, default="notfound")
    print("No match (set_only_first_path_match=True):", no_match)  # notfound
    d = {"wallets": [{"id": 1, "balance": 10}, {"id": 2, "balance": 20}]}
    print("Initial:", d)
    setpath(d, ["wallets", select_eq("id", 1), "balance"], 99)
    print("After set id=1 balance to 99:", d)
    setpath(d, ["wallets", select_eq("id", 2), "balance"], 77)
    print("After set id=2 balance to 77:", d)
    setpath(d, ["wallets", select_all, "extra"], "foo")
    print("After set extra=foo for all wallets:", d)
    # Show all matching paths for a selector path
    print("All balance paths:", list(selectorspaths(d, ["wallets", select_all, "balance"])))

    # Test set_only_first_path_match: only first wallet's balance is set
    d2 = {"wallets": [
        {"id": 1, "balance": 10},
        {"id": 2, "balance": 20},
        {"id": 3, "balance": 30}
    ]}
    print("\nTest set_only_first_path_match:")
    print("Before:", d2)
    setpath(d2, ["wallets", select_all, "balance"], 123, set_only_first_path_match=True)
    print("After set_only_first_path_match=True:", d2)
    # Check that only the first wallet's balance is set
    assert d2["wallets"][0]["balance"] == 123
    assert d2["wallets"][1]["balance"] == 20
    assert d2["wallets"][2]["balance"] == 30
    print("set_only_first_path_match test passed.")

    # --- getpaths demo/tests ---
    print("\ngetpaths demo/tests:")
    d4 = {"wallets": [
        {"id": 1, "balance": 10, "tags": ["a", "b"]},
        {"id": 2, "balance": 20, "tags": ["b", "c"]},
        {"id": 3, "balance": 30, "tags": ["c", "d"]}
    ]}
    selector_paths = [
        ["wallets", select_eq("id", 1), "balance"],
        ["wallets", select_eq("id", 2), "balance"],
        ["wallets", select_contains("tags", "b"), "balance"],
        ["wallets", select_all, "balance"],
    ]
    print("getpaths all matches:", getpaths(d4, selector_paths))
    print("getpaths first match per path:", getpaths(d4, selector_paths, set_only_first_path_match=True))
    # Test with missing path
    selector_paths2 = [
        ["wallets", select_eq("id", 99), "balance"],
        ["wallets", select_eq("id", 1), "balance"]
    ]
    print("getpaths with missing path:", getpaths(d4, selector_paths2, default="notfound"))
    # Show that getpaths is equivalent to list comprehension
    sc_path = ["wallets", select_contains("tags", "b"), "balance"]
    print("getpaths single selector path:", getpaths(d4, [sc_path]))
    print("List comprehension equivalent:", [getpath(d4, p) for p in [sc_path]])
