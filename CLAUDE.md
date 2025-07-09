# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Development and Testing
- **Development**: `uv run pywrangler dev` - Run the worker locally for development
- **Testing**: `uv run pytest tests` - Run the test suite
- **Linting**: `uv ruff check .` - Check for linting issues
- **Formatting**: `uv ruff format . --check` - Check code formatting

### Deployment
- **Deploy**: `uv run pywrangler deploy` - Deploy the worker to Cloudflare Workers

### Testing Endpoints
- **Local**: Connect to `http://localhost:8787/mcp/` during development
- **Production**: Connect to `https://hastra-fm-mcp.frank-siebenlist.workers.dev/mcp` after deployment

## Project Architecture

This is a Python-based MCP (Model Context Protocol) server that runs on Cloudflare Workers, providing tools for interacting with the Figure Markets exchange and Provenance Blockchain.

### Core Components

- **`src/worker.py`** - Main entry point and MCP server setup using FastMCP
- **`src/hastra.py`** - Core business logic for blockchain and exchange operations
- **`src/utils.py`** - Utility functions for datetime, HTTP requests, and amount/denomination operations
- **`src/exceptions.py`** - HTTP exception handling for Starlette framework

### Key Architecture Details

1. **FastMCP Framework**: Uses FastMCP for MCP server implementation with HTTP streaming support
2. **Async HTTP Client**: All external API calls use httpx with proper timeout and error handling
3. **Error Handling**: Standardized error responses with "MCP-ERROR" key for failed operations
4. **Amount/Denomination Types**: Custom utilities for handling blockchain token amounts with proper denomination validation
5. **Cloudflare Workers**: Deployed using workers-py with Python 3.12 compatibility

### MCP Tools Structure

The server exposes numerous tools for:
- **Account Management**: Fetching account info, balances, and vesting details
- **Delegation Operations**: Staking, rewards, unbonding, and redelegation data
- **Market Data**: Trading pairs, prices, and asset information
- **Blockchain Stats**: HASH token statistics and network information

### Dependencies

- **Production**: `mcp`, `structlog`
- **Development**: `workers-py`, `pytest`, `requests`, `pytest-asyncio`, `ruff`
- **External APIs**: Figure Markets exchange API and Provenance blockchain explorer API

### Configuration

- **Python Version**: 3.12 (strict)
- **Ruff**: Line length 100, uses modern Python features (pycodestyle, flake8-bugbear, isort, etc.)
- **Pytest**: Async support with session-scoped event loop
- **Cloudflare**: Uses python_workers compatibility flag

### Development Notes

- The codebase interacts with external APIs for blockchain and exchange data
- All network operations include proper timeout and error handling
- The server runs stateless HTTP mode for compatibility with Cloudflare Workers
- IDE integration: Use `.venv-workers/bin/python` as interpreter for proper autocompletion