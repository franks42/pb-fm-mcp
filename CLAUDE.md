# CLAUDE.md

# 🚨 RULE #1: READ THIS FILE FIRST
**Claude Code: Before ANY action, read this entire CLAUDE.md file. Follow it exactly. No exceptions.**

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 MANDATORY: Pre-Action Verification Protocol

**Before ANY deployment, build, or technical command, Claude Code MUST:**
1. **Read this CLAUDE.md file completely** - Never skip this step
2. **Verify current directory contents** with `ls` to see what files actually exist
3. **Use ONLY the commands/templates specified in this file** - No assumptions
4. **Never use "remembered" commands from other contexts** - Only what's documented here

## 🚨 Deployment Checklist (MANDATORY)
□ Read current CLAUDE.md file completely
□ Check what templates exist (`ls *.yaml`) 
□ Use exact template name specified in CLAUDE.md
□ Use exact commands documented in CLAUDE.md
□ No assumptions, no "habits", no prior knowledge from other projects

## 🚨 NEVER DO THESE THINGS
- **Never use template names not listed in this file**
- **Never assume commands from other projects/contexts**
- **Never skip reading this CLAUDE.md file first**
- **Never use "out of habit" or "remembered" approaches**
- **Never override what CLAUDE.md explicitly states**

## Error Prevention Warning
**If Claude Code uses wrong templates/commands, it can:**
- Deploy wrong configurations to production
- Break production systems and user access
- Waste hours debugging mysterious failures
- Create inconsistent deployments
- Force manual recovery procedures

**CLAUDE.MD IS THE SINGLE SOURCE OF TRUTH - Always consult it first.**

## 🚨 CRITICAL: Domain Name Spelling

**IMPORTANT: "creativeapptitude.com" is the correct spelling of the base domain name for prod and dev environments.**

This domain name is a clever wordplay combining "creative", "app", and "aptitude" - which confuses many people. Always use this exact spelling:
- ✅ **Correct**: creativeapptitude.com
- ❌ **Wrong**: creativeapttitude.com (missing 'i')
- ❌ **Wrong**: creativeaptitude.com (missing 'app')

**Production Domain**: pb-fm-mcp.creativeapptitude.com  
**Development Domain**: pb-fm-mcp-dev.creativeapptitude.com

## 🚨 CURRENT PROJECT: AI-Driven Webpage MVP (July 30, 2025)

**ACTIVE DEVELOPMENT**: Building MVP for AI-orchestrated webpage system using SQS message bus architecture.

### Current Session Status
- **Architecture Definition**: In progress in `docs/mvp-ai-driven-webpage.md`
- **Key Decision**: SQS as generic message bus for async component communication
- **Core Components Defined**:
  - AI-Agent (orchestrator using MCP functions)
  - Browser-JS (webpage renderer with component addressing)
  - S3-Queue-Handler (bulk data via S3 references only)
  - WebBrowser-Queue-Handler (browser↔SQS interface)

### Implementation Foundation
- **Existing Infrastructure**: SQS traffic light pattern working (~475ms AI→browser)
- **Working Functions**: `wait_for_user_input()`, `send_response_to_browser()` in `src/functions/sqs_traffic_light.py`
- **Message Format**: JSON with component addressing for routing
- **Storage Pattern**: Large content in S3, only references via SQS

### Next Session Tasks
1. **Complete Architecture Definition**: Finish component specification from user
2. **Define MVP Feature Set**: Specific capabilities and limitations
3. **Implementation Plan**: Phases and development roadmap
4. **Begin Development**: Start with enhanced SQS message routing

### Architectural Principles
- **No Bulk Data in SQS**: Only S3 identifiers/references
- **Component Addressing**: Each webpage component has unique address for message routing
- **AI Orchestration**: AI has complete freedom to decide layout, content, visualizations
- **Low-Latency Polling**: Call webserver → wait → timeout → repeat pattern

## 🚨 CRITICAL: Native MCP Handler Requirement (July 29, 2025)

**MANDATORY: Ensure that MCP requests are ALWAYS handled natively by the AWS MCP handlers. If not, it may cause connection issues with Claude.ai and possibly other MCP clients.**

