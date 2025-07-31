# MVP Implementation Todo List

## Phase 1: Infrastructure Setup

### 1.1 NEW AWS Resources Setup (Separate from Existing)
- [ ] **Create NEW S3 Bucket**
  - Bucket name: `pb-fm-webpage-mvp-assets` (new, separate bucket)
  - Region: `us-west-1` (match existing Lambda)
  - CORS configuration for browser access
  - Folder structure: `layouts/`, `components/`, `datasets/`, `sessions/`

- [ ] **Create NEW DynamoDB Tables**
  - **WebpageSessions Table** (new): 
    - Table name: `pb-fm-webpage-sessions`
    - PK: `SESSION#{session-id}`, SK: `METADATA` | `CLIENT#{client-id}` | `EVENT#{sequence}`
    - Global table to handle all session data in one table
  - **Keep existing DynamoDB tables untouched**

- [ ] **NEW SQS Queue Naming Convention**
  - Browser queues: `pb-fm-webpage-session-{session-id}-browser-{client-id}`
  - History queues: `pb-fm-webpage-session-{session-id}-browser-{client-id}-history`
  - Prefix `pb-fm-webpage-` to distinguish from existing SQS queues

### 1.2 Update Lambda Infrastructure (Additive Only)
- [ ] **Update CloudFormation Template (ADD ONLY)**
  - Add NEW S3 bucket resource: `pb-fm-webpage-mvp-assets`
  - Add NEW DynamoDB table: `pb-fm-webpage-sessions`
  - Add SQS permissions for new queue naming pattern
  - Add S3 permissions for new bucket only
  - **Leave all existing resources unchanged**

- [ ] **Deploy Infrastructure (Safe)**
  - Run: `./deploy.sh dev --clean --test`
  - Verify new resources created successfully
  - Verify existing functionality still works (run existing tests)

## Phase 2: Session Management API

### 2.1 NEW Session Functions (Separate Namespace)
- [ ] **Create `src/functions/webpage_session_management.py` (NEW FILE)**
  ```python
  # NEW functions with webpage_ prefix to avoid conflicts
  @api_function(protocols=["mcp", "rest"])
  async def webpage_create_session(session_id: str) -> dict
  
  @api_function(protocols=["rest"])
  async def webpage_join_session(session_id: str, client_id: str) -> dict
  
  @api_function(protocols=["rest"])
  async def webpage_get_session_status(session_id: str) -> dict
  ```

### 2.2 NEW Queue Management Functions
- [ ] **Create `src/functions/webpage_queue_management.py` (NEW FILE)**
  ```python
  # NEW functions with webpage_ prefix and new queue naming
  @api_function(protocols=["mcp"])
  async def webpage_create_browser_queues(session_id: str, client_id: str) -> dict
  
  @api_function(protocols=["rest"])
  async def webpage_poll_queue(queue_url: str, wait_time: int) -> dict
  
  @api_function(protocols=["rest"]) 
  async def webpage_delete_message(queue_url: str, receipt_handle: str) -> dict
  ```

### 2.3 Browser Registration
- [ ] **Create session registration endpoint**
  - Handle client cookie assignment
  - Determine master vs observer role
  - Create dual queues (history + live)
  - Return queue URLs and role information

## Phase 3: Frontend Development

### 3.1 Static Website Structure
- [ ] **Create `static/` directory**
- [ ] **Create `static/index.html`**
  - Basic HTML structure with price display
  - Session routing via URL path
  - Role indicator display

- [ ] **Create `static/js/session.js`**
  ```javascript
  class SessionManager {
    constructor(sessionId) 
    async connect()
    async pollQueue()
    async fetchFromS3(s3Ref)
    handleMessage(message)
  }
  ```

- [ ] **Create `static/css/style.css`**
  - Basic styling for price display
  - Role indicators (master/observer badges)
  - Loading states

### 3.2 Queue Polling Implementation
- [ ] **Implement dual-queue processor**
  ```javascript
  class DualQueueProcessor {
    async processHistoryQueue()
    async processLiveQueue() 
    handlePriceUpdate(data)
  }
  ```

- [ ] **Add S3 content fetching**
  - CORS-enabled S3 bucket access
  - JSON parsing and error handling
  - Cache management for repeated requests

## Phase 4: AI Integration

### 4.1 NEW MCP Functions (Webpage-Specific)
- [ ] **Create `src/functions/webpage_orchestration.py` (NEW FILE)**
  ```python
  # NEW functions with webpage_ prefix to avoid conflicts with existing MCP functions
  @api_function(protocols=["mcp"])
  async def webpage_update_hash_price_display(session_id: str) -> dict
  
  @api_function(protocols=["mcp"])
  async def webpage_send_to_browsers(message: dict, session_id: str) -> dict
  
  @api_function(protocols=["mcp"])
  async def webpage_get_session_participants(session_id: str) -> dict
  
  @api_function(protocols=["mcp"]) 
  async def webpage_transfer_control_to_observer(session_id: str, target_observer: str) -> dict
  ```

### 4.2 Message Fan-Out System
- [ ] **Implement SQS fan-out logic**
  - Get list of active browser queues
  - Send identical message to all queues
  - Handle queue failures gracefully

- [ ] **Add DynamoDB event storage**
  - Sequential numbering with atomic increment
  - Event metadata and S3 references
  - TTL for automatic cleanup

