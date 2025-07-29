"""
Dynamic Visualization Configuration System

Enables real-time Plotly chart updates through DynamoDB storage,
eliminating the need for code changes and redeployment.
"""

import json
import os
import boto3
from boto3.dynamodb.types import TypeSerializer
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from decimal import Decimal
from registry import api_function
from utils import JSONType


def convert_floats_to_decimal(obj):
    """Convert floats to Decimal for DynamoDB compatibility."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(v) for v in obj]
    else:
        return obj


@api_function(protocols=[])





async def update_chart_config(
    dashboard_id: str,
    chart_element: str,  # e.g., "gauge", "treemap", "scatter"
    updates: dict,
    context: str = "ai_optimization"
) -> JSONType:
    """
    AI can fine-tune chart appearance in real-time by updating DynamoDB config.
    
    Example updates for gauge chart:
    {
        "gauge.bar.color": "#00ff88",
        "gauge.steps[0].color": "rgba(255, 0, 0, 0.5)",
        "title.text": "Portfolio Health Score (AI Optimized)"
    }
    """
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ.get('DASHBOARDS_TABLE'))
        
        # Get current config
        config_key = f"config_{dashboard_id}"
        response = table.get_item(Key={'dashboard_id': config_key})
        
        if 'Item' not in response:
            # Initialize with default Portfolio Health config
            current_config = get_default_portfolio_health_config()
        else:
            current_config = response['Item']['plotly_config']
        
        # Apply updates using dot notation
        updated_config = apply_nested_updates(current_config, chart_element, updates)
        
        # Save updated config with version tracking (convert floats to Decimal for DynamoDB)
        table.put_item(
            Item={
                'dashboard_id': config_key,
                'plotly_config': convert_floats_to_decimal(updated_config),
                'last_modified': datetime.now().isoformat(),
                'modified_by': context,
                'version': response['Item'].get('version', 0) + 1 if 'Item' in response else 1,
                'ttl': int((datetime.now() + timedelta(days=30)).timestamp())
            }
        )
        
        return {
            'success': True,
            'message': f'Updated {chart_element} configuration',
            'preview_url': f'/dashboard/{dashboard_id}?config=latest',
            'changes_applied': updates,
            'version': response['Item'].get('version', 0) + 1 if 'Item' in response else 1
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to update config: {str(e)}'
        }


@api_function(protocols=["rest"])





async def get_dashboard_config(
    dashboard_id: str,
    version: Optional[int] = None
) -> JSONType:
    """
    Retrieve dashboard configuration for rendering.
    Used by dashboard JavaScript to poll for updates.
    """
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ.get('DASHBOARDS_TABLE'))
        
        config_key = f"config_{dashboard_id}"
        response = table.get_item(Key={'dashboard_id': config_key})
        
        if 'Item' not in response:
            # Return default config
            return {
                'success': True,
                'config': get_default_portfolio_health_config(),
                'version': 0,
                'is_default': True
            }
        
        return {
            'success': True,
            'config': response['Item']['plotly_config'],
            'version': response['Item'].get('version', 1),
            'last_modified': response['Item'].get('last_modified'),
            'is_default': False
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to get config: {str(e)}'
        }


@api_function(protocols=[])



async def optimize_chart_colors(
    dashboard_id: str,
    optimization_goal: str = "readability"
) -> JSONType:
    """
    Claude can experiment with different color schemes.
    
    Example: "Make the gauge more visible in dark mode"
    """
    
    color_schemes = {
        'high_contrast': {
            'gauge.bar.color': '#00ff00',
            'gauge.bgcolor': '#000000',
            'gauge.bordercolor': '#ffffff'
        },
        'colorblind_friendly': {
            'gauge.bar.color': '#0173B2',
            'gauge.steps[0].color': '#CC78BC',
            'gauge.steps[1].color': '#ECE133',
            'gauge.steps[2].color': '#56B4E9'
        },
        'subtle_dark': {
            'gauge.bar.color': '#4a9eff',
            'gauge.bgcolor': 'rgba(255, 255, 255, 0.05)',
            'gauge.bordercolor': 'rgba(255, 255, 255, 0.2)'
        }
    }
    
    # Apply color scheme based on goal
    scheme = color_schemes.get(optimization_goal, color_schemes['high_contrast'])
    
    result = await update_chart_config(
        dashboard_id=dashboard_id,
        chart_element='gauge',
        updates=scheme,
        context=f'ai_color_optimization_{optimization_goal}'
    )
    
    return {
        'success': result['success'],
        'optimization_goal': optimization_goal,
        'changes_applied': scheme,
        'message': f'Applied {optimization_goal} color scheme. Check the dashboard to see if it looks better.',
        'preview_url': result.get('preview_url')
    }


def apply_nested_updates(config: dict, element: str, updates: dict) -> dict:
    """
    Apply updates to nested configuration using dot notation.
    
    Example:
    element = "gauge"
    updates = {"bar.color": "#00ff88", "title.text": "New Title"}
    """
    
    import copy
    updated_config = copy.deepcopy(config)
    
    # Find the element in the data array
    for i, trace in enumerate(updated_config.get('data', [])):
        if trace.get('type') == element or (element == 'gauge' and trace.get('type') == 'indicator'):
            # Apply each update
            for key_path, value in updates.items():
                keys = key_path.split('.')
                current = trace
                
                # Navigate to the nested property
                for key in keys[:-1]:
                    if '[' in key:
                        # Handle array access like "steps[0]"
                        base_key, index = key.split('[')
                        index = int(index.rstrip(']'))
                        if base_key not in current:
                            current[base_key] = []
                        while len(current[base_key]) <= index:
                            current[base_key].append({})
                        current = current[base_key][index]
                    else:
                        if key not in current:
                            current[key] = {}
                        current = current[key]
                
                # Set the final value
                final_key = keys[-1]
                if '[' in final_key:
                    base_key, index = final_key.split('[')
                    index = int(index.rstrip(']'))
                    if base_key not in current:
                        current[base_key] = []
                    while len(current[base_key]) <= index:
                        current[base_key].append({})
                    current[base_key][index] = value
                else:
                    current[final_key] = value
            
            break
    
    # Also check layout updates
    if element == 'layout':
        for key_path, value in updates.items():
            keys = key_path.split('.')
            current = updated_config.get('layout', {})
            
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            current[keys[-1]] = value
    
    return updated_config


def get_default_portfolio_health_config() -> dict:
    """Get the default Portfolio Health dashboard configuration."""
    
    return {
        "data": [{
            "type": "indicator",
            "mode": "gauge+number+delta",
            "value": 75,
            "delta": {"reference": 80, "valueformat": ".0f"},
            "gauge": {
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkblue"},
                "bar": {"color": "#4a9eff"},
                "bgcolor": "rgba(255, 255, 255, 0.02)",
                "borderwidth": 2,
                "bordercolor": "rgba(255, 255, 255, 0.2)",
                "steps": [
                    {"range": [0, 50], "color": "rgba(255, 0, 0, 0.3)"},
                    {"range": [50, 80], "color": "rgba(255, 255, 0, 0.3)"},
                    {"range": [80, 100], "color": "rgba(0, 255, 0, 0.3)"}
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 90
                }
            },
            "title": {"text": "Portfolio Health Score", "font": {"size": 16, "color": "#ffffff"}},
            "domain": {"x": [0, 0.45], "y": [0.55, 0.95]}
        }],
        "layout": {
            "paper_bgcolor": "#1e1e1e",
            "plot_bgcolor": "#2a2a2a",
            "font": {"color": "#ffffff"},
            "height": 800,
            "showlegend": True,
            "margin": {"l": 50, "r": 150, "t": 80, "b": 50}
        }
    }


@api_function(protocols=[])



async def experiment_gauge_styles(
    dashboard_id: str,
    style: str = "modern"
) -> JSONType:
    """
    Claude can try different gauge styles quickly.
    
    Styles: modern, classic, minimal, bold, neon
    """
    
    styles = {
        'modern': {
            'gauge.bar.color': '#00ccff',
            'gauge.borderwidth': 0,
            'gauge.bgcolor': 'rgba(0, 204, 255, 0.1)',
            'gauge.axis.tickwidth': 0,
            'gauge.axis.showticklabels': False
        },
        'classic': {
            'gauge.bar.color': '#28a745',
            'gauge.borderwidth': 3,
            'gauge.bordercolor': '#ffffff',
            'gauge.bgcolor': '#f8f9fa',
            'gauge.axis.tickwidth': 2,
            'gauge.axis.tickcolor': '#495057'
        },
        'minimal': {
            'gauge.bar.color': '#ffffff',
            'gauge.borderwidth': 1,
            'gauge.bordercolor': 'rgba(255, 255, 255, 0.3)',
            'gauge.bgcolor': 'transparent',
            'gauge.axis.visible': False
        },
        'bold': {
            'gauge.bar.color': '#ff6b6b',
            'gauge.bar.thickness': 0.8,
            'gauge.borderwidth': 5,
            'gauge.bordercolor': '#ffffff',
            'gauge.bgcolor': '#4ecdc4'
        },
        'neon': {
            'gauge.bar.color': '#39ff14',
            'gauge.borderwidth': 2,
            'gauge.bordercolor': '#ff1493',
            'gauge.bgcolor': 'rgba(57, 255, 20, 0.1)',
            'title.font.color': '#39ff14'
        }
    }
    
    selected_style = styles.get(style, styles['modern'])
    
    result = await update_chart_config(
        dashboard_id=dashboard_id,
        chart_element='gauge',
        updates=selected_style,
        context=f'ai_style_experiment_{style}'
    )
    
    return {
        'success': result['success'],
        'style_applied': style,
        'changes': selected_style,
        'message': f'Applied {style} gauge style. Refresh the dashboard to see the changes.',
        'next_styles_to_try': [s for s in styles.keys() if s != style]
    }