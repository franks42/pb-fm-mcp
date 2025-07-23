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

**Policy**: Real wallet addresses are sensitive data that must be handled with the same security as API keys or passwords.

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
- **Linting**: `uv run ruff check .`
- **Python Scripts**: `uv run python script.py` (always use uv for dependency management)

### 🚨 DEPLOYMENT ENVIRONMENTS

**Production Environment**: `pb-fm-mcp-v2` stack (STABLE - Used by colleagues)
- **MCP Protocol**: `https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp` 
- **REST API**: `https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/api/*`
- **Documentation**: `https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/docs`
- **OpenAPI Spec**: `https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/openapi.json`
- **Deploy Command**: `sam deploy --stack-name pb-fm-mcp-v2 --resolve-s3`
- **Deploy Branch**: `main` branch ONLY, when explicitly requested

**Development Environment**: `pb-fm-mcp-dev` stack (ACTIVE - For testing new features)
- **MCP Protocol**: `https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod/mcp` ✅
- **REST API**: `https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod/api/*` ✅
- **Documentation**: `https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod/docs` ✅
- **OpenAPI Spec**: `https://q6302ue9w9.execute-api.us-west-1.amazonaws.com/Prod/openapi.json` ✅
- **Deploy Command**: `sam deploy --stack-name pb-fm-mcp-dev --resolve-s3`
- **Deploy Branch**: `dev` branch for all development work

**Local Testing**: `http://localhost:3000/*` (all endpoints)
- **Local Command**: `sam build && sam local start-api --port 3000`

## Project Architecture

This is a Python-based **dual-protocol server** running on **AWS Lambda**, providing both MCP (Model Context Protocol) and REST API access to Figure Markets exchange and Provenance Blockchain data.

### Core Components

- **`src/web_app_unified.py`** - Unified FastAPI application for AWS Lambda Web Adapter deployment (clean MCP+REST)
- **`src/functions/`** - Business logic modules with @api_function decorators for dual protocol exposure
- **`src/registry/`** - Function registry system for automatic MCP tool and REST endpoint generation
- **`src/utils.py`** - Utility functions for datetime, HTTP requests, and operations
- **`src/base64expand.py`** - Base64 data expansion utilities (ready for integration)
- **`src/jqpy/`** - Complete jq-like JSON processor (162/193 tests passing, core functionality solid)

### Removed Legacy Components (July 2025)
- ~~**`lambda_handler.py`**~~ - Replaced by unified web app (legacy mangum-based architecture)
- ~~**`async_wrapper.py`**~~ - No longer needed with AWS Lambda Web Adapter native async support
- ~~**`src/registry/integrations*.py`**~~ - Removed redundant integration files, logic moved to unified app

### Unified AWS Lambda Web Adapter Architecture (July 2025)

1. **AWS Lambda Web Adapter**: Native async event loop support with uvicorn + FastAPI
2. **Path-Based Routing**: `/mcp` for MCP protocol, `/api/*` for REST endpoints, `/docs` for documentation
3. **Unified Application**: Single `web_app_unified.py` handling both protocols with direct async support
4. **AWS MCP Lambda Handler**: For MCP protocol with comprehensive snake_case naming fix
5. **Function Registry**: Automatic dual-protocol exposure via @api_function decorator
6. **Perfect Name Matching**: MCP function names match REST paths exactly (e.g., `fetch_account_info` → `/api/fetch_account_info/`)
7. **Container Deployment**: Docker-based deployment with AWS Lambda Web Adapter
8. **CloudFormation/SAM**: Infrastructure as Code deployment

### MCP Tools Structure

The server exposes numerous tools for:
- **Account Management**: Fetching account info, balances, and vesting details
- **Delegation Operations**: Staking, rewards, unbonding, and redelegation data
- **Market Data**: Trading pairs, prices, and asset information
- **Blockchain Stats**: HASH token statistics and network information

### Dependencies

- **Production**: `awslabs-mcp-lambda-handler`, `httpx`, `structlog`, `fastapi`, `uvicorn[standard]`
- **Development**: `pytest`, `pytest-asyncio`, `ruff` (managed via uv)
- **External APIs**: Figure Markets exchange API and Provenance blockchain explorer API
- **Removed Legacy**: ~~`mangum`~~ (replaced by AWS Lambda Web Adapter + uvicorn)

### Configuration

- **Python Version**: 3.12 (AWS Lambda runtime)
- **Package Management**: `uv` for dependency management
- **Deployment**: AWS SAM with CloudFormation
- **Testing**: Local SAM + production Lambda
- **Region**: us-west-1

## Development Context for New Claude Sessions

### What We've Accomplished
1. **Cloudflare → AWS Migration**: Solved Python compatibility issues
2. **Unified Function Registry**: Complete @api_function decorator system for dual protocol exposure
3. **Flat Naming Architecture**: Consistent flat structure across MCP and REST (see naming rationale below)
4. **Standardized Naming**: Function names, API paths, and response keys all aligned (e.g., `/api/delegated_rewards_amount`)
5. **Equivalence Testing**: Automated verification that MCP and REST return identical results with live data tolerance
6. **Production Deployment**: Stable AWS Lambda with auto-generated MCP tools and REST endpoints
7. **Dual API Implementation**: MCP + REST protocols with single function definitions
8. **Full Documentation**: Working /docs endpoint with external Swagger UI integration
9. **CORS & Async**: Proper async patterns and CORS for browser compatibility
10. **Local Testing**: SAM environment with comprehensive testing suite
11. **🚀 AWS Lambda Web Adapter Migration (July 2025)**: Complete migration from problematic mangum architecture
12. **🚀 Perfect Name Consistency (July 2025)**: MCP function names match REST paths exactly - no arbitrary conversions
13. **🚀 Unified Container Deployment (July 2025)**: Single Docker container with both MCP and REST protocols
14. **🚀 Legacy Code Cleanup (July 2025)**: Removed mangum, async_wrapper, integration files - clean codebase

