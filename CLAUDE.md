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

### AWS Lambda Development (Current)
- **Local Testing**: `sam build && sam local start-api --port 3000`
- **Deploy Production**: `sam build && sam deploy --resolve-s3`
- **Testing**: `uv run pytest tests/test_base64expand.py tests/test_jqpy/test_core.py` (core tests pass)
- **Linting**: `uv ruff check .`

### Production Endpoints (STABLE - Used by colleagues)
- **MCP Protocol**: `https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp`
- **REST API**: `https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/api/*`
- **Documentation**: `https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/docs`
- **OpenAPI Spec**: `https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/openapi.json`

### Development Endpoints (TO BE CREATED)
- **Dev MCP Protocol**: `https://[DEV-GATEWAY]/Prod/mcp` (for testing new features)
- **Dev REST API**: `https://[DEV-GATEWAY]/Prod/api/*` (for development)
- **Local Testing**: `http://localhost:3000/*` (all endpoints)

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
2. **Production Deployment**: Stable AWS Lambda with 13 MCP tools
3. **Dual API Implementation**: MCP + REST protocols in single Lambda deployment
4. **Full Documentation**: Working /docs endpoint with external Swagger UI integration
5. **CORS & Async**: Proper async patterns and CORS for browser compatibility
6. **Local Testing**: SAM environment with Docker
7. **Code Preservation**: jqpy (JSON processor) and base64expand ready for integration

### Current Development Focus
**Phase 1 Complete**: Dual API architecture (MCP + REST) successfully implemented ✅

**CRITICAL NEXT**: Production/Development Environment Separation
- Create separate endpoints for production (stable) and development (testing)
- Implement git branch strategy: `main` for production, `dev` for active development
- Separate SAM stack deployments to prevent breaking colleagues' Claude integrations

**Phase 2**: Unified Function Registry Architecture
- Decorator-based function registry with `@api_function` for auto-generation
- Modular business function structure in domain-specific files
- Auto-generate both MCP tools and REST endpoints from single function definitions
- Full typing system with automatic validation and OpenAPI schema generation

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

**Current Status**: Production-ready dual-protocol server with comprehensive documentation.

⚠️ **CRITICAL**: Need to separate production and development environments before major refactoring to avoid breaking colleagues' Claude integrations.