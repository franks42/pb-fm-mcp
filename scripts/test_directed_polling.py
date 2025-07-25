#!/usr/bin/env python3
"""
Test server-directed polling where MCP response tells Claude when to check back
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from functions.webui_functions.conversation_functions import get_pending_messages

async def directed_polling_demo(session_id: str, max_polls: int = 5):
    """Demonstrate server-directed polling pattern."""
    print(f"🚀 Starting server-directed polling demo")
    print(f"Session: {session_id}")
    print(f"Max polls: {max_polls}\n")
    
    poll_count = 0
    
    while poll_count < max_polls:
        poll_count += 1
        print(f"📡 Poll #{poll_count} at {datetime.now().strftime('%H:%M:%S')}")
        
        # Call MCP function
        result = await get_pending_messages(session_id)
        
        # Show what we got
        print(f"   Messages: {result['count']}")
        print(f"   Status: {result['status']}")
        
        # Check for polling instructions
        if 'next_poll_instruction' in result:
            instruction = result['next_poll_instruction']
            print(f"   📋 Server says: '{instruction['message']}'")
            print(f"   Action: {instruction['action']}")
            print(f"   Wait: {instruction['delay_seconds']} seconds")
            
            if instruction['action'] == 'poll_again':
                # Follow server's instruction to wait and poll again
                print(f"   ⏳ Waiting {instruction['delay_seconds']} seconds as instructed...\n")
                await asyncio.sleep(instruction['delay_seconds'])
            else:
                # Server says process messages
                print(f"   ✅ Server says to process {result['count']} messages")
                for msg in result['messages']:
                    print(f"      - '{msg['message']}'")
                break
        else:
            print("   ❌ No polling instructions from server\n")
            break
    
    print(f"\n🏁 Polling demo complete after {poll_count} polls")

async def main():
    session_id = '2de6adb9-a6c2-43bc-b521-727580617ffd'
    await directed_polling_demo(session_id)

if __name__ == "__main__":
    asyncio.run(main())