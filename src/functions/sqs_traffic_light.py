"""
SQS Traffic Light Pattern - MCP Functions for AI

This module provides MCP functions that enable AI to participate in 
bidirectional real-time communication with web browsers using SQS queues.

Architecture:
- Browser → AI: User input goes to user-input-{session_id} queue
- AI → Browser: AI responses go to ai-response-{session_id} queue
- Both sides use SQS long polling for sub-second response times
"""

import json
import time
import boto3
from typing import Optional, Dict, Any

from registry import api_function
from utils import JSONType
from .event_store import store_event, EVENT_TYPES

# Initialize SQS client
sqs = boto3.client('sqs')

def get_queue_url(queue_type: str, session_id: str) -> str:
    """Get SQS queue URL for a session and direction"""
    account_id = boto3.client('sts').get_caller_identity()['Account']
    region = boto3.Session().region_name or 'us-west-1'
    return f"https://sqs.{region}.amazonaws.com/{account_id}/{queue_type}-{session_id}"

def ensure_queue_exists(queue_name: str) -> str:
    """Ensure SQS queue exists, create if needed"""
    try:
        response = sqs.get_queue_url(QueueName=queue_name)
        return response['QueueUrl']
    except sqs.exceptions.QueueDoesNotExist:
        response = sqs.create_queue(
            QueueName=queue_name,
            Attributes={
                'MessageRetentionPeriod': '3600',  # 1 hour
                'VisibilityTimeout': '30'
            }
        )
        return response['QueueUrl']

@api_function(
    protocols=["mcp"],
    description="Wait for user input from browser using SQS traffic light pattern. "
                "This function blocks until user interacts with the web interface "
                "or timeout is reached. Perfect for real-time AI-browser communication."
)
async def wait_for_user_input(
    session_id: str,
    timeout_seconds: int = 8
) -> JSONType:
    """
    Traffic light pattern: AI waits for user input from browser.
    
    This is the core of real-time communication - AI calls this function
    and waits efficiently (no CPU burn) until the user interacts with 
    the web interface.
    
    Args:
        session_id: Unique session identifier for user isolation
        timeout_seconds: How long to wait (max 20 seconds due to SQS limits)
        
    Returns:
        If user input received:
            {
                "has_input": True,
                "input_data": {...},  # The actual user input
                "timestamp": 1234567890.123,
                "session_id": "session123"
            }
        If timeout:
            {
                "has_input": False,
                "message": "No user input received",
                "timeout": 8
            }
    """
    try:
        queue_url = get_queue_url("user-input", session_id)
        
        # Ensure queue exists
        ensure_queue_exists(f"user-input-{session_id}")
        
        # SQS long polling - this is the traffic light!
        # AI waits here efficiently until user acts
        response = sqs.receive_message(
            QueueUrl=queue_url,
            WaitTimeSeconds=min(timeout_seconds, 20),  # SQS max is 20 seconds
            MaxNumberOfMessages=1
        )
        
        if 'Messages' in response:
            # 🟢 GREEN LIGHT! User input received
            message = response['Messages'][0]
            user_input = json.loads(message['Body'])
            
            # Delete message from queue (consume it)
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
            
            return {
                "has_input": True,
                "input_data": user_input.get("input_data", {}),
                "timestamp": user_input.get("timestamp", time.time()),
                "session_id": session_id,
                "message": f"Received user input: {user_input.get('input_data', {}).get('input_type', 'unknown')}"
            }
        else:
            # 🔴 RED LIGHT - Timeout reached, no user input
            return {
                "has_input": False,
                "message": "No user input received within timeout period",
                "timeout": timeout_seconds,
                "session_id": session_id,
                "instructions": "Call wait_for_user_input() again to continue monitoring"
            }
            
    except Exception as e:
        return {
            "has_input": False,
            "error": f"SQS error: {str(e)}",
            "session_id": session_id
        }

