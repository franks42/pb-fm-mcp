"""
AI-Driven Blockchain Visualization Functions

This module implements the revolutionary personalized dashboard system
and AI-driven visualization templates for blockchain data.
"""

import os
import uuid
import boto3
from datetime import datetime, timedelta
from typing import Optional

from registry.decorator import api_function
from utils import JSONType


def get_dashboards_table():
    """Get DynamoDB dashboards table"""
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ.get('DASHBOARDS_TABLE')
    if not table_name:
        raise ValueError("DASHBOARDS_TABLE environment variable not set")
    return dynamodb.Table(table_name)


@api_function(
    protocols=["mcp", "rest"],
    path="/api/create_personalized_dashboard",
    method="POST", 
    tags=["visualization", "dashboard"],
    description="AI creates unique personalized dashboard URL for user"
)
async def create_personalized_dashboard(
    wallet_address: str = None,
    dashboard_name: str = "My Blockchain Dashboard",
    ai_session_id: str = None
) -> JSONType:
    """
    AI can create a unique, personalized web dashboard for the user.
    
    This revolutionary feature allows AI assistants to generate custom
    dashboard URLs that users can bookmark and return to anytime.
    """
    
    try:
        # Generate unique dashboard ID
        dashboard_id = f"dash_{uuid.uuid4().hex[:12]}"
        
        # Create dashboard configuration
        now = datetime.now()
        ttl = int((now + timedelta(days=30)).timestamp())  # 30-day expiration
        
        dashboard_config = {
            'dashboard_id': dashboard_id,
            'created_by': 'ai_assistant',
            'ai_session_id': ai_session_id or 'unknown',
            'wallet_address': wallet_address,
            'dashboard_name': dashboard_name,
            'created_at': now.isoformat(),
            'last_updated': now.isoformat(),
            'canvas_layout': 'default',
            'theme': 'blockchain_dark',
            'active_visualizations': [],
            'user_preferences': {},
            'ttl': ttl
        }
        
        # Store in DynamoDB
        dashboards_table = get_dashboards_table()
        dashboards_table.put_item(Item=dashboard_config)
        
        # Generate URLs
        base_url = "https://pb-fm-mcp-dev.creativeapptitude.com"
        dashboard_url = f"{base_url}/dashboard/{dashboard_id}"
        
        return {
            'dashboard_id': dashboard_id,
            'dashboard_url': dashboard_url,
            'dashboard_name': dashboard_name,
            'wallet_address': wallet_address,
            'ai_session_id': ai_session_id,
            'created_at': dashboard_config['created_at'],
            'ai_instructions': f"Dashboard created! Share this URL with your user: {dashboard_url}",
            'success': True,
            'api_endpoints': {
                'visualizations': f"{base_url}/api/dashboard/{dashboard_id}/visualizations",
                'update': f"{base_url}/api/dashboard/{dashboard_id}/update",
                'config': f"{base_url}/api/dashboard/{dashboard_id}/config"
            }
        }
        
    except Exception as e:
        return {
            'error': f"Failed to create dashboard: {str(e)}",
            'success': False
        }


@api_function(
    protocols=["mcp", "rest"],
    path="/api/get_dashboard_info/{dashboard_id}",
    method="GET",
    tags=["visualization", "dashboard"],
    description="AI retrieves dashboard URL and info for user"
)
async def get_dashboard_info(
    dashboard_id: str = None, 
    ai_session_id: str = None
) -> JSONType:
    """
    AI can retrieve dashboard URL and info for user.
    
    Supports lookup by dashboard_id or ai_session_id to help AI
    find existing dashboards across conversations.
    """
    
    try:
        dashboards_table = get_dashboards_table()
        
        # If no dashboard_id, find by AI session
        if not dashboard_id and ai_session_id:
            response = dashboards_table.query(
                IndexName='AISessionIndex',
                KeyConditionExpression='ai_session_id = :session_id',
                ExpressionAttributeValues={':session_id': ai_session_id},
                ScanIndexForward=False,  # Get most recent first
                Limit=1
            )
            
            if response['Items']:
                dashboard_config = response['Items'][0]
            else:
                return {
                    'error': 'No dashboard found for this AI session',
                    'success': False,
                    'ai_session_id': ai_session_id
                }
        else:
            # Get by dashboard_id
            if not dashboard_id:
                return {
                    'error': 'Either dashboard_id or ai_session_id must be provided',
                    'success': False
                }
                
            response = dashboards_table.get_item(Key={'dashboard_id': dashboard_id})
            
            if 'Item' not in response:
                return {
                    'error': 'Dashboard not found',
                    'success': False,
                    'dashboard_id': dashboard_id
                }
            
            dashboard_config = response['Item']
        
        # Generate response
        base_url = "https://pb-fm-mcp-dev.creativeapptitude.com"
        dashboard_url = f"{base_url}/dashboard/{dashboard_config['dashboard_id']}"
        
        return {
            'dashboard_id': dashboard_config['dashboard_id'],
            'dashboard_url': dashboard_url,
            'dashboard_name': dashboard_config['dashboard_name'],
            'wallet_address': dashboard_config.get('wallet_address'),
            'ai_session_id': dashboard_config.get('ai_session_id'),
            'created_at': dashboard_config['created_at'],
            'last_updated': dashboard_config['last_updated'],
            'active_visualizations': dashboard_config.get('active_visualizations', []),
            'ai_message': f"Your dashboard is available at: {dashboard_url}",
            'success': True
        }
        
    except Exception as e:
        return {
            'error': f"Failed to retrieve dashboard info: {str(e)}",
            'success': False
        }


