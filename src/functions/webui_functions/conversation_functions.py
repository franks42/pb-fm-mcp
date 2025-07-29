"""
Web UI Conversation Functions for Heartbeat Communication Pattern

Functions for managing conversational interface between Claude.ai and web interface
through HTTP polling message queue system with complete session isolation.

All functions are decorated with @api_function to be automatically exposed via MCP 
and/or REST protocols.
"""

import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import structlog
import boto3
from botocore.exceptions import ClientError

from registry import api_function
from utils import JSONType

# Set up logging
logger = structlog.get_logger()

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
sessions_table = dynamodb.Table(os.environ.get('SESSIONS_TABLE', 'pb-fm-mcp-dev-conversation-sessions'))
messages_table = dynamodb.Table(os.environ.get('MESSAGES_TABLE', 'pb-fm-mcp-dev-conversation-messages'))

@dataclass
class UserMessage:
    """Data structure for user messages in conversation queue"""
    id: str
    message: str
    timestamp: datetime
    session_id: str
    processed: bool = False
    response: Optional[str] = None
    response_timestamp: Optional[datetime] = None

# Helper functions for DynamoDB operations
def create_session_record(session_id: str) -> dict:
    """Create a session record in DynamoDB."""
    now = datetime.now()
    ttl = int((now + timedelta(days=7)).timestamp())  # Session expires in 7 days
    
    session_item = {
        'session_id': session_id,
        'created_at': now.isoformat(),
        'last_activity': now.isoformat(),
        'message_count': 0,
        'claude_active': False,
        'web_active': False,
        'ttl': ttl
    }
    
    try:
        sessions_table.put_item(Item=session_item)
        return session_item
    except ClientError as e:
        logger.error("Failed to create session", session_id=session_id, error=str(e))
        raise

def get_session_record(session_id: str) -> Optional[dict]:
    """Get session record from DynamoDB."""
    try:
        response = sessions_table.get_item(Key={'session_id': session_id})
        return response.get('Item')
    except ClientError as e:
        logger.error("Failed to get session", session_id=session_id, error=str(e))
        return None

