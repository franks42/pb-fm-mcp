/**
 * Webpage MVP Session Management
 * 
 * Handles session connection, queue polling, and browser synchronization
 * for the AI-driven webpage MVP system.
 */

class WebpageSession {
    constructor(options) {
        this.sessionId = options.sessionId;
        this.requestedRole = options.requestedRole || 'master';
        this.onStatusUpdate = options.onStatusUpdate || (() => {});
        this.onPriceUpdate = options.onPriceUpdate || (() => {});
        this.onRoleChange = options.onRoleChange || (() => {});
        this.onParticipantsUpdate = options.onParticipantsUpdate || (() => {});
        this.onError = options.onError || (() => {});
        
        // Session state
        this.clientId = null;
        this.actualRole = null;
        this.queueUrl = null;
        this.isConnected = false;
        this.isPolling = false;
        this.currentDisplayFormat = 'compact';
        
        // API endpoints
        this.apiBase = window.location.origin;
        this.mcpEndpoint = `${this.apiBase}/mcp`;
        this.restEndpoint = `${this.apiBase}/api`;
        
        // Polling configuration
        this.pollInterval = 2000; // 2 seconds
        this.pollTimeoutId = null;
        this.consecutiveErrors = 0;
        this.maxRetries = 5;
        
        console.log('WebpageSession initialized:', {
            sessionId: this.sessionId,
            requestedRole: this.requestedRole,
            apiBase: this.apiBase
        });
    }
    
    async initialize() {
        try {
            this.onStatusUpdate('connecting', 'Connecting to session...');
            
            // Join the session
            const joinResult = await this.joinSession();
            if (!joinResult.success) {
                throw new Error(joinResult.error || 'Failed to join session');
            }
            
            // Update UI with session info
            this.updateSessionInfo(joinResult);
            
            // Start polling for messages
            this.startPolling();
            
            // Initial price update if we're the master
            if (this.actualRole === 'master') {
                setTimeout(() => this.requestPriceUpdate(), 1000);
            }
            
        } catch (error) {
            console.error('Session initialization failed:', error);
            this.onError(`Failed to initialize session: ${error.message}`);
            this.onStatusUpdate('disconnected', 'Connection failed');
        }
    }
    
