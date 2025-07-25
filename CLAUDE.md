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

### 🚨 CRITICAL: Dual-Path Architecture for MCP vs REST

**THIS PROJECT REQUIRES SEPARATE LAMBDA FUNCTIONS FOR MCP AND REST PROTOCOLS!**

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
│ • NO FastAPI wrapper     │  │ • Native async support         │
└──────────────────────────┘  └────────────────────────────────┘
```

**❌ NEVER route MCP through FastAPI/Web Adapter - it breaks the protocol!**
**✅ ALWAYS use separate Lambda functions with proper routing!**

### 🚨 CRITICAL: Always Clean Before Building

**ALWAYS clean build artifacts before every SAM build to prevent poisoned builds:**

```bash
# ✅ CORRECT: Clean before every build
rm -rf .aws-sam/
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
sam build --template-file template-dual-path.yaml

# ❌ WRONG: Building without cleaning (leads to internal server errors)
sam build --template-file template-dual-path.yaml
```

**Why This Matters:**
- Previous builds can leave corrupted artifacts in `.aws-sam/` directory
- Python bytecode files can conflict between different commits
- "Internal server error" issues are often caused by poisoned build cache
- Fresh builds from clean state eliminate mysterious deployment failures

### 🚨 CRITICAL: Lambda Package Size Management

**AWS Lambda has a 250 MB unzipped size limit. Our deployment uses `.samignore` for automatic pruning.**

**What Gets Excluded Automatically:**
- **81 MB** - `.venv-workers/` (Cloudflare Workers remnants with Pyodide)
- **16 MB** - `uvloop` (not needed for Lambda)
- **Test files** - All test directories and files
- **Documentation** - All .md, .rst, .txt files
- **Build artifacts** - .ruff_cache, __pycache__, etc.
- **Development tools** - Scripts, Docker files, configs
- **Unnecessary dependencies** - watchfiles, websockets, httptools

**Manual Cleanup Before First Build:**
```bash
# Remove any Cloudflare Workers remnants permanently
rm -rf .venv-workers/
rm -rf .wrangler/
rm -f tests/test_worker*.py

# Then proceed with clean build
rm -rf .aws-sam/
sam build --template-file template-dual-path.yaml
```

**Size Verification:**
```bash
# Check build size before deployment
du -sh .aws-sam/build/McpFunction/
# Should be well under 250 MB unzipped (typically ~50-70 MB)
```

### AWS Lambda Development (Current)

**🚀 Automated Deployment (Recommended)**:
- **Deploy Development**: `./scripts/deploy.sh dev` (includes clean build, versioning, pruning)
- **Deploy Production**: `./scripts/deploy.sh prod` (requires main branch, production warning)

**🧪 Testing & Development**:
- **Local Testing**: `sam local start-api --port 3000` (wallet only needed for actual API calls)
- **Core Tests**: `uv run pytest tests/test_base64expand.py tests/test_jqpy/test_core.py` (core tests pass)
- **Equivalence Testing**: `uv run python scripts/test_equivalence.py` (verifies MCP and REST return identical results)
- **MCP Testing**: `env TEST_WALLET_ADDRESS="wallet_here" uv run python scripts/mcp_test_client.py --mcp-url http://localhost:8080/mcp --test`
- **Linting**: `uv run ruff check .`
- **Python Scripts**: `uv run python script.py` (always use uv for dependency management)

**🔧 Manual Deployment (Advanced)**:
- **Build**: `rm -rf .aws-sam/ && sam build --template-file template-dual-path.yaml` (no wallet needed for build)
- **Deploy Development**: `sam deploy --stack-name pb-fm-mcp-dev --resolve-s3`
- **Deploy Production**: `sam deploy --stack-name pb-fm-mcp-v2 --resolve-s3`
- **⚠️ Warning**: Manual deployment requires manual pruning to stay under Lambda size limits

**⚠️ CRITICAL**: 
- Always use `template-dual-path.yaml` for ALL deployments
- Use automated `./scripts/deploy.sh` for best results (includes automatic versioning and pruning)

### 🚨 CRITICAL: API Gateway Stage Management

**Problem Solved**: AWS SAM defaults to ugly `/Prod/` stage prefix. We eliminated this with clean `/v1/` versioning.

**How to Change Stage Prefix** (e.g., from `/v1/` to `/v1.1/` or `/v2/`):

