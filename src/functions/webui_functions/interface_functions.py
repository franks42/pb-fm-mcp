"""
Web Interface Functions for serving the conversation HTML interface
"""

import os
from registry import api_function
from utils import JSONType

@api_function(
    protocols=[],  # Disabled for production
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
    
    # Get WebAssets S3 bucket URL from environment
    web_assets_bucket = os.environ.get('WEB_ASSETS_BUCKET')
    web_assets_bucket_url = f"https://{web_assets_bucket}.s3.us-west-1.amazonaws.com" if web_assets_bucket else ""
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude.ai Heartbeat Chat Interface</title>
    <link rel="stylesheet" href="{web_assets_bucket_url}/css/chat-interface.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Claude.ai Heartbeat Chat</h1>
            <p>Alternative conversation interface demonstrating the heartbeat communication pattern</p>
        </div>
        
        <div class="session-info">
            <strong>Session ID:</strong><br>
            <div class="session-id" id="sessionId">Initializing...</div>
        </div>
        
        <div class="status-bar" id="statusBar">
            Initializing session...
        </div>
        
        <div class="chat-container">
            <div class="messages" id="messages">
                <!-- Messages will be dynamically added here -->
            </div>
        </div>
        
        <div class="input-section">
            <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">Send</button>
        </div>
        
        <div class="instructions">
            <h3>💬 How to use this interface:</h3>
            <ul>
                <li>Type messages in the input field and press Enter or click Send</li>
                <li>The system will automatically poll for Claude's responses</li>
                <li>Session state is preserved in the URL for easy sharing</li>
                <li>All conversation history is maintained throughout the session</li>
            </ul>
            
            <h3>🔧 Claude.ai MCP Connection Instructions:</h3>
            <p>To connect Claude.ai to this system, use the MCP server URL: <code id="mcpUrl">Loading...</code></p>
        </div>
    </div>

    <!-- S3-hosted chat interface JavaScript -->
    <script src="{web_assets_bucket_url}/js/chat-interface.js"></script>
</body>
</html>"""
    
    # Return as FastAPI HTMLResponse manually
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)