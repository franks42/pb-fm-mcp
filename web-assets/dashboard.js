// PB-FM MCP Dashboard JavaScript
// Global variables
let dashboardId = '';
let apiBase = '';

// Initialize dashboard
async function initializeDashboard() {
    try {
        // Initialize global variables from server
        dashboardId = window.dashboardIdFromServer || window.dashboardConfig?.dashboard_id || '';
        apiBase = window.location.origin + (window.location.pathname.includes('/v1/') ? '/v1' : '');
        
        console.log('Dashboard initialized:', {dashboardId, apiBase});
        
        updateStatus('Loading dashboard configuration...', 'info');
        
        // Load initial visualization if any
        const activeVisualizations = window.dashboardConfig?.active_visualizations || [];
        
        if (activeVisualizations.length === 0) {
            updateStatus('No visualizations yet - use controls to add charts', 'info');
            document.getElementById('plotly-div').style.display = 'none';
        } else {
            updateStatus('Loading visualizations...', 'info');
            // TODO: Load saved visualizations
            await loadHashPriceChart(); // Default to HASH price chart
        }
        
    } catch (error) {
        console.error('Dashboard initialization error:', error);
        updateStatus('Failed to initialize dashboard: ' + error.message, 'error');
    }
}

// Load HASH price chart
async function loadHashPriceChart() {
    try {
        updateStatus('Loading HASH price chart...', 'info');
        
        const response = await fetch(`${apiBase}/api/create_hash_price_chart`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                time_range: '24h',
                dashboard_id: dashboardId
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const chartData = await response.json();
        
        if (chartData.success) {
            // Render Plotly chart
            const plotlySpec = chartData.visualization_spec;
            await Plotly.newPlot('plotly-div', plotlySpec.data, plotlySpec.layout, {
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToAdd: ['downloadSVG']
            });
            
            document.getElementById('plotly-div').style.display = 'block';
            
            // Force chart to resize to fill available canvas space
            setTimeout(() => {
                Plotly.Plots.resize('plotly-div');
            }, 100);
            
            updateStatus('HASH price chart loaded successfully', 'success');
            
            // Show AI insights
            if (chartData.ai_insights) {
                showAIInsights(chartData.ai_insights);
            }
            
        } else {
            throw new Error(chartData.error || 'Failed to create chart');
        }
        
    } catch (error) {
        console.error('Chart loading error:', error);
        updateStatus('Failed to load HASH price chart: ' + error.message, 'error');
    }
}

// Load Portfolio Health Dashboard with dynamic config support
async function loadPortfolioHealth() {
    try {
        updateStatus('Loading Portfolio Health Dashboard...', 'info');
        
        // Get wallet address from dashboard config
        const walletAddress = window.dashboardConfig?.wallet_address || 'pb1test';
        console.log('Portfolio Health: Using wallet address:', walletAddress);
        
        if (!walletAddress) {
            throw new Error('No wallet address configured for this dashboard');
        }
        
        // First check if we have a custom config in DynamoDB
        const configResponse = await fetch(`${apiBase}/api/get_dashboard_config?dashboard_id=${dashboardId}`);
        let useCustomConfig = false;
        let customConfig = null;
        
        if (configResponse.ok) {
            const configData = await configResponse.json();
            if (configData.success && !configData.is_default) {
                customConfig = configData.config;
                useCustomConfig = true;
                console.log('Using custom config version:', configData.version);
            }
        }
        
        const response = await fetch(`${apiBase}/api/create_portfolio_health`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                wallet_address: walletAddress,
                dashboard_id: dashboardId,
                use_custom_config: useCustomConfig,
                custom_config: customConfig
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const healthData = await response.json();
        
        if (healthData.success) {
            // Render Plotly chart
            const plotlySpec = healthData.visualization_spec;
            await Plotly.newPlot('plotly-div', plotlySpec.data, plotlySpec.layout, {
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToAdd: ['downloadSVG']
            });
            
            document.getElementById('plotly-div').style.display = 'block';
            
            // Force chart to resize to fill available canvas space  
            setTimeout(() => {
                Plotly.Plots.resize('plotly-div');
            }, 100);
            
            updateStatus('Portfolio Health Dashboard loaded successfully', 'success');
            
            // Show AI insights
            if (healthData.ai_insights) {
                showAIInsights(healthData.ai_insights);
            }
            
        } else {
            throw new Error(healthData.error || 'Failed to create portfolio health dashboard');
        }
        
    } catch (error) {
        console.error('Portfolio health loading error:', error);
        updateStatus('Failed to load Portfolio Health: ' + error.message, 'error');
    }
}

// Update status message
function updateStatus(message, type = 'info') {
    const statusEl = document.getElementById('status');
    statusEl.innerHTML = message;
    
    // Remove existing status classes
    statusEl.classList.remove('status-info', 'status-success', 'status-warning', 'status-error');
    
    // Add new status class
    statusEl.classList.add(`status-${type}`);
    
    // Show status
    statusEl.style.display = 'block';
    
    // Auto-hide success messages after 3 seconds
    if (type === 'success') {
        setTimeout(() => {
            statusEl.style.display = 'none';
        }, 3000);
    }
}

// Toggle theme
function toggleTheme() {
    const body = document.body;
    if (body.style.background.includes('1e1e1e')) {
        // Switch to light theme
        body.style.background = 'linear-gradient(135deg, #f0f0f0 0%, #ffffff 100%)';
        body.style.color = '#333333';
        updateStatus('Switched to light theme', 'success');
    } else {
        // Switch to dark theme
        body.style.background = 'linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%)';
        body.style.color = '#ffffff';
        updateStatus('Switched to dark theme', 'success');
    }
}

// Toggle live config mode
function toggleLiveConfigMode() {
    if (configPollingInterval) {
        stopConfigPolling();
        updateStatus('Live config polling disabled', 'info');
    } else {
        startConfigPolling();
        updateStatus('Live config polling enabled', 'success');
    }
}

// Show AI insights
function showAIInsights(insights) {
    const insightsEl = document.getElementById('ai-insights');
    const contentEl = document.getElementById('insights-content');
    contentEl.textContent = insights;
    insightsEl.style.display = 'block';
}

// Refresh dashboard
async function refreshDashboard() {
    await loadHashPriceChart();
}

// Take screenshot of current dashboard
async function takeScreenshot() {
    try {
        updateStatus('Taking screenshot...', 'info');
        
        // Try client-side screenshot first using html2canvas if available
        if (typeof html2canvas === 'function') {
            try {
                const canvas = await html2canvas(document.body, {
                    backgroundColor: '#1e1e1e',
                    scale: 1,
                    useCORS: true,
                    allowTaint: false
                });
                
                canvas.toBlob(function(blob) {
                    const link = document.createElement('a');
                    link.href = URL.createObjectURL(blob);
                    link.download = `dashboard-screenshot-${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.png`;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    URL.revokeObjectURL(link.href);
                    
                    updateStatus('Screenshot downloaded successfully (client-side)!', 'success');
                }, 'image/png');
                
                return; // Success, no need to try server-side
            } catch (clientError) {
                console.warn('Client-side screenshot failed:', clientError);
                // Continue to server-side approach
            }
        }
        
        // Fallback to server-side screenshot
        const response = await fetch(`${apiBase}/api/take_screenshot`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: window.location.href,
                width: 1400,
                height: 900,
                wait_seconds: 3
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const screenshotData = await response.json();
        
        if (screenshotData.success && screenshotData.screenshot_base64) {
            // Create and download the screenshot
            const link = document.createElement('a');
            link.href = 'data:image/png;base64,' + screenshotData.screenshot_base64;
            link.download = `dashboard-screenshot-${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            updateStatus('Screenshot downloaded successfully (server-side)!', 'success');
        } else {
            // Show detailed error information
            const errorMsg = screenshotData.message || screenshotData.error || 'Unknown error';
            const suggestion = screenshotData.suggestion || 'Try using browser developer tools to capture screenshot manually';
            updateStatus(`Screenshot failed: ${errorMsg}. Suggestion: ${suggestion}`, 'warning');
        }
        
    } catch (error) {
        console.error('Screenshot error:', error);
        updateStatus('Screenshot failed. Try right-click → Save Page As or browser developer tools to capture manually.', 'error');
    }
}

// Upload screenshot to server for Claude's analysis
async function uploadScreenshotToServer(context = 'user_screenshot', screenshotId = null) {
    try {
        updateStatus('Capturing screenshot for server upload...', 'info');
        
        if (typeof html2canvas !== 'undefined') {
            const canvas = await html2canvas(document.body, {
                backgroundColor: '#1e1e1e',
                scale: 1,
                useCORS: true,
                allowTaint: false,
                width: 1400,
                height: 900
            });
            
            const base64Data = canvas.toDataURL('image/png').split(',')[1];
            
            const response = await fetch(`${apiBase}/api/upload_screenshot`, {
                method: 'POST', 
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    screenshot_base64: base64Data,
                    dashboard_id: dashboardId,
                    context: context,
                    screenshot_id: screenshotId  // Use provided screenshot_id if available
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                updateStatus(`Screenshot uploaded successfully! Claude can now analyze it via: ${result.screenshot_id}`, 'success');
                return result.screenshot_id;
            } else {
                throw new Error(result.error || 'Upload failed');
            }
        } else {
            throw new Error('html2canvas not available');
        }
        
    } catch (error) {
        console.error('Screenshot upload error:', error);
        updateStatus('Failed to upload screenshot: ' + error.message, 'error');
        return null;
    }
}

// Poll for screenshot requests from server (Claude)
let screenshotPollingInterval = null;

function startScreenshotPolling() {
    if (screenshotPollingInterval) return; // Already polling
    
    screenshotPollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`${apiBase}/api/check_screenshot_requests`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    dashboard_id: dashboardId
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.screenshot_requested) {
                    console.log('Claude requested screenshot, capturing...', data);
                    // Pass the screenshot_id from the request data to the upload function
                    await uploadScreenshotToServer('claude_debug_request', data.screenshot_id);
                }
            }
        } catch (error) {
            console.warn('Screenshot polling error:', error);
        }
    }, 3000); // Poll every 3 seconds
}

function stopScreenshotPolling() {
    if (screenshotPollingInterval) {
        clearInterval(screenshotPollingInterval);
        screenshotPollingInterval = null;
    }
}

// Live configuration updates
let configPollingInterval = null;
let lastConfigVersion = 0;

async function startConfigPolling() {
    if (configPollingInterval) return;
    
    configPollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`${apiBase}/api/get_dashboard_config?dashboard_id=${dashboardId}`);
            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.version > lastConfigVersion) {
                    console.log('New config version detected:', data.version);
                    lastConfigVersion = data.version;
                    
                    // Update Plotly chart with new config
                    const plotlyDiv = document.getElementById('plotly-div');
                    if (plotlyDiv && plotlyDiv.data) {
                        // Reload current visualization with new config
                        await loadPortfolioHealth();
                    }
                }
            }
        } catch (error) {
            console.warn('Config polling error:', error);
        }
    }, 5000); // Poll every 5 seconds
}

function stopConfigPolling() {
    if (configPollingInterval) {
        clearInterval(configPollingInterval);
        configPollingInterval = null;
    }
}

// Draggable panel functionality
function makePanelDraggable() {
    const panel = document.getElementById('controlPanel');
    let isDragging = false;
    let currentX;
    let currentY;
    let initialX;
    let initialY;
    let xOffset = 0;
    let yOffset = 0;
    
    // Mouse events
    panel.addEventListener('mousedown', dragStart);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', dragEnd);
    
    // Touch events for mobile
    panel.addEventListener('touchstart', dragStart);
    document.addEventListener('touchmove', drag);
    document.addEventListener('touchend', dragEnd);
    
    function dragStart(e) {
        if (e.target.classList.contains('control-button')) return; // Don't drag on buttons
        
        if (e.type === 'touchstart') {
            initialX = e.touches[0].clientX - xOffset;
            initialY = e.touches[0].clientY - yOffset;
        } else {
            initialX = e.clientX - xOffset;
            initialY = e.clientY - yOffset;
        }
        
        if (e.target === panel || e.target.classList.contains('panel-header')) {
            isDragging = true;
            panel.classList.add('dragging');
        }
    }
    
    function drag(e) {
        if (isDragging) {
            e.preventDefault();
            
            if (e.type === 'touchmove') {
                currentX = e.touches[0].clientX - initialX;
                currentY = e.touches[0].clientY - initialY;
            } else {
                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;
            }
            
            xOffset = currentX;
            yOffset = currentY;
            
            // Constrain to viewport (allow some off-screen movement)
            const rect = panel.getBoundingClientRect();
            const panelWidth = rect.width;
            const panelHeight = rect.height;
            const margin = 50; // Allow 50px off-screen
            
            const minX = -panelWidth + margin; // Allow panel to go mostly off-screen left
            const maxX = window.innerWidth - margin; // Keep small part visible on right
            const minY = 0; // Don't allow above viewport
            const maxY = window.innerHeight - panelHeight; // Keep fully visible vertically
            
            xOffset = Math.max(minX, Math.min(maxX, xOffset));
            yOffset = Math.max(minY, Math.min(maxY, yOffset));
            
            panel.style.transform = `translate(${xOffset}px, ${yOffset}px)`;
        }
    }
    
    function dragEnd(e) {
        initialX = currentX;
        initialY = currentY;
        isDragging = false;
        panel.classList.remove('dragging');
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize global variables from the page
    dashboardId = window.dashboardIdFromServer || '';
    apiBase = window.location.origin;
    
    // Initialize dashboard
    initializeDashboard();
    
    // Start polling services
    startScreenshotPolling();
    
    // Initialize draggable panel
    makePanelDraggable();
});

// Stop polling when page unloads
window.addEventListener('beforeunload', () => {
    stopScreenshotPolling();
    stopConfigPolling();
});