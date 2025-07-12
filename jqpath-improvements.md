# jqpath.py Improvement Suggestions

## Performance Optimizations

### 1. Caching & Memoization
[X] Removed caching due to Cloudflare Workers incompatibility
- Cache compiled selectors to avoid recomputation
- Memoize path normalization results for repeated queries

**Implementation**:
```python
# Removed functools.lru_cache due to Cloudflare Workers incompatibility
# def _cached_normalize_path(path_str: str, separator: str = '.') -> tuple:
#     return tuple(_normalize_path(path_str, separator))
```

### 2. Early Termination
[X] Implemented max_results parameter
[X] Added depth-first traversal for negative indices

**Implementation**:
```python
def _find_selector_paths(obj, selectors, path_so_far=None, only_first=False, max_results=None):
    if max_results and results_count >= max_results:
        return
```

### 3. Memory Efficiency
[X] Improved path traversal with generators
[X] Optimized list operations for negative indices

**Implementation**:
```python
def _find_selector_paths_generator(obj, selectors, path_so_far=None):
    # Use yield instead of building full lists
    if not selectors:
        yield tuple(path_so_far) if path_so_far else ()
        return
```

## Error Handling & Validation

### 4. Input Validation
[X] Added negative index validation
[X] Improved path normalization

**Implementation**:
```python
def _validate_path(path) -> None:
    if not path:
        raise ValueError("Path cannot be empty")
    if isinstance(path, str) and path.startswith('.'):
        raise ValueError("Path cannot start with separator")
```

### 5. Better Error Messages
[X] Added context to index errors
[X] Improved error handling for missing paths

**Implementation**:
```python
class PathNotFoundError(KeyError):
    def __init__(self, path, context=""):
        super().__init__(f"Path {path} not found{context}")
        self.path = path
```

### 6. Graceful Degradation
[X] Implemented fallback paths in getpath
[X] Added support for negative array indices

**Implementation**:
```python
def safe_getpath(obj, path, fallback_strategies=None):
    strategies = fallback_strategies or ['exact', 'case_insensitive', 'partial_match']
    for strategy in strategies:
        try:
            return getpath_with_strategy(obj, path, strategy)
        except Exception:
            continue
    return None
```

## Recent Changes Summary
- Fixed negative array index handling
- Removed caching for Cloudflare Workers compatibility
- Added better error handling and fallback paths
- Improved path normalization
- All tests passing including negative index tests

## Remaining Items

## Code Organization

### 7. Split Into Modules
Break down the monolithic file into focused modules:
- `selectors.py` - Selector logic and matching
- `operations.py` - Core path operations (get, set, delete)
- `search.py` - Search and find functions
- `utils.py` - Flatten, merge, helper functions
- `cli.py` - Command-line interface

### 8. Reduce Function Complexity
**Location**: `src/jqpath.py:240-376` (_setpath function - 136 lines)
- Extract helper functions for different container types
- Separate operation-specific logic

**Implementation**:
```python
def _setpath_dict(current, key, value, operation):
    if operation == 'set':
        current[key] = value
    elif operation == 'delete':
        current.pop(key, None)
    # ... other operations

def _setpath_list(current, idx, value, operation):
    # List-specific logic
```

## Type Safety & Documentation

### 9. Stricter Types
**Implementation**:
```python
from typing import Protocol, TypeVar, Generic, Union

class PathSelector(Protocol):
    def __call__(self, key: Any, value: Any, path: list[Any]) -> bool: ...

T = TypeVar('T')
PathInput = Union[str, list[Union[str, int, PathSelector]]]

class PathResult(Generic[T]):
    value: T
    path: list[Any]
    success: bool
```

### 10. Comprehensive Docstrings
- Add examples for complex selector syntax
- Document performance characteristics
- Include migration guide from basic to advanced usage

