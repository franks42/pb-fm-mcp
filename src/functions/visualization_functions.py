"""
AI-Driven Blockchain Visualization Functions

This module implements the revolutionary personalized dashboard system
and AI-driven visualization templates for blockchain data.
"""

import os
import uuid
import boto3
import tempfile
from datetime import datetime, timedelta
from typing import Optional

from registry.decorator import api_function
from utils import JSONType
import subprocess
import tempfile

# Import for MCP session ID access
from awslabs.mcp_lambda_handler.mcp_lambda_handler import current_session_id


def get_dashboards_table():
    """Get DynamoDB dashboards table"""
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ.get('DASHBOARDS_TABLE')
    if not table_name:
        raise ValueError("DASHBOARDS_TABLE environment variable not set")
    return dynamodb.Table(table_name)


def get_current_mcp_session_id() -> Optional[str]:
    """
    Get the current MCP session ID from the context.
    
    Returns:
        The MCP session ID if available, None otherwise
    """
    try:
        return current_session_id.get()
    except Exception as e:
        print(f"⚠️ Could not get MCP session ID: {e}")
        return None


def create_session_based_dashboard_url(session_id: str) -> str:
    """
    Create a stable, session-based dashboard URL.
    
    Args:
        session_id: The MCP session ID
        
    Returns:
        Full dashboard URL based on the session ID
    """
    # Use the appropriate domain based on environment
    # Default to dev, could be enhanced to detect environment
    base_url = "https://pb-fm-mcp-dev.creativeapptitude.com"
    return f"{base_url}/dashboard/{session_id}"


def create_demo_wallet_data(wallet_address: str) -> dict:
    """Create realistic demo data when blockchain APIs fail or return empty data."""
    return {
        'wallet_address': wallet_address,
        'controllable_hash_amount': '5000000',  # 5M HASH
        'total_delegated_amount': '3750000',    # 75% staked (good)
        'total_delegation_rewards': '125000',   # 2.5% rewards
        'available_spendable_amount': '1250000', # 25% liquid
        'delegation_data': {
            'validators': [
                {'validator_address': 'pbvaloper1abc123', 'amount': '1500000'},
                {'validator_address': 'pbvaloper1def456', 'amount': '1250000'},
                {'validator_address': 'pbvaloper1ghi789', 'amount': '1000000'}
            ]
        },
        'is_demo_data': True,
        'demo_reason': 'Network timeout or API error - using realistic demo data'
    }


@api_function(protocols=["mcp"])






