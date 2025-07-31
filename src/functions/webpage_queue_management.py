"""
Webpage MVP Queue Management Functions

Handles SQS queue operations for browser-to-browser message synchronization.
Implements the fan-out pattern for multi-browser synchronization.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError

from registry import api_function

# Initialize AWS clients
sqs = boto3.client("sqs", region_name="us-west-1")
dynamodb = boto3.client("dynamodb", region_name="us-west-1")

# Configuration
TABLE_NAME = "pb-fm-webpage-sessions"
QUEUE_PREFIX = "pb-fm-webpage-"
MAX_MESSAGES = 10
POLL_TIMEOUT = 20  # seconds


@api_function(protocols=["mcp", "rest"])
def webpage_send_to_all_browsers(
    session_id: str, message: Dict[str, Any], exclude_client: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a message to all browsers in a session using fan-out pattern.

    Sends to all active client queues, optionally excluding the sender.
    """
    try:
        # Get all active clients in session
        clients_response = dynamodb.query(
            TableName=TABLE_NAME,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            FilterExpression="#status = :active",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":pk": {"S": f"SESSION#{session_id}"},
                ":sk_prefix": {"S": "CLIENT#"},
                ":active": {"S": "active"},
            },
        )

        # Prepare message with metadata
        fan_out_message = {
            **message,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "message_type": message.get("message_type", "content_update"),
        }

        message_body = json.dumps(fan_out_message)

        # Send to all client queues
        sent_count = 0
        failed_count = 0
        recipients = []

        for item in clients_response.get("Items", []):
            client_id = item.get("client_id", {}).get("S", "")
            queue_url = item.get("queue_url", {}).get("S", "")

            # Skip excluded client
            if exclude_client and client_id == exclude_client:
                continue

            if queue_url:
                try:
                    sqs.send_message(
                        QueueUrl=queue_url,
                        MessageBody=message_body,
                        MessageAttributes={
                            "session_id": {
                                "StringValue": session_id,
                                "DataType": "String",
                            },
                            "client_id": {
                                "StringValue": client_id,
                                "DataType": "String",
                            },
                        },
                    )
                    sent_count += 1
                    recipients.append(client_id)
                except ClientError:
                    failed_count += 1

        return {
            "success": True,
            "session_id": session_id,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "recipients": recipients,
            "excluded_client": exclude_client,
            "message_size": len(message_body),
            "sent_at": datetime.now().isoformat(),
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to send to all browsers: {str(e)}"}