### 4.3 NEW S3 Content Management
- [ ] **Create `src/functions/webpage_s3_helpers.py` (NEW FILE)**
  ```python
  # NEW S3 functions using the new bucket only
  WEBPAGE_BUCKET = "pb-fm-webpage-mvp-assets"  # New bucket only
  
  async def webpage_store_price_data(session_id: str, price_data: dict) -> dict
  async def webpage_store_layout_data(session_id: str, layout: dict) -> dict
  def webpage_generate_s3_key(session_id: str, content_type: str) -> str
  ```

## Phase 5: Multi-Browser Features

### 5.1 Browser Onboarding
- [ ] **Implement dual-queue setup**
  - Create history queue with past events
  - Add live queue to immediate fan-out
  - Send END_OF_HISTORY marker

- [ ] **Add event replay system**  
  - Fetch events from DynamoDB by sequence
  - Copy to history queue in order
  - Handle large event batches

### 5.2 NEW Session Lifecycle Management
- [ ] **Add heartbeat monitoring (webpage-specific)**
  ```python
  @api_function(protocols=["rest"])
  async def webpage_send_heartbeat(session_id: str, client_id: str) -> dict
  
  async def webpage_check_master_health(session_id: str) -> dict
  async def webpage_handle_master_disconnect(session_id: str) -> dict
  ```

- [ ] **Implement session cleanup**
  - Delete unused queues
  - Archive session data
  - Notify remaining participants

## Phase 6: Testing & Validation

### 6.1 Unit Tests
- [ ] **Test session management functions**
- [ ] **Test queue operations**
- [ ] **Test S3 content storage/retrieval**
- [ ] **Test message fan-out logic**

### 6.2 Integration Tests
- [ ] **Single browser test**
  - Price display functionality
  - Queue polling and S3 fetching
  - Role assignment

- [ ] **Multi-browser test**
  - Simultaneous price updates
  - Perfect synchronization
  - Message deduplication

- [ ] **Late joiner test**
  - History replay functionality
  - Dual-queue processing
  - Event ordering

### 6.3 Test Scenarios
- [ ] **Create test script**
  ```bash
  # Test 1: Basic functionality
  TEST_SESSION=mvp-test-1 uv run python scripts/test_mvp.py --single-browser
  
  # Test 2: Multi-browser sync
  TEST_SESSION=mvp-test-2 uv run python scripts/test_mvp.py --multi-browser
  
  # Test 3: Late joiner
  TEST_SESSION=mvp-test-3 uv run python scripts/test_mvp.py --late-joiner
  ```

## Phase 7: Deployment & Demo

### 7.1 Production Deployment
- [ ] **Deploy to dev environment**
  - `./deploy.sh dev --clean --test`
  - Verify all functions working

- [ ] **Create demo session**
  - Pre-configured session ID
  - Sample price data
  - Multi-browser demo setup

### 7.2 Documentation
- [ ] **Update README with MVP demo instructions**
- [ ] **Create user guide for testing**
- [ ] **Document API endpoints**

---

## Success Criteria

### Functional Requirements
- ✅ Single webpage displays HASH price
- ✅ AI updates price via MCP function call
- ✅ Multiple browsers show same price simultaneously
- ✅ New browsers see current price immediately
- ✅ Master/observer roles work correctly

### Technical Requirements  
- ✅ S3 reference pattern working
- ✅ SQS fan-out to multiple browsers
- ✅ DynamoDB event history and replay
- ✅ Dual-queue onboarding (no race conditions)
- ✅ One-message-at-a-time processing
- ✅ Cookie-based session management

### Performance Requirements
- ✅ Price updates appear within 2 seconds
- ✅ Browser registration completes within 5 seconds  
- ✅ History replay for late joiners under 10 seconds
- ✅ No message loss during browser onboarding

---

## Implementation Notes

### Code Organization (NEW Files Only)
```
src/functions/
├── webpage_session_management.py   # NEW: Webpage session CRUD 
├── webpage_queue_management.py     # NEW: Webpage-specific SQS ops
├── webpage_orchestration.py        # NEW: AI-facing webpage MCP functions
└── webpage_s3_helpers.py          # NEW: Webpage S3 storage helpers

static/                            # NEW: Static website directory
├── index.html                     # NEW: Main webpage
├── js/session.js                 # NEW: Browser session management
├── js/queue-processor.js         # NEW: Message processing
└── css/style.css                # NEW: Basic styling

scripts/
└── test_webpage_mvp.py           # NEW: Webpage MVP test script

# EXISTING FILES REMAIN UNCHANGED:
# - All existing src/functions/*.py files
# - All existing MCP functions 
# - All existing infrastructure
```

### Development Workflow (Safe Implementation)
1. **Phase 1-2**: Add new infrastructure, test existing functions still work
2. **Phase 3**: Create static website, test basic session creation  
3. **Phase 4**: Add new MCP functions, test AI integration in isolation
4. **Phase 5**: Add multi-browser features, test synchronization
5. **Validation**: Run existing test suite to ensure no regressions
6. **Integration**: Run new webpage MVP tests
7. **Deploy**: Safe deployment with rollback plan

### Safety Measures
- **Function Prefixes**: All new functions prefixed with `webpage_`
- **Resource Isolation**: New S3 bucket, DynamoDB table, SQS naming
- **Regression Testing**: Run existing tests after each phase
- **Incremental Deployment**: Deploy and test each phase separately
- **Rollback Plan**: Can disable new functions without affecting existing system

### Estimated Timeline
- **Week 1**: Phases 1-3 (Infrastructure + Frontend)
- **Week 2**: Phases 4-5 (AI + Multi-browser)
- **Week 3**: Phase 6-7 (Testing + Deployment)

**Total: 2-3 weeks for complete MVP implementation**