### Critical MCP Architecture Requirements:
- ✅ **Native AWS MCP Handler**: MCP requests must go directly to `awslabs.mcp_lambda_handler.MCPLambdaHandler`
- ❌ **Never intercept MCP with FastAPI**: Do NOT create FastAPI routes for `/mcp` endpoints
- ❌ **Never simulate MCP responses**: Do NOT manually construct JSON-RPC responses in FastAPI
- ✅ **Use Native Lambda Handler**: Deploy with `lambda_handler_unified.lambda_handler` for MCP compatibility

### Why This Matters:
- **Claude.ai Compatibility**: Claude.ai requires proper MCP protocol handling to discover and execute tools
- **MCP Client Standards**: Other MCP clients expect native protocol compliance
- **Tool Discovery**: Improper MCP handling causes "disabled" status instead of showing available tools
- **Protocol Compliance**: Native handlers ensure proper JSON-RPC 2.0 and MCP specification adherence

**If MCP clients show "disabled" or "no provided tools", check that MCP requests are handled natively, not intercepted by FastAPI routes.**

## 🚨 CRITICAL: Template Architecture

**IMPORTANT: Single unified template architecture in use.**

### Current Status
- ✅ **Single Template**: `template-unified.yaml` is the ONLY template to use
- ✅ **Unified Architecture**: Single Lambda function with AWS Web Adapter handles both MCP and REST
- ✅ **Testing Verified**: 100% function coverage with unified template architecture

### Deploy Commands (Current)
```bash
# Development deployment (ALWAYS use deploy script)
./deploy.sh dev --clean --test

# Production deployment (ALWAYS use deploy script)
./deploy.sh prod --clean --test
```

**Rule**: Always use `./deploy.sh` script for ALL deployments. Never use manual `sam` commands.

## 🚨 CRITICAL: Production Function Restrictions (CSV-Driven Protocol Management)

**IMPORTANT: Production deployment now uses CSV-driven protocol management with only 16 core functions exposed via MCP.**

### Production MCP Configuration  
- **MCP Functions**: Only 16 core blockchain/market functions exposed via MCP protocol
- **Development Functions**: 48+ experimental functions disabled using `protocols=[]` → `protocols=["local"]`
- **Configuration Files**: `function_protocols_prod.csv` defines production function access
- **Validation Script**: `scripts/validate_production_config.py` ensures compliance

### Core Production Functions (MCP Enabled)
```
1. fetch_account_info           - Blockchain account information
2. fetch_account_is_vesting     - Vesting account status
3. fetch_available_committed_amount - Committed HASH amounts
4. fetch_complete_wallet_summary - Comprehensive wallet data
5. fetch_current_fm_data        - Figure Markets exchange data
6. fetch_current_hash_statistics - HASH token statistics
7. fetch_figure_markets_assets_info - Trading assets information
8. fetch_last_crypto_token_price - Token price history
9. fetch_market_overview_summary - Market overview aggregate
10. fetch_total_delegation_data - Delegation information
11. fetch_vesting_total_unvested_amount - Vesting calculations
12. get_registry_introspection  - Function registry details
13. get_registry_summary        - Registry overview
14. get_system_context          - System information
15. mcp_test_server            - MCP testing utility
16. mcp_warmup_ping            - Lambda warming function
```

### Implementation Details
- **Protocol Enum**: Added `LOCAL = "local"` for registered but not exposed functions
- **Decorator Logic**: Empty protocols `[]` → `["local"]` to prevent MCP exposure
- **Registry Filtering**: `get_mcp_functions()` only returns functions with MCP protocol
- **CSV-Driven System**: Automated synchronization between CSV configs and function decorators

## 🚨 CURRENT DEPLOYMENT STATUS (July 29, 2025)

**SUCCESS: CSV-driven MCP deployment with 16 core production tools successfully deployed and tested.**

### Current Production Environment URLs
- **Custom Domain MCP**: https://pb-fm-mcp.creativeapptitude.com/mcp (16 production tools)
- **API Gateway MCP**: https://4d0i1tqdg4.execute-api.us-west-1.amazonaws.com/v1/mcp
- **Documentation**: https://4d0i1tqdg4.execute-api.us-west-1.amazonaws.com/v1/docs

### Current Development Environment URLs  
- **Custom Domain MCP**: https://pb-fm-mcp-dev.creativeapptitude.com/mcp (62 development tools)
- **API Gateway MCP**: https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/mcp
- **Documentation**: https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/docs

### Production Safety Features
- **Environment Isolation**: Separate CSV configs for dev vs prod
- **Automated Sync**: `deploy.sh` automatically syncs CSV to function decorators
- **Validation Pipeline**: Pre-deployment validation ensures configuration compliance
- **Zero Downtime**: CSV changes deployed without code modifications

