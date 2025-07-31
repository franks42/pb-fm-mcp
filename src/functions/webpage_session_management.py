"""
Webpage MVP Session Management Functions

Handles webpage session creation, browser client management, and session state.
Uses DynamoDB table 'pb-fm-webpage-sessions' with PK/SK structure for session data.
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError

from registry import api_function

# Initialize AWS clients
dynamodb = boto3.client("dynamodb", region_name="us-west-1")
sqs = boto3.client("sqs", region_name="us-west-1")

# Configuration
TABLE_NAME = "pb-fm-webpage-sessions"
QUEUE_PREFIX = "pb-fm-webpage-"
SESSION_TTL_HOURS = 24


def _get_ttl_timestamp() -> int:
    """Get TTL timestamp for DynamoDB (24 hours from now)"""
    return int((datetime.now() + timedelta(hours=SESSION_TTL_HOURS)).timestamp())


def _generate_client_id() -> str:
    """Generate unique client ID for browser instances"""
    return f"browser-{uuid.uuid4().hex[:8]}"


@api_function(protocols=["mcp", "rest"])
def webpage_create_session(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new webpage session with initial configuration.

    Returns session details including session ID and initial state.
    """
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = f"session-{int(time.time())}-{uuid.uuid4().hex[:6]}"

        # Check if session already exists
        try:
            response = dynamodb.get_item(
                TableName=TABLE_NAME,
                Key={"PK": {"S": f"SESSION#{session_id}"}, "SK": {"S": "METADATA"}},
            )
            if "Item" in response:
                return {
                    "success": False,
                    "error": f"Session {session_id} already exists",
                    "session_id": session_id,
                }
        except ClientError:
            pass  # Session doesn't exist, continue with creation

        # Create session metadata
        session_item = {
            "PK": {"S": f"SESSION#{session_id}"},
            "SK": {"S": "METADATA"},
            "status": {"S": "active"},
            "created_at": {"S": datetime.now().isoformat()},
            "last_activity": {"S": datetime.now().isoformat()},
            "participant_count": {"N": "0"},
            "master_client_id": {"S": ""},
            "observer_count": {"N": "0"},
            "ttl": {"N": str(_get_ttl_timestamp())},
        }

        dynamodb.put_item(TableName=TABLE_NAME, Item=session_item)

        return {
            "success": True,
            "session_id": session_id,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "participant_count": 0,
            "master_client_id": None,
            "observer_count": 0,
            "session_url": f"https://pb-fm-webpage.com/session/{session_id}",
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to create session: {str(e)}"}


@api_function(protocols=["mcp", "rest"])
def webpage_get_session_status(session_id: str) -> Dict[str, Any]:
    """
    Get comprehensive status information for a webpage session.

    Returns session metadata and list of active participants.
    """
    try:
        # Get session metadata
        response = dynamodb.get_item(
            TableName=TABLE_NAME,
            Key={"PK": {"S": f"SESSION#{session_id}"}, "SK": {"S": "METADATA"}},
        )
        if "Item" not in response:
            return {"success": False, "error": f"Session {session_id} not found"}

        session_data = response["Item"]

        # Get all clients in session
        clients_response = dynamodb.query(
            TableName=TABLE_NAME,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"SESSION#{session_id}"},
                ":sk_prefix": {"S": "CLIENT#"},
            },
        )

        participants = []
        for item in clients_response.get("Items", []):
            participants.append(
                {
                    "client_id": item.get("client_id", {}).get("S", ""),
                    "role": item.get("role", {}).get("S", ""),
                    "status": item.get("status", {}).get("S", ""),
                    "joined_at": item.get("joined_at", {}).get("S", ""),
                    "last_activity": item.get("last_activity", {}).get("S", ""),
                    "queue_name": item.get("queue_name", {}).get("S", ""),
                }
            )

        return {
            "success": True,
            "session_id": session_id,
            "status": session_data.get("status", {}).get("S", ""),
            "created_at": session_data.get("created_at", {}).get("S", ""),
            "last_activity": session_data.get("last_activity", {}).get("S", ""),
            "participant_count": int(
                session_data.get("participant_count", {}).get("N", "0")
            ),
            "observer_count": int(session_data.get("observer_count", {}).get("N", "0")),
            "master_client_id": session_data.get("master_client_id", {}).get("S", ""),
            "participants": participants,
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to get session status: {str(e)}"}
