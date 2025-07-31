#!/usr/bin/env python3
"""
Function Deployment Discrepancy Analysis
Compares expected CSV functions with actual deployed functions
"""

# Expected MCP Functions (71 total from CSV with MCP=YES)
expected_mcp = {
    "ai_terminal_conversation", "analyze_mcp_request_context", "browser_click", 
    "browser_close_session", "browser_execute_javascript", "browser_get_page_info", 
    "browser_get_text", "browser_navigate", "browser_screenshot", "browser_type", 
    "browser_wait_for_element", "check_screenshot_requests", "claude_take_screenshot", 
    "create_debug_dashboard", "create_example_dashboard", "create_hash_price_chart", 
    "create_layout_variant", "create_personalized_dashboard", "declare_chart_data", 
    "declare_dashboard_layout", "declare_plotly_charts", "download_screenshot", 
    "experiment_gauge_styles", "fetch_account_info", "fetch_account_is_vesting", 
    "fetch_available_committed_amount", "fetch_complete_wallet_summary", 
    "fetch_current_fm_data", "fetch_current_hash_statistics", 
    "fetch_figure_markets_assets_info", "fetch_last_crypto_token_price", 
    "fetch_market_overview_summary", "fetch_session_events", 
    "fetch_total_delegation_data", "fetch_vesting_total_unvested_amount", 
    "get_ai_terminal_status", "get_ai_terminal_url", "get_browser_connection_order", 
    "get_conversation_status", "get_dashboard_info", "get_pending_messages", 
    "get_registry_introspection", "get_registry_summary", "get_system_context", 
    "get_traffic_light_status", "mcp_test_server", "mcp_warmup_ping", 
    "optimize_chart_colors", "queue_user_message", "send_response_to_browser", 
    "send_response_to_web", "send_result_to_browser_and_fetch_new_instruction", 
    "set_dashboard_coordinates", "start_realtime_conversation", 
    "switch_dashboard_layout", "take_screenshot", "test_session_persistence", 
    "trigger_browser_screenshot", "update_chart_config", "upload_screenshot", 
    "wait_for_user_input", "create_portfolio_health", 
    "fetch_current_fm_account_balance_data", "fetch_current_fm_account_info", 
    "get_system_status", "webpage_create_new_session", "webpage_create_session", 
    "webpage_get_session_status", "webpage_send_to_all_browsers", 
    "webpage_store_content", "webpage_update_hash_price_display"
}

# Deployed MCP Functions (69 total)
deployed_mcp = {
    "fetch_current_hash_statistics", "get_system_context", "fetch_account_info", 
    "fetch_account_is_vesting", "fetch_total_delegation_data", 
    "fetch_vesting_total_unvested_amount", "fetch_available_committed_amount", 
    "fetch_current_fm_data", "fetch_last_crypto_token_price", 
    "fetch_figure_markets_assets_info", "fetch_complete_wallet_summary", 
    "fetch_market_overview_summary", "get_registry_introspection", 
    "get_registry_summary", "mcp_warmup_ping", "mcp_test_server", 
    "queue_user_message", "get_pending_messages", "send_response_to_web", 
    "get_conversation_status", "create_personalized_dashboard", 
    "get_dashboard_info", "create_hash_price_chart", "create_portfolio_health", 
    "take_screenshot", "claude_take_screenshot", "upload_screenshot", 
    "trigger_browser_screenshot", "download_screenshot", "check_screenshot_requests", 
    "browser_navigate", "browser_screenshot", "browser_click", "browser_type", 
    "browser_get_text", "browser_execute_javascript", "browser_wait_for_element", 
    "browser_close_session", "browser_get_page_info", "update_chart_config", 
    "optimize_chart_colors", "experiment_gauge_styles", "analyze_mcp_request_context", 
    "create_debug_dashboard", "test_session_persistence", "declare_dashboard_layout", 
    "declare_plotly_charts", "declare_chart_data", "create_example_dashboard", 
    "set_dashboard_coordinates", "switch_dashboard_layout", "create_layout_variant", 
    "fetch_session_events", "get_browser_connection_order", "wait_for_user_input", 
    "send_response_to_browser", "get_traffic_light_status", 
    "send_result_to_browser_and_fetch_new_instruction", "start_realtime_conversation", 
    "ai_terminal_conversation", "get_ai_terminal_status", "get_ai_terminal_url", 
    "create_ai_terminal_session", "webpage_create_session", 
    "webpage_get_session_status", "webpage_store_content", 
    "webpage_send_to_all_browsers", "webpage_update_hash_price_display", 
    "webpage_create_new_session"
}

# Expected REST Functions (37 total from CSV with REST=YES)
expected_rest = {
    "get_dashboard_config", "get_dashboard_coordinates", 
    "fetch_delegated_redelegation_amount", "fetch_delegated_rewards_amount", 
    "fetch_delegated_staked_amount", "fetch_delegated_unbonding_amount", 
    "fetch_wallet_liquid_balance", "create_new_session", "get_latest_response", 
    "cleanup_inactive_sessions", "serve_conversation_interface", "get_version_info", 
    "get_system_status", "webpage_create_new_session", "webpage_create_session", 
    "webpage_get_session_status", "webpage_send_to_all_browsers", 
    "webpage_store_content", "webpage_update_hash_price_display",
    # Plus all the core functions that support both MCP and REST
    "fetch_current_hash_statistics", "get_system_context", "fetch_account_info", 
    "fetch_account_is_vesting", "fetch_total_delegation_data", 
    "fetch_vesting_total_unvested_amount", "fetch_available_committed_amount", 
    "fetch_current_fm_data", "fetch_last_crypto_token_price", 
    "fetch_figure_markets_assets_info", "fetch_complete_wallet_summary", 
    "fetch_market_overview_summary", "get_registry_introspection", 
    "get_registry_summary", "mcp_warmup_ping", "create_portfolio_health"
}