**✅ SUCCESS**: Production deployment validated and ready for Claude.ai integration.

## Development Commands

### 🚨 CRITICAL: MCP Server Communication Policy

**ALWAYS use the MCP test client for MCP protocol communication:**
```bash
# ✅ CORRECT: For MCP protocol (tools/list, tools/call)
uv run python scripts/mcp_test_client.py --mcp-url <URL> --interactive

# ❌ WRONG: Direct curl to MCP endpoints (requires permission for each call)
curl -X POST <MCP_URL> -d '{"jsonrpc":"2.0","method":"tools/call",...}'
```

**Why This Matters:**
- **No Permission Required**: The test client batches MCP requests efficiently
- **Session Management**: Handles MCP session lifecycle automatically  
- **Better Error Handling**: Provides clear feedback on MCP protocol issues
- **Consistent Testing**: Standardized way to test all MCP functions

### 🚨 CRITICAL: Function Naming Standards
**NEVER change existing function names without explicit user approval. This breaks integrations.**
- **Standard**: Use snake_case (e.g., `fetch_current_hash_statistics`)
- **Legacy**: Production may have camelCase (e.g., `fetchCurrentHashStatistics`) 
- **Rule**: Always ask before renaming ANY function - this is a breaking change

### 🚨 CRITICAL: MCP Function Invocation Directive

**ALWAYS use the Python MCP test client instead of curl for MCP function calls:**

```bash
# ✅ CORRECT: Use Python MCP test client
uv run python scripts/mcp_test_client.py --mcp-url <URL> --interactive

# ❌ WRONG: curl commands (require user permission each time)
curl -X POST <MCP_URL> -d '{"jsonrpc":"2.0","method":"tools/call",...}'
```

**Why This Is Critical:**
- **✅ No User Permission Required**: Python scripts don't need approval for each call
- **✅ Official Full MCP SDK**: Uses the complete MCP protocol implementation
- **✅ Better Error Handling**: Proper MCP session management and error reporting
- **✅ Batch Operations**: Can perform multiple operations efficiently

### 🚨 CRITICAL: Function Architecture and Registration System

**MANDATORY: Understanding @api_function, __init__.py, and CSV Configuration**

**The function registration system has THREE interconnected components that MUST be synchronized:**

#### **1. @api_function Decorators (Code Definition)**
Every function that should be available via MCP or REST MUST have an `@api_function` decorator:

```python
@api_function(
    protocols=["mcp", "rest"],  # Which protocols to expose via
    description="MANDATORY description for AI/API understanding",
    # Optional: path, method, tags for REST customization
)
async def my_function(param: str) -> dict:
    return {"result": param}
```

**Critical Rules:**
- **✅ Description is MANDATORY** - AI needs this to understand when/how to call functions
- **✅ protocols=[]** means function is registered but disabled (better than commenting decorators)
- **❌ Never comment out decorators** - use CSV control instead

#### **2. src/functions/__init__.py (Import Registration)**
ALL modules containing `@api_function` decorators MUST be imported in `__init__.py`:

```python
# ✅ CORRECT: Direct module imports
try:
    from . import stats_functions
    from . import blockchain_functions
except Exception as e:
    print(f"❌ Failed to import: {e}")

# ✅ CORRECT: Subdirectory module imports  
try:
    from .webui_functions import conversation_functions
    from .webui_functions import interface_functions
except Exception as e:
    print(f"❌ Failed to import webui_functions: {e}")
```

**Why This Matters:**
- **Import triggers decorator execution** → Functions register in global registry
- **No import = No registration** → Function exists but is unreachable via MCP/REST
- **Silent failure** → No error, function just doesn't work

#### **3. CSV Configuration Files (Protocol Control)**
CSV files control which registered functions are exposed via which protocols:

**`function_protocols.csv` (Development):**
```csv
Function Name,MCP,REST,Description
my_function,YES,YES,Description here
disabled_function,,,Function disabled but available in registry
mcp_only_function,YES,,Only available via MCP protocol
```

**`function_protocols_prod.csv` (Production):**
- Same format but typically fewer functions enabled
- Production safety: sensitive functions disabled

**CSV Rules:**
- **Every @api_function MUST have CSV entry** 
- **Empty MCP/REST = disabled but registered**
- **CSV is single source of truth for protocol exposure**

