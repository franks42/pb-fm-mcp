# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 IMPORTANT: Project Status Update (July 2025)

**This project has been MIGRATED from Cloudflare Workers to AWS Lambda due to Python compatibility issues.**

### Current State
- ✅ **Production**: AWS Lambda deployment working perfectly
- ✅ **Local Testing**: SAM local environment configured
- ✅ **Documentation**: Complete testing and deployment guides in `docs/`
- ✅ **Dual API Architecture**: MCP + REST APIs fully implemented and deployed

### Previous Issues with Cloudflare Workers
- Pyodide WebAssembly environment couldn't handle Rust-based extensions (pydantic v2, rpds, etc.)
- Multiple dependency conflicts and performance issues
- **Solution**: Migrated to AWS Lambda for full Python 3.12 compatibility

## Development Commands

### 🚨 CRITICAL: Function Naming Standards
**NEVER change existing function names without explicit user approval. This breaks integrations.**
- **Standard**: Use snake_case (e.g., `fetch_current_hash_statistics`)
- **Legacy**: Production may have camelCase (e.g., `fetchCurrentHashStatistics`) 
- **Rule**: Always ask before renaming ANY function - this is a breaking change

### 🚨 CRITICAL: Code Quality Standards

**File Recovery Policy:**
**NEVER restore, copy back, or checkout deleted files without explicit user permission. When files are deleted during cleanup, they stay deleted unless the user specifically asks to restore them.**

**Import Standards:**
**NO ugly optional import statements with try/except fallbacks. Use explicit imports only. If a module cannot be imported, it's a bug that needs to be fixed, not worked around.**

**Code Duplication:**
**NO duplication of code, functions, or type definitions across files. Maintain single source of truth. Import from shared modules instead of copying code.**

**Architecture Changes:**
**DO NOT make new architectural decisions or start coding in new directions without getting user confirmation. Always discuss and get approval before implementing architectural changes. DO NOT update technical plans or architectural decisions without explicit user instruction. Never assume migration paths or suggest alternative implementations unless specifically asked.**

### 🚨 CRITICAL: Current Architecture Issues & Analysis Failures

**LESSON LEARNED (July 2025): Partial Success ≠ Complete Success**

**What went wrong:**
- Claude incorrectly assessed mangum + FastAPI as "working correctly" based on partial endpoint testing
- Failed to recognize that asyncio event loop errors in `/docs` and `/openapi.json` endpoints indicate fundamental async handling problems
- Dismissed the documented AWS Lambda Web Adapter migration as "unnecessary" when it was the planned solution for these exact issues
- Wasted 2+ hours debugging import paths when the real problem was architectural

**Current Reality:**
- ✅ **MCP Protocol**: Works (simple request/response)
- ✅ **REST Function Endpoints**: Work (e.g., `/api/current_hash_statistics`) 
- ❌ **REST Documentation Endpoints**: Fail with "no current event loop" errors
- ❌ **Unified Deployment**: Only 70% functional due to mangum async limitations

**Root Cause:** mangum adapter has known async event loop issues with complex FastAPI operations. The solution exists: AWS Lambda Web Adapter + uvicorn migration documented in `docs/lambda-web-adapter-migration.md`.

**Prevention Directives:**
1. **Test ALL endpoints** before declaring success, not just basic function calls
2. **Read existing documentation** before dismissing architectural decisions
3. **Recognize error patterns** - "no current event loop" = async handling issue
4. **Validate claims** - if user questions your assessment, they're probably right

### 🚨 CRITICAL: Git Commit Policy

**Always commit new work immediately:**
**When creating new files or features, ALWAYS commit them to git along with related updates. When in doubt, ASK before proceeding. Git is not just version control - it's our backup system for all work.**

**Why this matters:**
- We lost `web_app.py` because it was created but never committed
- "Accidentally" deleting uncommitted work wastes time and effort
- Every new file should be in git before any major refactoring

**Rule:** If you create it, commit it. If you're unsure whether to commit, ASK.

### 🚨 CRITICAL: Test Wallet Address Security Policy

**NEVER save real wallet addresses in files or commit them to git:**
1. **Privacy Protection**: Real wallet addresses are private information and must not be stored in code
2. **Security Requirement**: Wallet addresses should NEVER be committed to git repositories 
3. **Environment Variable Usage**: Always use environment variables to pass wallet addresses to scripts
4. **Ask When Needed**: When testing requires a real wallet address, ASK the user to provide one
5. **No Hardcoding**: Never hardcode real wallet addresses in test files, scripts, or documentation

**Implementation Pattern:**
```bash
# ✅ CORRECT: Use environment variable
export TEST_WALLET_ADDRESS="provided_by_user"
uv run python scripts/mcp_test_client.py --wallet-env TEST_WALLET_ADDRESS

# ❌ WRONG: Never hardcode real addresses
test_wallet = "pb1real_wallet_address_here"  # NEVER DO THIS
```

**Claude Code Environment Variable Handling:**
Environment variables do NOT persist between Claude Code Bash tool calls. Each bash command runs in an isolated session. For testing with wallet addresses in Claude Code:

```bash
# ✅ CORRECT: Set environment variable per command
env TEST_WALLET_ADDRESS="wallet_address_here" curl "http://localhost:8080/api/fetch_account_info/$TEST_WALLET_ADDRESS"

# ✅ ALTERNATIVE: Chain commands with variable
WALLET="wallet_address_here" && curl "http://localhost:8080/api/fetch_account_info/$WALLET"

# ❌ WRONG: These don't work across separate bash calls
export TEST_WALLET_ADDRESS="..."  # Lost in next command
echo $TEST_WALLET_ADDRESS         # Empty in separate bash call
```