def update_session_activity(session_id: str, claude_active: bool = None, web_active: bool = None):
    """Update session activity timestamp and status."""
    update_expr = "SET last_activity = :now"
    expr_values = {':now': datetime.now().isoformat()}
    
    if claude_active is not None:
        update_expr += ", claude_active = :claude_active"
        expr_values[':claude_active'] = claude_active
    
    if web_active is not None:
        update_expr += ", web_active = :web_active"
        expr_values[':web_active'] = web_active
    
    try:
        sessions_table.update_item(
            Key={'session_id': session_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
    except ClientError as e:
        logger.error("Failed to update session activity", session_id=session_id, error=str(e))

@api_function(
    protocols=["rest"],  # Web interface only - not needed in MCP
    path="/api/create_new_session", 
    method="POST",
    tags=["webui", "session"],
    description="Create new user session with unique UUID for web interface isolation"
)
async def create_new_session() -> JSONType:
    """
    Create new user session with unique UUID for complete user isolation.
    
    Returns:
        Dictionary containing:
        - session_id: Unique UUID for this user session
        - dashboard_url: URL path for user's personal web interface
        - claude_instructions: Instructions to provide to Claude.ai
        - created_at: Session creation timestamp
    """
    session_id = str(uuid.uuid4())
    
    # Create session record in DynamoDB
    session_record = create_session_record(session_id)
    
    logger.info("Created new session", session_id=session_id)
    
    return {
        "session_id": session_id,
        "dashboard_url": f"/dashboard/{session_id}",
        "claude_instructions": f'Connect to MCP server and use session_id: "{session_id}" for all function calls. Start monitoring with heartbeat pattern.',
        "created_at": session_record["created_at"],
        "status": "ready"
    }

@api_function(protocols=[])






async def queue_user_message(message: str, session_id: str = "default") -> JSONType:
    """
    Queue a user message for Claude to process during heartbeat polling.
    
    Args:
        message: The user's message text
        session_id: Unique session identifier for user isolation
        
    Returns:
        Dictionary containing:
        - success: Whether message was queued successfully
        - message_id: Unique identifier for this message
        - queued_at: Timestamp when message was queued
        - queue_position: Position in queue for this session
    """
    if not message.strip():
        return {"success": False, "error": "Empty message not allowed"}
    
    # Check if session exists, create if needed
    session_record = get_session_record(session_id)
    if not session_record:
        session_record = create_session_record(session_id)
    
    message_id = str(uuid.uuid4())
    now = datetime.now()
    ttl = int((now + timedelta(days=7)).timestamp())  # Message expires in 7 days
    
    # Store message in DynamoDB
    message_item = {
        'session_id': session_id,
        'message_id': message_id,
        'message': message.strip(),
        'timestamp': now.isoformat(),
        'processed': False,
        'processed_timestamp': '0',  # Used for GSI sorting - '0' means unprocessed
        'ttl': ttl
    }
    
    try:
        messages_table.put_item(Item=message_item)
        
        # Update session activity and message count
        sessions_table.update_item(
            Key={'session_id': session_id},
            UpdateExpression="SET last_activity = :now, web_active = :web_active, message_count = message_count + :inc",
            ExpressionAttributeValues={
                ':now': now.isoformat(),
                ':web_active': True,
                ':inc': 1
            }
        )
        
        # Count pending messages for queue position
        pending_response = messages_table.query(
            IndexName='ProcessedIndex',
            KeyConditionExpression='session_id = :session_id AND processed_timestamp = :unprocessed',
            ExpressionAttributeValues={
                ':session_id': session_id,
                ':unprocessed': '0'
            }
        )
        queue_position = pending_response['Count']
        
        logger.info("Queued user message", 
                    session_id=session_id, 
                    message_id=message_id,
                    queue_position=queue_position)
        
        return {
            "success": True,
            "message_id": message_id,
            "queued_at": now.isoformat(),
            "queue_position": queue_position,
            "session_id": session_id
        }
        
    except ClientError as e:
        logger.error("Failed to queue message", session_id=session_id, error=str(e))
        return {"success": False, "error": "Failed to queue message"}

@api_function(protocols=[])






async def get_pending_messages(session_id: str = "default") -> JSONType:
    """
    Get unprocessed messages for Claude to handle during heartbeat polling.
    
    This is the core function Claude calls during heartbeat to check for new user input.
    
    Args:
        session_id: Unique session identifier for user isolation
        
    Returns:
        Dictionary containing:
        - messages: List of unprocessed message objects
        - count: Number of pending messages
        - session_active: Whether this session exists and is active
    """
    # Check if session exists
    session_record = get_session_record(session_id)
    if not session_record:
        return {
            "messages": [], 
            "count": 0,
            "session_active": False,
            "status": "session_not_found"
        }
    
    try:
        # Query for unprocessed messages using GSI
        response = messages_table.query(
            IndexName='ProcessedIndex',
            KeyConditionExpression='session_id = :session_id AND processed_timestamp = :unprocessed',
            ExpressionAttributeValues={
                ':session_id': session_id,
                ':unprocessed': '0'
            }
        )
        
        pending_messages = response.get('Items', [])
        
        # Update Claude activity
        update_session_activity(session_id, claude_active=True)
        
        logger.debug("Claude checking for messages", 
                     session_id=session_id, 
                     pending_count=len(pending_messages))
        
        return {
            "messages": [
                {
                    "id": msg["message_id"],
                    "message": msg["message"],
                    "timestamp": msg["timestamp"],
                    "session_id": msg["session_id"]
                }
                for msg in pending_messages
            ],
            "count": len(pending_messages),
            "session_active": True,
            "status": "ok",
            "next_poll_instruction": {
                "action": "poll_again" if len(pending_messages) == 0 else "process_messages",
                "delay_seconds": 2,
                "message": "Check again in 2 seconds" if len(pending_messages) == 0 else "Process these messages first"
            }
        }
        
    except ClientError as e:
        logger.error("Failed to get pending messages", session_id=session_id, error=str(e))
        return {
            "messages": [],
            "count": 0,
            "session_active": False,
            "status": "error"
        }

@api_function(protocols=[])






async def send_response_to_web(message_id: str, response: str, session_id: str = None) -> JSONType:
    """
    Send Claude's response back to web interface for a specific message.
    
    Args:
        message_id: ID of the original message being responded to
        response: Claude's response text
        session_id: Session ID (optional - will be discovered if not provided)
        
    Returns:
        Dictionary containing:
        - success: Whether response was sent successfully
        - response_sent: Confirmation that response is available for web interface
        - timestamp: When response was sent
    """
    if not response.strip():
        return {"success": False, "error": "Empty response not allowed"}
    
    try:
        target_session_id = session_id
        original_message = None
        
        # If session_id not provided, try to find it by scanning recent sessions
        if not target_session_id:
            sessions_response = sessions_table.scan(
                FilterExpression='last_activity > :recent',
                ExpressionAttributeValues={':recent': (datetime.now() - timedelta(minutes=5)).isoformat()},
                Limit=10
            )
            
            # Check each recent session for the message
            for session in sessions_response.get('Items', []):
                session_id = session['session_id']
                try:
                    # Try to get the message directly
                    message_response = messages_table.get_item(
                        Key={'session_id': session_id, 'message_id': message_id}
                    )
                    if 'Item' in message_response:
                        target_session_id = session_id
                        original_message = message_response['Item']['message']
                        break
                except:
                    continue
        
        if not target_session_id:
            return {"success": False, "error": "Message not found"}
        
        # Update the message as processed with response
        now = datetime.now()
        messages_table.update_item(
            Key={'session_id': target_session_id, 'message_id': message_id},
            UpdateExpression="SET #proc = :processed, #resp = :response, response_timestamp = :resp_time, processed_timestamp = :proc_time",
            ExpressionAttributeNames={
                '#proc': 'processed',
                '#resp': 'response'
            },
            ExpressionAttributeValues={
                ':processed': True,
                ':response': response.strip(),
                ':resp_time': now.isoformat(),
                ':proc_time': now.isoformat()  # Used for GSI sorting
            }
        )
        
        # Update session activity
        update_session_activity(target_session_id)
        
        logger.info("Claude sent response", 
                   session_id=target_session_id,
                   message_id=message_id,
                   response_length=len(response))
        
        return {
            "success": True,
            "response_sent": True,
            "timestamp": now.isoformat(),
            "session_id": target_session_id
        }
        
    except ClientError as e:
        logger.error("Failed to send response", message_id=message_id, error=str(e))
        return {"success": False, "error": "Failed to send response"}

@api_function(
    protocols=["rest"],  # Web interface polling only
    path="/api/get_latest_response/{session_id}",
    method="GET",
    tags=["webui", "messaging"],
    description="Web interface polls for latest Claude response in their session"
)
async def get_latest_response(session_id: str = "default") -> JSONType:
    """
    Web interface polls for latest Claude response in their session.
    
    Args:
        session_id: Unique session identifier for user isolation
        
    Returns:
        Dictionary containing:
        - new_response: Whether there's a new response available
        - response: Claude's response text (if available)
        - timestamp: When response was sent
        - original_message: The user message Claude was responding to
    """
    try:
        # Query for processed messages, sorted by response timestamp (most recent first)
        response = messages_table.query(
            IndexName='ProcessedIndex',
            KeyConditionExpression='session_id = :session_id AND processed_timestamp > :zero',
            ExpressionAttributeValues={
                ':session_id': session_id,
                ':zero': '0'  # Get processed messages (timestamp > '0')
            },
            ScanIndexForward=False,  # Reverse order to get most recent first
            Limit=1  # Just get the latest one
        )
        
        # Update web activity
        update_session_activity(session_id, web_active=True)
        
        items = response.get('Items', [])
        if items:
            latest_message = items[0]
            
            # Check if this message has a response and hasn't been delivered yet
            if (latest_message.get('response') and 
                latest_message.get('response_timestamp') and 
                not latest_message.get('delivered_to_web', False)):
                
                # Mark as delivered to prevent duplicate deliveries
                messages_table.update_item(
                    Key={'session_id': session_id, 'message_id': latest_message['message_id']},
                    UpdateExpression="SET delivered_to_web = :delivered",
                    ExpressionAttributeValues={':delivered': True}
                )
                
                logger.debug("Delivered response to web interface", session_id=session_id)
                
                return {
                    "new_response": True,
                    "response": latest_message['response'],
                    "timestamp": latest_message['response_timestamp'],
                    "original_message": latest_message['message'],
                    "message_id": latest_message['message_id']
                }
        
        return {
            "new_response": False,
            "status": "no_response"
        }
        
    except ClientError as e:
        logger.error("Failed to get latest response", session_id=session_id, error=str(e))
        return {
            "new_response": False,
            "status": "error"
        }

@api_function(protocols=[])






async def get_conversation_status(session_id: str = "default") -> JSONType:
    """
    Check conversation status and message counts for a specific session.
    
    Args:
        session_id: Unique session identifier for user isolation
        
    Returns:
        Dictionary containing:
        - session_exists: Whether session is valid
        - total_messages: Total messages in session
        - pending_messages: Unprocessed messages count
        - processed_messages: Completed messages count
        - claude_active: Whether Claude is actively polling
        - web_active: Whether web interface is active
        - last_activity: Most recent activity timestamp
    """
    # Check if session exists
    session_record = get_session_record(session_id)
    if not session_record:
        return {
            "session_exists": False,
            "total_messages": 0,
            "pending_messages": 0,
            "processed_messages": 0,
            "claude_active": False,
            "web_active": False,
            "last_activity": None,
            "status": "session_not_found"
        }
    
    try:
        # Count total messages
        total_response = messages_table.query(
            KeyConditionExpression='session_id = :session_id',
            ExpressionAttributeValues={':session_id': session_id},
            Select='COUNT'
        )
        total_messages = total_response['Count']
        
        # Count pending messages
        pending_response = messages_table.query(
            IndexName='ProcessedIndex',
            KeyConditionExpression='session_id = :session_id AND processed_timestamp = :unprocessed',
            ExpressionAttributeValues={
                ':session_id': session_id,
                ':unprocessed': '0'
            },
            Select='COUNT'
        )
        pending_messages = pending_response['Count']
        
        # Count processed messages
        processed_response = messages_table.query(
            IndexName='ProcessedIndex',
            KeyConditionExpression='session_id = :session_id AND processed_timestamp > :zero',
            ExpressionAttributeValues={
                ':session_id': session_id,
                ':zero': '0'
            },
            Select='COUNT'
        )
        processed_messages = processed_response['Count']
        
        return {
            "session_exists": True,
            "session_id": session_id,
            "total_messages": total_messages,
            "pending_messages": pending_messages,
            "processed_messages": processed_messages,
            "claude_active": session_record.get("claude_active", False),
            "web_active": session_record.get("web_active", False),
            "last_activity": session_record.get("last_activity"),
            "message_count": session_record.get("message_count", 0),
            "status": "active"
        }
        
    except ClientError as e:
        logger.error("Failed to get conversation status", session_id=session_id, error=str(e))
        return {
            "session_exists": True,
            "session_id": session_id,
            "total_messages": 0,
            "pending_messages": 0,
            "processed_messages": 0,
            "claude_active": session_record.get("claude_active", False),
            "web_active": session_record.get("web_active", False),
            "last_activity": session_record.get("last_activity"),
            "message_count": session_record.get("message_count", 0),
            "status": "error"
        }

@api_function(
    protocols=["rest"],  # Admin/cleanup function
    path="/api/cleanup_inactive_sessions",
    method="POST", 
    tags=["webui", "admin"],
    description="Remove inactive sessions older than specified hours"
)
async def cleanup_inactive_sessions(max_age_hours: int = 24) -> JSONType:
    """
    Remove inactive sessions older than specified hours.
    
    Args:
        max_age_hours: Maximum age in hours before session is considered inactive
        
    Returns:
        Dictionary containing:
        - cleaned_sessions: Number of sessions removed
        - remaining_sessions: Number of active sessions remaining
        - cleanup_timestamp: When cleanup was performed
    """
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    cutoff_iso = cutoff.isoformat()
    removed_sessions = []
    
    try:
        # Find sessions to remove by scanning for old activity
        sessions_response = sessions_table.scan()
        
        for session in sessions_response.get('Items', []):
            session_id = session['session_id']
            last_activity = session.get('last_activity', '1970-01-01T00:00:00')
            
            if last_activity < cutoff_iso:
                # Delete all messages for this session first
                messages_response = messages_table.query(
                    KeyConditionExpression='session_id = :session_id',
                    ExpressionAttributeValues={':session_id': session_id}
                )
                
                # Delete messages in batches
                with messages_table.batch_writer() as batch:
                    for message in messages_response.get('Items', []):
                        batch.delete_item(
                            Key={
                                'session_id': message['session_id'],
                                'message_id': message['message_id']
                            }
                        )
                
                # Delete the session record
                sessions_table.delete_item(Key={'session_id': session_id})
                removed_sessions.append(session_id)
        
        # Count remaining sessions
        remaining_response = sessions_table.scan(Select='COUNT')
        remaining_count = remaining_response['Count']
        
        logger.info("Cleaned up inactive sessions", 
                    removed_count=len(removed_sessions),
                    remaining_count=remaining_count)
        
        return {
            "cleaned_sessions": len(removed_sessions),
            "remaining_sessions": remaining_count,
            "cleanup_timestamp": datetime.now().isoformat(),
            "max_age_hours": max_age_hours
        }
        
    except ClientError as e:
        logger.error("Failed to cleanup sessions", error=str(e))
        return {
            "cleaned_sessions": 0,
            "remaining_sessions": 0,
            "cleanup_timestamp": datetime.now().isoformat(),
            "max_age_hours": max_age_hours,
            "error": "Cleanup failed"
        }