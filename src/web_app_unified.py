"""
Unified FastAPI application for AWS Lambda Web Adapter deployment.
Clean implementation supporting both MCP protocol and REST API endpoints.

Architecture:
- MCP Protocol: Uses sync wrappers (AWS MCP Handler requirement)
- REST API: Uses native async (Web Adapter strength)  
- Both protocols share the same function registry
"""
import asyncio
import json
import sys
from functools import wraps
from pathlib import Path
from typing import Callable, Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory for version imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from version import get_version_string, get_full_version_info

# Import registry and function modules
from registry import get_registry
from registry.registry import FunctionRegistry, FunctionMeta
import functions  # This registers all @api_function decorated functions

# Import AWS MCP Handler
from awslabs.mcp_lambda_handler import MCPLambdaHandler


# =============================================================================
# AWS MCP Handler Snake Case Fix (Monkey Patch)
# =============================================================================

def create_snake_case_tool_decorator(original_tool_method):
    """
    Comprehensive monkey patch that preserves original function names instead of converting to camelCase.
    
    AWS Lambda MCP Handler (v0.1.6) automatically converts snake_case to camelCase, which:
    1. Violates MCP community standards (90% use snake_case) 
    2. Creates confusion and inconsistency between function names and tool names
    3. Goes against developer intent and naming conventions
    
    This monkey patch intercepts AWS's conversion and restores the original snake_case names
    by patching BOTH the tools registry (for display) AND tool_implementations (for execution).
    
    Related: GitHub issue awslabs/mcp#757 - AWS investigating this bug for future fix.
    TODO: Remove this patch when AWS provides native snake_case support.
    """
    def patched_tool(self):
        def decorator(func):
            # Store original name before AWS modifies it
            original_name = func.__name__
            
            # Let AWS create the tool with its camelCase conversion
            aws_decorator = original_tool_method(self)
            wrapped_func = aws_decorator(func)
            
            # Find and fix the name in AWS's internal tools registry
            camel_name = ''.join([original_name.split('_')[0]] + 
                               [word.capitalize() for word in original_name.split('_')[1:]])
            
            # Fix the tool registration if AWS changed the name
            if (hasattr(self, 'tools') and camel_name in self.tools and 
                camel_name != original_name):
                # Move tool from camelCase key to original name key
                tool_definition = self.tools.pop(camel_name)
                # Fix the name field in the tool definition
                if isinstance(tool_definition, dict) and 'name' in tool_definition:
                    tool_definition['name'] = original_name
                # Register with correct name
                self.tools[original_name] = tool_definition
                
                # Also fix the tool_implementations mapping - this is critical for execution
                if (hasattr(self, 'tool_implementations') and camel_name in self.tool_implementations):
                    tool_func = self.tool_implementations.pop(camel_name)
                    self.tool_implementations[original_name] = tool_func
            
            return wrapped_func
        return decorator
    return patched_tool

# Apply the monkey patch before creating any MCP server instances
print("🐍 Applying AWS MCP Handler snake_case monkey patch...")
MCPLambdaHandler.tool = create_snake_case_tool_decorator(MCPLambdaHandler.tool)
print("✅ Snake_case monkey patch applied successfully")


# =============================================================================
# MCP Integration - Clean sync wrapper for AWS MCP Handler limitation
# =============================================================================

def create_mcp_sync_wrapper(async_func: Callable) -> Callable:
    """
    Clean sync wrapper specifically for AWS MCP Handler.
    
    AWS MCP Handler calls functions synchronously, so we need to convert
    async functions to sync. This is a clean, minimal implementation.
    """
    @wraps(async_func)
    def sync_wrapper(*args, **kwargs):
        if not asyncio.iscoroutinefunction(async_func):
            return async_func(*args, **kwargs)
            
        # Try asyncio.run first (cleanest approach)
        try:
            return asyncio.run(async_func(*args, **kwargs))
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                # Fallback: create new event loop in thread
                import concurrent.futures
                import threading
                
                def run_in_thread():
                    # Create isolated event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(async_func(*args, **kwargs))
                    finally:
                        loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result(timeout=30)
            else:
                raise
    
    return sync_wrapper


