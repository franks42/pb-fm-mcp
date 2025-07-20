# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 IMPORTANT: Project Status Update (July 2025)

**This project has been MIGRATED from Cloudflare Workers to AWS Lambda due to Python compatibility issues.**

### Current State
- ✅ **Production**: AWS Lambda deployment working perfectly
- ✅ **Local Testing**: SAM local environment configured
- ✅ **Documentation**: Complete testing and deployment guides in `docs/`
- ✅ **Architecture**: Ready for dual API expansion (MCP + REST)

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

### Production Endpoints
- **Local**: `http://localhost:3000/mcp`
- **Production**: `https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod/mcp`

## Project Architecture

This is a Python-based MCP (Model Context Protocol) server running on **AWS Lambda**, providing tools for interacting with Figure Markets exchange and Provenance Blockchain.

### Core Components

- **`lambda_handler.py`** - Main AWS Lambda function with MCP server setup
- **`async_wrapper.py`** - Decorators for async function compatibility with AWS MCP handler
- **`src/hastra.py`** - Core business logic for blockchain and exchange operations
- **`src/utils.py`** - Utility functions for datetime, HTTP requests, and operations
- **`src/base64expand.py`** - Base64 data expansion utilities (ready for integration)
- **`src/jqpy/`** - Complete jq-like JSON processor (162/193 tests passing, core functionality solid)

### AWS Lambda Architecture

1. **MCPLambdaHandler**: Uses AWS Labs MCP Lambda handler for HTTP transport
2. **Async Wrapper Pattern**: `@async_to_sync_mcp_tool` decorators enable async functions
3. **API Gateway Integration**: HTTP endpoints with CORS support
4. **CloudFormation/SAM**: Infrastructure as Code deployment

### MCP Tools Structure

The server exposes numerous tools for:
- **Account Management**: Fetching account info, balances, and vesting details
- **Delegation Operations**: Staking, rewards, unbonding, and redelegation data
- **Market Data**: Trading pairs, prices, and asset information
- **Blockchain Stats**: HASH token statistics and network information

### Dependencies

- **Production**: `awslabs-mcp-lambda-handler`, `httpx`, `structlog`
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
3. **Local Testing**: SAM environment with Docker
4. **Code Preservation**: jqpy (JSON processor) and base64expand ready for integration
5. **Documentation**: Complete testing/deployment guides

### Current Development Focus
**Next Phase**: Dual API architecture (MCP + REST) with proxy layer refactoring

**Key Files to Review:**
- `docs/development_roadmap.md` - Architecture vision and todo priorities  
- `docs/testing-deploying-setup.md` - Complete testing and deployment workflows
- `lambda_handler.py` - Current MCP server implementation
- `src/jqpy/` - JSON processing capabilities (162/193 tests passing)
- `src/base64expand.py` - Data expansion utilities

### Testing & Deployment
- **Local**: `sam build && sam local start-api --port 3000`
- **Production**: `sam build && sam deploy --resolve-s3`
- **MCP Testing**: `npx @modelcontextprotocol/inspector http://localhost:3000/mcp`

### Architecture Goals
1. **Proxy Layer**: Separate async PB-API calls from MCP tool logic
2. **Dual APIs**: Expose both MCP protocol and REST endpoints
3. **jqpy Integration**: Add dynamic JSON transformation capabilities
4. **Standardization**: Clean data transformation layer

**Status**: Ready for proxy layer refactoring and dual API implementation.