#### **4. Automated Validation (Deployment Safety)**
The deploy script now includes comprehensive validation that checks:

```bash
./deploy.sh dev --clean --test
├─ Function Architecture Validation:
│  ├─ @api_function decorators → __init__.py imports ✓
│  ├─ @api_function decorators → CSV entries ✓  
│  ├─ CSV entries → source functions ✓
│  ├─ __init__.py imports → file existence ✓
│  ├─ Decorator syntax validation ✓
│  └─ Duplicate function names ✓
├─ AWS Deployment
└─ Function count validation
```

**Validation Script Available:**
```bash
# Run standalone validation anytime
uv run python scripts/validate_function_architecture.py
```

#### **5. Architecture Principles**
- **✅ Functions define capability** (via @api_function decorators)
- **✅ CSV controls availability** (which protocols expose them)
- **✅ No commented decorators** (use protocols=[] instead)
- **✅ Single source of truth** - CSV files manage protocol exposure
- **✅ Fail fast** - validation catches issues before deployment

#### **6. Common Pitfalls and Solutions**
**Problem: Function exists but not available via MCP/REST**
- **Check:** Is module imported in `__init__.py`?
- **Check:** Does function have `@api_function` decorator?
- **Check:** Is function listed in CSV with appropriate protocols?

**Problem: "Function count mismatch" during deployment**
- **Run:** `uv run python scripts/validate_function_architecture.py`
- **Fix:** Add missing imports or CSV entries as recommended

**Problem: Function works locally but not in deployed Lambda**
- **Cause:** Module not imported in `__init__.py` → decorator never executes
- **Fix:** Add import to trigger registration

This architecture prevents the "obscure bugs" where functions exist in code but are unreachable in production.

### 🚨 CRITICAL: Code Quality Standards

**🚨 MANDATORY: Code Validation Pipeline After Every Edit**
**ALWAYS run this complete validation pipeline immediately after creating or editing any Python file:**

```bash
# ✅ MANDATORY: Complete validation pipeline for every Python file edit
uv run black src/functions/new_function.py                    # 1. Format code
uv run flake8 src/functions/new_function.py                   # 2. Check syntax/style  
uv run python -m py_compile src/functions/new_function.py     # 3. Verify compilation

# ✅ BATCH: Validate multiple files at once
uv run black src/functions/webpage_*.py && \
uv run flake8 src/functions/webpage_*.py && \
find src/functions -name "webpage_*.py" -exec uv run python -m py_compile {} \;
```

**Why This Pipeline Is Critical:**
- **✅ Black**: Formats code and prevents basic syntax issues
- **✅ Flake8**: Catches decorator syntax errors (E304), unused imports, style violations
- **✅ py_compile**: Ensures valid Python syntax that will import properly
- **✅ Lambda Success**: Files passing this pipeline work reliably in Lambda environment

**Flake8 specifically catches issues that broke Lambda imports:**
- **E304**: Blank lines after function decorators (breaks function registration)
- **F401**: Unused imports that can cause memory issues
- **E501**: Long lines that indicate complex code needing refactoring
- **✅ Consistent Style**: Maintains uniform code formatting across the project
- **✅ AST-Based**: Uses Python's Abstract Syntax Tree for intelligent formatting

**🚨 CRITICAL: MCP Function Requirements**
**ALL MCP functions MUST have a description parameter. This is mandatory because AI needs to understand when and how to call each tool. For REST endpoints, descriptions help developers understand API usage.**

Example:
```python
@api_function(
    protocols=["mcp"],
    description="Mandatory description explaining what this function does and when to use it",
)
async def my_function():
    pass
```

**Import Standards:**
**NO ugly optional import statements with try/except fallbacks. Use explicit imports only. If a module cannot be imported, it's a bug that needs to be fixed, not worked around.**

**🚨 CRITICAL: Python Import Path Policy**
**NEVER EVER add "src." to import statements! This is bad practice and breaks the module structure.**
- ❌ WRONG: `from src.registry import api_function`
- ❌ WRONG: `from src.functions.utils import helper`
- ✅ CORRECT: `from registry import api_function`
- ✅ CORRECT: `from functions.utils import helper`

**Import issues are resolved by setting PYTHONPATH, NOT by adding "src." prefixes:**
```bash
# For scripts in scripts/ directory:
PYTHONPATH=/path/to/project/src uv run python scripts/test.py

# For Lambda/production:
export PYTHONPATH="/var/task/src:$PYTHONPATH"
```