def register_mcp_tools(mcp_server: MCPLambdaHandler, registry: FunctionRegistry):
    """
    Clean MCP tool registration with proper sync wrapping.
    The monkey patch ensures snake_case names are preserved automatically.
    """
    mcp_functions = registry.get_mcp_functions()
    
    for func_meta in mcp_functions:
        # Create sync-wrapped version for MCP
        if asyncio.iscoroutinefunction(func_meta.func):
            sync_func = create_mcp_sync_wrapper(func_meta.func)
        else:
            sync_func = func_meta.func
            
        # Register with MCP server (monkey patch handles snake_case preservation)
        mcp_tool = mcp_server.tool()(sync_func)


# =============================================================================
# REST Integration - Native async for Web Adapter
# =============================================================================

def register_rest_routes(app: FastAPI, registry: FunctionRegistry):
    """
    Clean REST route registration with native async support.
    Web Adapter provides proper event loop, no wrappers needed.
    """
    rest_functions = registry.get_rest_functions()
    
    for func_meta in rest_functions:
        if not func_meta.rest_path:
            continue
            
        def create_route_handler(meta: FunctionMeta):
            async def route_handler(request: Request):
                try:
                    # Extract parameters from request
                    kwargs = {}
                    
                    # Path parameters
                    for param_name, param_value in request.path_params.items():
                        kwargs[param_name] = param_value
                    
                    # POST body parameters (for JSON payload)
                    if request.method == "POST":
                        try:
                            body = await request.json()
                            if isinstance(body, dict):
                                for param_name, param in meta.signature.parameters.items():
                                    if param_name in ('self', 'cls') or param_name in kwargs:
                                        continue
                                    
                                    if param_name in body:
                                        raw_value = body[param_name]
                                        param_type = meta.type_hints.get(param_name, str)
                                        
                                        try:
                                            if param_type == int:
                                                kwargs[param_name] = int(raw_value)
                                            elif param_type == float:
                                                kwargs[param_name] = float(raw_value)
                                            elif param_type == bool:
                                                kwargs[param_name] = raw_value if isinstance(raw_value, bool) else raw_value.lower() in ('true', '1', 'yes', 'on')
                                            else:
                                                kwargs[param_name] = raw_value
                                        except (ValueError, TypeError):
                                            raise HTTPException(
                                                status_code=400,
                                                detail=f"Invalid value for parameter {param_name}: {raw_value}"
                                            )
                        except Exception as e:
                            # If JSON parsing fails, continue to query params
                            pass
                    
                    # Query parameters with type conversion (fallback)
                    for param_name, param in meta.signature.parameters.items():
                        if param_name in ('self', 'cls') or param_name in kwargs:
                            continue
                            
                        if param_name in request.query_params:
                            raw_value = request.query_params[param_name]
                            param_type = meta.type_hints.get(param_name, str)
                            
                            try:
                                if param_type == int:
                                    kwargs[param_name] = int(raw_value)
                                elif param_type == float:
                                    kwargs[param_name] = float(raw_value)
                                elif param_type == bool:
                                    kwargs[param_name] = raw_value.lower() in ('true', '1', 'yes', 'on')
                                else:
                                    kwargs[param_name] = raw_value
                            except (ValueError, TypeError):
                                raise HTTPException(
                                    status_code=400,
                                    detail=f"Invalid value for parameter {param_name}: {raw_value}"
                                )
                    
                    # Set defaults for missing optional parameters
                    for param_name, param in meta.signature.parameters.items():
                        if (param_name not in ('self', 'cls') and 
                            param_name not in kwargs and 
                            param.default != param.empty):
                            kwargs[param_name] = param.default
                    
                    # Execute function - native async support in Web Adapter!
                    if asyncio.iscoroutinefunction(meta.func):
                        result = await meta.func(**kwargs)  # Clean async execution
                    else:
                        result = meta.func(**kwargs)
                    
                    # Handle error responses
                    if isinstance(result, dict) and result.get("MCP-ERROR"):
                        raise HTTPException(status_code=500, detail=result["MCP-ERROR"])
                    
                    return result
                    
                except HTTPException:
                    raise
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))
            
            return route_handler
        
        # Register route
        handler = create_route_handler(func_meta)
        app.add_api_route(
            path=func_meta.rest_path,
            endpoint=handler,
            methods=[func_meta.rest_method],
            summary=func_meta.description,
            description=func_meta.docstring,
            tags=func_meta.tags,
            name=func_meta.name
        )


# =============================================================================
# Mock Lambda Context for Container Environment
# =============================================================================

