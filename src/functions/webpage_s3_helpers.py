"""
Webpage MVP S3 Content Helper Functions

Handles S3 storage and retrieval for webpage content using the reference pattern.
All large content is stored in S3, only references are passed via SQS.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import boto3
from botocore.exceptions import ClientError

from registry import api_function

# Initialize AWS clients
s3 = boto3.client("s3", region_name="us-west-1")

# Configuration
BUCKET_NAME = "pb-fm-webpage-mvp-assets"
DEFAULT_CONTENT_TYPE = "application/json"
MAX_CONTENT_SIZE = 5 * 1024 * 1024  # 5MB limit


def _generate_content_key(
    session_id: str, content_type: str, content_hash: str = None
) -> str:
    """Generate S3 key for content storage"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if content_hash:
        return (
            f"sessions/{session_id}/{content_type}/{timestamp}-{content_hash[:8]}.json"
        )
    else:
        return f"sessions/{session_id}/{content_type}/{timestamp}.json"


def _calculate_content_hash(content: Union[str, dict]) -> str:
    """Calculate MD5 hash of content for deduplication"""
    if isinstance(content, dict):
        content_str = json.dumps(content, sort_keys=True)
    else:
        content_str = str(content)
    return hashlib.md5(content_str.encode()).hexdigest()


@api_function(
    protocols=["mcp", "rest"],
    description="Store webpage content in S3 and return reference for SQS messaging using MVP architecture",
)
def webpage_store_content(
    session_id: str,
    content: Dict[str, Any],
    content_type: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Store content in S3 and return reference for SQS messaging.

    Uses content hashing for deduplication and generates stable references.
    """
    try:
        # Validate content size
        content_str = json.dumps(content)
        if len(content_str) > MAX_CONTENT_SIZE:
            return {
                "success": False,
                "error": f"Content too large: {len(content_str)} bytes (max: {MAX_CONTENT_SIZE})",
            }

        # Calculate content hash for deduplication
        content_hash = _calculate_content_hash(content)
        s3_key = _generate_content_key(session_id, content_type, content_hash)

        # Prepare storage object
        storage_object = {
            "content": content,
            "metadata": {
                "session_id": session_id,
                "content_type": content_type,
                "content_hash": content_hash,
                "stored_at": datetime.now().isoformat(),
                "size_bytes": len(content_str),
                **(metadata or {}),
            },
        }

        # Store in S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(storage_object),
            ContentType=DEFAULT_CONTENT_TYPE,
            Metadata={
                "session-id": session_id,
                "content-type": content_type,
                "content-hash": content_hash,
            },
        )

        # Generate public URL for browser access
        public_url = f"https://{BUCKET_NAME}.s3.us-west-1.amazonaws.com/{s3_key}"

        return {
            "success": True,
            "s3_reference": {
                "bucket": BUCKET_NAME,
                "key": s3_key,
                "url": public_url,
                "content_hash": content_hash,
                "content_type": content_type,
                "size_bytes": len(content_str),
            },
            "session_id": session_id,
            "stored_at": datetime.now().isoformat(),
        }

    except ClientError as e:
        return {"success": False, "error": f"Failed to store content in S3: {str(e)}"}
