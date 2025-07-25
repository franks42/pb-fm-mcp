#!/usr/bin/env python3
"""
Heartbeat Monitor - Continuously polls for messages and responds automatically
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from functions.webui_functions.conversation_functions import get_pending_messages
import boto3

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
messages_table = dynamodb.Table(os.environ.get('MESSAGES_TABLE', 'pb-fm-mcp-dev-conversation-messages'))

async def process_message(session_id: str, message: dict):
    """Process a single message and send response."""
    message_id = message['id']
    user_message = message['message']
    
    print(f"\n💬 New message from user: '{user_message}'")
    print(f"   Session: {session_id}")
    print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
    
    # Generate contextual response
    response_text = f"""I'm actively listening! I received your message: "{user_message}"

This is an automated response from the heartbeat monitor that's continuously polling every 2 seconds. No need to tell me to check - I'm always watching! 👀

Message received at: {datetime.now().strftime('%I:%M:%S %p')}"""
    
    # Send response
    now = datetime.now()
    try:
        messages_table.update_item(
            Key={'session_id': session_id, 'message_id': message_id},
            UpdateExpression='SET #proc = :processed, #resp = :response, response_timestamp = :resp_time, processed_timestamp = :proc_time',
            ExpressionAttributeNames={
                '#proc': 'processed',
                '#resp': 'response'
            },
            ExpressionAttributeValues={
                ':processed': True,
                ':response': response_text,
                ':resp_time': now.isoformat(),
                ':proc_time': now.isoformat()
            }
        )
        print(f"✅ Response sent at {now.strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"❌ Error sending response: {e}")

async def heartbeat_monitor(session_id: str, poll_interval: int = 2):
    """Continuously monitor a session for new messages."""
    print(f"🫀 Starting heartbeat monitor for session: {session_id}")
    print(f"⏰ Polling every {poll_interval} seconds")
    print("Press Ctrl+C to stop\n")
    
    message_count = 0
    
    try:
        while True:
            # Check for pending messages
            result = await get_pending_messages(session_id)
            
            if result['count'] > 0:
                print(f"\n🔔 Found {result['count']} pending message(s)!")
                
                # Process each message
                for message in result['messages']:
                    message_count += 1
                    await process_message(session_id, message)
            else:
                # Print heartbeat indicator every 10 polls (20 seconds)
                if int(time.time()) % 20 < poll_interval:
                    print(f"💓 Heartbeat - {datetime.now().strftime('%H:%M:%S')} - Monitoring... (processed {message_count} messages so far)")
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Heartbeat monitor stopped")
        print(f"📊 Total messages processed: {message_count}")

async def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
    else:
        # Use the current test session by default
        session_id = '2de6adb9-a6c2-43bc-b521-727580617ffd'
    
    await heartbeat_monitor(session_id)

if __name__ == "__main__":
    asyncio.run(main())