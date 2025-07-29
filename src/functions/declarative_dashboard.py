"""
Declarative Dashboard Functions - MVP for Progressive Loading

This module demonstrates AI-orchestrated dashboard creation through
declarative JSON specifications uploaded to S3 in three phases:
1. HTML/CSS layout
2. Plotly configuration (empty charts)
3. Data population
"""

import json
import boto3
from datetime import datetime
from typing import Dict, List, Optional, Any

from registry.decorator import api_function
from utils import JSONType


def get_s3_client():
    """Get S3 client for uploading declarations."""
    return boto3.client('s3')


def get_web_assets_bucket() -> str:
    """Get the web assets bucket name from environment."""
    import os
    bucket = os.environ.get('WEB_ASSETS_BUCKET', '')
    if not bucket:
        raise ValueError("WEB_ASSETS_BUCKET not configured")
    return bucket


@api_function(protocols=["mcp"])



async def declare_dashboard_layout(
    session_id: str,
    layout_html: str,
    layout_css: str,
    title: str = "Blockchain Analytics Dashboard"
) -> JSONType:
    """
    Upload HTML/CSS layout declaration to S3 for dashboard initialization.
    This creates the structure and styling before any data is loaded.
    """
    try:
        s3 = get_s3_client()
        bucket = get_web_assets_bucket()
        
        # Create layout declaration
        layout_spec = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "description": f"Dashboard layout: {title}",
            "html": layout_html,
            "css": layout_css,
            "containers": []
        }
        
        # Upload to S3
        key = f"declarations/{session_id}/layout.json"
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(layout_spec, indent=2),
            ContentType='application/json',
            CacheControl='no-cache'
        )
        
        return {
            'success': True,
            'session_id': session_id,
            'phase': 'layout',
            's3_key': key,
            'dashboard_url': f"/dashboard/declarative?session={session_id}",
            'message': 'Layout declaration uploaded - dashboard will load structure'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to declare dashboard layout'
        }


@api_function(protocols=["mcp"])



async def declare_plotly_charts(
    session_id: str,
    charts: List[Dict[str, Any]]
) -> JSONType:
    """
    Upload Plotly chart configurations to S3.
    Charts will be initialized with axes, titles, and styling but no data.
    
    Example chart config:
    {
        "id": "hash-chart",
        "containerId": "chart-div",
        "layout": {
            "title": "Hash Statistics",
            "xaxis": {"title": "Time"},
            "yaxis": {"title": "Value"}
        }
    }
    """
    try:
        s3 = get_s3_client()
        bucket = get_web_assets_bucket()
        
        # Create Plotly declaration
        plotly_spec = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "description": "Plotly chart configurations",
            "charts": charts
        }
        
        # Upload to S3
        key = f"declarations/{session_id}/plotly.json"
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(plotly_spec, indent=2),
            ContentType='application/json',
            CacheControl='no-cache'
        )
        
        return {
            'success': True,
            'session_id': session_id,
            'phase': 'plotly',
            's3_key': key,
            'charts_configured': len(charts),
            'message': 'Plotly configurations uploaded - charts will initialize empty'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to declare Plotly charts'
        }


@api_function(protocols=["mcp"])



async def declare_chart_data(
    session_id: str,
    datasets: List[Dict[str, Any]]
) -> JSONType:
    """
    Upload data specifications to S3 for chart population.
    Can include direct data or endpoints for fetching.
    
    Example dataset:
    {
        "chartId": "hash-chart",
        "endpoint": "/api/chart/hash_statistics"
    }
    or
    {
        "chartId": "hash-chart",
        "traces": [{
            "x": [...],
            "y": [...],
            "type": "scatter"
        }]
    }
    """
    try:
        s3 = get_s3_client()
        bucket = get_web_assets_bucket()
        
        # Create data declaration
        data_spec = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "description": "Chart data sources",
            "datasets": datasets
        }
        
        # Upload to S3
        key = f"declarations/{session_id}/data.json"
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(data_spec, indent=2),
            ContentType='application/json',
            CacheControl='no-cache'
        )
        
        return {
            'success': True,
            'session_id': session_id,
            'phase': 'data',
            's3_key': key,
            'datasets_configured': len(datasets),
            'message': 'Data declarations uploaded - charts will populate with live data'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to declare chart data'
        }


@api_function(protocols=["mcp"])



