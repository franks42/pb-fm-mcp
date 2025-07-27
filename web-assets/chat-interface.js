// Claude.ai Heartbeat Chat Interface JavaScript
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
            updateStatus(`Using existing session: ${sessionId}`, 'success');
            
            // Load existing messages for this session
            await loadExistingMessages();
        } else {
            // Create new session
            const response = await fetch(`${API_BASE}/api/create_conversation_session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                sessionId = data.session_id;
                document.getElementById('sessionId').textContent = sessionId;
                updateStatus(`New session created: ${sessionId}`, 'success');
                
                // Update URL with session ID
                const newUrl = new URL(window.location);
                newUrl.searchParams.set('session', sessionId);
                window.history.replaceState({}, '', newUrl);
            } else {
                throw new Error(`Failed to create session: ${response.statusText}`);
            }
        }
        
        // Get MCP URL for Claude.ai connection
        const mcpResponse = await fetch(`${API_BASE}/mcp`);
        if (mcpResponse.ok) {
            document.getElementById('mcpUrl').textContent = `${window.location.origin}/v1/mcp`;
        }
        
        // Start polling for Claude responses
        startPolling();
        
    } catch (error) {
        console.error('Session initialization error:', error);
        updateStatus(`Failed to initialize session: ${error.message}`, 'error');
    }
}

// Load existing messages for the session
async function loadExistingMessages() {
    try {
        const response = await fetch(`${API_BASE}/api/get_conversation_messages?session_id=${sessionId}`);
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.messages) {
                data.messages.forEach(message => {
                    addMessage(message.content, message.role);
                });
            }
        }
    } catch (error) {
        console.error('Failed to load existing messages:', error);
    }
}

// Send a message
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message || !sessionId) return;
    
    // Disable input while sending
    input.disabled = true;
    document.querySelector('button').disabled = true;
    
    try {
        // Add user message to UI immediately
        addMessage(message, 'user');
        
        // Clear input
        input.value = '';
        
        // Send to API
        const response = await fetch(`${API_BASE}/api/send_message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                message: message
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                updateStatus('Message sent successfully', 'success');
                // Claude's response will come via polling
            } else {
                throw new Error(data.error || 'Failed to send message');
            }
        } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
    } catch (error) {
        console.error('Send message error:', error);
        updateStatus(`Failed to send message: ${error.message}`, 'error');
    } finally {
        // Re-enable input
        input.disabled = false;
        document.querySelector('button').disabled = false;
        input.focus();
    }
}

// Add message to the chat
function addMessage(content, role) {
    const messagesContainer = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const timestamp = new Date().toLocaleTimeString();
    const roleDisplay = role === 'user' ? '👤 You' : role === 'assistant' ? '🤖 Claude' : '📊 System';
    
    messageDiv.innerHTML = `
        <strong>${roleDisplay}</strong> <em>${timestamp}</em><br>
        ${content.replace(/\n/g, '<br>')}
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Poll for new messages from Claude
function startPolling() {
    if (pollingInterval) clearInterval(pollingInterval);
    
    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/poll_responses?session_id=${sessionId}`);
            
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.new_messages && data.new_messages.length > 0) {
                    data.new_messages.forEach(message => {
                        addMessage(message.content, message.role);
                    });
                }
            }
        } catch (error) {
            console.warn('Polling error:', error);
        }
    }, 2000); // Poll every 2 seconds
}

// Update status bar
function updateStatus(message, type = 'info') {
    const statusBar = document.getElementById('statusBar');
    statusBar.textContent = message;
    statusBar.className = `status-bar ${type}`;
}

// Handle enter key in input
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Initialize when page loads
window.addEventListener('load', initializeSession);

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (pollingInterval) clearInterval(pollingInterval);
});