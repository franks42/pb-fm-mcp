"""
Webpage MVP Orchestration Functions

High-level AI-facing functions that orchestrate the webpage MVP functionality.
These are the main functions the AI will call to manage webpage sessions and content.
"""

import json
from datetime import datetime
from typing import Dict, Optional, Any
from registry import api_function

# Import all required functions at top level
from .stats_functions import fetch_current_hash_statistics
from .webpage_s3_helpers import webpage_store_content
from .webpage_queue_management import webpage_send_to_all_browsers
from .webpage_session_management import webpage_create_session


@api_function(
    protocols=["mcp", "rest"],
    description="Fetch current HASH price, store in S3, and update all browsers via SQS fan-out - main MVP function",
)
async def webpage_update_hash_price_display(
    session_id: str, display_format: str = "compact"
) -> Dict[str, Any]:
    """
    Fetch current HASH price and update all browsers in the session.

    This is the main function for the MVP - fetches price data, stores in S3,
    and sends references to all browsers via SQS fan-out.
    """
    try:
        # 1. Fetch current HASH price data
        price_result = await fetch_current_hash_statistics()
        if not price_result.get(
            "success", True
        ):  # Some functions don't have success field
            return {
                "success": False,
                "error": "Failed to fetch HASH price data",
                "details": price_result,
            }

        # Extract price data from the result
        # The fetch_current_hash_statistics returns content in a specific format
        price_data = {}
        if "content" in price_result and price_result["content"]:
            # Handle MCP format response
            content_item = price_result["content"][0]
            if "text" in content_item:
                price_text = content_item["text"]
                if isinstance(price_text, str):
                    try:
                        price_data = json.loads(price_text)
                    except json.JSONDecodeError:
                        price_data = {"raw_response": price_text}
                else:
                    price_data = price_text
        else:
            # Handle direct response format
            price_data = price_result

        # 2. Store formatted price data in S3

        # Format price data for display
        current_price = price_data.get("current_price_usd", 0)
        price_change_24h = price_data.get("price_change_percentage_24h", 0)

        if display_format == "compact":
            formatted_content = {
                "price": f"${current_price:.4f}",
                "change_24h": f"{price_change_24h:+.2f}%",
                "change_direction": "up" if price_change_24h >= 0 else "down",
                "last_updated": datetime.now().isoformat(),
                "display_format": "compact",
            }
        else:  # detailed format
            formatted_content = {
                "price": f"${current_price:.4f}",
                "change_24h": f"{price_change_24h:+.2f}%",
                "change_direction": "up" if price_change_24h >= 0 else "down",
                "market_cap": (
                    f"${price_data.get('market_cap', 0):,.0f}"
                    if price_data.get("market_cap")
                    else "N/A"
                ),
                "volume_24h": (
                    f"${price_data.get('total_volume', 0):,.0f}"
                    if price_data.get("total_volume")
                    else "N/A"
                ),
                "last_updated": datetime.now().isoformat(),
                "display_format": "detailed",
                "raw_data": price_data,
            }

        storage_result = webpage_store_content(
            session_id=session_id,
            content=formatted_content,
            content_type="hash-price-data",
            metadata={
                "display_format": display_format,
                "raw_price": current_price,
                "price_change_24h": price_change_24h,
            },
        )

        if not storage_result.get("success"):
            return {
                "success": False,
                "error": "Failed to store price data",
                "details": storage_result,
            }

        s3_reference = storage_result["s3_reference"]

        # 3. Prepare message for browsers
        update_message = {
            "message_type": "price_update",
            "component": "hash-price-display",
            "action": "update",
            "s3_reference": s3_reference,
            "display_format": display_format,
            "price_summary": {
                "price": current_price,
                "change_24h": price_change_24h,
            },
        }

        # 4. Fan-out to all browsers in session

        fanout_result = webpage_send_to_all_browsers(
            session_id=session_id, message=update_message
        )

        if not fanout_result.get("success"):
            return {
                "success": False,
                "error": "Failed to send updates to browsers",
                "details": fanout_result,
            }

        return {
            "success": True,
            "session_id": session_id,
            "price_data": {
                "current_price_usd": current_price,
                "price_change_24h": price_change_24h,
                "last_updated": storage_result.get("stored_at"),
            },
            "s3_reference": s3_reference,
            "browsers_updated": fanout_result.get("sent_count", 0),
            "update_timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update HASH price display: {str(e)}",
        }


@api_function(
    protocols=["mcp", "rest"],
    description="Create new webpage session and return all necessary connection details for browsers",
)
def webpage_create_new_session(
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new webpage session and return all necessary connection details.

    This is a convenience function that creates the session and provides
    everything needed for browsers to connect.
    """
    try:
        # Create the session

        creation_result = webpage_create_session(session_id)

        if not creation_result.get("success"):
            return creation_result

        actual_session_id = creation_result["session_id"]

        # Return comprehensive connection information
        return {
            "success": True,
            "session_id": actual_session_id,
            "session_url": f"https://pb-fm-webpage.com/session/{actual_session_id}",
            "master_url": f"https://pb-fm-webpage.com/session/{actual_session_id}",
            "observer_url": f"https://pb-fm-webpage.com/session/{actual_session_id}?role=observer",
            "connection_info": {
                "created_at": creation_result["created_at"],
                "status": "active",
                "participant_count": 0,
                "ready_for_connections": True,
            },
            "next_steps": [
                "Share the session_url with participants",
                "First browser to connect becomes the master",
                "Additional browsers become observers",
                "Use webpage_update_hash_price_display() to start showing data",
            ],
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create new session: {str(e)}",
        }
