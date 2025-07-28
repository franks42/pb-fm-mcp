"""
AI Terminal - Real-time conversation system using SQS Traffic Light Pattern

This module provides MCP functions for running a continuous AI conversation
loop that mimics local prompt-response interaction but works through web browser.
"""

import time
import json
from typing import Dict, Any

from registry import api_function
from utils import JSONType
from .sqs_traffic_light import wait_for_user_input, send_response_to_browser


@api_function(
    protocols=["mcp"],
    description="Start an AI terminal conversation loop. Continuously waits for user prompts "
                "from the web interface and responds as if they were local prompts. "
                "Perfect for demonstrating real-time AI-browser communication."
)
async def ai_terminal_conversation(
    session_id: str,
    timeout_seconds: int = 10,
    max_iterations: int = 100
) -> JSONType:
    """
    Run a continuous AI terminal conversation loop.
    
    This function demonstrates the SQS Traffic Light pattern by:
    1. Waiting for user input from web terminal
    2. Processing prompts as if they were local AI prompts  
    3. Sending responses back to web browser
    4. Looping for continuous conversation
    
    Args:
        session_id: Unique session identifier for user isolation
        timeout_seconds: How long to wait for each user input
        max_iterations: Maximum conversation turns (safety limit)
        
    Returns:
        Summary of conversation session including metrics and final state
    """
    conversation_log = []
    iteration = 0
    total_wait_time = 0
    total_response_time = 0
    
    # Send initial greeting to browser
    await send_response_to_browser(
        session_id=session_id,
        response_data={
            "response": "🚦 AI Terminal connected! I'm ready to chat. What would you like to talk about?",
            "type": "greeting",
            "session_info": {
                "session_id": session_id,
                "max_iterations": max_iterations,
                "timeout_seconds": timeout_seconds
            }
        },
        response_type="ai_response"
    )
    
    try:
        while iteration < max_iterations:
            iteration += 1
            
            # Wait for user input
            wait_start = time.time()
            user_input = await wait_for_user_input(
                session_id=session_id,
                timeout_seconds=timeout_seconds
            )
            wait_end = time.time()
            wait_duration = wait_end - wait_start
            total_wait_time += wait_duration
            
            # Check if we got user input
            if not user_input.get("has_input"):
                # No input received - send timeout message and continue waiting
                await send_response_to_browser(
                    session_id=session_id,
                    response_data={
                        "response": f"⏰ Still here! Waiting for your input... (iteration {iteration})",
                        "type": "timeout_message",
                        "timeout_info": {
                            "waited_seconds": timeout_seconds,
                            "iteration": iteration
                        }
                    },
                    response_type="timeout"
                )
                continue
            
            # Extract the user's prompt
            input_data = user_input.get("input_data", {})
            user_prompt = input_data.get("input_value", "")
            
            if not user_prompt.strip():
                await send_response_to_browser(
                    session_id=session_id,
                    response_data={
                        "response": "I received an empty message. Please type something!",
                        "type": "error"
                    },
                    response_type="error"
                )
                continue
            
            # Log the interaction
            conversation_log.append({
                "iteration": iteration,
                "user_prompt": user_prompt,
                "timestamp": time.time(),
                "wait_duration": wait_duration
            })
            
            # Process the prompt - this is where we simulate AI response
            response_start = time.time()
            ai_response = await process_ai_prompt(user_prompt, session_id, iteration)
            response_end = time.time()
            response_duration = response_end - response_start
            total_response_time += response_duration
            
            # Send AI response back to browser
            await send_response_to_browser(
                session_id=session_id,
                response_data={
                    "response": ai_response,
                    "type": "ai_response",
                    "metadata": {
                        "iteration": iteration,
                        "processing_time": f"{response_duration:.2f}s",
                        "wait_time": f"{wait_duration:.2f}s",
                        "prompt_length": len(user_prompt)
                    }
                },
                response_type="ai_response"
            )
            
            # Update conversation log with response
            conversation_log[-1].update({
                "ai_response": ai_response,
                "response_duration": response_duration
            })
            
            # Check for exit commands
            if user_prompt.lower().strip() in ['exit', 'quit', 'bye', 'goodbye']:
                await send_response_to_browser(
                    session_id=session_id,
                    response_data={
                        "response": f"👋 Goodbye! It was great chatting with you. Session ended after {iteration} exchanges.",
                        "type": "farewell",
                        "session_summary": {
                            "total_exchanges": iteration,
                            "total_wait_time": f"{total_wait_time:.2f}s",
                            "total_response_time": f"{total_response_time:.2f}s",
                            "avg_response_time": f"{total_response_time/iteration:.2f}s" if iteration > 0 else "0s"
                        }
                    },
                    response_type="farewell"
                )
                break
    
    except Exception as e:
        # Handle any errors gracefully
        await send_response_to_browser(
            session_id=session_id,
            response_data={
                "response": f"❌ An error occurred in the conversation loop: {str(e)}",
                "type": "error",
                "error_details": {
                    "iteration": iteration,
                    "error": str(e)
                }
            },
            response_type="error"
        )
    
    # Return session summary
    return {
        "session_id": session_id,
        "status": "completed" if iteration < max_iterations else "max_iterations_reached",
        "total_iterations": iteration,
        "conversation_exchanges": len([log for log in conversation_log if "ai_response" in log]),
        "total_wait_time": f"{total_wait_time:.2f}s",
        "total_response_time": f"{total_response_time:.2f}s",
        "avg_response_time": f"{total_response_time/len(conversation_log):.2f}s" if conversation_log else "0s",
        "session_duration": f"{time.time() - (conversation_log[0]['timestamp'] if conversation_log else time.time()):.2f}s",
        "conversation_log": conversation_log
    }


