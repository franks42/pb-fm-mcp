# Browser Extension Architecture for Scalable AI Control

## The Problem with Server-Side Browser Automation
- 300MB RAM per browser session
- Doesn't scale beyond 10-20 concurrent users
- Expensive infrastructure requirements
- Separation from user's actual browser context

## Solution: Browser Extension Bridge

### Architecture Overview
```
User's Browser
    ↓ (Browser Extension)
Extension Background Script
    ↓ (WebSocket/Server-Sent Events)
MCP Server
    ↓ (MCP Protocol)
Claude.ai
```

### Core Components

#### 1. Browser Extension (Chrome/Firefox)
```javascript
// manifest.json
{
  "manifest_version": 3,
  "name": "Claude Dashboard Controller",
  "permissions": [
    "activeTab",
    "scripting", 
    "webNavigation"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [{
    "matches": ["https://your-dashboard-domain.com/*"],
    "js": ["content.js"]
  }]
}
```

#### 2. Lightweight MCP Functions
```python
@api_function(protocols=["mcp"])
async def browser_send_command(
    user_session_id: str,
    command: str,
    selector: str = None,
    data: str = None
) -> JSONType:
    """Send command to user's browser extension"""
    
    # Store command for browser to poll
    await store_browser_command(user_session_id, {
        'command': command,
        'selector': selector, 
        'data': data,
        'timestamp': datetime.now().isoformat()
    })
    
    return {
        'success': True,
        'message': f'Command sent to browser: {command}'
    }

@api_function(protocols=["mcp"])  
async def browser_get_response(
    user_session_id: str,
    timeout_seconds: int = 10
) -> JSONType:
    """Get response from user's browser"""
    
    # Wait for browser response
    response = await wait_for_browser_response(user_session_id, timeout_seconds)
    
    return {
        'success': True,
        'response': response
    }
```

#### 3. Extension-Server Communication
```javascript
// background.js - Extension side
class ClaudeConnector {
    constructor() {
        this.serverUrl = 'wss://your-mcp-server.com/browser-bridge';
        this.websocket = null;
        this.sessionId = this.generateSessionId();
    }
    
    async connect() {
        this.websocket = new WebSocket(this.serverUrl);
        
        this.websocket.onmessage = (event) => {
            const command = JSON.parse(event.data);
            this.executeCommand(command);
        };
    }
    
    async executeCommand(command) {
        const tabs = await chrome.tabs.query({active: true, currentWindow: true});
        const tab = tabs[0];
        
        switch(command.type) {
            case 'click':
                await chrome.scripting.executeScript({
                    target: {tabId: tab.id},
                    func: (selector) => {
                        document.querySelector(selector).click();
                    },
                    args: [command.selector]
                });
                break;
                
            case 'screenshot':
                const screenshot = await chrome.tabs.captureVisibleTab();
                this.sendResponse({screenshot: screenshot});
                break;
                
            case 'get_text':
                const result = await chrome.scripting.executeScript({
                    target: {tabId: tab.id},
                    func: (selector) => {
                        return document.querySelector(selector).textContent;
                    },
                    args: [command.selector]
                });
                this.sendResponse({text: result[0].result});
                break;
        }
    }
    
    sendResponse(data) {
        this.websocket.send(JSON.stringify({
            sessionId: this.sessionId,
            response: data,
            timestamp: new Date().toISOString()
        }));
    }
}
```

### Advantages of Extension Approach

#### Resource Efficiency
- **Server RAM**: ~0MB per user (no browser processes)
- **Network**: Minimal WebSocket messages
- **Scaling**: Linear with WebSocket connections (very cheap)

#### User Experience  
- **Real Browser**: Uses user's actual browser with their data
- **No Installation**: Just install browser extension
- **Performance**: Native browser performance
- **Security**: Runs in user's security context

#### Development Simplicity
- **No Container Images**: No 400MB browser containers
- **No Complex Setup**: No Chrome/Playwright in Lambda
- **Standard Web Tech**: JavaScript, WebSockets, DOM APIs

### Implementation Effort
```
Server-side browser automation: 2-3 weeks development + complex deployment
Browser extension approach: 1 week development + simple deployment
```

## Alternative: Hybrid Approach

### Option 2: Smart Screenshot Analysis
Instead of full browser control, enhance our screenshot system:

```python
@api_function(protocols=["mcp"])
async def analyze_dashboard_issue(
    screenshot_base64: str,
    issue_description: str
) -> JSONType:
    """Use AI vision to analyze dashboard screenshots and suggest fixes"""
    
    # Use Claude's vision capabilities to analyze the screenshot
    analysis = await analyze_screenshot_with_vision(screenshot_base64, issue_description)
    
    # Generate specific recommendations
    recommendations = generate_fix_recommendations(analysis)
    
    return {
        'success': True,
        'analysis': analysis,
        'recommendations': recommendations,
        'suggested_actions': [
            'Check CSS selector: .chart-container',
            'Verify data loading in network tab',
            'Test responsive breakpoints'
        ]
    }
```

### Option 3: Micro-Automation
Very targeted automation for specific, high-value use cases:

```python
@api_function(protocols=["mcp"])
async def quick_dashboard_test(
    dashboard_url: str,
    test_type: str = "basic_load"
) -> JSONType:
    """Run lightweight dashboard tests without full browser automation"""
    
    if test_type == "basic_load":
        # Just check if page loads and key elements exist
        response = await simple_http_check(dashboard_url)
        return analyze_simple_response(response)
    elif test_type == "screenshot_only":
        # Single screenshot for visual analysis
        return await take_one_screenshot(dashboard_url)
```

## Recommendation: Start with Extension

### Phase 1: Browser Extension (Week 1)
- Simple Chrome extension for dashboard domains
- Basic commands: click, screenshot, get_text
- WebSocket connection to MCP server

### Phase 2: Enhanced Commands (Week 2)  
- Form filling, navigation, waiting
- Error detection and reporting
- Performance monitoring

### Phase 3: AI Integration (Week 3)
- Screenshot analysis with Claude vision
- Automated issue detection
- Smart recommendations

This approach gives you **90% of the browser automation benefits** with **5% of the infrastructure cost** and complexity.

Would you like me to implement the browser extension approach instead?