**Code Duplication:**
**NO duplication of code, functions, or type definitions across files. Maintain single source of truth. Import from shared modules instead of copying code.**

### 🚨 CRITICAL: Testing Requirements Policy

**MANDATORY TESTING REQUIREMENTS: All Tests Must Pass Before Proceeding**

**Current Testing Approach:**
1. **Deploy-First Testing**: Deploy to Lambda first, then test deployed endpoints
2. **Lambda Deployment Testing**: Both MCP and REST API endpoints must work in deployed Lambda
3. **Failure Policy**: If ANY test fails (Lambda MCP or Lambda API), the ENTIRE test suite is considered failed
4. **No Partial Success**: We will NOT proceed with further development until ALL tests pass
5. **Fix Before Proceed**: All test failures must be resolved before moving to next steps

**Testing Protocol:**
```bash
# 1. Deploy to Lambda first
./deploy.sh dev --clean --test

# 2. Test comprehensive function coverage (REQUIRED)
TEST_WALLET_ADDRESS="user_provided_address" uv run python scripts/test_function_coverage.py --mcp-url <url> --rest-url <url>
```

**Critical Testing Requirements:**
- **Always use the MCP test client** for comprehensive testing, not constructed JSON-RPC calls
- **If MCP test client tests fail, the overall test FAILS** regardless of other tests
- The MCP test client validates both MCP and REST protocols return matching data

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
```

## 🤖 FOR NEW CLAUDE INSTANCES: Quick Takeover Guide

**If you're a new Claude instance taking over this project, here's what you need to know:**

### ✅ Current Status (July 29, 2025)
- **Project is COMPLETE and PRODUCTION-READY**
- **Both dev and production environments are fully functional**
- **CSV-driven protocol management with 16 production tools**

### 🚀 Immediate Actions Available
1. **Test Current Deployments**: Use URLs above to verify everything works
2. **Run Test Suite**: `TEST_WALLET_ADDRESS="user_provided_address" uv run python scripts/test_function_coverage.py --mcp-url <url> --rest-url <url>`
3. **Deploy to Dev**: `./deploy.sh dev --clean --test`
4. **Deploy to Production**: Only deploy to main branch with user approval

### 🔑 Critical Files to Understand
- **`template-unified.yaml`**: THE deployment template (only one to use)
- **`lambda_handler_unified.py`**: Unified Lambda handler with native MCP support
- **`scripts/test_function_coverage.py`**: Comprehensive testing script
- **`function_protocols_prod.csv`**: Production function configuration
- **`src/functions/`**: All business logic functions with @api_function decorator

### 🚨 Critical Constraints
- **NEVER change function names** without explicit user approval
- **ALWAYS use unified Lambda architecture** (single function with protocol routing)
- **ALWAYS test before deployment** (both protocols must have 100% success)
- **ALWAYS use `template-unified.yaml`** for deployments
- **NEVER commit real wallet addresses** to git

### 🎯 Success Metrics to Maintain
- **MCP Protocol**: Must achieve 100% success rate (16/16 tools in production)
- **REST API**: Must achieve 100% success rate (21/21 endpoints)  
- **Overall Functions**: Must achieve 80%+ success rate (accounts for real-time data differences)
- **Data Equivalence**: MCP and REST must return equivalent data structures

## 🔄 Code & Deployment Lifecycle (MANDATORY PROCESS)

**⚠️ CRITICAL: Follow this exact workflow for ALL development and deployment activities.**

### 🚨 **1. Development Phase**

**Always use `uv` for Python operations:**
```bash
# ✅ CORRECT: Always use uv
uv run python scripts/mcp_test_client.py --test
uv run python scripts/test_function_coverage.py
uv run pytest tests/

# ❌ WRONG: Never use python directly
python scripts/mcp_test_client.py  # FORBIDDEN
pytest tests/                      # FORBIDDEN
```

### 🚨 **2. Deployment Phase**

**Use automated deployment script (MANDATORY):**
```bash
# Standard development deployment
./deploy.sh dev --clean --test

# Production deployment (main branch only)
./deploy.sh prod --clean --test