@api_function(
    protocols=["mcp", "rest"],
    path="/api/create_hash_price_chart",
    method="POST",
    tags=["visualization", "charts"],
    description="Create simple HASH price vs time chart for last 24 hours"
)
async def create_hash_price_chart(
    time_range: str = "24h",
    dashboard_id: str = None
) -> JSONType:
    """
    Create simple HASH price vs time chart using existing market data.
    
    This is our starting point - a basic but functional chart that
    demonstrates the AI visualization system.
    """
    
    try:
        # Import here to avoid circular imports
        from functions.figure_markets_functions import fetch_last_crypto_token_price
        
        # Get recent HASH trades (use existing function)
        price_data = await fetch_last_crypto_token_price("HASH-USD", 50)
        
        if 'MCP-ERROR' in price_data:
            return {
                'error': f"Failed to get price data: {price_data['MCP-ERROR']}",
                'success': False
            }
        
        # Extract time and price data from matches
        matches = price_data.get('matches', [])
        if not matches:
            return {
                'error': 'No price data available',
                'success': False
            }
        
        # Sort by time (oldest first for proper line chart)
        matches_sorted = sorted(matches, key=lambda x: x['created'])
        
        times = [trade['created'] for trade in matches_sorted]
        prices = [float(trade['price']) for trade in matches_sorted]
        volumes = [float(trade['quantity']) for trade in matches_sorted]
        
        # Create simple but attractive Plotly line chart
        plotly_spec = {
            'data': [
                {
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'x': times,
                    'y': prices,
                    'name': 'HASH-USD Price',
                    'line': {
                        'color': '#00ff88',
                        'width': 3
                    },
                    'marker': {
                        'color': '#00ff88',
                        'size': 6,
                        'symbol': 'circle'
                    },
                    'hovertemplate': '<b>%{y:.4f} USD</b><br>%{x}<br><extra></extra>'
                }
            ],
            'layout': {
                'title': {
                    'text': f'HASH Price - Last {len(matches)} Trades',
                    'font': {'size': 20, 'color': '#ffffff'}
                },
                'xaxis': {
                    'title': 'Time',
                    'color': '#ffffff',
                    'gridcolor': '#333333'
                },
                'yaxis': {
                    'title': 'Price (USD)',
                    'color': '#ffffff', 
                    'gridcolor': '#333333',
                    'tickformat': '.4f'
                },
                'paper_bgcolor': '#1e1e1e',
                'plot_bgcolor': '#2a2a2a',
                'font': {'color': '#ffffff'},
                'hovermode': 'closest',
                'showlegend': True,
                'legend': {
                    'bgcolor': 'rgba(0,0,0,0.5)',
                    'bordercolor': '#ffffff',
                    'borderwidth': 1
                }
            }
        }
        
        # Calculate some basic stats
        current_price = prices[-1]
        price_change = prices[-1] - prices[0] if len(prices) > 1 else 0
        price_change_percent = (price_change / prices[0] * 100) if prices[0] != 0 else 0
        total_volume = sum(volumes)
        
        return {
            'visualization_spec': plotly_spec,
            'chart_type': 'hash_price_chart',
            'dashboard_id': dashboard_id,
            'data_points': len(prices),
            'time_range': time_range,
            'current_price': current_price,
            'price_change': price_change,
            'price_change_percent': price_change_percent,
            'total_volume': total_volume,
            'ai_insights': f"HASH is currently trading at ${current_price:.4f}, "
                          f"{'up' if price_change >= 0 else 'down'} "
                          f"{abs(price_change_percent):.2f}% from the start of this data range. "
                          f"Total volume: {total_volume:.0f} HASH across {len(matches)} trades.",
            'success': True
        }
        
    except Exception as e:
        return {
            'error': f"Failed to create HASH price chart: {str(e)}",
            'success': False
        }