@api_function(
    protocols=["mcp"],
    description="Send AI response to browser via SQS queue. "
                "Browser will receive this immediately through its polling loop. "
                "Use this to update dashboards, show analysis results, or send any data to the UI."
)
async def send_response_to_browser(
    session_id: str,
    response_data: Dict[str, Any],
    response_type: str = "dashboard_update"
) -> JSONType:
    """
    Send AI response back to browser for immediate display.
    
    The browser is waiting on the ai-response queue and will receive
    this message within ~100ms via its traffic light polling.
    
    Args:
        session_id: Session identifier (same as wait_for_user_input)
        response_data: Data to send to browser (will be JSON serialized)
        response_type: Type of response for browser handling
        
    Returns:
        {
            "status": "sent_to_browser",
            "session_id": "session123",
            "timestamp": 1234567890.123,
            "message": "Response delivered to browser queue"
        }
    """
    try:
        queue_url = get_queue_url("ai-response", session_id)
        
        # Ensure queue exists
        ensure_queue_exists(f"ai-response-{session_id}")
        
        # Prepare message for browser
        message_body = {
            'session_id': session_id,
            'timestamp': time.time(),
            'response_type': response_type,
            'response_data': response_data
        }
        
        # Send to browser queue
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body)
        )
        
        return {
            "status": "sent_to_browser",
            "session_id": session_id,
            "timestamp": time.time(),
            "response_type": response_type,
            "message": f"Response delivered to browser queue: {response_type}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to send response: {str(e)}",
            "session_id": session_id
        }