1. **Edit `template-dual-path.yaml`** - Update 4 places:
```yaml
Resources:
  MyServerlessApi:
    Properties:
      StageName: v2  # Change this

  RestApiFunction:  # NOT McpFunction - only REST needs stage path
    Environment:
      Variables:
        API_GATEWAY_STAGE_PATH: /v2  # Change this

Outputs:
  # Update ALL output URLs to use new prefix
  ApiUrl:
    Value: !Sub "https://${MyServerlessApi}.execute-api.${AWS::Region}.amazonaws.com/v2/"
  McpUrl:
    Value: !Sub "https://${MyServerlessApi}.execute-api.${AWS::Region}.amazonaws.com/v2/mcp"
  OpenApiUrl:
    Value: !Sub "https://${MyServerlessApi}.execute-api.${AWS::Region}.amazonaws.com/v2/openapi.json"
  SwaggerDocsUrl:
    Value: !Sub "https://generator3.swagger.io/index.html?url=https://${MyServerlessApi}.execute-api.${AWS::Region}.amazonaws.com/v2/openapi.json"
```

2. **Deploy**:
```bash
sam build --template-file template-dual-path.yaml
sam deploy --stack-name pb-fm-mcp-dev --resolve-s3
```

**Why This Works**: Uses explicit `AWS::Serverless::Api` resource with `RestApiId` references and proper dual-path routing.

**Critical Files**:
- **✅ Primary Template**: `template-dual-path.yaml` (dual Lambda functions - ALWAYS USE THIS!)
- **❌ Wrong Template**: `template-simple.yaml` (single function - BREAKS MCP PROTOCOL!)
- **❌ Legacy Template**: `template.yaml` (old complex approach - deprecated)

## ✅ PROJECT STATUS: Dual-Path Architecture IMPLEMENTED (July 2025)

**ARCHITECTURE SUCCESS**: Dual Lambda function deployment with proper protocol separation.

### Why Dual-Path Architecture is REQUIRED

**Initial Attempt**: Tried to route both MCP and REST through single Lambda with Web Adapter
- ❌ **Result**: MCP protocol failed - "Method Not Allowed", tools not discovered
- ❌ **Root Cause**: MCP requires direct AWS MCP Handler, incompatible with FastAPI wrapper

**Final Solution**: Separate Lambda functions for each protocol
- ✅ **McpFunction**: Direct AWS MCP Handler for `/mcp` endpoint
- ✅ **RestApiFunction**: FastAPI + Web Adapter for `/api/*`, `/docs`, etc.
- ✅ **Result**: Both protocols working perfectly, Claude.ai connection successful

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

**Current Status**: ⚠️ **MISSION INCOMPLETE** - Docker deployment validated, Lambda deployment blocked.

## 🚨 MISSION CRITICAL: Single Lambda Deployment Goal

**GOAL**: Achieve stable, reproducible single AWS Lambda deployment supporting both MCP and REST APIs.

**Current Issue**: Successfully created unified MCP + REST architecture but deployment is split:
- ✅ **Docker Deployment**: Fully working with all 16 MCP tools + 22 REST endpoints
- ❌ **Lambda Deployment**: Internal server errors, 0 tools discovered

**Root Problem**: Architecture mismatch between ZIP Lambda deployment vs Container Lambda deployment
- **ZIP Deployment**: Traditional `lambda_handler(event, context)` with limited async support
- **Container Deployment**: Native HTTP server with AWS Lambda Web Adapter (our target)

**Mission Requirements:**
1. **Single Lambda Function**: One deployment serving both `/mcp` and `/api/*` routes
2. **Production Stability**: No async event loop errors or internal server failures  
3. **Feature Completeness**: All 16 MCP tools and 22 REST endpoints working
4. **Real Data**: Validated with live wallet data (19B+ nhash amounts)
5. **Reproducible**: Reliable deployment process via SAM/CloudFormation

**Deployment Options to Investigate:**
- **Option A**: Fix ZIP deployment with proper lambda_handler bridge
- **Option B**: Container deployment with ECR repository (original plan)
- **Option C**: Hybrid approach with unified codebase supporting both

**Success Criteria**: 
```bash
curl https://your-lambda-url/mcp -d '{"jsonrpc":"2.0","method":"tools/list","id":"1"}' 
# Returns: {"result": {"tools": [... 16 tools ...]}}

curl https://your-lambda-url/api/fetch_current_hash_statistics
# Returns: {"maxSupply": {"amount": "100000000000000000000", ...}}
```

**Status**: ✅ **MISSION ACCOMPLISHED** - Single Lambda deployment achieved July 23, 2025!

## 🎉 Mission Completion Details

