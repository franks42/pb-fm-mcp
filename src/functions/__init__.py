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
    from .webui_functions import conversation_functions
    from .webui_functions import interface_functions
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

try:
    from . import declarative_dashboard
except Exception as e:
    print(f"❌ Failed to import declarative_dashboard: {e}")

try:
    from . import dashboard_coordinator
except Exception as e:
    print(f"❌ Failed to import dashboard_coordinator: {e}")

try:
    from . import sqs_traffic_light
except Exception as e:
    print(f"❌ Failed to import sqs_traffic_light: {e}")

try:
    from . import ai_terminal
except Exception as e:
    print(f"❌ Failed to import ai_terminal: {e}")

try:
    from . import event_store
except Exception as e:
    print(f"❌ Failed to import event_store: {e}")

try:
    from . import test_broken_decorator
except Exception as e:
    print(f"❌ Failed to import test_broken_decorator: {e}")

try:
    from . import test_decorator
except Exception as e:
    print(f"❌ Failed to import test_decorator: {e}")

try:
    from . import version_functions
except Exception as e:
    print(f"❌ Failed to import version_functions: {e}")

try:
    from . import webpage_session_management
except Exception as e:
    print(f"❌ Failed to import webpage_session_management: {e}")

try:
    from . import webpage_s3_helpers
except Exception as e:
    print(f"❌ Failed to import webpage_s3_helpers: {e}")

try:
    from . import webpage_queue_management
except Exception as e:
    print(f"❌ Failed to import webpage_queue_management: {e}")

try:
    from . import webpage_orchestration
except Exception as e:
    print(f"❌ Failed to import webpage_orchestration: {e}")

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
    "declarative_dashboard",
    "dashboard_coordinator",
    "sqs_traffic_light",
    "ai_terminal",
    "webpage_session_management",
    "webpage_s3_helpers", 
    "webpage_queue_management",
    "webpage_orchestration",
]