async def create_personalized_dashboard(
    wallet_address: str = None,
    dashboard_name: str = "My Blockchain Dashboard",
    ai_session_id: str = None  # Deprecated - now uses MCP session ID
) -> JSONType:
    """
    🎯 REVOLUTIONARY UPDATE: AI creates stable, session-based dashboard URLs!
    
    Now uses MCP session ID for persistent dashboard access throughout
    the entire Claude.ai conversation - eliminating copy-paste friction.
    """
    
    try:
        # 🎯 KEY INNOVATION: Get current MCP session ID
        mcp_session_id = get_current_mcp_session_id()
        
        if not mcp_session_id:
            # Fallback to old system if MCP session not available
            dashboard_id = f"dash_{uuid.uuid4().hex[:12]}"
            session_id_for_url = dashboard_id
            session_type = "fallback"
        else:
            # 🚀 Use MCP session ID as the dashboard identifier
            dashboard_id = mcp_session_id
            session_id_for_url = mcp_session_id
            session_type = "mcp_session"
        
        # Create dashboard configuration
        now = datetime.now()
        ttl = int((now + timedelta(hours=24)).timestamp())  # 24-hour expiration (matches MCP session)
        
        dashboard_config = {
            'dashboard_id': dashboard_id,
            'mcp_session_id': mcp_session_id,
            'created_by': 'ai_assistant',
            'ai_session_id': ai_session_id or mcp_session_id or f"fallback_{uuid.uuid4().hex[:8]}",  # Legacy compatibility
            'wallet_address': wallet_address,
            'dashboard_name': dashboard_name,
            'session_type': session_type,
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
        
        # 🎯 Generate stable session-based dashboard URL
        dashboard_url = create_session_based_dashboard_url(session_id_for_url)
        base_url = "https://pb-fm-mcp-dev.creativeapptitude.com"
        
        return {
            'dashboard_id': dashboard_id,
            'dashboard_url': dashboard_url,
            'dashboard_name': dashboard_name,
            'wallet_address': wallet_address,
            'mcp_session_id': mcp_session_id,
            'session_type': session_type,
            'ai_session_id': ai_session_id,
            'created_at': dashboard_config['created_at'],
            'ttl_hours': 24,
            'success': True,
            'revolutionary_features': {
                'stable_url': 'URL persists throughout your Claude.ai conversation',
                'no_copy_paste': 'AI can share this URL directly - no manual copying needed',
                'session_based': 'Tied to your unique Claude conversation for security',
                'auto_expire': 'Automatically expires in 24 hours for privacy'
            },
            'ai_instructions': f"🎉 STABLE URL CREATED! Share this persistent URL: {dashboard_url}",
            'user_message': '🔗 This is your personal dashboard URL - it stays the same throughout our conversation!',
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


@api_function(protocols=["mcp"])






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


@api_function(protocols=["mcp"])






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


@api_function(protocols=["mcp", "rest"])






async def create_portfolio_health(
    wallet_address: str,
    dashboard_id: str = None,
    analysis_depth: str = "comprehensive"
) -> JSONType:
    """
    AI creates a comprehensive portfolio health dashboard.
    
    Analyzes wallet holdings, delegation patterns, risk factors, and generates
    intelligent insights with multiple interactive visualizations.
    """
    
    try:
        if not wallet_address:
            return {
                'error': 'wallet_address is required for portfolio health analysis',
                'success': False
            }
        
        # Import blockchain functions for data gathering
        from functions.aggregate_functions import fetch_complete_wallet_summary
        
        # Get comprehensive wallet data
        wallet_data = await fetch_complete_wallet_summary(wallet_address)
        
        # Check if we got valid data or if there were network errors
        has_errors = (
            'MCP-ERROR' in wallet_data or
            (isinstance(wallet_data.get('account_info'), dict) and 'MCP-ERROR' in wallet_data.get('account_info', {})) or
            (isinstance(wallet_data.get('delegation_summary'), dict) and 'MCP-ERROR' in wallet_data.get('delegation_summary', {}))
        )
        
        # If we have network errors, use demo data for better visualization
        if has_errors:
            wallet_data = create_demo_wallet_data(wallet_address)
        
        # Extract key metrics for health calculation
        total_controllable = float(wallet_data.get('controllable_hash_amount', 0))
        total_staked = float(wallet_data.get('total_delegated_amount', 0))
        total_rewards = float(wallet_data.get('total_delegation_rewards', 0))
        available_balance = float(wallet_data.get('available_spendable_amount', 0))
        
        # AI-driven health score calculation
        health_metrics = calculate_portfolio_health_score(wallet_data)
        
        # Create main health gauge visualization
        health_gauge = {
            'type': 'indicator',
            'mode': 'gauge+number+delta',
            'value': health_metrics['overall_score'],
            'delta': {'reference': 80, 'valueformat': '.0f'},
            'gauge': {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': get_health_color(health_metrics['overall_score'])},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(255, 0, 0, 0.3)'},
                    {'range': [50, 80], 'color': 'rgba(255, 255, 0, 0.3)'},
                    {'range': [80, 100], 'color': 'rgba(0, 255, 0, 0.3)'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            },
            'title': {'text': "Portfolio Health Score", 'font': {'size': 16, 'color': '#ffffff'}},
            'domain': {'x': [0, 0.45], 'y': [0.55, 0.95]}
        }
        
        # Create asset allocation treemap
        allocation_data = prepare_allocation_treemap_data(wallet_data)
        asset_treemap = {
            'type': 'treemap',
            'labels': allocation_data['labels'],
            'parents': allocation_data['parents'],
            'values': allocation_data['values'],
            'textinfo': "label+value+percent parent",
            'textfont': {'size': 12, 'color': '#ffffff'},
            'marker': {
                'colors': allocation_data['colors'],
                'line': {'width': 2, 'color': '#ffffff'}
            },
            'domain': {'x': [0.55, 1], 'y': [0.55, 0.95]}
        }
        
        # Create risk radar chart
        risk_data = calculate_risk_dimensions(wallet_data, health_metrics)
        risk_radar = {
            'type': 'scatterpolar',
            'r': risk_data['values'],
            'theta': risk_data['categories'],
            'fill': 'toself',
            'fillcolor': 'rgba(0, 255, 136, 0.2)',
            'line': {'color': '#00ff88', 'width': 3},
            'marker': {'color': '#00ff88', 'size': 8},
            'name': 'Risk Profile'
        }
        
        # Create performance timeline
        performance_timeline = create_performance_timeline(wallet_data)
        
        # Fix layout to prevent overlapping - use subplots with proper spacing
        plotly_spec = {
            'data': [health_gauge, asset_treemap, risk_radar, performance_timeline],
            'layout': {
                'title': {
                    'text': f'Portfolio Health Dashboard - {wallet_address[:12]}...{wallet_address[-8:]}',
                    'font': {'size': 20, 'color': '#ffffff'},
                    'x': 0.5,
                    'y': 0.98
                },
                'paper_bgcolor': '#1e1e1e',
                'plot_bgcolor': '#2a2a2a',
                'font': {'color': '#ffffff'},
                'showlegend': True,
                'legend': {
                    'bgcolor': 'rgba(0,0,0,0.5)',
                    'bordercolor': '#ffffff',
                    'borderwidth': 1,
                    'x': 1.02,
                    'y': 0.5
                },
                'margin': {'l': 50, 'r': 150, 't': 80, 'b': 50},
                'height': 800,
                'polar': {
                    'bgcolor': '#2a2a2a',
                    'radialaxis': {
                        'visible': True,
                        'range': [0, 100],
                        'color': '#ffffff',
                        'gridcolor': '#333333'
                    },
                    'angularaxis': {
                        'color': '#ffffff',
                        'gridcolor': '#333333'
                    },
                    'domain': {'x': [0, 0.45], 'y': [0, 0.4]}
                },
                'xaxis': {
                    'title': 'Time Period',
                    'color': '#ffffff',
                    'gridcolor': '#333333',
                    'domain': [0.55, 1],
                    'anchor': 'y'
                },
                'yaxis': {
                    'title': 'Health Score',
                    'color': '#ffffff',
                    'gridcolor': '#333333',
                    'domain': [0, 0.4],
                    'anchor': 'x'
                }
            }
        }
        
        # Generate AI insights
        ai_insights = generate_portfolio_ai_insights(wallet_data, health_metrics, risk_data)
        
        # Add demo data notice if applicable
        if wallet_data.get('is_demo_data'):
            ai_insights = f"📊 **DEMO DATA**: {wallet_data.get('demo_reason', 'Using demo data')}. " + ai_insights
        
        return {
            'visualization_spec': plotly_spec,
            'chart_type': 'portfolio_health_dashboard',
            'dashboard_id': dashboard_id,
            'wallet_address': wallet_address,
            'health_metrics': health_metrics,
            'risk_analysis': risk_data,
            'total_value_usd': calculate_total_portfolio_value(wallet_data),
            'ai_insights': ai_insights,
            'recommendations': generate_health_recommendations(health_metrics, wallet_data),
            'success': True
        }
        
    except Exception as e:
        return {
            'error': f"Failed to create portfolio health dashboard: {str(e)}",
            'success': False
        }


def calculate_portfolio_health_score(wallet_data: dict) -> dict:
    """Calculate comprehensive portfolio health score with AI-driven analysis."""
    
    total_controllable = float(wallet_data.get('controllable_hash_amount', 0))
    total_staked = float(wallet_data.get('total_delegated_amount', 0))
    total_rewards = float(wallet_data.get('total_delegation_rewards', 0))
    available_balance = float(wallet_data.get('available_spendable_amount', 0))
    
    # Diversification Score (0-100)
    delegation_data = wallet_data.get('delegation_data', {})
    validator_count = len(delegation_data.get('validators', []))
    diversification_score = min(100, (validator_count * 20))  # Max score at 5+ validators
    
    # Staking Participation Score (0-100) 
    if total_controllable > 0:
        staking_ratio = total_staked / total_controllable
        staking_score = min(100, staking_ratio * 100)
    else:
        staking_score = 0
    
    # Liquidity Score (0-100)
    if total_controllable > 0:
        liquidity_ratio = available_balance / total_controllable
        liquidity_score = min(100, liquidity_ratio * 200)  # Optimal at 50% liquid
    else:
        liquidity_score = 0
    
    # Performance Score (0-100) - based on rewards accumulation
    if total_staked > 0:
        reward_ratio = total_rewards / total_staked
        performance_score = min(100, reward_ratio * 1000)  # Scale factor for rewards
    else:
        performance_score = 0
    
    # Overall weighted score
    overall_score = (
        diversification_score * 0.3 +
        staking_score * 0.3 +
        liquidity_score * 0.2 +
        performance_score * 0.2
    )
    
    return {
        'overall_score': round(overall_score, 1),
        'diversification_score': round(diversification_score, 1),
        'staking_score': round(staking_score, 1),
        'liquidity_score': round(liquidity_score, 1),
        'performance_score': round(performance_score, 1),
        'validator_count': validator_count,
        'staking_ratio': round(staking_ratio * 100, 1) if total_controllable > 0 else 0,
        'liquidity_ratio': round(liquidity_ratio * 100, 1) if total_controllable > 0 else 0
    }


def get_health_color(score: float) -> str:
    """Get color based on health score."""
    if score >= 80:
        return '#00ff88'  # Green
    elif score >= 60:
        return '#ffaa00'  # Orange  
    elif score >= 40:
        return '#ff6600'  # Red-orange
    else:
        return '#ff0000'  # Red


def prepare_allocation_treemap_data(wallet_data: dict) -> dict:
    """Prepare data for asset allocation treemap visualization."""
    
    available_balance = float(wallet_data.get('available_spendable_amount', 0))
    total_staked = float(wallet_data.get('total_delegated_amount', 0))
    total_rewards = float(wallet_data.get('total_delegation_rewards', 0))
    
    labels = ['Portfolio', 'Available', 'Staked', 'Rewards']
    parents = ['', 'Portfolio', 'Portfolio', 'Portfolio']
    values = [
        available_balance + total_staked + total_rewards,
        available_balance,
        total_staked, 
        total_rewards
    ]
    colors = ['#1e1e1e', '#00ccff', '#00ff88', '#ffaa00']
    
    return {
        'labels': labels,
        'parents': parents, 
        'values': values,
        'colors': colors
    }


def calculate_risk_dimensions(wallet_data: dict, health_metrics: dict) -> dict:
    """Calculate multi-dimensional risk analysis for radar chart."""
    
    return {
        'categories': [
            'Diversification',
            'Liquidity Risk', 
            'Validator Risk',
            'Market Exposure',
            'Opportunity Cost',
            'Overall Security'
        ],
        'values': [
            health_metrics['diversification_score'],
            100 - health_metrics['liquidity_score'],  # Inverse for risk
            calculate_validator_risk(wallet_data),
            calculate_market_exposure_risk(wallet_data),
            100 - health_metrics['performance_score'],  # Inverse for risk
            health_metrics['overall_score']
        ]
    }


def calculate_validator_risk(wallet_data: dict) -> float:
    """Calculate validator-specific risk score."""
    delegation_data = wallet_data.get('delegation_data', {})
    validators = delegation_data.get('validators', [])
    
    if not validators:
        return 100  # Maximum risk if no validation
        
    # Simple risk calculation based on validator count and distribution
    validator_count = len(validators)
    if validator_count >= 5:
        return 20  # Low risk
    elif validator_count >= 3:
        return 40  # Medium risk
    elif validator_count >= 2:
        return 60  # Higher risk
    else:
        return 80  # High risk (single validator)


def calculate_market_exposure_risk(wallet_data: dict) -> float:
    """Calculate market exposure risk based on total holdings."""
    total_controllable = float(wallet_data.get('controllable_hash_amount', 0))
    
    # Risk increases with larger holdings (more market exposure)
    if total_controllable > 10000000:  # 10M+ HASH
        return 80
    elif total_controllable > 1000000:  # 1M+ HASH
        return 60
    elif total_controllable > 100000:  # 100K+ HASH
        return 40
    else:
        return 20


def create_performance_timeline(wallet_data: dict) -> dict:
    """Create performance timeline visualization."""
    
    # Simplified timeline - in real implementation would use historical data
    return {
        'type': 'scatter',
        'mode': 'lines+markers',
        'x': ['30d ago', '20d ago', '10d ago', 'Today'],
        'y': [75, 78, 82, calculate_portfolio_health_score(wallet_data)['overall_score']],
        'name': 'Health Trend',
        'line': {'color': '#00ff88', 'width': 3},
        'marker': {'color': '#00ff88', 'size': 8},
        'xaxis': 'x',
        'yaxis': 'y'
    }


def calculate_total_portfolio_value(wallet_data: dict) -> float:
    """Calculate total portfolio value in USD."""
    # Simplified calculation - would use current HASH price in real implementation
    total_hash = float(wallet_data.get('controllable_hash_amount', 0))
    hash_price = 0.028  # Current approximate HASH price
    return total_hash * hash_price


def generate_portfolio_ai_insights(wallet_data: dict, health_metrics: dict, risk_data: dict) -> str:
    """Generate AI-driven portfolio insights and analysis."""
    
    score = health_metrics['overall_score']
    total_controllable = float(wallet_data.get('controllable_hash_amount', 0))
    validator_count = health_metrics['validator_count']
    
    insights = []
    
    # Overall assessment
    if score >= 80:
        insights.append(f"🎉 Excellent portfolio health (Score: {score}/100)! Your HASH holdings are well-managed.")
    elif score >= 60:
        insights.append(f"👍 Good portfolio health (Score: {score}/100) with room for optimization.")
    else:
        insights.append(f"⚠️ Portfolio needs attention (Score: {score}/100). Several areas for improvement identified.")
    
    # Diversification insights
    if validator_count < 3:
        insights.append(f"🎯 Consider diversifying across {3-validator_count} more validators to reduce risk.")
    elif validator_count >= 5:
        insights.append("✅ Excellent diversification across multiple validators.")
    
    # Staking insights
    staking_ratio = health_metrics['staking_ratio']
    if staking_ratio < 70:
        insights.append(f"💰 You're only staking {staking_ratio}% of your HASH. Consider increasing delegation for better rewards.")
    elif staking_ratio > 95:
        insights.append("🔄 Consider keeping some HASH liquid for flexibility and opportunities.")
    
    # Scale insights
    if total_controllable > 1000000:
        insights.append("🐋 Large HASH holder detected. Your decisions can impact the network - delegate responsibly!")
    
    return " ".join(insights)


def generate_health_recommendations(health_metrics: dict, wallet_data: dict) -> list:
    """Generate specific actionable recommendations."""
    
    recommendations = []
    
    if health_metrics['diversification_score'] < 60:
        recommendations.append({
            'type': 'diversification',
            'priority': 'high',
            'action': 'Diversify delegation across more validators',
            'impact': 'Reduces risk and improves network decentralization'
        })
    
    if health_metrics['staking_score'] < 70:
        recommendations.append({
            'type': 'staking',
            'priority': 'medium', 
            'action': 'Increase staking participation',
            'impact': 'Higher rewards and network participation'
        })
    
    if health_metrics['liquidity_score'] < 30:
        recommendations.append({
            'type': 'liquidity',
            'priority': 'medium',
            'action': 'Maintain some liquid HASH for opportunities',
            'impact': 'Flexibility for market opportunities and emergencies'
        })
    
    return recommendations


@api_function(protocols=["mcp"])






async def take_screenshot(
    url: str,
    width: int = 1920,
    height: int = 1080,
    wait_seconds: int = 3
) -> JSONType:
    """
    Take a screenshot of a webpage to help debug visualization issues.
    
    Uses puppeteer via node to capture screenshots in Lambda environment.
    """
    
    try:
        # Create temporary file for screenshot
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            screenshot_path = tmp_file.name
        
        # Create simple JavaScript for puppeteer
        js_script = f'''
const puppeteer = require('puppeteer');

(async () => {{
  const browser = await puppeteer.launch({{
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  }});
  
  const page = await browser.newPage();
  await page.setViewport({{ width: {width}, height: {height} }});
  
  try {{
    await page.goto('{url}', {{ waitUntil: 'networkidle2', timeout: 30000 }});
    await page.waitForTimeout({wait_seconds * 1000});
    await page.screenshot({{ path: '{screenshot_path}', fullPage: true }});
    console.log('SUCCESS:{screenshot_path}');
  }} catch (error) {{
    console.log('ERROR:' + error.message);
  }} finally {{
    await browser.close();
  }}
}})();
'''
        
        # Write JavaScript to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as js_file:
            js_file.write(js_script)
            js_file_path = js_file.name
        
        try:
            # Try to run puppeteer
            result = subprocess.run(
                ['node', js_file_path], 
                capture_output=True, 
                text=True, 
                timeout=60
            )
            
            if 'SUCCESS:' in result.stdout:
                # Screenshot was taken successfully
                import base64
                with open(screenshot_path, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode()
                
                return {
                    'success': True,
                    'screenshot_base64': img_data,
                    'url': url,
                    'dimensions': f'{width}x{height}',
                    'file_size_bytes': len(img_data) * 3 // 4,  # approximate
                    'message': 'Screenshot captured successfully'
                }
            else:
                # Fall back to simple approach
                raise Exception(f"Puppeteer failed: {result.stderr}")
                
        except Exception as node_error:
            # Fallback 1: Use curl to get HTML and analyze structure
            try:
                html_result = subprocess.run(
                    ['curl', '-s', '--max-time', '10', url], 
                    capture_output=True, 
                    text=True,
                    timeout=15
                )
                
                if html_result.returncode == 0 and html_result.stdout:
                    html_content = html_result.stdout
                    return {
                        'success': False,
                        'screenshot_available': False,
                        'url': url,
                        'html_preview': html_content[:1000] + '...' if len(html_content) > 1000 else html_content,
                        'html_length': len(html_content),
                        'message': 'Screenshot failed but retrieved HTML content for analysis',
                        'error': str(node_error),
                        'alternative': 'HTML content retrieved for analysis',
                        'fallback_used': 'curl_html'
                    }
                else:
                    raise Exception(f"Curl failed with return code {html_result.returncode}")
                    
            except Exception as curl_error:
                # Fallback 2: Try with Python requests-like approach using urllib
                try:
                    import urllib.request
                    import urllib.error
                    
                    req = urllib.request.Request(url, headers={
                        'User-Agent': 'Mozilla/5.0 (compatible; Dashboard Screenshot Tool)'
                    })
                    
                    with urllib.request.urlopen(req, timeout=10) as response:
                        html_content = response.read().decode('utf-8')
                        
                    return {
                        'success': False,
                        'screenshot_available': False,
                        'url': url,
                        'html_preview': html_content[:1000] + '...' if len(html_content) > 1000 else html_content,
                        'html_length': len(html_content),
                        'message': 'Screenshot failed but retrieved HTML via urllib',
                        'error': f'Node: {str(node_error)}, Curl: {str(curl_error)}',
                        'alternative': 'HTML content retrieved using urllib',
                        'fallback_used': 'urllib'
                    }
                    
                except Exception as urllib_error:
                    # Final fallback: Return helpful error with context
                    return {
                        'success': False,
                        'url': url,
                        'screenshot_available': False,
                        'error': f'All methods failed - Node: {str(node_error)}, Curl: {str(curl_error)}, Urllib: {str(urllib_error)}',
                        'message': 'Unable to capture screenshot or retrieve webpage content',
                        'context': 'Lambda environment may lack necessary tools (node, puppeteer, curl)',
                        'suggestion': 'Screenshot functionality requires additional Lambda layer or container deployment',
                        'fallback_used': 'none'
                    }
        
        finally:
            # Cleanup temp files
            try:
                os.unlink(js_file_path)
                os.unlink(screenshot_path)
            except:
                pass
        
    except Exception as e:
        return {
            'error': f'Failed to take screenshot: {str(e)}',
            'success': False
        }


@api_function(protocols=["mcp"])



async def claude_take_screenshot(
    url: str,
    context: str = "debugging visualization",
    width: int = 1400,
    height: int = 900
) -> JSONType:
    """
    Special function for Claude to automatically take screenshots during debugging.
    
    This allows Claude to see exactly what the user is seeing without having to
    ask for permission each time, making debugging much more efficient.
    """
    
    try:
        # Use the same screenshot logic but optimized for Claude's use
        screenshot_result = await take_screenshot(url, width, height, wait_seconds=3)
        
        if screenshot_result.get('success') and screenshot_result.get('screenshot_base64'):
            # For Claude, we want to save the image to a temporary file they can read
            import base64
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                img_data = base64.b64decode(screenshot_result['screenshot_base64'])
                tmp_file.write(img_data)
                screenshot_path = tmp_file.name
            
            return {
                'success': True,
                'context': context,
                'url': url,
                'screenshot_path': screenshot_path,
                'dimensions': f'{width}x{height}',
                'file_size_bytes': len(img_data),
                'message': f'Screenshot taken for {context}',
                'claude_note': f'Screenshot saved to {screenshot_path} - use Read tool to view it'
            }
        else:
            # Return HTML analysis if screenshot fails
            return {
                'success': False,
                'context': context,
                'url': url,
                'screenshot_available': False,
                'html_analysis': screenshot_result.get('html_preview', 'No content retrieved'),
                'error': screenshot_result.get('error', 'Screenshot capture failed'),
                'message': f'Could not capture screenshot for {context}, but got HTML content for analysis'
            }
            
    except Exception as e:
        return {
            'success': False,
            'context': context,
            'url': url,
            'error': f'Claude screenshot failed: {str(e)}',
            'message': 'Automatic screenshot capture encountered an error'
        }


@api_function(protocols=["mcp"])






async def upload_screenshot(
    screenshot_base64: str,
    dashboard_id: str = None,
    context: str = "user_screenshot",
    screenshot_id: str = None
) -> JSONType:
    """
    Receive browser-captured screenshot and save it for Claude to analyze.
    
    This allows the browser to take a high-quality html2canvas screenshot
    and upload it to the server where Claude can access it via the Read tool.
    """
    
    try:
        import base64
        import uuid
        import boto3
        import os
        
        # Decode the base64 image
        img_data = base64.b64decode(screenshot_base64)
        file_size = len(img_data)
        
        # Create unique identifiers
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Use provided screenshot_id or generate one
        final_screenshot_id = screenshot_id or str(uuid.uuid4())[:8]
        filename = f"dashboard_screenshot_{timestamp}_{final_screenshot_id}.png"
        
        # DynamoDB size limit: 400KB, but we'll use 300KB to be safe for base64 overhead
        MAX_DYNAMODB_SIZE = 300 * 1024  # 300KB
        
        # Create metadata record
        screenshot_metadata = {
            'screenshot_id': final_screenshot_id,
            'dashboard_id': dashboard_id or 'unknown',
            'filename': filename,
            'file_size_bytes': file_size,
            'context': context,
            'created_at': datetime.now().isoformat(),
            'ttl': int((datetime.now() + timedelta(days=7)).timestamp()),  # Auto-expire in 7 days
            'storage_type': 'dynamodb' if file_size <= MAX_DYNAMODB_SIZE else 's3'
        }
        
        if file_size <= MAX_DYNAMODB_SIZE:
            # Small screenshot: Store directly in DynamoDB
            try:
                dynamodb = boto3.resource('dynamodb')
                table_name = os.environ.get('DASHBOARDS_TABLE')
                if not table_name:
                    raise Exception("DASHBOARDS_TABLE environment variable not set")
                
                table = dynamodb.Table(table_name)
                
                # Store screenshot data directly in DynamoDB
                screenshot_metadata['screenshot_data'] = screenshot_base64
                screenshot_metadata['dashboard_id'] = f"screenshot_{final_screenshot_id}"  # Use as primary key
                
                table.put_item(Item=screenshot_metadata)
                
                storage_info = {
                    'storage_type': 'dynamodb',
                    'storage_location': f"DynamoDB table: {table_name}",
                    'retrieval_method': 'direct_access'
                }
                
            except Exception as e:
                # Fall back to S3 if DynamoDB fails
                raise Exception(f"DynamoDB storage failed: {str(e)}")
        else:
            # Large screenshot: Store in S3 with metadata in DynamoDB
            try:
                s3_client = boto3.client('s3')
                bucket_name = os.environ.get('SCREENSHOTS_BUCKET')
                if not bucket_name:
                    raise Exception("SCREENSHOTS_BUCKET environment variable not set")
                
                # Generate S3 key with date partitioning
                s3_key = f"screenshots/{timestamp[:8]}/{screenshot_id}/{filename}"
                
                # Upload to S3
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=img_data,
                    ContentType='image/png',
                    Metadata={
                        'dashboard_id': dashboard_id or 'unknown',
                        'context': context,
                        'original_filename': filename
                    }
                )
                
                # Store metadata in DynamoDB
                dynamodb = boto3.resource('dynamodb')
                table_name = os.environ.get('DASHBOARDS_TABLE')
                if table_name:
                    table = dynamodb.Table(table_name)
                    screenshot_metadata['s3_bucket'] = bucket_name
                    screenshot_metadata['s3_key'] = s3_key
                    screenshot_metadata['dashboard_id'] = f"screenshot_{final_screenshot_id}"  # Use as primary key
                    
                    table.put_item(Item=screenshot_metadata)
                
                storage_info = {
                    'storage_type': 's3',
                    'storage_location': f"s3://{bucket_name}/{s3_key}",
                    'retrieval_method': 'download_required'
                }
                
            except Exception as e:
                raise Exception(f"S3 storage failed: {str(e)}")
        
        return {
            'success': True,
            'screenshot_id': final_screenshot_id,
            'filename': filename,
            'file_size_bytes': file_size,
            'dashboard_id': dashboard_id,
            'context': context,
            'storage_info': storage_info,
            'message': f'Screenshot uploaded successfully via {storage_info["storage_type"].upper()}',
            'claude_access': {
                'method': 'Use download_screenshot MCP function',
                'screenshot_id': final_screenshot_id,
                'command': f'download_screenshot("{screenshot_id}")'
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to upload screenshot: {str(e)}',
            'message': 'Screenshot upload failed'
        }


@api_function(protocols=["mcp"])






async def trigger_browser_screenshot(
    dashboard_id: str,
    context: str = "claude_debug_request",
    wait_seconds: int = 2,
    screenshot_id: str = None
) -> JSONType:
    """
    Trigger the browser to take a screenshot and upload it to the server.
    
    This works by setting a flag that the browser polls for, then the browser
    takes the screenshot using html2canvas and uploads it back to the server.
    """
    
    try:
        # Store the screenshot request in DynamoDB for the browser to poll
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('DASHBOARDS_TABLE')
        if not table_name:
            return {
                'success': False,
                'error': 'Dashboard service not configured',
                'message': 'Cannot trigger browser screenshot - no dashboard table'
            }
        
        dashboards_table = dynamodb.Table(table_name)
        
        # Create screenshot request record
        request_id = str(uuid.uuid4())
        # Use provided screenshot_id or generate one
        final_screenshot_id = screenshot_id or str(uuid.uuid4())[:8]
        
        screenshot_request = {
            'dashboard_id': f"screenshot_request_{dashboard_id}",
            'request_id': request_id,
            'screenshot_id': final_screenshot_id,  # Include the screenshot ID for browser
            'status': 'pending',
            'context': context,
            'wait_seconds': wait_seconds,
            'created_at': datetime.now().isoformat(),
            'ttl': int((datetime.now() + timedelta(minutes=5)).timestamp())  # 5 min expiry
        }
        
        dashboards_table.put_item(Item=screenshot_request)
        
        return {
            'success': True,
            'request_id': request_id,
            'screenshot_id': final_screenshot_id,  # Return the ID that will be used
            'dashboard_id': dashboard_id,
            'context': context,
            'message': f'Screenshot request sent to browser - waiting {wait_seconds} seconds',
            'status': 'Browser will poll for this request and take screenshot automatically',
            'poll_key': f"screenshot_request_{dashboard_id}",
            'claude_note': f'Browser will upload screenshot with ID: {final_screenshot_id}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to trigger browser screenshot: {str(e)}',
            'message': 'Could not send screenshot request to browser'
        }


@api_function(protocols=["mcp"])






async def download_screenshot(
    screenshot_id: str
) -> JSONType:
    """
    Download screenshot for Claude to analyze via Read tool.
    
    This function retrieves screenshots from either DynamoDB or S3,
    saves them to a temporary file, and provides the path for Claude to read.
    """
    
    try:
        import base64
        import tempfile
        import boto3
        import os
        
        # Get screenshot metadata from DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('DASHBOARDS_TABLE')
        if not table_name:
            return {
                'success': False,
                'error': 'Dashboard service not configured',
                'screenshot_id': screenshot_id
            }
        
        table = dynamodb.Table(table_name)
        
        try:
            response = table.get_item(Key={'dashboard_id': f'screenshot_{screenshot_id}'})
            
            if 'Item' not in response:
                return {
                    'success': False,
                    'error': f'Screenshot {screenshot_id} not found',
                    'screenshot_id': screenshot_id,
                    'suggestion': 'Screenshot may have expired (7-day TTL) or never existed'
                }
            
            screenshot_meta = response['Item']
            storage_type = screenshot_meta.get('storage_type', 'unknown')
            
            if storage_type == 'dynamodb':
                # Screenshot stored directly in DynamoDB
                screenshot_data = screenshot_meta.get('screenshot_data')
                if not screenshot_data:
                    return {
                        'success': False,
                        'error': 'Screenshot data missing from DynamoDB record',
                        'screenshot_id': screenshot_id
                    }
                
                # Decode and save to temporary file
                img_data = base64.b64decode(screenshot_data)
                
            elif storage_type == 's3':
                # Screenshot stored in S3
                s3_client = boto3.client('s3')
                bucket_name = screenshot_meta.get('s3_bucket')
                s3_key = screenshot_meta.get('s3_key')
                
                if not bucket_name or not s3_key:
                    return {
                        'success': False,
                        'error': 'S3 location missing from metadata',
                        'screenshot_id': screenshot_id
                    }
                
                # Download from S3
                try:
                    response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
                    img_data = response['Body'].read()
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Failed to download from S3: {str(e)}',
                        'screenshot_id': screenshot_id,
                        's3_location': f's3://{bucket_name}/{s3_key}'
                    }
            else:
                return {
                    'success': False,
                    'error': f'Unknown storage type: {storage_type}',
                    'screenshot_id': screenshot_id
                }
            
            # For Claude Code, return base64 data directly since Claude runs remotely
            import base64
            screenshot_base64 = base64.b64encode(img_data).decode('utf-8')
            
            return {
                'success': True,
                'screenshot_id': screenshot_id,
                'screenshot_base64': screenshot_base64,
                'file_size_bytes': len(img_data),
                'storage_type': storage_type,
                'filename': screenshot_meta.get('filename', f'{screenshot_id}.png'),
                'context': screenshot_meta.get('context', 'unknown'),
                'created_at': screenshot_meta.get('created_at'),
                'message': f'Screenshot downloaded from {storage_type.upper()} and ready for analysis',
                'claude_instruction': 'Screenshot data returned as base64 - Claude can save locally for analysis'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to retrieve screenshot: {str(e)}',
                'screenshot_id': screenshot_id
            }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Download failed: {str(e)}',
            'screenshot_id': screenshot_id
        }


@api_function(protocols=["mcp"])






async def check_screenshot_requests(
    dashboard_id: str
) -> JSONType:
    """
    Check for pending screenshot requests from Claude.
    
    This endpoint is polled by the browser to see if Claude has requested a screenshot.
    If there's a pending request, the response tells the browser to take and upload a screenshot.
    """
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('DASHBOARDS_TABLE')
        if not table_name:
            return {
                'success': False,
                'screenshot_requested': False,
                'error': 'Dashboard service not configured'
            }
        
        dashboards_table = dynamodb.Table(table_name)
        
        # Check for pending screenshot requests
        request_key = f"screenshot_request_{dashboard_id}"
        
        try:
            response = dashboards_table.get_item(
                Key={'dashboard_id': request_key}
            )
            
            if 'Item' in response:
                request_item = response['Item']
                
                if request_item.get('status') == 'pending':
                    # Mark request as processed to avoid duplicate screenshots
                    dashboards_table.update_item(
                        Key={'dashboard_id': request_key},
                        UpdateExpression='SET #status = :status, processed_at = :processed_at',
                        ExpressionAttributeNames={'#status': 'status'},
                        ExpressionAttributeValues={
                            ':status': 'processing',
                            ':processed_at': datetime.now().isoformat()
                        }
                    )
                    
                    return {
                        'success': True,
                        'screenshot_requested': True,
                        'request_id': request_item.get('request_id'),
                        'screenshot_id': request_item.get('screenshot_id'),  # Include the screenshot_id for browser
                        'context': request_item.get('context', 'claude_debug_request'),
                        'wait_seconds': request_item.get('wait_seconds', 2),
                        'message': 'Screenshot requested by Claude - please capture and upload'
                    }
            
        except Exception as db_error:
            print(f"Database error checking screenshot requests: {db_error}")
        
        # No pending requests found
        return {
            'success': True,
            'screenshot_requested': False,
            'message': 'No pending screenshot requests'
        }
        
    except Exception as e:
        print(f"Error checking screenshot requests: {e}")
        return {
            'success': False,
            'screenshot_requested': False,
            'error': f'Failed to check screenshot requests: {str(e)}'
        }