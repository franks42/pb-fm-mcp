"""
Dashboard Coordination System - Queue-Based S3 Reference Management

This module implements the coordination queue that tells browsers:
- Which S3 bucket/path to poll for layouts
- When to switch between different dashboard variants
- How to handle dynamic theming and personalization

The AI orchestrates dashboard experiences by updating coordination records,
allowing instant switching between pre-staged S3 layouts without deployment.
"""

import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import uuid

from registry.decorator import api_function
from utils import JSONType


def get_dashboards_table():
    """Get DynamoDB table for coordination records."""
    import os
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ.get('DASHBOARDS_TABLE')
    if not table_name:
        raise ValueError("DASHBOARDS_TABLE not configured")
    return dynamodb.Table(table_name)


@api_function(protocols=["rest"])






async def get_dashboard_coordinates(session_id: str) -> JSONType:
    """
    Browser polling endpoint to get current S3 coordinates for a dashboard session.
    
    This tells the browser:
    - Which S3 bucket/path to poll for layouts
    - Current theme and variant settings
    - Polling interval and other parameters
    """
    try:
        table = get_dashboards_table()
        
        # Look for coordination record
        coord_key = f"coordinates_{session_id}"
        response = table.get_item(Key={'dashboard_id': coord_key})
        
        if 'Item' not in response:
            # Return default coordinates if none set
            return {
                'session_id': session_id,
                'has_coordinates': False,
                'message': 'No coordination set - using defaults',
                'default_polling': True
            }
        
        coord_data = response['Item']
        
        # Check if coordinates are still valid (not expired)
        if coord_data.get('expires_at'):
            expires_at = datetime.fromisoformat(coord_data['expires_at'])
            if datetime.now() > expires_at:
                # Coordinates expired, clean up
                table.delete_item(Key={'dashboard_id': coord_key})
                return {
                    'session_id': session_id,
                    'has_coordinates': False,
                    'message': 'Coordinates expired',
                    'expired': True
                }
        
        return {
            'session_id': session_id,
            'has_coordinates': True,
            's3_base_url': coord_data.get('s3_base_url'),
            's3_path_prefix': coord_data.get('s3_path_prefix', 'declarations'),
            'layout_variant': coord_data.get('layout_variant', 'default'),
            'theme': coord_data.get('theme', 'dark'),
            'poll_interval': coord_data.get('poll_interval', 2000),
            'last_updated': coord_data.get('last_updated'),
            'coordinator': coord_data.get('coordinator', 'system'),
            'message': 'Active coordination found'
        }
        
    except Exception as e:
        return {
            'session_id': session_id,
            'has_coordinates': False,
            'error': str(e),
            'message': 'Failed to get coordinates'
        }


@api_function(protocols=[])



async def set_dashboard_coordinates(
    session_id: str,
    s3_base_url: str,
    s3_path_prefix: str = "declarations",
    layout_variant: str = "default",
    theme: str = "dark",
    poll_interval: int = 2000,
    expires_in_minutes: int = 60
) -> JSONType:
    """
    AI function to set new S3 coordinates for a dashboard session.
    This causes browsers to switch to polling a different S3 location.
    
    Parameters:
    - s3_base_url: Base S3 URL (e.g., "https://bucket.s3.amazonaws.com")
    - s3_path_prefix: Path within bucket (e.g., "layouts/advanced")
    - layout_variant: Variant name for tracking
    - theme: Theme identifier
    - poll_interval: How often browser should poll (ms)
    - expires_in_minutes: When coordinates expire
    """
    try:
        table = get_dashboards_table()
        
        # Create coordination record
        coord_key = f"coordinates_{session_id}"
        expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)
        
        coordination_record = {
            'dashboard_id': coord_key,
            'session_id': session_id,
            's3_base_url': s3_base_url,
            's3_path_prefix': s3_path_prefix,
            'layout_variant': layout_variant,
            'theme': theme,
            'poll_interval': poll_interval,
            'coordinator': 'ai_assistant',
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat(),
            'ttl': int(expires_at.timestamp())
        }
        
        table.put_item(Item=coordination_record)
        
        return {
            'success': True,
            'session_id': session_id,
            'coordinates_set': True,
            's3_base_url': s3_base_url,
            's3_path_prefix': s3_path_prefix,
            'layout_variant': layout_variant,
            'theme': theme,
            'poll_interval': poll_interval,
            'expires_in': f"{expires_in_minutes} minutes",
            'message': f'Coordinates set - browsers will switch to {layout_variant} layout'
        }
        
    except Exception as e:
        return {
            'success': False,
            'session_id': session_id,
            'error': str(e),
            'message': 'Failed to set coordinates'
        }