# Skip version check if needed
./deploy.sh dev --clean --test --skip-check
```

**Deployment automatically includes:**
- ✅ Dependency checking (AWS CLI, SAM CLI, uv)
- ✅ Git version tracking (commit hash + branch tags in CloudFormation)
- ✅ Certificate validation
- ✅ Clean build from scratch
- ✅ Comprehensive testing (MCP + REST protocols)
- ✅ Smart version checking (skips if no changes)

### 🚨 **3. Post-Deployment Verification**

**MANDATORY: Verify deployment with proper tools:**
```bash
# Test MCP endpoint (NEVER use curl!)
uv run python scripts/mcp_test_client.py --mcp-url "https://pb-fm-mcp-dev.creativeapptitude.com/mcp" --test

# Test comprehensive function coverage (with user-provided wallet)
TEST_WALLET_ADDRESS="user_provided_address" uv run python scripts/test_function_coverage.py \
  --mcp-url "https://pb-fm-mcp-dev.creativeapptitude.com/mcp" \
  --rest-url "https://pb-fm-mcp-dev.creativeapptitude.com"
```

### 🚨 **4. Git Lifecycle (MANDATORY)**

**After EVERY successful deployment:**
```bash
# 1. Commit all changes
git add .
git commit -m "🚀 Feature: Brief description

- Detailed changes
- Test results
- Deployment verified