    async joinSession() {
        try {
            const response = await fetch(`${this.restEndpoint}/webpage_join_session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    role: this.requestedRole
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('Join session result:', result);
            
            if (result.success) {
                this.clientId = result.client_id;
                this.actualRole = result.assigned_role;
                this.queueUrl = result.queue_url;
                this.isConnected = true;
            }
            
            return result;
            
        } catch (error) {
            console.error('Failed to join session:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    updateSessionInfo(joinResult) {
        // Update session ID display
        document.getElementById('sessionId').textContent = this.sessionId;
        
        // Update client role
        const roleElement = document.getElementById('clientRole');
        roleElement.textContent = this.actualRole;
        roleElement.className = `role-badge ${this.actualRole}`;
        
        // Update connection status
        this.onStatusUpdate('connected', 'Connected to session');
        
        // Show master controls if applicable
        if (this.actualRole === 'master') {
            document.getElementById('masterControls').style.display = 'block';
        }
        
        // Handle role assignment feedback
        if (this.requestedRole === 'master' && this.actualRole === 'observer') {
            this.onError('Session already has a master. You were assigned as an observer.');
        }
        
        console.log('Session info updated:', {
            clientId: this.clientId,
            actualRole: this.actualRole,
            queueUrl: this.queueUrl
        });
    }
    
    startPolling() {
        if (this.isPolling) return;
        
        this.isPolling = true;
        console.log('Starting message polling...');
        this.pollForMessages();
    }
    
    stopPolling() {
        this.isPolling = false;
        if (this.pollTimeoutId) {
            clearTimeout(this.pollTimeoutId);
            this.pollTimeoutId = null;
        }
        console.log('Stopped message polling');
    }
    
    async pollForMessages() {
        if (!this.isPolling || !this.queueUrl) return;
        
        try {
            const response = await fetch(`${this.restEndpoint}/webpage_poll_queue`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    queue_url: this.queueUrl,
                    max_messages: 5,
                    wait_time: 5
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success && result.messages && result.messages.length > 0) {
                console.log(`Received ${result.messages.length} messages:`, result.messages);
                
                // Process each message
                for (const message of result.messages) {
                    await this.processMessage(message);
                    
                    // Delete the processed message
                    await this.deleteMessage(message.receipt_handle);
                }
            }
            
            // Reset error counter on success
            this.consecutiveErrors = 0;
            
        } catch (error) {
            console.error('Polling error:', error);
            this.consecutiveErrors++;
            
            if (this.consecutiveErrors >= this.maxRetries) {
                this.onError(`Connection lost: ${error.message}`);
                this.onStatusUpdate('disconnected', 'Connection lost');
                this.stopPolling();
                return;
            } else {
                this.onStatusUpdate('connecting', `Reconnecting... (${this.consecutiveErrors}/${this.maxRetries})`);
            }
        }
        
        // Schedule next poll
        if (this.isPolling) {
            this.pollTimeoutId = setTimeout(() => this.pollForMessages(), this.pollInterval);
        }
    }
    
    async processMessage(message) {
        try {
            const messageBody = message.body;
            console.log('Processing message:', messageBody);
            
            switch (messageBody.message_type) {
                case 'price_update':
                    await this.handlePriceUpdate(messageBody);
                    break;
                    
                case 'role_change':
                    this.handleRoleChange(messageBody);
                    break;
                    
                case 'participants_update':
                    this.handleParticipantsUpdate(messageBody);
                    break;
                    
                default:
                    console.log('Unknown message type:', messageBody.message_type);
            }
            
        } catch (error) {
            console.error('Error processing message:', error);
        }
    }
    
    async handlePriceUpdate(messageBody) {
        try {
            // Show loading state
            this.showLoading(true);
            
            // Get S3 reference and fetch content
            const s3Reference = messageBody.s3_reference;
            if (!s3Reference) {
                throw new Error('No S3 reference in price update message');
            }
            
            // Fetch content from S3
            const contentResponse = await fetch(s3Reference.url);
            if (!contentResponse.ok) {
                throw new Error(`Failed to fetch price data: ${contentResponse.status}`);
            }
            
            const contentData = await contentResponse.json();
            const priceContent = contentData.content;
            
            console.log('Fetched price content:', priceContent);
            
            // Update price display
            this.updatePriceDisplay(priceContent);
            
            // Hide loading state
            this.showLoading(false);
            
            // Show success message
            this.showMessage('success', 'Price Updated', 'HASH price data refreshed successfully');
            
        } catch (error) {
            console.error('Error handling price update:', error);
            this.showLoading(false);
            this.onError(`Failed to update price: ${error.message}`);
        }
    }
    
    updatePriceDisplay(priceData) {
        // Update current price
        const priceElement = document.getElementById('currentPrice');
        priceElement.textContent = priceData.price || '$0.0000';
        
        // Update price change
        const changeElement = document.getElementById('priceChange');
        changeElement.textContent = priceData.change_24h || '+0.00%';
        
        // Update change styling based on direction
        changeElement.className = `change-value ${priceData.change_direction || 'neutral'}`;
        
        // Update last updated time
        const updateTimeElement = document.getElementById('updateTime');
        const updateTime = new Date(priceData.last_updated || new Date()).toLocaleTimeString();
        updateTimeElement.textContent = updateTime;
        
        // Show additional info if detailed format
        const additionalInfo = document.getElementById('additionalInfo');
        if (priceData.display_format === 'detailed' && priceData.market_cap) {
            document.getElementById('marketCap').textContent = priceData.market_cap;
            document.getElementById('volume24h').textContent = priceData.volume_24h || 'N/A';
            additionalInfo.style.display = 'block';
        } else {
            additionalInfo.style.display = 'none';
        }
        
        // Store current format
        this.currentDisplayFormat = priceData.display_format || 'compact';
        
        console.log('Price display updated:', priceData);
    }
    
    handleRoleChange(messageBody) {
        if (messageBody.new_master === this.clientId) {
            this.actualRole = 'master';
            document.getElementById('clientRole').textContent = 'master';
            document.getElementById('clientRole').className = 'role-badge master';
            document.getElementById('masterControls').style.display = 'block';
            this.showMessage('success', 'Role Changed', 'You are now the session master');
        } else if (messageBody.former_master === this.clientId) {
            this.actualRole = 'observer';
            document.getElementById('clientRole').textContent = 'observer';
            document.getElementById('clientRole').className = 'role-badge observer';
            document.getElementById('masterControls').style.display = 'none';
            this.showMessage('info', 'Role Changed', 'You are now an observer');
        }
        
        this.onRoleChange(this.actualRole);
    }
    
    handleParticipantsUpdate(messageBody) {
        this.onParticipantsUpdate(messageBody.participants || []);
    }
    
    async deleteMessage(receiptHandle) {
        try {
            await fetch(`${this.restEndpoint}/webpage_delete_message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    queue_url: this.queueUrl,
                    receipt_handle: receiptHandle
                })
            });
        } catch (error) {
            console.error('Failed to delete message:', error);
        }
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = show ? 'flex' : 'none';
    }
    
    showMessage(type, title, content) {
        const messagesContainer = document.getElementById('messages');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        
        messageElement.innerHTML = `
            <div class="message-content">
                <div class="message-title">${title}</div>
                <div>${content}</div>
                <div class="message-time">${new Date().toLocaleTimeString()}</div>
            </div>
        `;
        
        messagesContainer.appendChild(messageElement);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 5000);
    }
    
    // Master control methods
    async requestPriceUpdate() {
        if (this.actualRole !== 'master') {
            this.onError('Only the session master can refresh prices');
            return;
        }
        
        try {
            this.showLoading(true);
            
            const response = await fetch(`${this.restEndpoint}/webpage_update_hash_price_display`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    display_format: this.currentDisplayFormat
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('Price update result:', result);
            
            if (!result.success) {
                throw new Error(result.error || 'Price update failed');
            }
            
            this.showMessage('success', 'Update Requested', 'Price refresh initiated for all browsers');
            
        } catch (error) {
            console.error('Failed to request price update:', error);
            this.onError(`Failed to refresh price: ${error.message}`);
        } finally {
            // Don't hide loading here - let the price update message handle it
        }
    }
    
    toggleDisplayFormat() {
        if (this.actualRole !== 'master') {
            this.onError('Only the session master can change display format');
            return;
        }
        
        this.currentDisplayFormat = this.currentDisplayFormat === 'compact' ? 'detailed' : 'compact';
        this.requestPriceUpdate();
    }
    
    async getParticipants() {
        try {
            const response = await fetch(`${this.restEndpoint}/webpage_get_session_participants`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('Participants result:', result);
            
            return result;
            
        } catch (error) {
            console.error('Failed to get participants:', error);
            this.onError(`Failed to get participants: ${error.message}`);
            return { success: false, error: error.message };
        }
    }
}

// UI Helper Functions
function updateConnectionStatus(status, message) {
    const statusIndicator = document.getElementById('connectionStatus');
    const statusText = document.getElementById('connectionText');
    
    statusIndicator.className = `status-indicator ${status}`;
    statusText.textContent = message;
}

function updatePriceDisplay(priceData) {
    // This is handled by the WebpageSession class
    console.log('Price display update requested:', priceData);
}

function handleRoleChange(newRole) {
    console.log('Role changed to:', newRole);
}

function updateParticipantsList(participants) {
    const container = document.getElementById('participantsList');
    
    if (!participants || participants.length === 0) {
        container.innerHTML = '<div class="participant-item">No participants found</div>';
        return;
    }
    
    container.innerHTML = participants.map(p => `
        <div class="participant-item">
            <span class="participant-id">${p.client_id}</span>
            <span class="participant-role ${p.role}">${p.role}</span>
        </div>
    `).join('');
}

function showErrorMessage(message) {
    const messagesContainer = document.getElementById('messages');
    const messageElement = document.createElement('div');
    messageElement.className = 'message error';
    
    messageElement.innerHTML = `
        <div class="message-content">
            <div class="message-title">Error</div>
            <div>${message}</div>
            <div class="message-time">${new Date().toLocaleTimeString()}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageElement);
    
    // Auto-remove after 8 seconds for errors
    setTimeout(() => {
        if (messageElement.parentNode) {
            messageElement.parentNode.removeChild(messageElement);
        }
    }, 8000);
}

function setupMasterControls(session) {
    // Refresh price button
    document.getElementById('refreshPrice').addEventListener('click', () => {
        session.requestPriceUpdate();
    });
    
    // Toggle format button
    document.getElementById('toggleFormat').addEventListener('click', () => {
        session.toggleDisplayFormat();
    });
    
    // Show participants button
    document.getElementById('showParticipants').addEventListener('click', async () => {
        const result = await session.getParticipants();
        if (result.success) {
            updateParticipantsList(result.participants);
            document.getElementById('participantsPanel').style.display = 'block';
        }
    });
    
    // Hide participants button
    document.getElementById('hideParticipants').addEventListener('click', () => {
        document.getElementById('participantsPanel').style.display = 'none';
    });
}