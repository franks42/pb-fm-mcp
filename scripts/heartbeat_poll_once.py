#!/usr/bin/env python3
"""
Simple heartbeat polling script that checks for messages once.
This allows Claude Code to poll without needing Bash permission each time.
"""

import sys
import json
import httpx
import asyncio
from datetime import datetime

async def poll_for_messages(session_id: str, mcp_url: str = "https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/mcp"):
    """Poll MCP server once for pending messages."""
    
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "get_pending_messages",
            "arguments": {
                "session_id": session_id
            }
        },
        "id": f"poll-{datetime.now().timestamp()}"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(mcp_url, json=payload)
        result = response.json()
        
        # Extract the actual response content
        if "result" in result and "content" in result["result"]:
            content = result["result"]["content"][0]["text"]
            # Parse the string representation of the dict
            data = eval(content)  # Safe here as we control the server response
            
            print(f"\n🫀 Heartbeat Poll at {datetime.now().strftime('%H:%M:%S')}")
            print(f"📊 Session: {session_id}")
            print(f"📬 Messages found: {data['count']}")
            print(f"🎯 Server instruction: {data['next_poll_instruction']['action']}")
            print(f"💬 Message: {data['next_poll_instruction']['message']}")
            
            if data['count'] > 0:
                print("\n📨 Pending messages:")
                for i, msg in enumerate(data['messages'], 1):
                    print(f"  {i}. {msg['message'][:50]}...")
                    print(f"     ID: {msg['id']}")
                    print(f"     Time: {msg['timestamp']}")
            
            return data
        else:
            print(f"❌ Error: {result}")
            return None

def main():
    if len(sys.argv) < 2:
        print("Usage: heartbeat_poll_once.py <session_id>")
        sys.exit(1)
    
    session_id = sys.argv[1]
    result = asyncio.run(poll_for_messages(session_id))
    
    # Return exit code based on whether messages were found
    if result and result['count'] > 0:
        sys.exit(0)  # Messages found
    else:
        sys.exit(1)  # No messages

if __name__ == "__main__":
    main()