**Example**:
```python
def getpath(obj, path, default=None, separator='.', only_first_path_match=False):
    """Get value at path in nested structure with advanced selector support.
    
    Args:
        obj: The object to query
        path: Path string ('user.name') or list (['user', 'name'])
        default: Value to return if path not found
        separator: Path separator character (default: '.')
        only_first_path_match: Stop at first match for selector paths
    
    Returns:
        Value at path or default if not found
    
    Examples:
        >>> getpath({'user': {'name': 'John'}}, 'user.name')
        'John'
        
        >>> getpath([{'id': 1}, {'id': 2}], [{'id': 2}])
        {'id': 2}
    
    Performance:
        O(n*m) where n=object size, m=path depth
        Consider caching for repeated queries on same object
    """
```

## API Consistency

### 11. Standardize Parameters
- Consistent `separator` parameter across all functions
- Uniform error handling strategies
- Standard return types (consider `Optional` vs exceptions)

**Implementation**:
```python
# Consistent parameter ordering
def operation(obj, path, *, separator='.', create_missing=False, **kwargs):
    pass
```

### 12. Backwards Compatibility
**Implementation**:
```python
def getpath_v2(obj, path, *, default=None, create_missing=False, strict_types=True):
    """New API with keyword-only arguments for clarity"""
    pass

# Keep old API for compatibility
def getpath(obj, path, default=None, separator='.', only_first_path_match=False):
    """Legacy API - use getpath_v2 for new code"""
    return getpath_v2(obj, path, default=default)
```

## Testing & Reliability

### 13. Property-Based Testing
**Implementation**:
```python
from hypothesis import given, strategies as st

@given(st.recursive(st.dictionaries(st.text(), st.integers()) | st.lists(st.integers())))
def test_roundtrip_property(data):
    """Test that set -> get returns the same value"""
    if not data:
        return
    
    path = ['test_key']
    value = 42
    
    modified = setpath(data.copy(), path, value)
    retrieved = getpath(modified, path)
    assert retrieved == value
```

### 14. Benchmark Suite
**Implementation**:
```python
import time
import json

def benchmark_getpath():
    # Large nested structure
    data = json.loads('...')  # 1MB+ JSON
    
    start = time.perf_counter()
    for _ in range(1000):
        getpath(data, 'deeply.nested.path')
    end = time.perf_counter()
    
    print(f"getpath: {(end-start)*1000:.2f}ms for 1000 operations")
```

### 15. Fuzzing
**Implementation**:
```python
import string
import random

def fuzz_test_paths():
    """Generate random paths and ensure no crashes"""
    for _ in range(10000):
        path_parts = []
        for _ in range(random.randint(1, 10)):
            if random.choice([True, False]):
                path_parts.append(''.join(random.choices(string.ascii_letters, k=5)))
            else:
                path_parts.append(random.randint(0, 100))
        
        try:
            getpath({'test': [1, 2, {'nested': 'value'}]}, path_parts)
        except Exception as e:
            # Should only raise expected exceptions
            assert isinstance(e, (KeyError, IndexError, TypeError))
```

## Priority Implementation Order

### High Priority
1. **Performance caching** - Immediate impact on repeated operations
2. **Input validation** - Prevents runtime errors
3. **Better error messages** - Improves debugging experience

### Medium Priority
4. **Function splitting** - Improves maintainability
5. **Module reorganization** - Better code structure
6. **Type safety improvements** - Catches bugs early

### Low Priority
7. **Comprehensive testing** - Long-term reliability
8. **API v2 design** - Future-proofing
9. **Documentation overhaul** - User experience

## Implementation Notes

- Maintain 100% backwards compatibility during improvements
- Add deprecation warnings for old patterns before removing them
- Include migration scripts for major API changes
- Performance improvements should not sacrifice code clarity
- All changes should include comprehensive tests

## Estimated Impact

- **Performance**: 2-5x improvement for repeated operations
- **Maintainability**: Significant reduction in bug reports
- **Developer Experience**: Faster debugging and development
- **Reliability**: Fewer runtime errors in production