@api_function(protocols=[])



async def switch_dashboard_layout(
    session_id: str,
    layout_variant: str,
    s3_bucket: str = None
) -> JSONType:
    """
    AI function to instantly switch a dashboard to a different pre-staged layout.
    
    Pre-staged layouts are stored in S3 at:
    s3://bucket/layouts/{variant}/layout.json
    s3://bucket/layouts/{variant}/plotly.json  
    s3://bucket/layouts/{variant}/data.json
    """
    try:
        # Use default bucket if none specified
        if not s3_bucket:
            import os
            s3_bucket = os.environ.get('WEB_ASSETS_BUCKET', '')
            if not s3_bucket:
                raise ValueError("No S3 bucket specified and WEB_ASSETS_BUCKET not set")
        
        s3_base_url = f"https://{s3_bucket}.s3.us-west-1.amazonaws.com"
        s3_path_prefix = f"layouts/{layout_variant}"
        
        # Set new coordinates pointing to the variant
        result = await set_dashboard_coordinates(
            session_id=session_id,
            s3_base_url=s3_base_url,
            s3_path_prefix=s3_path_prefix,
            layout_variant=layout_variant,
            theme="dark",  # Could be parameterized
            poll_interval=1000,  # Faster polling for switching
            expires_in_minutes=120  # 2 hours
        )
        
        if result['success']:
            return {
                'success': True,
                'session_id': session_id,
                'layout_switched': True,
                'variant': layout_variant,
                'new_s3_path': f"{s3_base_url}/{s3_path_prefix}",
                'message': f'Dashboard will switch to {layout_variant} layout within 2 seconds'
            }
        else:
            return result
            
    except Exception as e:
        return {
            'success': False,
            'session_id': session_id,
            'error': str(e),
            'message': f'Failed to switch to {layout_variant} layout'
        }


@api_function(protocols=[])



async def create_layout_variant(
    variant_name: str,
    layout_html: str,
    layout_css: str,
    plotly_charts: List[Dict] = None,
    sample_data: List[Dict] = None,
    s3_bucket: str = None
) -> JSONType:
    """
    AI function to create a new pre-staged layout variant in S3.
    This allows instant switching to the new layout later.
    """
    try:
        if not s3_bucket:
            import os
            s3_bucket = os.environ.get('WEB_ASSETS_BUCKET', '')
        
        s3 = boto3.client('s3')
        s3_path = f"layouts/{variant_name}"
        
        # Create layout declaration
        layout_spec = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "variant": variant_name,
            "description": f"Pre-staged layout variant: {variant_name}",
            "html": layout_html,
            "css": layout_css,
            "containers": []
        }
        
        # Upload layout
        s3.put_object(
            Bucket=s3_bucket,
            Key=f"{s3_path}/layout.json",
            Body=json.dumps(layout_spec, indent=2),
            ContentType='application/json',
            CacheControl='no-cache'
        )
        
        files_created = [f"{s3_path}/layout.json"]
        
        # Upload Plotly config if provided
        if plotly_charts:
            plotly_spec = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "variant": variant_name,
                "description": f"Plotly charts for {variant_name}",
                "charts": plotly_charts
            }
            
            s3.put_object(
                Bucket=s3_bucket,
                Key=f"{s3_path}/plotly.json",
                Body=json.dumps(plotly_spec, indent=2),
                ContentType='application/json',
                CacheControl='no-cache'
            )
            files_created.append(f"{s3_path}/plotly.json")
        
        # Upload sample data if provided
        if sample_data:
            data_spec = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "variant": variant_name,
                "description": f"Sample data for {variant_name}",
                "datasets": sample_data
            }
            
            s3.put_object(
                Bucket=s3_bucket,
                Key=f"{s3_path}/data.json",
                Body=json.dumps(data_spec, indent=2),
                ContentType='application/json',
                CacheControl='no-cache'
            )
            files_created.append(f"{s3_path}/data.json")
        
        return {
            'success': True,
            'variant_name': variant_name,
            's3_bucket': s3_bucket,
            's3_path': s3_path,
            'files_created': files_created,
            'switch_command': f'switch_dashboard_layout("{variant_name}")',
            'message': f'Layout variant {variant_name} created and ready for instant switching'
        }
        
    except Exception as e:
        return {
            'success': False,
            'variant_name': variant_name,
            'error': str(e),
            'message': f'Failed to create layout variant {variant_name}'
        }