class MockLambdaContext:
    """Minimal mock context for AWS MCP Handler in container environment."""
    def __init__(self):
        self.function_name = "pb-fm-mcp-container"
        self.function_version = "$LATEST"  
        self.invoked_function_arn = "arn:aws:lambda:us-west-1:123456789012:function:pb-fm-mcp-container"
        self.memory_limit_in_mb = "512"
        self.remaining_time_in_millis = lambda: 30000
        self.aws_request_id = "container-request-id"


# =============================================================================
# Unified FastAPI Application
# =============================================================================

# Initialize MCP server
print("🔧 Initializing MCP server...")
mcp_server = MCPLambdaHandler(name="pb-fm-mcp", version=get_version_string())

# Create FastAPI app
# Handle API Gateway stage path for proper documentation URLs
import os

# Get the stage path from environment or use empty string for local development
stage_path = os.environ.get("API_GATEWAY_STAGE_PATH", "")

app = FastAPI(
    title="PB-FM Unified API",
    description="Unified MCP + REST API for Provenance Blockchain and Figure Markets data",
    version=get_version_string(),
    docs_url="/docs",
    openapi_url="/openapi.json",
    root_path=stage_path,  # This ensures Swagger UI uses correct paths
    servers=[
        {"url": stage_path, "description": "Current deployment"},
        {"url": "/", "description": "Local development"}
    ] if stage_path else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for container readiness."""
    return {"status": "healthy", "version": get_version_string()}

# Static file endpoint for heartbeat test interface
@app.get("/api/heartbeat-test")
async def heartbeat_test_interface():
    """Serve the heartbeat conversation system test interface."""
    import os
    from pathlib import Path
    from fastapi.responses import FileResponse, HTMLResponse
    
    # Path to static file
    static_file = Path(__file__).parent.parent / "static" / "heartbeat-test.html"
    
    if static_file.exists():
        with open(static_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return HTMLResponse(content=content)
    else:
        return HTMLResponse(
            content="<h1>Heartbeat Test Interface Not Found</h1><p>The static file is not available.</p>",
            status_code=404
        )

# Personalized Dashboard endpoint
@app.get("/dashboard/{dashboard_id}")
async def serve_personalized_dashboard(dashboard_id: str):
    """Serve personalized dashboard HTML with Plotly.js integration."""
    from fastapi.responses import HTMLResponse
    import boto3
    
    try:
        # Get dashboard configuration from DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('DASHBOARDS_TABLE')
        if not table_name:
            raise HTTPException(status_code=500, detail="Dashboard service not configured")
        
        dashboards_table = dynamodb.Table(table_name)
        response = dashboards_table.get_item(Key={'dashboard_id': dashboard_id})
        
        if 'Item' not in response:
            return HTMLResponse(
                content=f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Dashboard Not Found</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; text-align: center; }}
                        .error {{ color: #e74c3c; }}
                    </style>
                </head>
                <body>
                    <h1 class="error">Dashboard Not Found</h1>
                    <p>Dashboard ID: {dashboard_id}</p>
                    <p>This dashboard may have expired or never existed.</p>
                    <p><a href="/">← Back to API Home</a></p>
                </body>
                </html>
                """,
                status_code=404
            )
        
        dashboard_config = response['Item']
        
        # Generate dashboard HTML with Plotly.js integration
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{dashboard_config['dashboard_name']} - PB-FM Dashboard</title>
            
            <!-- Plotly.js CDN -->
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            
            <!-- html2canvas for client-side screenshots -->
            <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js" integrity="sha512-BNaRQnYJYiPSqHHDb58B0yaPfCu+Wgds8Gp/gU33kqBtgNS4tSPHuGibyoeqMV/TJlSKda6FXzoEyYGjTe+vXA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
            
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
                    color: #ffffff;
                    min-height: 100vh;
                }}
                
                .dashboard-header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 12px;
                    backdrop-filter: blur(10px);
                }}
                
                .dashboard-title {{
                    font-size: 2.5em;
                    margin: 0;
                    background: linear-gradient(45deg, #00ff88, #00ccff);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }}
                
                .dashboard-info {{
                    color: #888;
                    margin-top: 10px;
                }}
                
                .visualization-container {{
                    background: rgba(255, 255, 255, 0.02);
                    border-radius: 12px;
                    padding: 20px;
                    margin-bottom: 30px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }}
                
                .loading-spinner {{
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    border: 3px solid rgba(255, 255, 255, 0.3);
                    border-radius: 50%;
                    border-top-color: #00ff88;
                    animation: spin 1s ease-in-out infinite;
                }}
                
                @keyframes spin {{
                    to {{ transform: rotate(360deg); }}
                }}
                
                .status-message {{
                    text-align: center;
                    padding: 20px;
                    background: rgba(0, 255, 136, 0.1);
                    border-radius: 8px;
                    border-left: 4px solid #00ff88;
                }}
                
                .control-panel {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: rgba(0, 0, 0, 0.8);
                    padding: 15px;
                    border-radius: 8px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}
                
                .control-button {{
                    display: block;
                    width: 100%;
                    padding: 8px 16px;
                    margin: 5px 0;
                    background: linear-gradient(45deg, #00ff88, #00ccff);
                    color: #000;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: bold;
                    transition: transform 0.2s;
                }}
                
                .control-button:hover {{
                    transform: translateY(-2px);
                }}
                
                #plotly-div {{
                    width: 100%;
                    height: 600px;
                    background: #2a2a2a;
                    border-radius: 8px;
                }}
                
                .ai-insights {{
                    background: rgba(0, 255, 136, 0.05);
                    border-left: 4px solid #00ff88;
                    padding: 15px;
                    margin-top: 20px;
                    border-radius: 0 8px 8px 0;
                }}
                
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding: 20px;
                    color: #666;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                }}
            </style>
        </head>
        <body>
            <div class="dashboard-header">
                <h1 class="dashboard-title">{dashboard_config['dashboard_name']}</h1>
                <div class="dashboard-info">
                    Created: {dashboard_config['created_at']}<br>
                    {'Wallet: ' + dashboard_config.get('wallet_address', 'Not specified') if dashboard_config.get('wallet_address') else ''}
                    Dashboard ID: {dashboard_id}
                </div>
            </div>
            
            <div class="control-panel">
                <button class="control-button" onclick="refreshDashboard()">🔄 Refresh</button>
                <button class="control-button" onclick="loadHashPriceChart()">📈 HASH Price</button>
                <button class="control-button" onclick="loadPortfolioHealth()">🏥 Portfolio Health</button>
                <button class="control-button" onclick="takeScreenshot()">📸 Screenshot</button>
                <button class="control-button" onclick="toggleTheme()">🌙 Theme</button>
            </div>
            
            <div class="visualization-container">
                <div id="status" class="status-message">
                    <div class="loading-spinner"></div>
                    Initializing dashboard...
                </div>
                <div id="plotly-div" style="display: none;"></div>
                <div id="ai-insights" class="ai-insights" style="display: none;">
                    <h3>🤖 AI Insights</h3>
                    <p id="insights-content">Analyzing data...</p>
                </div>
            </div>
            
            <div class="footer">
                <p>🚀 Generated with AI-Driven Dashboard System | PB-FM MCP Server v{get_version_string()}</p>
                <p><a href="/docs" style="color: #00ff88;">API Documentation</a> | 
                   <a href="/" style="color: #00ccff;">API Home</a></p>
            </div>
            
            <script>
                // Dashboard JavaScript functionality
                const dashboardId = '{dashboard_id}';
                const apiBase = window.location.origin;
                
                // Initialize dashboard
                async function initializeDashboard() {{
                    try {{
                        updateStatus('Loading dashboard configuration...', 'info');
                        
                        // Load initial visualization if any
                        const activeVisualizations = {dashboard_config.get('active_visualizations', [])};
                        
                        if (activeVisualizations.length === 0) {{
                            updateStatus('No visualizations yet - use controls to add charts', 'info');
                            document.getElementById('plotly-div').style.display = 'none';
                        }} else {{
                            updateStatus('Loading visualizations...', 'info');
                            // TODO: Load saved visualizations
                            await loadHashPriceChart(); // Default to HASH price chart
                        }}
                        
                    }} catch (error) {{
                        console.error('Dashboard initialization error:', error);
                        updateStatus('Failed to initialize dashboard: ' + error.message, 'error');
                    }}
                }}
                
                // Load HASH price chart
                async function loadHashPriceChart() {{
                    try {{
                        updateStatus('Loading HASH price chart...', 'info');
                        
                        const response = await fetch(`${{apiBase}}/api/create_hash_price_chart`, {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                time_range: '24h',
                                dashboard_id: dashboardId
                            }})
                        }});
                        
                        if (!response.ok) {{
                            throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                        }}
                        
                        const chartData = await response.json();
                        
                        if (chartData.success) {{
                            // Render Plotly chart
                            const plotlySpec = chartData.visualization_spec;
                            await Plotly.newPlot('plotly-div', plotlySpec.data, plotlySpec.layout, {{
                                responsive: true,
                                displayModeBar: true,
                                modeBarButtonsToAdd: ['downloadSVG']
                            }});
                            
                            document.getElementById('plotly-div').style.display = 'block';
                            updateStatus('HASH price chart loaded successfully', 'success');
                            
                            // Show AI insights
                            if (chartData.ai_insights) {{
                                showAIInsights(chartData.ai_insights);
                            }}
                            
                        }} else {{
                            throw new Error(chartData.error || 'Failed to create chart');
                        }}
                        
                    }} catch (error) {{
                        console.error('Chart loading error:', error);
                        updateStatus('Failed to load HASH price chart: ' + error.message, 'error');
                    }}
                }}
                
                // Load Portfolio Health Dashboard
                async function loadPortfolioHealth() {{
                    try {{
                        updateStatus('Loading Portfolio Health Dashboard...', 'info');
                        
                        // Get wallet address from dashboard config
                        const walletAddress = '{dashboard_config.get('wallet_address', '')}';
                        if (!walletAddress) {{
                            throw new Error('No wallet address configured for this dashboard');
                        }}
                        
                        const response = await fetch(`${{apiBase}}/api/create_portfolio_health`, {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                wallet_address: walletAddress,
                                dashboard_id: dashboardId,
                                analysis_depth: 'comprehensive'
                            }})
                        }});
                        
                        if (!response.ok) {{
                            throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                        }}
                        
                        const portfolioData = await response.json();
                        
                        if (portfolioData.success) {{
                            // Render complex multi-chart dashboard
                            const plotlySpec = portfolioData.visualization_spec;
                            await Plotly.newPlot('plotly-div', plotlySpec.data, plotlySpec.layout, {{
                                responsive: true,
                                displayModeBar: true,
                                modeBarButtonsToAdd: ['downloadSVG']
                            }});
                            
                            document.getElementById('plotly-div').style.display = 'block';
                            updateStatus(`Portfolio Health Dashboard loaded (Score: ${{Math.round(portfolioData.health_metrics.overall_score)}}/100)`, 'success');
                            
                            // Show comprehensive AI insights and recommendations
                            if (portfolioData.ai_insights) {{
                                const insightsHtml = `
                                    <h3>🤖 AI Portfolio Analysis</h3>
                                    <p>${{portfolioData.ai_insights}}</p>
                                    ${{portfolioData.recommendations && portfolioData.recommendations.length > 0 ? `
                                        <h4>📋 Recommendations:</h4>
                                        <ul>
                                            ${{portfolioData.recommendations.map(rec => 
                                                `<li><strong>${{rec.type.charAt(0).toUpperCase() + rec.type.slice(1)}}:</strong> ${{rec.action}} - ${{rec.impact}}</li>`
                                            ).join('')}}
                                        </ul>
                                    ` : ''}}
                                    <div style="margin-top: 15px; padding: 10px; background: rgba(0,255,136,0.1); border-radius: 5px;">
                                        <strong>💰 Portfolio Value:</strong> ~$$${{Math.round(portfolioData.total_value_usd).toLocaleString()}} USD<br>
                                        <strong>📊 Health Score:</strong> ${{portfolioData.health_metrics.overall_score}}/100<br>
                                        <strong>🏦 Validators:</strong> ${{portfolioData.health_metrics.validator_count}}<br>
                                        <strong>🔒 Staking Ratio:</strong> ${{portfolioData.health_metrics.staking_ratio}}%
                                    </div>
                                `;
                                document.getElementById('insights-content').innerHTML = insightsHtml;
                                document.getElementById('ai-insights').style.display = 'block';
                            }}
                            
                        }} else {{
                            throw new Error(portfolioData.error || 'Failed to create portfolio health dashboard');
                        }}
                        
                    }} catch (error) {{
                        console.error('Portfolio health loading error:', error);
                        updateStatus('Failed to load Portfolio Health Dashboard: ' + error.message, 'error');
                    }}
                }}
                
                // Update status message
                function updateStatus(message, type = 'info') {{
                    const statusEl = document.getElementById('status');
                    const colors = {{
                        info: 'rgba(0, 255, 136, 0.1)',
                        success: 'rgba(0, 255, 136, 0.2)', 
                        error: 'rgba(231, 76, 60, 0.2)',
                        warning: 'rgba(255, 193, 7, 0.2)'
                    }};
                    
                    statusEl.style.background = colors[type] || colors.info;
                    statusEl.innerHTML = type === 'info' && message.includes('Loading') 
                        ? `<div class="loading-spinner"></div> ${{message}}`
                        : message;
                }}
                
                // Show AI insights
                function showAIInsights(insights) {{
                    const insightsEl = document.getElementById('ai-insights');
                    const contentEl = document.getElementById('insights-content');
                    contentEl.textContent = insights;
                    insightsEl.style.display = 'block';
                }}
                
                // Refresh dashboard
                async function refreshDashboard() {{
                    await loadHashPriceChart();
                }}
                
                // Take screenshot of current dashboard
                async function takeScreenshot() {{
                    try {{
                        updateStatus('Taking screenshot...', 'info');
                        
                        // Try client-side screenshot first using html2canvas if available
                        if (typeof html2canvas === 'function') {{
                            try {{
                                const canvas = await html2canvas(document.body, {{
                                    backgroundColor: '#1e1e1e',
                                    scale: 1,
                                    useCORS: true,
                                    allowTaint: false
                                }});
                                
                                canvas.toBlob(function(blob) {{
                                    const link = document.createElement('a');
                                    link.href = URL.createObjectURL(blob);
                                    link.download = `dashboard-screenshot-${{new Date().toISOString().slice(0,19).replace(/:/g,'-')}}.png`;
                                    document.body.appendChild(link);
                                    link.click();
                                    document.body.removeChild(link);
                                    URL.revokeObjectURL(link.href);
                                    
                                    updateStatus('Screenshot downloaded successfully (client-side)!', 'success');
                                }}, 'image/png');
                                
                                return; // Success, no need to try server-side
                            }} catch (clientError) {{
                                console.warn('Client-side screenshot failed:', clientError);
                                // Continue to server-side approach
                            }}
                        }}
                        
                        // Fallback to server-side screenshot
                        const response = await fetch(`${{apiBase}}/api/take_screenshot`, {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                url: window.location.href,
                                width: 1400,
                                height: 900,
                                wait_seconds: 3
                            }})
                        }});
                        
                        if (!response.ok) {{
                            throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                        }}
                        
                        const screenshotData = await response.json();
                        
                        if (screenshotData.success && screenshotData.screenshot_base64) {{
                            // Create and download the screenshot
                            const link = document.createElement('a');
                            link.href = 'data:image/png;base64,' + screenshotData.screenshot_base64;
                            link.download = `dashboard-screenshot-${{new Date().toISOString().slice(0,19).replace(/:/g,'-')}}.png`;
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                            
                            updateStatus('Screenshot downloaded successfully (server-side)!', 'success');
                        }} else {{
                            // Show detailed error information
                            const errorMsg = screenshotData.message || screenshotData.error || 'Unknown error';
                            const suggestion = screenshotData.suggestion || 'Try using browser developer tools to capture screenshot manually';
                            updateStatus(`Screenshot failed: ${{errorMsg}}. Suggestion: ${{suggestion}}`, 'warning');
                        }}
                        
                    }} catch (error) {{
                        console.error('Screenshot error:', error);
                        updateStatus('Screenshot failed. Try right-click → Save Page As or browser developer tools to capture manually.', 'error');
                    }}
                }}
                
                // Toggle dark/light theme
                function toggleTheme() {{
                    const body = document.body;
                    const isDark = body.style.background.includes('1e1e1e');
                    
                    if (isDark) {{
                        body.style.background = 'linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%)';
                        body.style.color = '#333';
                    }} else {{
                        body.style.background = 'linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%)';
                        body.style.color = '#ffffff';
                    }}
                }}
                
                // Initialize dashboard when page loads
                window.addEventListener('load', initializeDashboard);
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        print(f"Dashboard serving error: {e}")
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Dashboard Error</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; text-align: center; }}
                    .error {{ color: #e74c3c; }}
                </style>
            </head>
            <body>
                <h1 class="error">Dashboard Error</h1>
                <p>Failed to load dashboard: {str(e)}</p>
                <p><a href="/">← Back to API Home</a></p>
            </body>
            </html>
            """,
            status_code=500
        )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with unified API information."""
    version_info = get_full_version_info()
    registry = get_registry()
    return {
        "name": "PB-FM Unified API",
        "version": version_info["version"],
        "build_number": version_info["build_number"],
        "build_datetime": version_info["build_datetime"],
        "environment": version_info["deployment_environment"],
        "description": "Unified MCP + REST API for Provenance Blockchain and Figure Markets data",
        "protocols": {
            "mcp": {
                "endpoint": "/mcp",
                "method": "POST",
                "tools": len(registry.get_mcp_functions())
            },
            "rest": {
                "endpoints": len(registry.get_rest_functions()),
                "docs": "/docs",
                "openapi": "/openapi.json"
            }
        },
        "endpoints": {
            "mcp": "/mcp",
            "docs": "/docs",
            "openapi": "/openapi.json", 
            "health": "/health"
        }
    }

# MCP connection test endpoint for Claude.ai
@app.get("/mcp")
async def mcp_connection_test(request: Request):
    """Handle MCP connection test requests from Claude.ai with SSE negotiation"""
    headers = dict(request.headers)
    accept_header = headers.get('accept', '').lower()
    
    # Check for SSE request like the old working version
    if 'text/event-stream' in accept_header:
        print("❌ Client requesting SSE - returning 405 like working version")
        # Client wants SSE - we don't support it, return 405 like the old version
        raise HTTPException(
            status_code=405, 
            detail="Method Not Allowed - SSE not supported, use HTTP POST"
        )
    
    return {
        "name": "PB-FM MCP Server",
        "version": get_version_string(), 
        "description": "MCP server for Provenance Blockchain and Figure Markets data",
        "protocol": "Model Context Protocol",
        "methods": ["POST"],
        "message": "Send POST requests with JSON-RPC 2.0 format to interact with MCP tools"
    }

# MCP endpoint - Use direct AWS MCP Handler like the working version
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Handle MCP protocol requests using direct AWS MCP Handler approach."""
    try:
        # Get raw request data
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8') if body_bytes else ''
        
        # Create Lambda event format exactly like the working version
        lambda_event = {
            "httpMethod": "POST",
            "path": "/mcp",
            "headers": dict(request.headers),
            "body": body_str,
            "pathParameters": None,
            "queryStringParameters": None,
            "requestContext": {
                "requestId": "container-request-id",
                "identity": {
                    "sourceIp": request.client.host if request.client else "unknown"
                }
            }
        }
        
        context = MockLambdaContext()
        
        # Debug headers like the working version
        headers = dict(request.headers)
        accept_header = headers.get('accept', '').lower()
        print(f"🔍 === MCP REQUEST DEBUG ===")
        print(f"📍 Accept header: {accept_header}")
        print(f"📍 All headers: {headers}")
        
        # Check if client accepts both application/json and text/event-stream (like working version)
        if 'application/json' in accept_header and 'text/event-stream' in accept_header:
            print("✅ Proper MCP client detected - using MCP handler")
        else:
            print("⚠️ Non-standard accept header - using MCP handler anyway")
        
        # Direct MCP handler call like the working version
        print(f"🔧 Processing MCP request with direct handler")
        mcp_response = mcp_server.handle_request(lambda_event, context)
        
        # Extract response body and return as JSON
        if isinstance(mcp_response, dict):
            if 'body' in mcp_response:
                # Parse JSON body from Lambda response format
                response_body = mcp_response['body']
                if isinstance(response_body, str):
                    response_data = json.loads(response_body)
                else:
                    response_data = response_body
                
                # Set response headers if present
                if 'headers' in mcp_response:
                    for header_name, header_value in mcp_response['headers'].items():
                        if header_name.lower() not in ['content-length', 'content-type']:
                            # Let FastAPI handle content-type and content-length
                            pass
                
                return response_data
            else:
                # Direct response
                return mcp_response
        else:
            return {"error": "Invalid MCP response format"}
            
    except json.JSONDecodeError as e:
        print(f"🚨 JSON decode error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        print(f"🚨 MCP handler error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"MCP processing error: {str(e)}")

# Register both protocols
print("🔧 Registering API functions...")
registry = get_registry()

print("🔧 Registering MCP tools...")
register_mcp_tools(mcp_server, registry)
print(f"✅ Registered {len(registry.get_mcp_functions())} MCP tools")

print("🔧 Registering REST routes...")
register_rest_routes(app, registry)
print(f"✅ Registered {len(registry.get_rest_functions())} REST endpoints")

print("📝 Unified MCP + REST server ready")