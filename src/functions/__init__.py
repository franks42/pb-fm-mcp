"""
Business Functions for pb-fm-mcp

This module contains all business logic functions organized by domain.
Each function is decorated with @api_function to be automatically exposed
via both MCP and REST protocols.
"""

# Import function modules to trigger decorator registration
try:
    from . import stats_functions
except Exception as e:
    print(f"❌ Failed to import stats_functions: {e}")

try:
    from . import delegation_functions
except Exception as e:
    print(f"❌ Failed to import delegation_functions: {e}")

try:
    from . import blockchain_functions
except Exception as e:
    print(f"❌ Failed to import blockchain_functions: {e}")

# TODO: Import other modules as we create them
# from . import market_functions

__all__ = [
    "stats_functions",
    "delegation_functions",
    "blockchain_functions",
]