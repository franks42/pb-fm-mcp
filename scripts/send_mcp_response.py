#!/usr/bin/env python3
"""
Send a response via MCP protocol to a specific message.
"""

import sys
import json
import httpx
import asyncio
from datetime import datetime

async def send_response(message_id: str, response: str, session_id: str, mcp_url: str = "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/mcp"):
    """Send response to web interface via MCP."""
    
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "send_response_to_web",
            "arguments": {
                "message_id": message_id,
                "response": response,
                "session_id": session_id
            }
        },
        "id": f"response-{datetime.now().timestamp()}"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(mcp_url, json=payload)
        result = response.json()
        
        if "result" in result:
            print("✅ Response sent successfully!")
            return True
        else:
            print(f"❌ Error: {result}")
            return False

def main():
    if len(sys.argv) < 4:
        print("Usage: send_mcp_response.py <message_id> <response> <session_id>")
        sys.exit(1)
    
    message_id = sys.argv[1]
    response_text = sys.argv[2]
    session_id = sys.argv[3]
    
    success = asyncio.run(send_response(message_id, response_text, session_id))
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()