@api_function(
    protocols=["mcp"],
    description="Get the current status of SQS queues for a session. "
                "Useful for debugging communication issues or checking message counts."
)
async def get_traffic_light_status(session_id: str) -> JSONType:
    """
    Get status of both traffic light queues for debugging.
    
    Returns:
        {
            "session_id": "session123",
            "user_input_queue": {
                "messages_available": 0,
                "messages_in_flight": 0
            },
            "ai_response_queue": {
                "messages_available": 1,
                "messages_in_flight": 0
            },
            "timestamp": 1234567890.123
        }
    """
    try:
        status = {
            "session_id": session_id,
            "timestamp": time.time()
        }
        
        # Check user input queue
        try:
            user_queue_url = get_queue_url("user-input", session_id)
            user_attrs = sqs.get_queue_attributes(
                QueueUrl=user_queue_url,
                AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
            )
            status["user_input_queue"] = {
                "messages_available": int(user_attrs['Attributes'].get('ApproximateNumberOfMessages', 0)),
                "messages_in_flight": int(user_attrs['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0)),
                "queue_exists": True
            }
        except sqs.exceptions.QueueDoesNotExist:
            status["user_input_queue"] = {"queue_exists": False}
        
        # Check AI response queue
        try:
            ai_queue_url = get_queue_url("ai-response", session_id)
            ai_attrs = sqs.get_queue_attributes(
                QueueUrl=ai_queue_url,
                AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
            )
            status["ai_response_queue"] = {
                "messages_available": int(ai_attrs['Attributes'].get('ApproximateNumberOfMessages', 0)),
                "messages_in_flight": int(ai_attrs['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0)),
                "queue_exists": True
            }
        except sqs.exceptions.QueueDoesNotExist:
            status["ai_response_queue"] = {"queue_exists": False}
        
        return status
        
    except Exception as e:
        return {
            "session_id": session_id,
            "error": f"Failed to get status: {str(e)}",
            "timestamp": time.time()
        }


@api_function(
    protocols=["mcp"],
    description="Unified function for AI Terminal conversation. Sends result to browser, "
                "then waits for new instruction. Returns instruction for Claude to follow."
)
async def send_result_to_browser_and_fetch_new_instruction(
    session_id: str,
    result_text: str = "",
    timeout_seconds: int = 8
) -> JSONType:
    """
    Unified conversation function that combines sending results and fetching instructions.
    
    This function:
    1. If result_text provided, sends it to browser via SQS
    2. Waits for user input from browser (with timeout)
    3. Returns instruction for Claude to follow
    
    The instruction will always be to call this function again with the result.
    
    Args:
        session_id: Unique session identifier for conversation isolation
        result_text: Claude's response to send to browser (empty string if none)
        timeout_seconds: How long to wait for user input (default 8s)
        
    Returns:
        {
            "instruction": "User said: hello" or "No input received",
            "next_call": "send_result_to_browser_and_fetch_new_instruction(session_id, 'your_response')"
        }
    """
    # Step 1: Send result to browser if provided
    if result_text:
        await send_response_to_browser(
            session_id=session_id,
            response_data={
                "response": result_text,
                "type": "claude_response"
            },
            response_type="claude_response"
        )
        
        # Store Claude response event for replay
        await store_event(
            session_id=session_id,
            event_type=EVENT_TYPES["CLAUDE_RESPONSE"],
            content=result_text,
            metadata={"timestamp": time.time()}
        )
    
    # Step 2: Wait for user input
    user_input = await wait_for_user_input(session_id, timeout_seconds)
    
    # Step 3: Construct instruction for Claude
    if user_input.get("has_input"):
        user_message = user_input["input_data"]["input_value"]
        
        # Store user message event for replay
        await store_event(
            session_id=session_id,
            event_type=EVENT_TYPES["USER_MESSAGE"],
            content=user_message,
            metadata={"timestamp": time.time()}
        )
        
        instruction = f"User said: {user_message}"
        next_call = f"send_result_to_browser_and_fetch_new_instruction('{session_id}', 'your_response_to_user')"
    else:
        instruction = "No input received - continue listening"
        next_call = f"send_result_to_browser_and_fetch_new_instruction('{session_id}', '')"
    
    return {
        "instruction": instruction,
        "next_call": next_call,
        "session_id": session_id,
        "timestamp": time.time()
    }


@api_function(
    protocols=["mcp"],
    description="Start a real-time conversation session with a web browser. "
                "Returns instructions for Claude on how to use the traffic light pattern "
                "for bidirectional communication."
)
async def start_realtime_conversation(session_id: str) -> JSONType:
    """
    Initialize a real-time conversation session.
    
    This sets up the SQS queues and provides Claude with instructions
    on how to use the traffic light pattern for real-time communication.
    
    Returns:
        Instructions and session info for Claude to begin monitoring.
    """
    try:
        # Ensure both queues exist
        user_queue_url = ensure_queue_exists(f"user-input-{session_id}")
        ai_queue_url = ensure_queue_exists(f"ai-response-{session_id}")
        
        return {
            "status": "session_started",
            "session_id": session_id,
            "timestamp": time.time(),
            "instructions": f"""
🚦 Real-time conversation session started!

SESSION ID: {session_id}

To communicate with the web browser in real-time:

1. **Monitor for user input**:
   Call wait_for_user_input('{session_id}', 8) repeatedly
   This will block for up to 8 seconds waiting for user interactions

2. **When user input arrives**:
   Process the input data (form changes, clicks, etc.)
   Analyze the data and prepare your response

3. **Send responses to browser**:
   Call send_response_to_browser('{session_id}', response_data, 'dashboard_update')
   Browser will receive this within ~100ms

4. **Continue the loop**:
   After sending response, call wait_for_user_input() again
   This creates continuous real-time communication

EXAMPLE WORKFLOW:
- wait_for_user_input() → User types wallet address
- Process wallet data, create dashboard
- send_response_to_browser() → Browser updates immediately  
- wait_for_user_input() → Ready for next user action

The browser is now ready to communicate with you in real-time!
            """,
            "queues_created": {
                "user_input": user_queue_url,
                "ai_response": ai_queue_url
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "session_id": session_id,
            "error": f"Failed to start session: {str(e)}",
            "timestamp": time.time()
        }