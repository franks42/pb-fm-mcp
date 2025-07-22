# AWS Lambda + FastAPI + Mangum Async Issues Analysis

## Problem Summary

Getting "There is no current event loop in thread 'MainThread'" errors in REST API endpoints while MCP protocol works fine. This document analyzes the issue and provides solutions based on 2024/2025 best practices.

## Current Architecture

- **AWS Lambda** with Python 3.12 runtime
- **FastAPI** with Mangum adapter for ASGI-to-Lambda translation
- **Dual Protocol**: MCP (works) + REST API (failing)
- **MCP Uses**: `@async_to_sync_mcp_tool` decorator with `sync_wrapper()`
- **REST Uses**: Direct async functions through FastAPI integration

## Root Cause Analysis

### The Event Loop Problem

The error occurs because of conflicting async patterns between:

1. **MCP Handler**: Uses `async_wrapper.py` with `asyncio.run()` or `loop.run_until_complete()`
2. **FastAPI Integration**: Expects to run within an existing event loop context
3. **Lambda Environment**: Single-threaded, synchronous request handling

### Key Finding: Line 154-155 in `integrations.py`

```python
# Current problematic code:
if asyncio.iscoroutinefunction(function_meta.func):
    result = await function_meta.func(**kwargs)  # ❌ May not have event loop
else:
    loop = asyncio.get_event_loop()              # ❌ Deprecated in Python 3.12
    result = await loop.run_in_executor(None, lambda: function_meta.func(**kwargs))
```

### Why MCP Works But REST Fails

- **MCP**: `sync_wrapper()` handles event loop creation with `asyncio.run()` fallback
- **REST**: FastAPI integration assumes it's running within Mangum's ASGI event loop

## Solutions & Best Practices (2024/2025)

### Option 1: Fix Current Integration (Recommended)

Update `src/registry/integrations.py` lines 150-156:

```python
# Call the function with proper async handling
if asyncio.iscoroutinefunction(function_meta.func):
    # Check if we're already in an event loop
    try:
        # Try to get the running loop (Python 3.7+)
        loop = asyncio.get_running_loop()
        result = await function_meta.func(**kwargs)
    except RuntimeError:
        # No running loop - create one (fallback for edge cases)
        result = asyncio.run(function_meta.func(**kwargs))
else:
    # Sync function - use thread executor if in async context
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: function_meta.func(**kwargs))
    except RuntimeError:
        # No event loop - call directly
        result = function_meta.func(**kwargs)
```

### Option 2: Unified Async Wrapper

Apply the same `sync_wrapper` pattern used for MCP to REST functions:

```python
from async_wrapper import sync_wrapper

# In integrations.py route handler:
# Instead of direct async calls, use sync_wrapper
wrapped_func = sync_wrapper(function_meta.func)
result = wrapped_func(**kwargs)  # Always sync call
```

### Option 3: Use `run_in_executor` Pattern

For Lambda + FastAPI, always use thread executor for async functions:

```python
# Always use executor pattern for consistency
if asyncio.iscoroutinefunction(function_meta.func):
    import functools
    loop = asyncio.get_running_loop()
    partial_func = functools.partial(
        asyncio.run, 
        function_meta.func(**kwargs)
    )
    result = await loop.run_in_executor(None, partial_func)
else:
    result = function_meta.func(**kwargs)
```

## AWS Lambda + Async Best Practices (2024/2025)

### Event Loop Management

1. **Prefer `asyncio.get_running_loop()`** over deprecated `asyncio.get_event_loop()`
2. **Use `asyncio.run()`** for creating new event loops in Lambda handlers
3. **Handle RuntimeError** when no event loop exists
4. **Don't assume event loop persistence** between Lambda invocations

### Mangum Configuration

```python
# Recommended Mangum setup for Lambda
fastapi_handler = Mangum(
    fastapi_app, 
    lifespan="off"  # Avoid unnecessary overhead in Lambda
)
```

### FastAPI + Lambda Patterns

1. **CPU-bound tasks**: Use `loop.run_in_executor()` with ThreadPoolExecutor
2. **I/O-bound tasks**: Use async/await within existing event loop
3. **Mixed workloads**: Detect function type and handle appropriately

### Performance Considerations

- **Lambda Execution Model**: One request per container, limited async concurrency benefits
- **Mangum Overhead**: Minimal, just restructures event dictionaries
- **Thread Pool**: Use for blocking operations to prevent worker thread blocking

## Recommended Solution

**Option 1** is recommended because it:

1. ✅ Handles both `get_running_loop()` and fallback scenarios
2. ✅ Works with Mangum's ASGI event loop when present
3. ✅ Maintains compatibility with current MCP implementation
4. ✅ Follows 2024/2025 asyncio best practices
5. ✅ Minimal code changes required

## Implementation Steps

1. **Update** `src/registry/integrations.py` lines 150-156 with Option 1 code
2. **Test** REST endpoints locally with `sam local start-api`
3. **Verify** MCP functionality still works
4. **Deploy** to development environment
5. **Run** equivalence testing to ensure identical results

## Alternative Architectures

### If Problems Persist

Consider separating MCP and REST into different Lambda functions:

- **MCP Lambda**: Pure MCP protocol with current async_wrapper pattern
- **REST Lambda**: Pure FastAPI with standard async patterns
- **Shared Layer**: Common business logic in Lambda Layer

This would eliminate the async pattern conflicts but increase infrastructure complexity.

## Debugging Tools

```python
# Add to route handler for debugging
import asyncio
print(f"Event loop running: {asyncio._get_running_loop() is not None}")
print(f"Thread: {threading.current_thread().name}")
print(f"Event loop: {asyncio.get_event_loop()}")
```

## References

- [FastAPI Async Guide](https://fastapi.tiangolo.com/async/)
- [AWS Lambda Python Asyncio Best Practices](https://aws.amazon.com/blogs/compute/parallel-processing-in-python-with-aws-lambda/)
- [Mangum Documentation](https://mangum.io/)
- [Python 3.12 Asyncio Changes](https://docs.python.org/3/library/asyncio-eventloop.html)