**Achievement**: Successfully deployed unified MCP + REST server to AWS Lambda using Web Adapter Layer.

**Solution**: AWS Lambda Web Adapter with ZIP deployment (not container required)
- Fixed Python path issues with proper PYTHONPATH configuration
- Web Adapter Layer provides native async support
- Single Lambda function serves both `/mcp` and `/api/*` endpoints

**Key Fix**: The critical issue was Python module path resolution:
```bash
# In run.sh startup script:
export PYTHONPATH="/var/task/src:$PYTHONPATH"
exec python -m uvicorn web_app_unified:app --host 0.0.0.0 --port $PORT
```

**Current Deployment URLs (Clean v1 API Versioning)**:
- **Development**: https://48fs6126ba.execute-api.us-west-1.amazonaws.com/v1/
- **Production**: https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/ (legacy /Prod prefix)

**Major Update**: Eliminated ugly `/Prod/` prefix in favor of clean `/v1/` API versioning.

**Validation**: All 16 MCP tools and 22 REST endpoints working with real wallet data.

## 🗂️ KEY FILES FOR DUAL-PATH ARCHITECTURE

### Critical Implementation Files

1. **`template-dual-path.yaml`** - ✅ THE ONLY TEMPLATE TO USE
   - Defines two separate Lambda functions (McpFunction + RestApiFunction)
   - Configures path-based routing at API Gateway level
   - **ALWAYS use this for deployments**

2. **`lambda_handler_unified.py`** - MCP Protocol Handler
   - Direct AWS MCP Handler implementation
   - Handles `/mcp` endpoint without FastAPI
   - Contains snake_case monkey patch for AWS bug

3. **`src/web_app_unified.py`** - REST API Handler
   - FastAPI application for REST endpoints
   - Handles `/api/*`, `/docs`, `/health`
   - Uses AWS Lambda Web Adapter

4. **`run.sh`** - Startup script for REST function only
   - Launches uvicorn for FastAPI
   - Used ONLY by RestApiFunction
   - NOT used by McpFunction

### Templates to AVOID

- **❌ `template-simple.yaml`** - Single function approach (BREAKS MCP)
- **❌ `template.yaml`** - Old complex approach (deprecated)
- **❌ Any template without dual Lambda functions**

## 🚨 DEPLOYMENT ENVIRONMENTS

**Current Deployment URLs (after July 24, 2025 update with dynamic versioning):**

**Development Environment**: `pb-fm-mcp-dev` stack (ACTIVE - For testing new features)
- **STABLE Lambda Function URL**: `https://x2jhgtntjmnxw7hpqbouf3os240dipub.lambda-url.us-west-1.on.aws/` ✅ **USE THIS FOR CLAUDE.AI**
- **API Gateway MCP**: `https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/mcp` ✅
- **API Gateway REST**: `https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/api/*` ✅
- **Documentation**: `https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/docs` ✅
- **OpenAPI Spec**: `https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/openapi.json` ✅
- **Deploy Command**: `./scripts/deploy.sh dev`
- **Deploy Branch**: `dev` branch for all development work

**Note**: The Lambda Function URL is stable and won't change between deployments!

## 🤖 Claude.ai MCP Configuration

To configure this MCP server with Claude.ai:

### Development Server (Latest) - STABLE URL
```
MCP Server URL: https://x2jhgtntjmnxw7hpqbouf3os240dipub.lambda-url.us-west-1.on.aws/
```

**This is a Lambda Function URL that is stable and won't change between deployments!**

### Steps to Add to Claude.ai:
1. Go to Claude.ai settings
2. Navigate to MCP Servers or External Tools
3. Add new MCP server with the URL above
4. Test connection - it should discover 16 MCP tools
5. Tools include blockchain data, account info, delegation data, and market information

### Available MCP Tools:
- `fetch_current_hash_statistics` - Blockchain statistics
- `fetch_account_info` - Wallet account information  
- `fetch_total_delegation_data` - Staking/delegation data
- `fetch_current_fm_data` - Figure Markets exchange data
- `fetch_complete_wallet_summary` - Comprehensive wallet analysis
- `fetch_market_overview_summary` - Complete market overview
- And 10 more specialized tools for blockchain and exchange data

### Version Information:
- **Dynamic Versioning**: Each deployment uses format `{git-commit}-{datetime}`
- **Current Version**: Check via `curl https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/mcp`
- **Auto-Update**: Version updates automatically on every deployment via `./scripts/deploy.sh`

## 🚨 ORIGINAL DEPLOYMENT ENVIRONMENTS (Legacy)