**Recommended User Workflow:**
1. User provides wallet address when invoking Claude Code
2. User can set `export TEST_WALLET_ADDRESS="..."` in their terminal before Claude Code
3. Claude Code uses `env TEST_WALLET_ADDRESS="..." command` pattern for testing
4. Never store wallet addresses in files, git, or persistent variables

**Policy**: Real wallet addresses are sensitive data that must be handled with the same security as API keys or passwords.

**Workflow Notes:**
- When api calls to the blockchain server give 404 errors, and the api needs a wallet address then ask for test wallet address 

### 📋 AWS Lambda Web Adapter Migration Status (July 2025)

**Current Situation:**
- Using mangum + FastAPI → causes async event loop errors on /docs and /openapi.json endpoints
- MCP protocol works, REST functions work, but REST docs/openapi fail with "no current event loop" 
- Solution exists: AWS Lambda Web Adapter + uvicorn (documented in `docs/lambda-web-adapter-migration.md`)

**Migration Progress:**
✅ `src/web_app.py` - FastAPI app for Web Adapter (recovered from docs)
✅ Migration guide - Complete in `docs/lambda-web-adapter-migration.md`
❌ `Dockerfile` - Needs to be created (template in migration guide)
❌ `template-container.yaml` - SAM template for container deployment (template in guide)
❌ Update `src/registry/integrations.py` - Simplify FastAPIIntegration for direct async
❌ Container build and deployment scripts
❌ Testing of Web Adapter deployment

**Key Files for Migration:**
- **Read first**: `docs/lambda-web-adapter-migration.md` (complete migration guide)
- **FastAPI app**: `src/web_app.py` (ready to use)
- **Current broken**: `lambda_handler.py` lines ~440-470 (docs endpoint with async issues)
- **Registry**: `src/registry/integrations.py` (needs simplification per guide)

**Quick Test to Verify Issue:**
```bash
curl https://eckqzu5foc.execute-api.us-west-1.amazonaws.com/Prod/docs
# Returns: {"error": "Internal server error", "message": "There is no current event loop in thread 'MainThread'."}
```

### 🚨 AWS MCP Lambda Handler Bug Fix

**Issue**: AWS MCP Lambda Handler (v0.1.6) automatically converts snake_case function names to camelCase, violating MCP community standards (90% use snake_case) and causing confusion.

**Root Cause**: Hardcoded conversion in `awslabs.mcp_lambda_handler.mcp_lambda_handler:164-169`
- **GitHub Issue**: [awslabs/mcp#757](https://github.com/awslabs/mcp/issues/757) (reported by Sophie Margolis, assigned to Lukas Xue)
- **Example**: `fetch_account_info` → `fetchAccountInfo` (unwanted conversion)

**Our Solution**: Comprehensive monkey patch in `lambda_handler.py:22-68` that:
1. Preserves original function names exactly as written
2. Intercepts AWS's camelCase conversion and restores snake_case
3. Patches BOTH `tools` registry (display) AND `tool_implementations` (execution)
4. Maintains perfect compatibility with existing functions
5. **Status**: ✅ Fully implemented and tested - MCP functions execute correctly

**Tracking**: Monitor AWS updates for native snake_case support to eventually remove our patch.

### 🚨 IMPORTANT: Always use `uv` for Python execution
**ALWAYS use `uv run python` instead of `python` or `python3` for all Python scripts and commands.**

### AWS Lambda Development (Current)
- **Local Testing**: `sam build && sam local start-api --port 3000`
- **Deploy Production**: `sam build && sam deploy --resolve-s3`
- **Deploy Development**: `sam build && sam deploy --stack-name pb-fm-mcp-dev --resolve-s3`
- **Testing**: `uv run pytest tests/test_base64expand.py tests/test_jqpy/test_core.py` (core tests pass)
- **Equivalence Testing**: `uv run python scripts/test_equivalence.py` (verifies MCP and REST return identical results)
- **MCP Testing**: `env TEST_WALLET_ADDRESS="wallet_here" uv run python scripts/mcp_test_client.py --mcp-url http://localhost:8080/mcp --test`
- **Linting**: `uv run ruff check .`
- **Python Scripts**: `uv run python script.py` (always use uv for dependency management)

## ✅ PROJECT STATUS: AWS Lambda Web Adapter Migration COMPLETED (July 2025)

**MIGRATION SUCCESS**: Unified MCP + REST deployment in single container runtime with native async support.

### Latest Achievements:
- ✅ **AWS Lambda Web Adapter Migration**: Complete replacement of mangum with native async support
- ✅ **Unified Container Deployment**: Single Docker image supporting both MCP and REST protocols  
- ✅ **Snake_case Preservation**: Comprehensive monkey patch solving AWS MCP Handler naming bug
- ✅ **Environment Variable Security**: Documented Claude Code patterns for secure wallet testing
- ✅ **Enhanced MCP Test Client**: Now supports `TEST_WALLET_ADDRESS` environment variable
- ✅ **Real Data Validation**: Both protocols tested with live wallet data (19B+ nhash staked, 2.7B+ rewards)
- ✅ **Perfect Protocol Consistency**: MCP and REST return identical data structures
- ✅ **Production Ready**: All 16 MCP tools and 19 REST endpoints working flawlessly

### Key Technical Accomplishments:
- **Async Resolution**: Eliminated all "no current event loop" errors via AWS Lambda Web Adapter
- **Protocol Unification**: Both MCP (`/mcp`) and REST (`/api/*`) routes in same FastAPI application
- **Name Consistency**: Function names exactly match between MCP tools and REST paths
- **Security Implementation**: Wallet addresses properly handled via environment variables
- **Comprehensive Testing**: Full test suite validates both protocols with real blockchain data

**Current Status**: Production-ready dual-protocol server successfully deployed and validated.

## 🚨 DEPLOYMENT ENVIRONMENTS