# Deployed REST Functions (32 total)
deployed_rest = {
    "fetch_current_hash_statistics", "get_system_context", "delegated_rewards_amount", 
    "delegated_staked_amount", "delegated_unbonding_amount", 
    "delegated_redelegation_amount", "fetch_account_info", "fetch_account_is_vesting", 
    "fetch_total_delegation_data", "fetch_vesting_total_unvested_amount", 
    "wallet_liquid_balance", "fetch_available_committed_amount", 
    "fetch_current_fm_data", "fetch_last_crypto_token_price", 
    "fetch_figure_markets_assets_info", "fetch_complete_wallet_summary", 
    "fetch_market_overview_summary", "get_registry_introspection", 
    "get_registry_summary", "mcp_warmup_ping", "create_new_session", 
    "get_latest_response", "cleanup_inactive_sessions", "create_portfolio_health", 
    "get_dashboard_config", "get_dashboard_coordinates", "webpage_create_session", 
    "webpage_get_session_status", "webpage_store_content", 
    "webpage_send_to_all_browsers", "webpage_update_hash_price_display", 
    "webpage_create_new_session"
}

def analyze_discrepancies():
    print("=" * 80)
    print("FUNCTION DEPLOYMENT DISCREPANCY ANALYSIS")
    print("=" * 80)
    
    print(f"\nExpected MCP Functions: {len(expected_mcp)}")
    print(f"Deployed MCP Functions: {len(deployed_mcp)}")
    print(f"Expected REST Functions: {len(expected_rest)}")
    print(f"Deployed REST Functions: {len(deployed_rest)}")
    
    # Find missing MCP functions
    missing_mcp = expected_mcp - deployed_mcp
    extra_mcp = deployed_mcp - expected_mcp
    
    print("\n" + "=" * 50)
    print("MISSING MCP FUNCTIONS (Expected but not deployed)")
    print("=" * 50)
    for func in sorted(missing_mcp):
        print(f"- {func}")
    
    print(f"\nTotal Missing MCP: {len(missing_mcp)}")
    
    # Find missing REST functions
    missing_rest = expected_rest - deployed_rest
    extra_rest = deployed_rest - expected_rest
    
    print("\n" + "=" * 50)
    print("MISSING REST FUNCTIONS (Expected but not deployed)")
    print("=" * 50)
    for func in sorted(missing_rest):
        print(f"- {func}")
    
    print(f"\nTotal Missing REST: {len(missing_rest)}")
    
    # Find naming discrepancies (functions that might have different names)
    print("\n" + "=" * 50)
    print("POTENTIAL NAMING DISCREPANCIES")
    print("=" * 50)
    
    # Check for functions with similar names but different prefixes
    naming_discrepancies = []
    
    # Check REST naming patterns
    rest_patterns = [
        ("fetch_delegated_rewards_amount", "delegated_rewards_amount"),
        ("fetch_delegated_staked_amount", "delegated_staked_amount"),
        ("fetch_delegated_unbonding_amount", "delegated_unbonding_amount"),
        ("fetch_delegated_redelegation_amount", "delegated_redelegation_amount"),
        ("fetch_wallet_liquid_balance", "wallet_liquid_balance"),
    ]
    
    for expected, deployed in rest_patterns:
        if expected in expected_rest and deployed in deployed_rest:
            naming_discrepancies.append((expected, deployed))
    
    if naming_discrepancies:
        for expected, deployed in naming_discrepancies:
            print(f"- Expected: '{expected}' → Deployed: '{deployed}'")
    else:
        print("No obvious naming discrepancies found.")
    
    # Extra functions (deployed but not expected)
    print("\n" + "=" * 50)
    print("EXTRA MCP FUNCTIONS (Deployed but not expected)")
    print("=" * 50)
    for func in sorted(extra_mcp):
        print(f"- {func}")
    
    print(f"\nTotal Extra MCP: {len(extra_mcp)}")
    
    print("\n" + "=" * 50)
    print("EXTRA REST FUNCTIONS (Deployed but not expected)")
    print("=" * 50)
    for func in sorted(extra_rest):
        print(f"- {func}")
    
    print(f"\nTotal Extra REST: {len(extra_rest)}")
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Missing MCP Functions: {len(missing_mcp)} (Expected: {len(expected_mcp)}, Deployed: {len(deployed_mcp)})")
    print(f"Missing REST Functions: {len(missing_rest)} (Expected: {len(expected_rest)}, Deployed: {len(deployed_rest)})")
    print(f"Extra MCP Functions: {len(extra_mcp)}")
    print(f"Extra REST Functions: {len(extra_rest)}")
    print(f"Naming Discrepancies: {len(naming_discrepancies)}")

if __name__ == "__main__":
    analyze_discrepancies()