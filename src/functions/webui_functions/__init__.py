"""
Web UI Functions for Heartbeat Conversation Pattern

This module provides functions for managing conversational interface between 
Claude.ai and web interface through HTTP polling message queue system with 
complete session isolation.

All functions are decorated with @api_function to be automatically exposed 
via MCP and/or REST protocols.
"""

from .conversation_functions import (
    create_new_session,
    queue_user_message,
    get_pending_messages,
    send_response_to_web,
    get_latest_response,
    get_conversation_status,
    cleanup_inactive_sessions
)

from .interface_functions import (
    serve_conversation_interface
)

__all__ = [
    'create_new_session',
    'queue_user_message',
    'get_pending_messages',
    'send_response_to_web',
    'get_latest_response',
    'get_conversation_status',
    'cleanup_inactive_sessions',
    'serve_conversation_interface'
]