🎯 Generated with Claude Code (https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 2. Create deployment tag
git tag -a "deploy-$(date +%Y-%m-%d)-$(git rev-list --count HEAD)" -m "Deployment: $(date)"

# 3. Push everything
git push origin $(git rev-parse --abbrev-ref HEAD)
git push origin --tags
```

### 🚨 **5. Security Requirements**

**NEVER commit sensitive data:**
- ❌ Real wallet addresses in any file
- ❌ API keys or secrets  
- ❌ Production credentials
- ✅ Use environment variables at runtime only

## 🛠️ Build and Test Quick Reference

**🚀 AUTOMATED DEPLOYMENT (RECOMMENDED):**
```bash
# Development deployment with testing (single command does everything!)
./deploy.sh dev --clean --test

# Production deployment (requires main branch)
./deploy.sh prod --clean --test

# Deploy without custom domain
./deploy.sh dev --no-domain

# Force deployment (bypass branch checks)
./deploy.sh dev --force

# Show deployment script options
./deploy.sh --help
```

**Success Criteria:**
- ✅ MCP Protocol: 100% success (16/16 tools in production)
- ✅ REST API: 100% success (21/21 endpoints)  
- ✅ Overall: 80%+ success (17+/21 functions)

### 🚨 CRITICAL: Always Clean Before Building

**ALWAYS clean build artifacts before every SAM build to prevent poisoned builds:**

```bash
# ✅ CORRECT: Clean before every build
rm -rf .aws-sam/
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
sam build --template-file template-unified.yaml

# ❌ WRONG: Building without cleaning (leads to internal server errors)
sam build --template-file template-unified.yaml
```

**Why This Matters:**
- Previous builds can leave corrupted artifacts in `.aws-sam/` directory
- Python bytecode files can conflict between different commits
- "Internal server error" issues are often caused by poisoned build cache
- Fresh builds from clean state eliminate mysterious deployment failures

## 🤖 Claude.ai MCP Configuration

To configure this MCP server with Claude.ai, use these **STABLE CUSTOM DOMAIN URLs** (never change):

### 🚀 Development Server (Latest Features)
```
MCP Server URL: https://pb-fm-mcp-dev.creativeapptitude.com/mcp
```

### 🏆 Production Server (Stable Release)
```
MCP Server URL: https://pb-fm-mcp.creativeapptitude.com/mcp
```

### Steps to Add to Claude.ai:
1. Go to Claude.ai settings
2. Navigate to MCP Servers or External Tools
3. Add new MCP server with the URL above
4. Test connection - it should discover 16 MCP tools (production) or 62 tools (development)
5. Tools include blockchain data, account info, delegation data, and market information

### Available MCP Tools:
**Blockchain & Market Data (16 core production tools):**
- `fetch_current_hash_statistics` - Blockchain statistics
- `fetch_account_info` - Wallet account information  
- `fetch_total_delegation_data` - Staking/delegation data
- `fetch_current_fm_data` - Figure Markets exchange data
- `fetch_complete_wallet_summary` - Comprehensive wallet analysis
- `fetch_market_overview_summary` - Complete market overview
- And 10 more specialized tools for blockchain and exchange data

**✨ Recommendation**: Use the custom domain URLs for permanent integrations - they never change with deployments!

## 🗂️ KEY FILES FOR UNIFIED LAMBDA ARCHITECTURE

### Critical Implementation Files

1. **`template-unified.yaml`** - ✅ THE ONLY TEMPLATE TO USE
   - Defines single Lambda function with AWS Web Adapter
   - Configures unified routing for both MCP and REST protocols
   - **ALWAYS use this for deployments**

2. **`lambda_handler_unified.py`** - Unified Lambda Handler
   - Single Lambda handler supporting both MCP and REST protocols
   - Uses native AWS MCP Handler for MCP protocol compliance
   - Uses AWS Lambda Web Adapter for REST API support

3. **`function_protocols_prod.csv`** - Production Configuration
   - Defines which functions are exposed via MCP protocol in production
   - Automated synchronization with function decorators via deploy script
   - Separate dev/prod configurations for environment isolation

4. **`src/functions/`** - All business logic functions with @api_function decorator
   - Protocol assignment controlled by CSV configuration
   - Automatic registry building and MCP tool exposure

### Templates Status

- **✅ Current Template**: `template-unified.yaml` (ONLY template to use)
- **❌ Deleted Templates**: All other templates have been removed for clarity
- **Architecture**: Single Lambda function with unified protocol handling

## 🚨 DEPLOYMENT ENVIRONMENTS

**Current Deployment Status (July 29, 2025):**

**Production Environment**: `pb-fm-mcp-v2` stack (STABLE - Used by colleagues and external integrations)
- **🔧 MCP Endpoint**: `https://pb-fm-mcp.creativeapptitude.com/mcp` ✅
- **🌐 REST API**: `https://pb-fm-mcp.creativeapptitude.com/api/*` ✅
- **📖 Documentation**: `https://pb-fm-mcp.creativeapptitude.com/docs` ✅
- **Deploy Command**: `./deploy.sh prod --clean --test`
- **Deploy Branch**: `main` branch ONLY, when explicitly requested
- **Status**: ✅ 100% MCP protocol success (16/16 tools)

**Development Environment**: `pb-fm-mcp-dev` stack (ACTIVE - For testing new features)
- **🔧 MCP Endpoint**: `https://pb-fm-mcp-dev.creativeapptitude.com/mcp` ✅
- **🌐 REST API**: `https://pb-fm-mcp-dev.creativeapptitude.com/api/*` ✅  
- **📖 Documentation**: `https://pb-fm-mcp-dev.creativeapptitude.com/docs` ✅
- **Deploy Command**: `./deploy.sh dev --clean --test`
- **Deploy Branch**: `dev` branch for all development work  
- **Status**: ✅ 100% MCP protocol success, all development functions available

**🔒 Both environments are fully functional and production-ready with unified Lambda architecture.**

## 🚨 IMPORTANT: Always use `uv` for Python execution
**ALWAYS use `uv run python` instead of `python` or `python3` for all Python scripts and commands.**

## AWS Lambda Development (Current)

**🚀 AUTOMATED DEPLOYMENT SCRIPT (HIGHLY RECOMMENDED):**

We now have a comprehensive `deploy.sh` script that automates the entire deployment process with:

✅ **Automatic Dependency Checks:**
- AWS CLI, SAM CLI, uv availability
- Certificate validation
- Route 53 hosted zone verification
- Git branch validation

✅ **Smart Certificate Management:**
- Uses known certificate ARN for `creativeapptitude.com`
- Validates certificate exists and is valid
- Falls back gracefully if domain setup fails

✅ **Reliable Build Process:**
- Automatic clean build (prevents poisoned builds)
- Uses `template-unified.yaml` (unified Lambda architecture)
- Includes Lambda size management

✅ **Comprehensive Testing:**
- Tests both API Gateway and custom domain endpoints
- Runs function coverage tests with `uv`
- Validates MCP and REST API functionality

**🔒 Security Features:**
- Never hardcodes wallet addresses
- Requires `TEST_WALLET_ADDRESS` environment variable for testing
- Validates git branch before production deployments
- Includes rollback guidance

## Important Instructions (Keep All)

- Do what has been asked; nothing more, nothing less.
- NEVER create files unless they're absolutely necessary for achieving your goal.
- ALWAYS prefer editing an existing file to creating a new one.
- NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

**IMPORTANT: this context may or may not be relevant to your tasks. You should not respond to this context unless it is highly relevant to your task.**