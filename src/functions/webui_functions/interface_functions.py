"""
Web Interface Functions for serving the conversation HTML interface
"""

from registry import api_function
from utils import JSONType

@api_function(
    protocols=["rest"],
    path="/api/conversation",
    method="GET",
    tags=["webui", "interface"],
    description="Serve the conversation web interface HTML page"
)
async def serve_conversation_interface():
    """
    Serve the conversation web interface HTML page.
    
    Returns:
        HTML content for the conversation interface
    """
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude.ai Heartbeat Chat Interface</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #5a67d8;
            margin-bottom: 10px;
        }
        
        .session-info {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 25px;
        }
        
        .session-id {
            font-family: 'Courier New', monospace;
            background: #2d3748;
            color: #ffffff;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 14px;
            word-break: break-all;
        }
        
        .chat-container {
            min-height: 400px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            margin-bottom: 20px;
            background: #fafafa;
        }
        
        .messages {
            padding: 20px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 12px;
            border-radius: 8px;
        }
        
        .message.user {
            background: #e6fffa;
            border-left: 4px solid #38b2ac;
        }
        
        .message.claude {
            background: #f0fff4;
            border-left: 4px solid #48bb78;
        }
        
        .message.status {
            background: #fef5e7;
            border-left: 4px solid #ed8936;
            font-style: italic;
        }
        
        .input-section {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        #messageInput {
            flex: 1;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 16px;
        }
        
        #messageInput:focus {
            outline: none;
            border-color: #5a67d8;
        }
        
        button {
            padding: 12px 20px;
            background: #5a67d8;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.2s;
        }
        
        button:hover {
            background: #4c51bf;
        }
        
        button:disabled {
            background: #a0aec0;
            cursor: not-allowed;
        }
        
        .status-bar {
            background: #2d3748;
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 14px;
            margin-bottom: 20px;
        }
        
        .instructions {
            background: #ebf8ff;
            border: 1px solid #90cdf4;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
        }
        
        .error {
            background: #fed7d7;
            border: 1px solid #fc8181;
            color: #742a2a;
        }
        
        .success {
            background: #c6f6d5;
            border: 1px solid #68d391;
            color: #2f855a;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Claude.ai Heartbeat Chat</h1>
            <p>Alternative conversation interface demonstrating the heartbeat communication pattern</p>
        </div>
        
        <div class="session-info">
            <strong>Session ID:</strong><br>
            <div class="session-id" id="sessionId">Loading...</div>
        </div>
        
        <div class="status-bar" id="statusBar">
            Initializing session...
        </div>
        
        <div class="chat-container">
            <div class="messages" id="messages">
                <div class="message status">
                    Welcome to the Claude.ai heartbeat chat interface! Your session is being initialized...
                </div>
            </div>
        </div>
        
        <div class="input-section">
            <input type="text" id="messageInput" placeholder="Type your message to Claude..." disabled>
            <button id="sendButton" onclick="sendMessage()" disabled>Send</button>
        </div>
        
        <div class="instructions">
            <h3>📋 How This Works:</h3>
            <ol>
                <li><strong>Unique Session:</strong> Each user gets a unique UUID-based session for complete isolation</li>
                <li><strong>Message Queue:</strong> Your messages are queued in the system waiting for Claude to process</li>
                <li><strong>Heartbeat Pattern:</strong> Claude continuously polls the MCP server to check for new messages</li>
                <li><strong>Real-time Responses:</strong> When Claude processes your message, the response appears here automatically</li>
            </ol>
            
            <h3>🔧 Claude.ai MCP Connection Instructions:</h3>
            <p>To connect Claude.ai to this system, use the MCP server URL: <code id="mcpUrl">Loading...</code></p>
        </div>
    </div>

    <script>
        let sessionId = null;
        let pollingInterval = null;
        const API_BASE = window.location.origin + '/v1';
        
        // Get session ID from URL parameter or create new one
        function getSessionFromUrl() {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get('session');
        }
        
        // Initialize the session
        async function initializeSession() {
            try {
                // Check if session ID provided in URL
                const urlSessionId = getSessionFromUrl();
                
                if (urlSessionId) {
                    // Use existing session from URL
                    sessionId = urlSessionId;
                    document.getElementById('sessionId').textContent = sessionId;
                    document.getElementById('mcpUrl').textContent = `${API_BASE}/mcp`;
                    document.getElementById('statusBar').textContent = 'Using existing session! You can now send messages to Claude.';
                    document.getElementById('messageInput').disabled = false;
                    document.getElementById('sendButton').disabled = false;
                    
                    addMessage('status', `✅ Using session ${sessionId}`);
                    addMessage('status', `🔗 Claude.ai MCP URL: ${API_BASE}/mcp`);
                    addMessage('status', `📝 Use session_id: "${sessionId}" in all Claude function calls`);
                } else {
                    // Create new session
                    const response = await fetch(`${API_BASE}/api/create_new_session`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        }
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    sessionId = data.session_id;
                    
                    document.getElementById('sessionId').textContent = sessionId;
                    document.getElementById('mcpUrl').textContent = `${API_BASE}/mcp`;
                    document.getElementById('statusBar').textContent = 'Session ready! You can now send messages to Claude.';
                    document.getElementById('messageInput').disabled = false;
                    document.getElementById('sendButton').disabled = false;
                    
                    addMessage('status', `✅ Session ${sessionId} created successfully!`);
                    addMessage('status', `🔗 Claude.ai MCP URL: ${API_BASE}/mcp`);
                    addMessage('status', `📝 Use session_id: "${sessionId}" in all Claude function calls`);
                }
                
                // Start polling for responses
                startPolling();
                
            } catch (error) {
                console.error('Failed to initialize session:', error);
                document.getElementById('statusBar').textContent = `Error: ${error.message}`;
                addMessage('status', `❌ Failed to initialize session: ${error.message}`);
            }
        }
        
        // Send a message
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || !sessionId) return;
            
            try {
                addMessage('user', message);
                input.value = '';
                input.disabled = true;
                document.getElementById('sendButton').disabled = true;
                
                const response = await fetch(`${API_BASE}/api/queue_user_message?message=${encodeURIComponent(message)}&session_id=${sessionId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage('status', `📤 Message queued (position ${data.queue_position}). Waiting for Claude to process...`);
                    document.getElementById('statusBar').textContent = `Message sent! Queue position: ${data.queue_position}`;
                } else {
                    throw new Error(data.error || 'Failed to queue message');
                }
                
            } catch (error) {
                console.error('Failed to send message:', error);
                addMessage('status', `❌ Failed to send message: ${error.message}`);
                document.getElementById('statusBar').textContent = `Error: ${error.message}`;
            } finally {
                input.disabled = false;
                document.getElementById('sendButton').disabled = false;
                input.focus();
            }
        }
        
        // Poll for responses
        function startPolling() {
            if (pollingInterval) clearInterval(pollingInterval);
            
            pollingInterval = setInterval(async () => {
                if (!sessionId) return;
                
                try {
                    const response = await fetch(`${API_BASE}/api/get_latest_response/${sessionId}`);
                    
                    if (response.ok) {
                        const data = await response.json();
                        
                        if (data.new_response) {
                            addMessage('claude', data.response);
                            document.getElementById('statusBar').textContent = 'Claude responded! You can send another message.';
                        }
                    }
                } catch (error) {
                    console.error('Polling error:', error);
                }
            }, 2000); // Poll every 2 seconds
        }
        
        // Add message to chat
        function addMessage(type, content) {
            const messages = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            const timestamp = new Date().toLocaleTimeString();
            let prefix = '';
            
            switch(type) {
                case 'user':
                    prefix = '👤 You: ';
                    break;
                case 'claude':
                    prefix = '🤖 Claude: ';
                    break;
                case 'status':
                    prefix = '📊 System: ';
                    break;
            }
            
            messageDiv.innerHTML = `<strong>${prefix}</strong>${content} <small style="color: #666;">(${timestamp})</small>`;
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }
        
        // Handle Enter key
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Initialize when page loads
        window.addEventListener('load', initializeSession);
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (pollingInterval) clearInterval(pollingInterval);
        });
    </script>
</body>
</html>"""
    
    # Return as FastAPI HTMLResponse manually
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)