### Flat API Structure Rationale
**MCP Protocol Constraint**: MCP tool functions require a flat naming structure with no namespace hierarchy support. Function names like `fetchAccountInfo` or `fetchDelegatedRewardsAmount` cannot be organized into namespaces like `account.fetchInfo` or `delegation.fetchRewards`.

**Design Decision**: To maintain perfect 1:1 mapping between MCP tools and REST endpoints, we use exact name matching:
- **MCP Function**: `fetch_account_info` 
- **REST Endpoint**: `/api/fetch_account_info/{wallet_address}`
- **Response Key**: `fetch_account_info`

**July 2025 Update**: Implemented perfect name consistency - MCP function names match REST paths exactly with no arbitrary conversions. This eliminates any impedance mismatch between protocols and ensures predictable API behavior.

### Current Development Focus
**Phase 1 & 2 Complete**: Unified Function Registry Architecture fully implemented ✅

✅ **PHASE 1 COMPLETE**: Production/Development Environment Separation  
- Separate endpoints: Production (stable) + Development (testing) ✅
- Git branch strategy: `main` (production) vs `dev` (development) ✅  
- Separate SAM stack deployments: Colleagues' integrations protected ✅

✅ **PHASE 2 COMPLETE**: Unified Function Registry Architecture
- ✅ Decorator-based function registry with `@api_function` for auto-generation
- ✅ Modular business function structure in domain-specific files
- ✅ Auto-generate both MCP tools and REST endpoints from single function definitions
- ✅ **Single-source documentation**: Function docstrings automatically become both MCP tool descriptions AND OpenAPI documentation
- ✅ Full typing system with automatic validation and OpenAPI schema generation

✅ **PHASE 2.5 COMPLETE**: System Operations & Monitoring
- ✅ **Version Management**: Automated semantic versioning with build tracking (v0.1.5)
- ✅ **System Introspection**: Registry analysis tools showing 21 functions, 16 MCP tools, 19 REST endpoints
- ✅ **Lambda Warming**: Ultra-fast ping function for cold start mitigation (<100ms)
- ✅ **Cross-Server Testing**: Dev-to-prod MCP communication testing with performance analysis
- ✅ **Deployment Automation**: One-command deployment scripts with version increment
- ✅ **Async Issue Resolution**: Permanent fix for recurring Lambda async/thread pool problems

**Phase 3**: Enhanced Integration Capabilities
- jqpy JSON processing integration (162/193 tests passing - core functionality solid)
- Base64 data expansion for blockchain data
- Dynamic query transformation tools

**Key Files to Review:**
- `src/web_app_unified.py` - Unified MCP+REST application with AWS Lambda Web Adapter
- `src/functions/` - Business logic modules with @api_function decorators
- `src/registry/` - Function registry system for automatic protocol exposure
- `docs/async-event-loop-analysis.md` - Comprehensive analysis of migration from mangum
- `docs/lambda-web-adapter-migration.md` - Migration guide and architecture decisions
- `scripts/mcp_test_client.py` - Dynamic testing client with no hardcoded function names
- `src/jqpy/` - JSON processing capabilities (162/193 tests passing)
- `src/base64expand.py` - Data expansion utilities

### Testing & Deployment

**Container-Based (Current - July 2025):**
- **Local Container**: `docker build -f Dockerfile-clean -t pb-fm-unified-clean . && docker run -d -p 8080:8080 pb-fm-unified-clean`
- **MCP Testing**: `uv run python scripts/mcp_test_client.py --mcp-url http://localhost:8080/mcp --test`
- **REST Testing**: Browser access to `http://localhost:8080/docs` and endpoints

**Legacy SAM-Based:**
- **Local**: `sam build && sam local start-api --port 3000`
- **Production**: `sam build && sam deploy --resolve-s3`
- **MCP Testing**: `npx @modelcontextprotocol/inspector http://localhost:3000/mcp`

### Architecture Status (Updated July 2025)
✅ **Unified Deployment**: Single container with both MCP and REST protocols using AWS Lambda Web Adapter
✅ **Perfect Name Consistency**: MCP function names match REST paths exactly (no arbitrary conversions)
✅ **Native Async Support**: Direct async/await with AWS Lambda Web Adapter (no thread pool workarounds)
✅ **Clean Codebase**: Removed legacy mangum, async_wrapper, and integration files
✅ **Comprehensive Testing**: Dynamic test client with environment variable support for wallet addresses
✅ **Documentation**: Full OpenAPI docs with external Swagger UI integration  
✅ **CORS**: Cross-origin access enabled for browser compatibility  
✅ **Security**: Wallet address security policy implemented - no hardcoded addresses in code
✅ **Production Ready**: 21 functions (16 MCP tools, 19 REST endpoints) with complete dual-protocol support

**Current Status (July 2025)**: Successfully migrated from problematic mangum architecture to clean AWS Lambda Web Adapter deployment. Achieved perfect naming consistency between MCP and REST protocols. Single unified container supports both protocols with native async support and comprehensive security policies for sensitive data handling.