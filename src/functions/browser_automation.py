"""
Browser Automation Functions for AI-Controlled Dashboard Interaction

This module provides MCP functions that simulate browser interactions.
All functions return mock responses as browser automation is not available in Lambda environment.
"""

import uuid
from datetime import datetime
from typing import Dict, Optional

from registry import api_function
from utils import JSONType


class MockBrowserSession:
    """Mock browser session for simulating browser interactions."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.current_url = None
        self.page_title = "Mock Page"
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
    
    def is_expired(self, timeout_minutes: int = 10) -> bool:
        """Check if session has expired."""
        return (datetime.now() - self.last_activity).total_seconds() > (timeout_minutes * 60)


# Global session manager
_browser_sessions: Dict[str, MockBrowserSession] = {}


def get_or_create_session(session_id: str = None) -> MockBrowserSession:
    """Get existing session or create new one."""
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    # Clean up expired sessions
    expired_sessions = [sid for sid, session in _browser_sessions.items() 
                       if session.is_expired()]
    for sid in expired_sessions:
        del _browser_sessions[sid]
    
    # Get or create session
    if session_id not in _browser_sessions:
        _browser_sessions[session_id] = MockBrowserSession(session_id)
    
    session = _browser_sessions[session_id]
    session.update_activity()
    return session


@api_function(
    protocols=[],
    description="Navigate browser to specified URL - returns mock response"
)
async def browser_navigate(
    url: str,
    session_id: str = None,
    wait_for_load: bool = True,
    timeout_seconds: int = 30
) -> JSONType:
    """Navigate browser to URL - returns mock response."""
    session = get_or_create_session(session_id)
    session.current_url = url
    session.page_title = f"Mock Page - {url}"
    
    return {
        'success': False,
        'error': 'Browser automation not available in this environment',
        'mock_response': True,
        'message': f'Would navigate to: {url}',
        'session_id': session.session_id
    }


@api_function(
    protocols=[],
    description="Take screenshot of browser page - returns mock response"
)
async def browser_screenshot(
    session_id: str = None,
    full_page: bool = True,
    element_selector: str = None,
    context: str = "AI debugging"
) -> JSONType:
    """Take screenshot - returns mock response."""
    return {
        'success': False,
        'error': 'Browser automation not available',
        'mock_response': True,
        'message': 'Would take screenshot',
        'context': context
    }


@api_function(
    protocols=[],
    description="Click element on page - returns mock response"
)
async def browser_click(
    selector: str,
    session_id: str = None,
    wait_timeout: int = 10,
    force: bool = False
) -> JSONType:
    """Click element - returns mock response."""
    return {
        'success': False,
        'error': 'Browser automation not available',
        'mock_response': True,
        'message': f'Would click element: {selector}'
    }


@api_function(
    protocols=[],
    description="Type text into input field - returns mock response"
)
async def browser_type(
    selector: str,
    text: str,
    session_id: str = None,
    clear_first: bool = True,
    wait_timeout: int = 10
) -> JSONType:
    """Type text - returns mock response."""
    return {
        'success': False,
        'error': 'Browser automation not available',
        'mock_response': True,
        'message': f'Would type "{text}" into {selector}'
    }


@api_function(
    protocols=[],
    description="Get text content of element - returns mock response"
)
async def browser_get_text(
    selector: str,
    session_id: str = None,
    wait_timeout: int = 10
) -> JSONType:
    """Get text - returns mock response."""
    return {
        'success': False,
        'error': 'Browser automation not available',
        'mock_response': True,
        'message': f'Would get text from: {selector}'
    }


@api_function(
    protocols=[],
    description="Execute JavaScript code - returns mock response"
)
async def browser_execute_javascript(
    javascript_code: str,
    session_id: str = None
) -> JSONType:
    """Execute JavaScript - returns mock response."""
    return {
        'success': False,
        'error': 'Browser automation not available',
        'mock_response': True,
        'message': f'Would execute JavaScript: {javascript_code[:100]}...'
    }


@api_function(
    protocols=[],
    description="Wait for element to appear - returns mock response"
)
async def browser_wait_for_element(
    selector: str,
    session_id: str = None,
    state: str = "visible",
    timeout_seconds: int = 30
) -> JSONType:
    """Wait for element - returns mock response."""
    return {
        'success': False,
        'error': 'Browser automation not available',
        'mock_response': True,
        'message': f'Would wait for {selector} to be {state}'
    }


@api_function(
    protocols=[],
    description="Close browser session - returns mock response"
)
async def browser_close_session(
    session_id: str = None
) -> JSONType:
    """Close session - returns mock response."""
    if session_id and session_id in _browser_sessions:
        del _browser_sessions[session_id]
        return {
            'success': True,
            'session_id': session_id,
            'message': 'Mock browser session closed',
            'mock_response': True
        }
    else:
        return {
            'success': False,
            'error': 'Session not found',
            'session_id': session_id,
            'mock_response': True
        }


@api_function(
    protocols=[],
    description="Get current page information - returns mock response"
)
async def browser_get_page_info(
    session_id: str = None
) -> JSONType:
    """Get page info - returns mock response."""
    if session_id and session_id in _browser_sessions:
        session = _browser_sessions[session_id]
        return {
            'success': True,
            'session_id': session.session_id,
            'title': session.page_title,
            'url': session.current_url or 'about:blank',
            'mock_response': True,
            'session_created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat()
        }
    else:
        return {
            'success': False,
            'error': 'No active browser session',
            'mock_response': True
        }