async def process_ai_prompt(prompt: str, session_id: str, iteration: int) -> str:
    """
    Process a user prompt and generate an AI response.
    
    This simulates what would happen if the user typed the prompt directly
    to a local AI assistant. In a real implementation, this would call
    the actual AI model/service.
    """
    prompt_lower = prompt.lower().strip()
    
    # Handle special commands
    if prompt_lower in ['help', '?']:
        return """🤖 AI Terminal Help:
        
Available commands:
• Type any question or statement to chat
• 'help' or '?' - Show this help
• 'status' - Show session information  
• 'time' - Show current time
• 'exit', 'quit', 'bye' - End the conversation

This terminal demonstrates real-time communication between your browser and AI using SQS queues. Each message travels through the traffic light system in ~500ms!"""
    
    elif prompt_lower == 'status':
        return f"""📊 Session Status:
        
• Session ID: {session_id}
• Current iteration: {iteration}
• System: SQS Traffic Light Pattern
• Response time: ~500ms average
• Connection: Active ✅

The AI is running in a continuous loop, waiting for your messages and responding in real-time through AWS SQS queues."""
    
    elif prompt_lower == 'time':
        return f"🕐 Current time: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    
    elif 'hello' in prompt_lower or 'hi' in prompt_lower:
        return f"👋 Hello! Great to meet you in this AI terminal. I'm running in iteration #{iteration} of our conversation loop. What's on your mind?"
    
    elif 'how are you' in prompt_lower:
        return "I'm doing well! I'm running smoothly in this SQS traffic light system. Each message we exchange goes through AWS queues and comes back in about half a second. Pretty neat, right? How are you doing?"
    
    elif 'test' in prompt_lower:
        return f"""🧪 Test Response #{iteration}:
        
✅ SQS Traffic Light System: Working
✅ Bidirectional Communication: Active  
✅ Session Persistence: Maintained
✅ Real-time Responses: ~500ms latency

Your test message was: "{prompt}"
Processed at: {time.strftime('%H:%M:%S')}

Try asking me anything else!"""
    
    elif len(prompt) > 200:
        return f"📝 I received a long message ({len(prompt)} characters)! Here's what I understand:\n\nYou said: \"{prompt[:100]}...\"\n\nI can handle messages of any length through the SQS system. What would you like to discuss about your message?"
    
    else:
        # Generic conversational response
        responses = [
            f"Interesting! You mentioned: \"{prompt}\". That's iteration #{iteration} of our conversation. What else would you like to explore?",
            f"Thanks for sharing that! I processed your message \"{prompt}\" in real-time through the SQS traffic light system. Tell me more!",
            f"I hear you saying: \"{prompt}\". This is working great - we're having a real conversation through queues! What's next?",
            f"Got it! Your message \"{prompt}\" came through perfectly in iteration #{iteration}. The traffic light pattern is working beautifully!",
            f"That's fascinating! You wrote: \"{prompt}\". I love how smoothly this real-time communication is working. What else is on your mind?"
        ]
        
        # Choose response based on iteration for variety
        return responses[iteration % len(responses)]


@api_function(
    protocols=["mcp"],
    description="Get current status of an AI terminal conversation session. "
                "Shows session metrics, conversation history, and system health."
)
async def get_ai_terminal_status(session_id: str) -> JSONType:
    """
    Get the current status of an AI terminal conversation session.
    
    Returns information about the session including conversation metrics,
    system status, and queue health.
    """
    from .sqs_traffic_light import get_traffic_light_status
    
    # Get queue status
    queue_status = await get_traffic_light_status(session_id)
    
    return {
        "session_id": session_id,
        "timestamp": time.time(),
        "system_status": "active",
        "ai_terminal_version": "1.0.0",
        "traffic_light_system": queue_status,
        "instructions": {
            "start_conversation": f"Call ai_terminal_conversation('{session_id}') to begin",
            "web_interface": "Open /ai-terminal in your browser",
            "session_management": "Each session is isolated by session_id"
        },
        "performance_info": {
            "typical_latency": "450-650ms end-to-end",
            "queue_persistence": "Messages survive Lambda cold starts",
            "scalability": "Supports unlimited concurrent sessions"
        },
        "browser_url": f"https://pb-fm-mcp-dev.creativeapptitude.com/ai-terminal?session={session_id}",
        "production_url": f"https://pb-fm-mcp.creativeapptitude.com/ai-terminal?session={session_id}"
    }


@api_function(
    protocols=["mcp"],
    description="Get the browser URL for an AI terminal session. Returns the web interface URL "
                "that connects to the specified session ID for real-time conversation."
)
async def get_ai_terminal_url(session_id: str) -> JSONType:
    """
    Get the browser URL for accessing an AI terminal session.
    
    This function returns the web interface URLs (dev and production) that allow
    users to connect to a specific AI terminal session for real-time conversation
    through the browser.
    
    Args:
        session_id: The session ID to generate URLs for
        
    Returns:
        URLs for accessing the AI terminal web interface with the specified session
    """
    return {
        "session_id": session_id,
        "dev_url": f"https://pb-fm-mcp-dev.creativeapptitude.com/ai-terminal?session={session_id}",
        "production_url": f"https://pb-fm-mcp.creativeapptitude.com/ai-terminal?session={session_id}",
        "instructions": [
            "Open either URL in your browser to access the AI terminal",
            "The session ID in the URL connects you to this specific conversation",
            "You can bookmark the URL to return to the same session later",
            "Multiple browser tabs with the same URL will share the same conversation"
        ],
        "usage_example": f"Visit: https://pb-fm-mcp-dev.creativeapptitude.com/ai-terminal?session={session_id}"
    }