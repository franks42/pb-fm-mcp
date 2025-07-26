"""
Browser Automation Functions for AI-Controlled Dashboard Interaction

This module provides MCP functions that enable Claude to control browser interactions
through Playwright, creating the first AI-driven browser automation system.
"""

import asyncio
import base64
import json
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Note: These imports would be added to requirements.txt for deployment
# playwright==1.40.0
# playwright-stealth==1.0.6

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Browser automation functions will return mock responses.")

from src.utils.api_utils import api_function, JSONType


class BrowserSession:
    """Manages a persistent browser session for AI interaction."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.playwright = None
    
    async def start(self):
        """Initialize browser session."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not available in this environment")
        
        self.playwright = await async_playwright().start()
        
        # Launch browser with optimal Lambda settings
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--single-process',
                '--disable-gpu'
            ]
        )
        
        # Create browser context
        self.context = await self.browser.new_context(
            viewport={'width': 1400, 'height': 900},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Create page
        self.page = await self.context.new_page()
        
        # Enable console log capture
        self.page.on('console', lambda msg: print(f"Browser console: {msg.text}"))
        
    async def cleanup(self):
        """Clean up browser resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Browser cleanup error: {e}")
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
    
    def is_expired(self, timeout_minutes: int = 10) -> bool:
        """Check if session has expired."""
        return (datetime.now() - self.last_activity).total_seconds() > (timeout_minutes * 60)


# Global session manager
_browser_sessions: Dict[str, BrowserSession] = {}


async def get_or_create_session(session_id: str = None) -> BrowserSession:
    """Get existing session or create new one."""
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    # Clean up expired sessions
    expired_sessions = [sid for sid, session in _browser_sessions.items() 
                       if session.is_expired()]
    for sid in expired_sessions:
        await _browser_sessions[sid].cleanup()
        del _browser_sessions[sid]
    
    # Get or create session
    if session_id not in _browser_sessions:
        session = BrowserSession(session_id)
        await session.start()
        _browser_sessions[session_id] = session
    
    session = _browser_sessions[session_id]
    session.update_activity()
    return session


@api_function(
    protocols=["mcp"],
    description="Navigate browser to specified URL - starts new browser session if needed"
)
async def browser_navigate(
    url: str,
    session_id: str = None,
    wait_for_load: bool = True,
    timeout_seconds: int = 30
) -> JSONType:
    """
    Navigate browser to URL and optionally wait for page load.
    
    This is typically the first function called to start browser automation.
    """
    
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'success': False,
            'error': 'Browser automation not available in this environment',
            'mock_response': True,
            'message': 'Would navigate to: ' + url
        }
    
    try:
        session = await get_or_create_session(session_id)
        
        # Navigate to URL
        if wait_for_load:
            await session.page.goto(url, wait_until='networkidle', timeout=timeout_seconds * 1000)
        else:
            await session.page.goto(url, timeout=timeout_seconds * 1000)
        
        # Get page info
        title = await session.page.title()
        current_url = session.page.url
        
        return {
            'success': True,
            'session_id': session.session_id,
            'url': current_url,
            'title': title,
            'message': f'Successfully navigated to {current_url}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Navigation failed: {str(e)}',
            'url': url
        }


@api_function(
    protocols=["mcp"],
    description="Take screenshot of current browser page with AI analysis context"
)
async def browser_screenshot(
    session_id: str = None,
    full_page: bool = True,
    element_selector: str = None,
    context: str = "AI debugging"
) -> JSONType:
    """
    Take screenshot of browser page for AI analysis.
    
    Can capture full page or specific element.
    """
    
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'success': False,
            'error': 'Browser automation not available',
            'mock_response': True
        }
    
    try:
        if session_id not in _browser_sessions:
            return {
                'success': False,
                'error': 'No active browser session. Call browser_navigate first.'
            }
        
        session = _browser_sessions[session_id]
        session.update_activity()
        
        # Take screenshot
        if element_selector:
            element = await session.page.locator(element_selector).first
            screenshot_bytes = await element.screenshot()
        else:
            screenshot_bytes = await session.page.screenshot(full_page=full_page)
        
        # Convert to base64
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode()
        
        # Get page context
        title = await session.page.title()
        url = session.page.url
        
        return {
            'success': True,
            'session_id': session.session_id,
            'screenshot_base64': screenshot_base64,
            'page_title': title,
            'page_url': url,
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'message': f'Screenshot captured of {url}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Screenshot failed: {str(e)}'
        }


@api_function(
    protocols=["mcp"],
    description="Click element on page by CSS selector"
)
async def browser_click(
    selector: str,
    session_id: str = None,
    wait_timeout: int = 10,
    force: bool = False
) -> JSONType:
    """
    Click an element on the page by CSS selector.
    
    Waits for element to be visible and clickable before clicking.
    """
    
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'success': False,
            'error': 'Browser automation not available',
            'mock_response': True,
            'message': f'Would click element: {selector}'
        }
    
    try:
        if session_id not in _browser_sessions:
            return {
                'success': False,
                'error': 'No active browser session. Call browser_navigate first.'
            }
        
        session = _browser_sessions[session_id]
        session.update_activity()
        
        # Wait for element and click
        element = session.page.locator(selector)
        await element.wait_for(state='visible', timeout=wait_timeout * 1000)
        
        if force:
            await element.click(force=True)
        else:
            await element.click()
        
        # Get element info
        element_text = await element.text_content()
        
        return {
            'success': True,
            'session_id': session.session_id,
            'selector': selector,
            'element_text': element_text,
            'message': f'Successfully clicked element: {selector}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Click failed: {str(e)}',
            'selector': selector
        }


@api_function(
    protocols=["mcp"],
    description="Type text into input field by CSS selector"
)
async def browser_type(
    selector: str,
    text: str,
    session_id: str = None,
    clear_first: bool = True,
    wait_timeout: int = 10
) -> JSONType:
    """
    Type text into an input field.
    
    Waits for element to be visible and focuses before typing.
    """
    
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'success': False,
            'error': 'Browser automation not available',
            'mock_response': True,
            'message': f'Would type "{text}" into {selector}'
        }
    
    try:
        if session_id not in _browser_sessions:
            return {
                'success': False,
                'error': 'No active browser session. Call browser_navigate first.'
            }
        
        session = _browser_sessions[session_id]
        session.update_activity()
        
        # Wait for element and type
        element = session.page.locator(selector)
        await element.wait_for(state='visible', timeout=wait_timeout * 1000)
        
        if clear_first:
            await element.clear()
        
        await element.type(text)
        
        return {
            'success': True,
            'session_id': session.session_id,
            'selector': selector,
            'text': text,
            'message': f'Successfully typed text into: {selector}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Type failed: {str(e)}',
            'selector': selector
        }


@api_function(
    protocols=["mcp"],
    description="Get text content of element by CSS selector"
)
async def browser_get_text(
    selector: str,
    session_id: str = None,
    wait_timeout: int = 10
) -> JSONType:
    """
    Get text content of an element.
    
    Useful for reading dashboard values, error messages, etc.
    """
    
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'success': False,
            'error': 'Browser automation not available',
            'mock_response': True,
            'message': f'Would get text from: {selector}'
        }
    
    try:
        if session_id not in _browser_sessions:
            return {
                'success': False,
                'error': 'No active browser session. Call browser_navigate first.'
            }
        
        session = _browser_sessions[session_id]
        session.update_activity()
        
        # Wait for element and get text
        element = session.page.locator(selector)
        await element.wait_for(state='visible', timeout=wait_timeout * 1000)
        
        text_content = await element.text_content()
        inner_text = await element.inner_text()
        
        return {
            'success': True,
            'session_id': session.session_id,
            'selector': selector,
            'text_content': text_content,
            'inner_text': inner_text,
            'message': f'Retrieved text from: {selector}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Get text failed: {str(e)}',
            'selector': selector
        }


@api_function(
    protocols=["mcp"],
    description="Execute JavaScript code in browser context"
)
async def browser_execute_javascript(
    javascript_code: str,
    session_id: str = None
) -> JSONType:
    """
    Execute JavaScript code in the browser context.
    
    Powerful for custom interactions and data extraction.
    """
    
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'success': False,
            'error': 'Browser automation not available',
            'mock_response': True,
            'message': f'Would execute JavaScript: {javascript_code[:100]}...'
        }
    
    try:
        if session_id not in _browser_sessions:
            return {
                'success': False,
                'error': 'No active browser session. Call browser_navigate first.'
            }
        
        session = _browser_sessions[session_id]
        session.update_activity()
        
        # Execute JavaScript
        result = await session.page.evaluate(javascript_code)
        
        return {
            'success': True,
            'session_id': session.session_id,
            'javascript_code': javascript_code,
            'result': result,
            'message': 'JavaScript executed successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'JavaScript execution failed: {str(e)}',
            'javascript_code': javascript_code
        }


@api_function(
    protocols=["mcp"],
    description="Wait for element to appear or condition to be met"
)
async def browser_wait_for_element(
    selector: str,
    session_id: str = None,
    state: str = "visible",
    timeout_seconds: int = 30
) -> JSONType:
    """
    Wait for element to reach specified state.
    
    States: visible, hidden, attached, detached
    """
    
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'success': False,
            'error': 'Browser automation not available',
            'mock_response': True
        }
    
    try:
        if session_id not in _browser_sessions:
            return {
                'success': False,
                'error': 'No active browser session. Call browser_navigate first.'
            }
        
        session = _browser_sessions[session_id]
        session.update_activity()
        
        # Wait for element
        element = session.page.locator(selector)
        await element.wait_for(state=state, timeout=timeout_seconds * 1000)
        
        return {
            'success': True,
            'session_id': session.session_id,
            'selector': selector,
            'state': state,
            'message': f'Element {selector} reached state: {state}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Wait failed: {str(e)}',
            'selector': selector,
            'state': state
        }


@api_function(
    protocols=["mcp"],
    description="Close browser session and clean up resources"
)
async def browser_close_session(
    session_id: str = None
) -> JSONType:
    """
    Close browser session and clean up resources.
    
    Should be called when done with browser automation.
    """
    
    try:
        if session_id and session_id in _browser_sessions:
            session = _browser_sessions[session_id]
            await session.cleanup()
            del _browser_sessions[session_id]
            
            return {
                'success': True,
                'session_id': session_id,
                'message': 'Browser session closed successfully'
            }
        else:
            return {
                'success': False,
                'error': 'Session not found',
                'session_id': session_id
            }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Session cleanup failed: {str(e)}',
            'session_id': session_id
        }


@api_function(
    protocols=["mcp"],
    description="Get current page information and status"
)
async def browser_get_page_info(
    session_id: str = None
) -> JSONType:
    """
    Get comprehensive information about current page.
    
    Useful for understanding current browser state.
    """
    
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'success': False,
            'error': 'Browser automation not available',
            'mock_response': True
        }
    
    try:
        if session_id not in _browser_sessions:
            return {
                'success': False,
                'error': 'No active browser session. Call browser_navigate first.'
            }
        
        session = _browser_sessions[session_id]
        session.update_activity()
        
        # Get page information
        title = await session.page.title()
        url = session.page.url
        
        # Get viewport size
        viewport = session.page.viewport_size
        
        # Check if page is loaded  
        ready_state = await session.page.evaluate('document.readyState')
        
        return {
            'success': True,
            'session_id': session.session_id,
            'title': title,
            'url': url,
            'viewport': viewport,
            'ready_state': ready_state,
            'session_created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'message': f'Page info retrieved for: {url}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Get page info failed: {str(e)}'
        }