"""
Event Store for Traffic Light Pattern with Event Replay Architecture

This module provides event storage and retrieval for multi-browser synchronization.
Every conversation event is stored and can be replayed to achieve identical state.
"""

import time
import json
from typing import Dict, List, Any, Optional
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

from registry import api_function
from utils import JSONType

# DynamoDB client
dynamodb = boto3.resource('dynamodb')

# Event types
EVENT_TYPES = {
    "USER_MESSAGE": "user_message",
    "CLAUDE_RESPONSE": "claude_response", 
    "SYSTEM_MESSAGE": "system_message",
    "LAYOUT_CHANGE": "layout_change",
    "DATA_UPDATE": "data_update",
    "BROWSER_CONNECT": "browser_connect",
    "BROWSER_DISCONNECT": "browser_disconnect"
}


def get_event_table():
    """Get or create the event store table."""
    import os
    table_name = os.environ.get('MESSAGES_TABLE', 'pb-fm-mcp-event-store')
    
    try:
        table = dynamodb.Table(table_name)
        table.load()
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Create table if it doesn't exist
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'session_id', 'KeyType': 'HASH'},  # Partition key
                    {'AttributeName': 'sequence', 'KeyType': 'RANGE'}    # Sort key
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'session_id', 'AttributeType': 'S'},
                    {'AttributeName': 'sequence', 'AttributeType': 'N'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            table.wait_until_exists()
            return table
        raise


async def store_event(
    session_id: str,
    event_type: str,
    content: Any,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Store an event in the event store.
    
    Args:
        session_id: Session identifier
        event_type: Type of event (from EVENT_TYPES)
        content: Event content (message, layout, data, etc.)
        metadata: Optional metadata for the event
        
    Returns:
        The stored event with sequence number
    """
    table = get_event_table()
    
    # Get next sequence number for this session
    try:
        response = table.query(
            KeyConditionExpression='session_id = :sid',
            ExpressionAttributeValues={':sid': session_id},
            ProjectionExpression='sequence',
            ScanIndexForward=False,  # Get highest sequence first
            Limit=1
        )
        
        if response['Items']:
            next_sequence = int(response['Items'][0]['sequence']) + 1
        else:
            next_sequence = 1
            
    except Exception:
        next_sequence = 1
    
    # Create event
    event = {
        'session_id': session_id,
        'sequence': next_sequence,
        'event_type': event_type,
        'content': json.dumps(content) if not isinstance(content, str) else content,
        'timestamp': Decimal(str(time.time())),
        'metadata': json.dumps(metadata or {})
    }
    
    # Store event
    table.put_item(Item=event)
    
    return {
        'session_id': session_id,
        'sequence': next_sequence,
        'event_type': event_type,
        'content': content,
        'timestamp': float(event['timestamp']),
        'metadata': metadata or {}
    }


@api_function(
    protocols=["mcp", "rest"],
    description="Fetch all events for a session to enable browser replay and synchronization."
)
async def fetch_session_events(
    session_id: str,
    start_sequence: int = 0,
    limit: int = 1000
) -> JSONType:
    """
    Fetch events for a session to enable replay.
    
    Args:
        session_id: Session identifier
        start_sequence: Starting sequence number (0 for beginning)
        limit: Maximum number of events to return
        
    Returns:
        List of events in sequence order
    """
    # Handle test session gracefully - TEMPORARILY DISABLED FOR CLAUDE.AI TESTING
    # if session_id == '__TEST_SESSION__':
    #     return {
    #         'session_id': session_id,
    #         'events': [],
    #         'count': 0,
    #         'has_more': False,
    #         'test_mode': True,
    #         'message': 'Test session - no events stored'
    #     }
    table = get_event_table()
    
    try:
        # Build query
        key_condition = 'session_id = :sid'
        expression_values = {':sid': session_id}
        
        if start_sequence > 0:
            key_condition += ' AND sequence > :seq'
            expression_values[':seq'] = start_sequence
        
        # Query events
        response = table.query(
            KeyConditionExpression=key_condition,
            ExpressionAttributeValues=expression_values,
            Limit=limit,
            ScanIndexForward=True  # Return in sequence order
        )
        
        # Parse events
        events = []
        for item in response['Items']:
            events.append({
                'sequence': int(item['sequence']),
                'event_type': item['event_type'],
                'content': json.loads(item['content']) if item['content'].startswith('{') else item['content'],
                'timestamp': float(item['timestamp']),
                'metadata': json.loads(item.get('metadata', '{}'))
            })
        
        return {
            'session_id': session_id,
            'events': events,
            'count': len(events),
            'has_more': response.get('LastEvaluatedKey') is not None
        }
        
    except Exception as e:
        return {
            'session_id': session_id,
            'error': f"Failed to fetch events: {str(e)}",
            'events': []
        }


@api_function(
    protocols=["mcp", "rest"],
    description="Get browser connection order to determine input control privileges."
)
async def get_browser_connection_order(session_id: str) -> JSONType:
    """
    Determine browser connection order for input control.
    
    The first browser to connect gets input control, others are observers.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Connection order and control status
    """
    # Handle test session gracefully - TEMPORARILY DISABLED FOR CLAUDE.AI TESTING
    # if session_id == '__TEST_SESSION__':
    #     return {
    #         'session_id': session_id,
    #         'total_browsers': 0,
    #         'browsers': [],
    #         'test_mode': True,
    #         'message': 'Test session - no browser connections'
    #     }
    table = get_event_table()
    
    try:
        # Query browser_connect events
        response = table.query(
            KeyConditionExpression='session_id = :sid',
            FilterExpression='event_type = :etype',
            ExpressionAttributeValues={
                ':sid': session_id,
                ':etype': EVENT_TYPES['BROWSER_CONNECT']
            },
            ProjectionExpression='sequence, content, #ts',
            ExpressionAttributeNames={'#ts': 'timestamp'}
        )
        
        # Track unique browser IDs
        browsers = []
        seen_browser_ids = set()
        
        for item in response['Items']:
            content = json.loads(item['content'])
            browser_id = content.get('browser_id')
            
            if browser_id and browser_id not in seen_browser_ids:
                browsers.append({
                    'browser_id': browser_id,
                    'connection_order': len(browsers) + 1,
                    'has_input_control': len(browsers) == 0,  # First browser gets control
                    'connected_at': float(item['timestamp'])
                })
                seen_browser_ids.add(browser_id)
        
        return {
            'session_id': session_id,
            'total_browsers': len(browsers),
            'browsers': browsers
        }
        
    except Exception as e:
        return {
            'session_id': session_id,
            'error': f"Failed to get connection order: {str(e)}",
            'browsers': []
        }