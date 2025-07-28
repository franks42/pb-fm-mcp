# Traffic Light Architecture Summary: Real-time User Input Processing

## Overview

This document summarizes the converged architectural solutions for enabling real-time user input processing in our MCP + REST API system. The core innovation is the "Traffic Light Pattern" that eliminates polling delays and enables sub-second response times.

## Core Innovation: Traffic Light Pattern

### The Pattern
```python
# Elegant async waiting without polling
await asyncio.wait_for(
    wake_up_signals[session_id].wait(),
    timeout=timeout_seconds
)
```

### How It Works
- **🔴 Red Light**: AI waits efficiently without CPU burn
- **🟢 Green Light**: User input triggers immediate wake-up (traffic light turns green)
- **⏱️ Timeout**: Graceful fallback after timeout period (5-10 seconds)
- **🔄 Reset**: AI resumes waiting after processing input

### Benefits
- ✅ **Sub-second response**: ~300ms instead of 5-10 seconds
- ✅ **No CPU waste**: True async waiting, no polling loops
- ✅ **Interruptible**: User can always interrupt AI within timeout window
- ✅ **Reliable fallback**: Works even if wake-up signal fails

## Architectural Options

### Option A: Dual-Path Architecture (Current Working)

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (v1)                          │
├─────────────────────────────────────────────────────────────┤
│  /mcp endpoint          │  /api/*, /docs, /health endpoints │
└──────────┬──────────────┴─────────────┬─────────────────────┘
           │                            │
           ▼                            ▼
┌──────────────────────────┐  ┌────────────────────────────────┐
│   McpFunction Lambda     │  │   RestApiFunction Lambda       │
│ ━━━━━━━━━━━━━━━━━━━━━━━ │  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ • Direct AWS MCP Handler │  │ • FastAPI + Web Adapter        │
│ • lambda_handler.py      │  │ • web_app_unified.py           │
│ • Traffic light waiting  │  │ • HTTP poke for wake-up        │
│ • DynamoDB persistence   │  │ • User input handling          │
└──────────────────────────┘  └────────────────────────────────┘
```

**Communication**: Simple HTTP call between Lambda functions to turn traffic light green.

### Option B: Unified Process (To Test)

```
┌─────────────────────────────────────────────────────────────┐
│                Single Lambda + Web Adapter                   │
├─────────────────────────────────────────────────────────────┤
│ • FastAPI handles both /mcp and /api/* routes               │
│ • MCP JSON-RPC as FastAPI POST endpoint                     │
│ • Shared in-memory queues for traffic light pattern        │
│ • Real-time user input processing                           │
│ • No cross-Lambda HTTP calls needed                         │
└─────────────────────────────────────────────────────────────┘
```

**Communication**: Direct function call within same process to turn traffic light green.

## User Input Flow (Both Options)

```
Timeline: User Types Wallet Address

0.0s: User types wallet address in form field
0.1s: Browser detects change, POSTs to /api/user-input/{session_id}
0.1s: API stores input in queue (DynamoDB OR in-memory)
0.2s: API pokes MCP side (HTTP call OR function call)
0.2s: MCP traffic light turns green (wake_up_signals[session_id].set())
0.3s: AI immediately processes wallet data
2.0s: AI finishes analysis, updates S3 dashboard layout
2.1s: Browser polls coordination endpoint, gets new layout
2.2s: Browser instantly loads new wallet-specific dashboard from S3

Total Response Time: ~2 seconds (vs 5-10 seconds with polling)
```

## Implementation Details

### Traffic Light Implementation
```python
# Global wake-up signals per session
wake_up_signals = {}  # session_id -> asyncio.Event

@api_function(protocols=["mcp"])
async def wait_for_user_input(session_id: str, timeout_seconds: int = 8) -> JSONType:
    # Create traffic light for this session
    wake_up_signals[session_id] = asyncio.Event()
    
    try:
        # Wait for green light OR timeout
        await asyncio.wait_for(
            wake_up_signals[session_id].wait(),
            timeout=timeout_seconds
        )
        
        # Green light! Check for actual message
        message = await get_user_input_from_queue(session_id)
        if message:
            return {"has_input": True, **message}
        
    except asyncio.TimeoutError:
        # Timeout reached - normal behavior
        pass
    finally:
        # Clean up traffic light
        wake_up_signals.pop(session_id, None)
    
    return {"has_input": False}

# Function to turn traffic light green
async def wake_up_session(session_id: str):
    """Turn the traffic light green for waiting AI"""
    if session_id in wake_up_signals:
        wake_up_signals[session_id].set()  # 🟢 GREEN LIGHT!
```

### Persistence Options

#### DynamoDB (Cross-Lambda Reliability)
```python
# Messages survive Lambda cold starts
await dynamodb.put_item({
    'PK': f'user_input#{session_id}',
    'SK': timestamp,
    'input_type': 'wallet_address',
    'input_value': 'pb1xyz...',
    'expires_at': timestamp + 3600  # 1 hour TTL
})
```

#### In-Memory (Real-time Performance)
```python
# Instant communication within single Lambda
session_queues: Dict[str, asyncio.Queue] = {}

await session_queues[session_id].put({
    'input_type': 'wallet_address',
    'input_value': 'pb1xyz...'
})
```

## Key Architectural Principles

### 1. Persistence Strategy
- **DynamoDB**: For cross-Lambda reliability and session persistence
- **In-Memory**: For real-time performance within single process
- **Hybrid**: DynamoDB backup with in-memory fast path

### 2. Real-time Responsiveness
- **Traffic Light Pattern**: Sub-second wake-up for waiting AI
- **No Polling**: Eliminates CPU waste and improves response time
- **Graceful Fallback**: Always works even if real-time signaling fails

### 3. User Experience
- **Form Changes**: Instant AI response to wallet address entry
- **Dashboard Updates**: S3 coordination for instant layout switching
- **Conversational Flow**: AI can be interrupted within 5-10 seconds max

### 4. Scalability
- **Session-Scoped**: Queues and signals are per-session
- **Lambda-Friendly**: Works within Lambda timeout constraints
- **Cost-Effective**: Pay only for actual processing time

## Comparison: Dual vs Single Process

| Aspect | Dual-Path | Single Process |
|--------|-----------|----------------|
| **Communication** | HTTP call between Lambdas | Direct function call |
| **Persistence** | DynamoDB required | In-memory sufficient |
| **Complexity** | Two deployments | One deployment |
| **Reliability** | Cross-cold-start survival | Session-scoped only |
| **Performance** | ~300ms wake-up | ~100ms wake-up |
| **Cost** | Two Lambda invocations | One Lambda invocation |
| **Development** | Current working state | Needs testing |

## Implementation Plan

### Phase 1: Test Single Lambda Approach
1. Create `single-lambda` branch from current `ui` branch
2. Implement unified FastAPI app with MCP JSON-RPC endpoint
3. Add in-memory traffic light pattern
4. Test MCP protocol compatibility with FastAPI + Web Adapter
5. Validate all existing functionality works

### Phase 2: Decision Point
- **If single Lambda works**: Merge back to `ui` branch, continue with unified approach
- **If single Lambda fails**: Keep `ui` branch with dual-path, implement HTTP traffic light pattern

### Phase 3: Production Enhancement
- Implement traffic light pattern in chosen architecture
- Add user input processing functions
- Deploy and test real-time dashboard interactions

## Success Metrics

### Technical Performance
- ✅ User input response time < 1 second
- ✅ AI can be interrupted within 8 seconds max
- ✅ No CPU waste from polling loops
- ✅ All existing MCP/REST functionality preserved

### User Experience
- ✅ Form changes trigger immediate AI analysis
- ✅ Dashboard updates reflect user input instantly
- ✅ Conversational flow feels natural and responsive

## Conclusion

The Traffic Light Pattern represents a breakthrough in MCP server responsiveness, eliminating the traditional polling delays that made real-time user interaction challenging. Whether implemented in dual-path or single-process architecture, this pattern enables the responsive, AI-driven dashboard experience we're building.

The key insight is that `asyncio.wait_for()` with event signals provides elegant, efficient waiting that can be interrupted instantly - turning the challenge of real-time MCP communication into a simple traffic light analogy that any developer can understand and implement.