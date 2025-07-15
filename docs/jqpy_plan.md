# jqpy Implementation Plan

## Overview
This document outlines the plan to create `jqpy`, a new implementation of jq-like functionality in Python that improves upon the existing `jqpath.py` implementation. The goal is to create a more robust, jq-compatible path handling system.

## Goals
1. Create a clean, well-tested implementation of jq's path handling
2. Maintain backward compatibility where possible
3. Improve handling of special characters in keys
4. Add better support for jq's path expressions
5. Create comprehensive test coverage

## File Structure
```
src/
  jqpy/           # New package
    __init__.py   # Package initialization
    parser.py     # Path parser implementation
    path.py       # Path handling
    selectors.py  # Selector implementations
    utils.py      # Utility functions
  jqpath.py       # Existing implementation (will be deprecated)
tests/
  test_jqpy/      # Tests for the new implementation
    __init__.py
    test_parser.py
    test_path.py
    test_selectors.py
  test_jqpath.py  # Existing tests
docs/
  jqpy_plan.md    # This document
  jq_reference.md # jq reference for path expressions
```

## Implementation Phases

### Phase 1: Core Path Parsing
1. **Path Parser** (`jqpy/parser.py`)
   - Lexer for jq path expressions
   - Parser for path components
   - Support for:
     - Dot notation: `.a.b.c`
     - Bracket notation: `.["a"]["b"]["c"]`
     - Array indices: `.[0]`, `.[-1]`
     - String literals with special characters

2. **Basic Path Handling** (`jqpy/path.py`)
   - `Path` class to represent parsed paths
   - `get`/`set`/`delete` operations
   - Path resolution logic

### Phase 2: Advanced Features
1. **Selectors** (`jqpy/selectors.py`)
   - Basic selectors: `.[]`, `.[]?`
   - Index/string filters
   - Array slicing
   - Comma operator

2. **Extended Path Operations**
   - Path manipulation utilities
   - Path composition
   - Relative path resolution

### Phase 3: jq Compatibility
1. **jq Functions**
   - Core jq functions
   - Path-related functions
   - String/number operations

2. **Performance & Polish**
   - Optimizations
   - Benchmarks
   - Documentation

## Testing Strategy
1. Unit tests for each component
2. Property-based tests
3. Compatibility tests
4. Performance benchmarks

## Progress Tracking
- [x] Phase 1: Core Path Parsing
  - [x] Path Parser
    - [x] Dot notation: `.a.b.c`
    - [x] Bracket notation: `.["a"]["b"]["c"]`
    - [x] Array indices: `.[0]`, `.[-1]`
    - [x] String literals with special characters
    - [x] Escaped characters in keys
    - [x] Proper handling of `raw_value` for all components
  - [x] Basic Path Resolution
    - [x] `get_path()` function
    - [x] `has_path()` function
    - [x] `set_path()` function (basic implementation)
    - [ ] `delete_path()` function
    - [x] Comprehensive test coverage for all path operations
- [ ] Phase 2: Advanced Features
  - [ ] Selectors
    - [x] Basic selector `[]`
    - [ ] Optional selector `[]?`
    - [ ] Array slicing
  - [ ] Path Construction
- [ ] Phase 3: jq Compatibility
  - [ ] jq Functions
  - [ ] Performance Optimization

## Current Snapshot (2024-07-14)
- Basic path parsing and resolution implemented
- Core functionality tested and working
- Good test coverage for path parsing
- Basic selector support with `[]`

### Next Steps
1. Implement `set_path()` and `delete_path()` functions
2. Add more test cases for edge cases
3. Implement optional selector `[]?`
4. Add array slicing support
5. Document the API with more examples

## Getting Started
1. Review `test_jqpath.py` for expected behavior
2. Start with `test_jqpy/test_parser.py`
3. Follow test-driven development

## Next Steps
1. Create the directory structure
2. Add initial test cases
3. Implement the basic parser

## Open Questions
- Should we maintain 100% backward compatibility with jqpath?
- What's the deprecation plan for jqpath?
- Should we support both string and list paths?

## References
- [jq Manual](https://stedolan.github.io/jq/manual/)
- [jq Path Expressions](https://stedolan.github.io/jq/manual/#Basicfilters)