async def create_example_dashboard(
    session_id: str,
    wallet_address: str = "demo_wallet"
) -> JSONType:
    """
    One-click creation of a complete example dashboard demonstrating
    the three-phase declarative loading system.
    """
    try:
        # Phase 1: Layout
        layout_html = f"""
        <div id='dashboard-container'>
            <header id='dashboard-header'>
                <h1>Blockchain Analytics - {wallet_address[:8]}...</h1>
                <div id='status-bar'>Loading progressive dashboard...</div>
            </header>
            <main id='dashboard-grid'>
                <section id='panel-main' class='dashboard-panel'>
                    <h2>Hash Price Trends</h2>
                    <div id='price-chart' class='chart-container'></div>
                </section>
                <aside id='panel-side' class='dashboard-panel'>
                    <h2>Portfolio Distribution</h2>
                    <div id='portfolio-chart' class='chart-container'></div>
                </aside>
            </main>
        </div>
        """
        
        layout_css = """
        #dashboard-container {
            min-height: 100vh;
            background: linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%);
            color: #ffffff;
            font-family: system-ui, -apple-system, sans-serif;
        }
        #dashboard-header {
            background: rgba(0,255,136,0.1);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(0,255,136,0.3);
            padding: 24px;
        }
        #dashboard-header h1 {
            margin: 0;
            font-size: 32px;
            background: linear-gradient(135deg, #00ff88 0%, #0088ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        #dashboard-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 24px;
            padding: 24px;
            max-width: 1400px;
            margin: 0 auto;
        }
        .dashboard-panel {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 24px;
            backdrop-filter: blur(5px);
        }
        .chart-container {
            width: 100%;
            height: 400px;
            border-radius: 8px;
            overflow: hidden;
        }
        @media (max-width: 768px) {
            #dashboard-grid { grid-template-columns: 1fr; }
        }
        """
        
        layout_result = await declare_dashboard_layout(
            session_id=session_id,
            layout_html=layout_html,
            layout_css=layout_css,
            title=f"Analytics for {wallet_address}"
        )
        
        if not layout_result['success']:
            return layout_result
        
        # Phase 2: Plotly Charts
        charts = [
            {
                "id": "price-trends",
                "containerId": "price-chart",
                "layout": {
                    "title": {
                        "text": "Hash Price - Last 30 Days",
                        "font": {"color": "#00ff88", "size": 18}
                    },
                    "xaxis": {
                        "title": "Date",
                        "type": "date",
                        "gridcolor": "rgba(255,255,255,0.1)"
                    },
                    "yaxis": {
                        "title": "Price (USD)",
                        "gridcolor": "rgba(255,255,255,0.1)"
                    },
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0.3)",
                    "font": {"color": "#ffffff"}
                },
                "config": {
                    "displayModeBar": false,
                    "responsive": true
                }
            },
            {
                "id": "portfolio-dist",
                "containerId": "portfolio-chart",
                "layout": {
                    "title": {
                        "text": "Portfolio Allocation",
                        "font": {"color": "#00ff88", "size": 18}
                    },
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "font": {"color": "#ffffff"},
                    "showlegend": true,
                    "legend": {"orientation": "v", "x": 0, "y": 0.5}
                },
                "config": {
                    "displayModeBar": false,
                    "responsive": true
                }
            }
        ]
        
        plotly_result = await declare_plotly_charts(
            session_id=session_id,
            charts=charts
        )
        
        if not plotly_result['success']:
            return plotly_result
        
        # Phase 3: Data
        datasets = [
            {
                "chartId": "price-trends",
                "traces": [{
                    "x": ["2024-01-01", "2024-01-08", "2024-01-15", "2024-01-22", "2024-01-29"],
                    "y": [0.0082, 0.0085, 0.0087, 0.0084, 0.0088],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Hash Price",
                    "line": {"color": "#00ff88", "width": 3},
                    "marker": {"size": 10, "color": "#00ff88"}
                }]
            },
            {
                "chartId": "portfolio-dist",
                "traces": [{
                    "labels": ["Staked", "Available", "Rewards", "Vesting"],
                    "values": [19000000000, 2700000000, 1500000000, 800000000],
                    "type": "pie",
                    "hole": 0.4,
                    "marker": {
                        "colors": ["#00ff88", "#0088ff", "#ff8800", "#8800ff"],
                        "line": {"color": "#ffffff", "width": 2}
                    },
                    "textinfo": "label+percent",
                    "textposition": "outside"
                }]
            }
        ]
        
        data_result = await declare_chart_data(
            session_id=session_id,
            datasets=datasets
        )
        
        # Return comprehensive result
        return {
            'success': True,
            'session_id': session_id,
            'dashboard_url': f"/dashboard/declarative?session={session_id}",
            'phases_completed': ['layout', 'plotly', 'data'],
            'message': 'Complete dashboard declared - visit URL to see progressive loading',
            'details': {
                'layout': layout_result,
                'plotly': plotly_result,
                'data': data_result
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to create example dashboard'
        }