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

try:
    from . import figure_markets_functions
except Exception as e:
    print(f"❌ Failed to import figure_markets_functions: {e}")

try:
    from . import aggregate_functions
except Exception as e:
    print(f"❌ Failed to import aggregate_functions: {e}")

try:
    from . import system_functions
except Exception as e:
    print(f"❌ Failed to import system_functions: {e}")

try:
    from . import webui_functions
except Exception as e:
    print(f"❌ Failed to import webui_functions: {e}")

try:
    from . import visualization_functions
except Exception as e:
    print(f"❌ Failed to import visualization_functions: {e}")

try:
    from . import browser_automation
except Exception as e:
    print(f"❌ Failed to import browser_automation: {e}")

try:
    from . import dynamic_visualization
except Exception as e:
    print(f"❌ Failed to import dynamic_visualization: {e}")

try:
    from . import debug_functions
except Exception as e:
    print(f"❌ Failed to import debug_functions: {e}")

__all__ = [
    "stats_functions",
    "delegation_functions", 
    "blockchain_functions",
    "figure_markets_functions",
    "aggregate_functions",
    "system_functions",
    "webui_functions",
    "visualization_functions",
    "browser_automation",
    "dynamic_visualization",
    "debug_functions",
]