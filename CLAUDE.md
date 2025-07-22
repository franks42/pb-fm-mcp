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

- **`lambda_handler.py`** - Main AWS Lambda function with dual MCP+REST API setup
- **`async_wrapper.py`** - Decorators for async function compatibility with AWS MCP handler
- **`src/hastra.py`** - Core business logic for blockchain and exchange operations
- **`src/utils.py`** - Utility functions for datetime, HTTP requests, and operations
- **`src/base64expand.py`** - Base64 data expansion utilities (ready for integration)
- **`src/jqpy/`** - Complete jq-like JSON processor (162/193 tests passing, core functionality solid)

### Dual-Protocol AWS Lambda Architecture

1. **Path-Based Routing**: `/mcp` for MCP protocol, `/api/*` for REST endpoints, `/docs` for documentation
2. **MCPLambdaHandler**: AWS Labs MCP Lambda handler for MCP protocol transport  
3. **FastAPI + Mangum**: REST API with automatic OpenAPI documentation and CORS
4. **Async Thread Pool**: All endpoints use proper async patterns with thread pool execution
5. **API Gateway Integration**: Single deployment supporting both protocols
6. **CloudFormation/SAM**: Infrastructure as Code deployment

### MCP Tools Structure

The server exposes numerous tools for:
- **Account Management**: Fetching account info, balances, and vesting details
- **Delegation Operations**: Staking, rewards, unbonding, and redelegation data
- **Market Data**: Trading pairs, prices, and asset information
- **Blockchain Stats**: HASH token statistics and network information

### Dependencies

- **Production**: `awslabs-mcp-lambda-handler`, `httpx`, `structlog`, `fastapi`, `mangum`
- **Development**: `pytest`, `pytest-asyncio`, `ruff` (managed via uv)
- **External APIs**: Figure Markets exchange API and Provenance blockchain explorer API

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

### Flat API Structure Rationale
**MCP Protocol Constraint**: MCP tool functions require a flat naming structure with no namespace hierarchy support. Function names like `fetchAccountInfo` or `fetchDelegatedRewardsAmount` cannot be organized into namespaces like `account.fetchInfo` or `delegation.fetchRewards`.

**Design Decision**: To maintain perfect 1:1 mapping between MCP tools and REST endpoints, we use a flat API structure:
- **MCP Function**: `fetch_delegated_rewards_amount` 
- **REST Endpoint**: `/api/delegated_rewards_amount/{wallet_address}`
- **Response Key**: `delegated_rewards_amount`

This eliminates any impedance mismatch between protocols and creates a clean data dictionary where function names directly correspond to API paths and response keys.

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
- `docs/development_roadmap.md` - Architecture vision and todo priorities  
- `docs/testing-deploying-setup.md` - Complete testing and deployment workflows
- `lambda_handler.py` - Dual MCP+REST API implementation
- `src/jqpy/` - JSON processing capabilities (162/193 tests passing)
- `src/base64expand.py` - Data expansion utilities

### Testing & Deployment
- **Local**: `sam build && sam local start-api --port 3000`
- **Production**: `sam build && sam deploy --resolve-s3`
- **MCP Testing**: `npx @modelcontextprotocol/inspector http://localhost:3000/mcp`
- **REST Testing**: Browser access to documentation and endpoints

### Architecture Status
✅ **Dual APIs**: Both MCP protocol and REST endpoints working  
✅ **Documentation**: Full OpenAPI docs with external Swagger UI integration  
✅ **CORS**: Cross-origin access enabled for browser compatibility  
✅ **Async**: Proper async patterns with thread pool execution  
✅ **Production**: Stable deployment with fast response times
✅ **Environment Separation**: Production and development stacks isolated
✅ **Quality Assurance**: Comprehensive equivalence testing (91% pass rate)
✅ **Security**: Environment variable protection for sensitive data
✅ **Data Standardization**: Consistent asset amount formats

**Current Status**: Production-ready dual-protocol server with unified registry architecture, comprehensive system operations, version management, cross-server testing capabilities, and fully resolved async issues. Latest version v0.1.5 deployed to dev environment with 21 functions (16 MCP tools, 19 REST endpoints).