# Enhanced MCP Polling with Result Feedback - Python Implementation

## Overview

This document provides a complete Python implementation of an enhanced Model Context Protocol (MCP) server that enables Claude AI to:

1. **Poll for directives** from external systems
2. **Execute directives** and provide detailed results
3. **Report results** back to the MCP server in subsequent calls
4. **Enable smart follow-ups** based on execution results
5. **Provide analytics and monitoring** capabilities

## Core Implementation

### MCP Server with Result Feedback

```python
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
import asyncio
import aiohttp
from collections import defaultdict
import logging

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    URGENT = "urgent"

class NextAction(Enum):
    EXECUTE_THEN_POLL = "EXECUTE_THEN_POLL"
    WAIT_THEN_POLL = "WAIT_THEN_POLL"
    STOP = "STOP"

@dataclass
class DirectiveResult:
    directive_id: str
    success: bool
    result: str
    execution_time: Optional[float] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FollowUpRule:
    condition: str  # Simple condition string
    next_directive: str
    priority: Priority = Priority.MEDIUM
    delay_seconds: int = 0

@dataclass
class DirectiveOptions:
    priority: Priority = Priority.MEDIUM
    webhook: Optional[str] = None
    follow_up_rules: List[FollowUpRule] = field(default_factory=list)
    retry_on_failure: bool = False
    max_retries: int = 3
    retry_delay: int = 30
    tags: List[str] = field(default_factory=list)
    timeout_seconds: Optional[int] = None

@dataclass
class Directive:
    id: str
    content: str
    priority: Priority
    timestamp: datetime
    options: DirectiveOptions = field(default_factory=DirectiveOptions)
    retry_count: int = 0
    
@dataclass 
class DirectiveResponse:
    has_directive: bool
    directive: Optional[str] = None
    directive_id: Optional[str] = None
    priority: Optional[str] = None
    next_action: NextAction = NextAction.WAIT_THEN_POLL
    wait_seconds: int = 5
    instructions: str = ""
    expect_result: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DirectiveAnalytics:
    total_completed: int
    success_rate: float
    average_execution_time: float
    pending_count: int
    active_count: int
    daily_volume: Dict[str, int]
    success_by_priority: Dict[str, float]
    common_failure_patterns: List[str]

class EnhancedDirectiveServer:
    def __init__(self):
        self.directive_queue: List[Directive] = []
        self.completed_directives: Dict[str, DirectiveResult] = {}
        self.pending_directives: Dict[str, Directive] = {}
        self.is_active = False
        self.session_id: Optional[str] = None
        self.global_webhooks: List[str] = []
        self.logger = logging.getLogger(__name__)
        
    async def start_directive_monitoring(self) -> Dict[str, Any]:
        """Initialize directive monitoring session"""
        self.is_active = True
        self.session_id = str(uuid.uuid4())
        
        return {
            "message": "Directive monitoring started. Call get_next_directive() to begin loop.",
            "session_id": self.session_id,
            "instructions": """You should now call get_next_directive() and continue calling it based on the response.
            
When you receive a directive:
1. Execute the directive completely
2. Call get_next_directive() again with the result parameter
3. Continue the loop indefinitely until instructed to stop

When no directive is available:
1. Wait the specified number of seconds
2. Call get_next_directive() again (no parameters needed)
3. Continue monitoring"""
        }
    
    async def get_next_directive(self, previous_result: Optional[DirectiveResult] = None) -> DirectiveResponse:
        """Main polling method - gets next directive and processes previous result"""
        
        # Process result from previous directive if provided
        if previous_result:
            await self._process_directive_result(previous_result)
        
        if not self.is_active:
            return DirectiveResponse(
                has_directive=False,
                next_action=NextAction.STOP,
                wait_seconds=0,
                instructions="Monitoring stopped"
            )
        
        # Get next directive from queue
        directive = self._get_next_directive_from_queue()
        
        if directive:
            # Store as pending
            self.pending_directives[directive.id] = directive
            
            return DirectiveResponse(
                has_directive=True,
                directive=directive.content,
                directive_id=directive.id,
                priority=directive.priority.value,
                next_action=NextAction.EXECUTE_THEN_POLL,
                wait_seconds=1,
                expect_result=True,
                instructions=f"""Execute this directive: "{directive.content}"

After completion, call get_next_directive() again with the result parameter using this exact format:

get_next_directive(DirectiveResult(
    directive_id="{directive.id}",
    success=True/False,
    result="detailed description of what you accomplished",
    execution_time=optional_seconds_as_float,
    error="error description if failed" or None,
    metadata={{"additional": "contextual information"}}
))

Be thorough in your result description - include key findings, actions taken, and any relevant data.""",
                metadata={
                    "timeout": directive.options.timeout_seconds,
                    "tags": directive.options.tags,
                    "retry_count": directive.retry_count
                }
            )
        else:
            # No directives available
            wait_time = self._calculate_polling_interval()
            return DirectiveResponse(
                has_directive=False,
                next_action=NextAction.WAIT_THEN_POLL,
                wait_seconds=wait_time,
                expect_result=False,
                instructions=f"No pending directives. Wait {wait_time} seconds, then call get_next_directive() again (no parameters needed when no previous directive to report)."
            )
    
    def _get_next_directive_from_queue(self) -> Optional[Directive]:
        """Get highest priority directive from queue"""
        if not self.directive_queue:
            return None
        
        # Sort by priority (urgent > high > medium > low) then by timestamp
        priority_order = {Priority.URGENT: 4, Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}
        
        self.directive_queue.sort(
            key=lambda d: (priority_order[d.priority], d.timestamp)
        )
        
        return self.directive_queue.pop(0)
    
    def _calculate_polling_interval(self) -> int:
        """Dynamic polling interval based on recent activity"""
        recent_cutoff = datetime.now() - timedelta(minutes=5)
        recent_completions = sum(
            1 for result in self.completed_directives.values()
            if result.timestamp > recent_cutoff
        )
        
        if recent_completions > 10:
            return 1  # Very active
        elif recent_completions > 5:
            return 3  # Active
        elif recent_completions > 0:
            return 5  # Some activity
        else:
            return 15  # Quiet period
    
    async def _process_directive_result(self, result: DirectiveResult):
        """Process the result from a completed directive"""
        # Store the result
        self.completed_directives[result.directive_id] = result
        
        # Get the original directive
        directive = self.pending_directives.pop(result.directive_id, None)
        
        if directive:
            self.logger.info(f"Directive '{directive.content}' completed: {result.success}")
            
            # Notify external systems
            await self._notify_external_systems(directive, result)
            
            # Handle follow-up actions
            await self._handle_directive_followup(directive, result)
        
    async def _notify_external_systems(self, directive: Directive, result: DirectiveResult):
        """Send notifications to external systems via webhooks"""
        notification = {
            "event": "directive_completed",
            "directive_id": directive.id,
            "directive": directive.content,
            "result": result.result,
            "success": result.success,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp.isoformat(),
            "session_id": self.session_id,
            "tags": directive.options.tags
        }
        
        # Collect all webhook URLs
        webhooks = []
        if directive.options.webhook:
            webhooks.append(directive.options.webhook)
        webhooks.extend(self.global_webhooks)
        
        # Send notifications concurrently
        if webhooks:
            await asyncio.gather(
                *[self._send_webhook(url, notification) for url in webhooks],
                return_exceptions=True
            )
    
    async def _send_webhook(self, url: str, data: Dict[str, Any]):
        """Send webhook notification"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status >= 400:
                        self.logger.warning(f"Webhook failed {url}: {response.status}")
        except Exception as e:
            self.logger.error(f"Webhook error {url}: {e}")
    
    async def _handle_directive_followup(self, directive: Directive, result: DirectiveResult):
        """Handle follow-up actions based on directive results"""
        
        # Handle follow-up rules
        if result.success and directive.options.follow_up_rules:
            for rule in directive.options.follow_up_rules:
                if self._evaluate_condition(rule.condition, result):
                    # Add follow-up directive
                    await asyncio.sleep(rule.delay_seconds)
                    await self.add_directive(
                        rule.next_directive,
                        DirectiveOptions(priority=rule.priority)
                    )
        
        # Handle retries on failure
        if not result.success and directive.options.retry_on_failure:
            directive.retry_count += 1
            
            if directive.retry_count < directive.options.max_retries:
                # Re-queue with delay
                await asyncio.sleep(directive.options.retry_delay)
                
                # Modify directive content to include retry context
                directive.content += f" (Retry #{directive.retry_count}, previous error: {result.error})"
                self.directive_queue.insert(0, directive)  # Add to front for priority
                
                self.logger.info(f"Retrying directive {directive.id} (attempt {directive.retry_count})")
    
    def _evaluate_condition(self, condition: str, result: DirectiveResult) -> bool:
        """Simple condition evaluation for follow-up rules"""
        condition = condition.lower()
        result_text = result.result.lower()
        
        # Simple keyword-based conditions
        if "success" in condition and result.success:
            return True
        elif "error" in condition and not result.success:
            return True
        elif "contains" in condition:
            # Extract the contains condition: 'result.contains("keyword")'
            try:
                keyword = condition.split('"')[1]
                return keyword in result_text
            except:
                pass
        
        return False
    
    async def add_directive(self, content: str, options: DirectiveOptions = None) -> str:
        """Add a new directive to the queue"""
        if options is None:
            options = DirectiveOptions()
        
        directive = Directive(
            id=str(uuid.uuid4()),
            content=content,
            priority=options.priority,
            timestamp=datetime.now(),
            options=options
        )
        
        self.directive_queue.append(directive)
        self.logger.info(f"Added directive: {content[:50]}...")
        
        return directive.id
    
    async def stop_monitoring(self) -> Dict[str, Any]:
        """Stop directive monitoring"""
        self.is_active = False
        
        return {
            "message": "Directive monitoring stopped",
            "session_id": self.session_id,
            "completed_directives": len(self.completed_directives),
            "pending_directives": len(self.pending_directives)
        }
    
    async def get_directive_analytics(self) -> DirectiveAnalytics:
        """Get comprehensive analytics about directive execution"""
        results = list(self.completed_directives.values())
        successful = [r for r in results if r.success]
        
        # Calculate daily volume
        daily_volume = defaultdict(int)
        for result in results:
            date_key = result.timestamp.strftime("%Y-%m-%d")
            daily_volume[date_key] += 1
        
        # Success rate by priority
        success_by_priority = {}
        for priority in Priority:
            priority_results = [
                r for r in results 
                if self.pending_directives.get(r.directive_id, 
                   Directive("", "", priority, datetime.now())).priority == priority
            ]
            if priority_results:
                success_count = sum(1 for r in priority_results if r.success)
                success_by_priority[priority.value] = success_count / len(priority_results)
        
        # Common failure patterns
        failure_patterns = []
        failed_results = [r for r in results if not r.success]
        error_counts = defaultdict(int)
        for result in failed_results:
            if result.error:
                # Simple error categorization
                if "timeout" in result.error.lower():
                    error_counts["timeout"] += 1
                elif "access" in result.error.lower():
                    error_counts["access_denied"] += 1
                elif "format" in result.error.lower():
                    error_counts["format_error"] += 1
                else:
                    error_counts["other"] += 1
        
        failure_patterns = [f"{error}: {count}" for error, count in error_counts.most_common(5)]
        
        return DirectiveAnalytics(
            total_completed=len(results),
            success_rate=len(successful) / len(results) if results else 0,
            average_execution_time=sum(r.execution_time or 0 for r in successful) / len(successful) if successful else 0,
            pending_count=len(self.directive_queue),
            active_count=len(self.pending_directives),
            daily_volume=dict(daily_volume),
            success_by_priority=success_by_priority,
            common_failure_patterns=failure_patterns
        )
    
    async def get_recent_results(self, limit: int = 10) -> List[DirectiveResult]:
        """Get recent directive results"""
        results = sorted(
            self.completed_directives.values(),
            key=lambda r: r.timestamp,
            reverse=True
        )
        return results[:limit]
    
    def add_global_webhook(self, webhook_url: str):
        """Add a global webhook that receives all directive results"""
        self.global_webhooks.append(webhook_url)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "pending_directives": len(self.directive_queue),
            "active_directives": len(self.pending_directives),
            "completed_directives": len(self.completed_directives),
            "is_monitoring": self.is_active,
            "session_id": self.session_id
        }
```

## FastAPI Web Server Implementation

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="Enhanced MCP Directive Server")

# Enable CORS for web interfaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global directive server instance
directive_server = EnhancedDirectiveServer()

# Pydantic models for API
class DirectiveRequest(BaseModel):
    directive: str
    priority: str = "medium"
    webhook: Optional[str] = None
    follow_up_rules: List[Dict[str, Any]] = []
    retry_on_failure: bool = False
    max_retries: int = 3
    tags: List[str] = []

class DirectiveResultRequest(BaseModel):
    directive_id: str
    success: bool
    result: str
    execution_time: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}

# MCP Tool Endpoints (called by Claude)
@app.post("/mcp/start_monitoring")
async def start_monitoring():
    """MCP Tool: Start directive monitoring"""
    return await directive_server.start_directive_monitoring()

@app.post("/mcp/get_next_directive")
async def get_next_directive(previous_result: Optional[DirectiveResultRequest] = None):
    """MCP Tool: Get next directive with optional result from previous"""
    result_obj = None
    if previous_result:
        result_obj = DirectiveResult(
            directive_id=previous_result.directive_id,
            success=previous_result.success,
            result=previous_result.result,
            execution_time=previous_result.execution_time,
            error=previous_result.error,
            metadata=previous_result.metadata
        )
    
    response = await directive_server.get_next_directive(result_obj)
    return response.__dict__

@app.post("/mcp/stop_monitoring") 
async def stop_monitoring():
    """MCP Tool: Stop directive monitoring"""
    return await directive_server.stop_monitoring()

@app.get("/mcp/analytics")
async def get_analytics():
    """MCP Tool: Get directive analytics"""
    analytics = await directive_server.get_directive_analytics()
    return analytics.__dict__

# External API Endpoints (for external systems)
@app.post("/api/directives")
async def add_directive(request: DirectiveRequest):
    """External API: Add new directive"""
    try:
        priority = Priority(request.priority.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid priority")
    
    # Convert follow-up rules
    follow_up_rules = []
    for rule_data in request.follow_up_rules:
        rule = FollowUpRule(
            condition=rule_data.get("condition", ""),
            next_directive=rule_data.get("next_directive", ""),
            priority=Priority(rule_data.get("priority", "medium")),
            delay_seconds=rule_data.get("delay_seconds", 0)
        )
        follow_up_rules.append(rule)
    
    options = DirectiveOptions(
        priority=priority,
        webhook=request.webhook,
        follow_up_rules=follow_up_rules,
        retry_on_failure=request.retry_on_failure,
        max_retries=request.max_retries,
        tags=request.tags
    )
    
    directive_id = await directive_server.add_directive(request.directive, options)
    return {"success": True, "directive_id": directive_id}

@app.get("/api/queue")
async def get_queue_status():
    """External API: Get queue status"""
    return directive_server.get_queue_status()

@app.get("/api/results")
async def get_recent_results(limit: int = 10):
    """External API: Get recent results"""
    results = await directive_server.get_recent_results(limit)
    return [result.__dict__ for result in results]

@app.post("/api/webhook")
async def add_global_webhook(webhook_url: str):
    """External API: Add global webhook"""
    directive_server.add_global_webhook(webhook_url)
    return {"success": True}

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "monitoring": directive_server.is_active}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## MCP Server Configuration

```json
{
  "mcpServers": {
    "directive-server": {
      "command": "python",
      "args": ["-m", "uvicorn", "directive_server:app", "--host", "0.0.0.0", "--port", "8000"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

## Usage Examples

### 1. Starting Monitoring (Claude Conversation)

```
Human: Start monitoring for directives and execute them with detailed result reporting.

Claude: I'll start the enhanced directive monitoring system. Let me initialize it...

*calls start_directive_monitoring()*

Monitoring started with session ID: abc123-def456-789

Now I'll begin the polling loop to check for directives...

*calls get_next_directive()*

No pending directives currently. I'll wait 15 seconds and check again...

*waits 15 seconds, calls get_next_directive() again*

Found new directive: "Analyze the latest customer satisfaction survey results and create a summary report with actionable insights"

I'll execute this directive now...

[Performs comprehensive analysis of survey data]

Analysis completed! Here's what I accomplished:
- Analyzed 1,247 customer satisfaction responses from Q4 2024
- Overall satisfaction score: 4.2/5.0 (improvement from 3.9 in Q3)
- Key positive themes: Product quality (87% positive), Customer service (82% positive)
- Key improvement areas: Shipping speed (34% negative), Website usability (28% negative)
- Generated 5 specific actionable recommendations with priority rankings

Let me report these results and check for the next directive...

*calls get_next_directive(DirectiveResult(
    directive_id="abc-123",
    success=True,
    result="Completed comprehensive analysis of 1,247 customer satisfaction survey responses. Overall satisfaction improved to 4.2/5.0 from 3.9 in Q3. Key findings: Product quality leads positives (87%), shipping speed is primary concern (34% negative feedback). Created prioritized action plan with 5 specific recommendations including expedited shipping options, website UX improvements, and enhanced communication protocols.",
    execution_time=67.5,
    metadata={"survey_count": 1247, "satisfaction_score": 4.2, "improvement_areas": 2}
))*

Results recorded successfully! Checking for next directive...
```

### 2. External System Integration

```python
import aiohttp
import asyncio

async def send_directive_with_followup():
    """Example: Send directive with smart follow-up rules"""
    directive_data = {
        "directive": "Analyze Q4 sales performance by region and product category",
        "priority": "high",
        "webhook": "https://mycompany.com/webhooks/claude-results",
        "follow_up_rules": [
            {
                "condition": "success AND result.contains('declining')",
                "next_directive": "Create detailed action plan to address declining sales trends identified in the analysis",
                "priority": "high",
                "delay_seconds": 30
            },
            {
                "condition": "success AND result.contains('growth')",
                "next_directive": "Prepare executive presentation highlighting successful growth strategies for leadership review",
                "priority": "medium", 
                "delay_seconds": 60
            }
        ],
        "retry_on_failure": True,
        "max_retries": 2,
        "tags": ["sales", "quarterly-review", "executive"]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/api/directives",
            json=directive_data
        ) as response:
            result = await response.json()
            print(f"Directive added: {result['directive_id']}")

# Webhook handler for results
from flask import Flask, request

webhook_app = Flask(__name__)

@webhook_app.route('/webhooks/claude-results', methods=['POST'])
def handle_claude_result():
    data = request.json
    
    print(f"Claude completed: {data['directive']}")
    print(f"Success: {data['success']}")
    print(f"Result: {data['result']}")
    print(f"Execution time: {data['execution_time']} seconds")
    
    # Update your systems based on results
    if data['success']:
        if 'sales' in data.get('tags', []):
            update_sales_dashboard(data['result'])
        elif 'customer' in data['directive'].lower():
            update_customer_metrics(data['result'])
    else:
        escalate_to_human(data)
    
    return {"received": True}

def update_sales_dashboard(result):
    """Update sales dashboard with Claude's analysis"""
    # Extract insights and update your business intelligence systems
    pass

def escalate_to_human(failed_directive):
    """Handle failed directives"""
    # Send notification to team, create ticket, etc.
    pass
```

### 3. Monitoring and Analytics

```python
async def get_system_analytics():
    """Get comprehensive analytics"""
    async with aiohttp.ClientSession() as session:
        # Get analytics
        async with session.get("http://localhost:8000/mcp/analytics") as response:
            analytics = await response.json()
            
        # Get recent results
        async with session.get("http://localhost:8000/api/results?limit=20") as response:
            recent_results = await response.json()
        
        print(f"Total completed directives: {analytics['total_completed']}")
        print(f"Success rate: {analytics['success_rate']:.2%}")
        print(f"Average execution time: {analytics['average_execution_time']:.1f} seconds")
        print(f"Currently pending: {analytics['pending_count']}")
        
        print("\nRecent Results:")
        for result in recent_results[:5]:
            status = "✅" if result['success'] else "❌" 
            print(f"{status} {result['result'][:100]}...")

# Schedule regular monitoring
async def monitor_system():
    while True:
        await get_system_analytics()
        await asyncio.sleep(300)  # Check every 5 minutes
```

## Advanced Features

### 1. Conditional Workflows

```python
# Complex workflow example
await send_directive({
    "directive": "Perform security audit of our web applications",
    "priority": "high",
    "follow_up_rules": [
        {
            "condition": "success AND result.contains('vulnerabilities')",
            "next_directive": "Create detailed vulnerability remediation plan with timeline and resource requirements",
            "priority": "urgent"
        },
        {
            "condition": "success AND result.contains('compliant')",
            "next_directive": "Generate security compliance report for stakeholders",
            "priority": "medium"
        }
    ]
})
```

### 2. Error Recovery and Retries

```python
# Directive with intelligent retry
await send_directive({
    "directive": "Generate monthly financial report from ERP system",
    "priority": "medium",
    "retry_on_failure": True,
    "max_retries": 3,
    "tags": ["finance", "monthly-report"]
})
```

### 3. Real-time Monitoring Dashboard

```python
# Simple monitoring dashboard
import streamlit as st
import asyncio

st.title("Claude Directive Monitoring Dashboard")

# Real-time metrics
col1, col2, col3, col4 = st.columns(4)

async def update_dashboard():
    analytics = await get_analytics()
    
    with col1:
        st.metric("Completed Directives", analytics['total_completed'])
    
    with col2:
        st.metric("Success Rate", f"{analytics['success_rate']:.1%}")
    
    with col3:
        st.metric("Avg Execution Time", f"{analytics['average_execution_time']:.1f}s")
    
    with col4:
        st.metric("Pending", analytics['pending_count'])

# Auto-refresh every 30 seconds
if st.button("Start Monitoring"):
    while True:
        update_dashboard()
        time.sleep(30)
```

## Benefits and Limitations

### ✅ Benefits

- **Complete Audit Trail**: Every directive and result is tracked with timestamps
- **Smart Automation**: Follow-up directives based on results enable complex workflows  
- **Error Recovery**: Automatic retries with context about previous failures
- **Real-time Integration**: Webhooks provide immediate updates to external systems
- **Performance Analytics**: Detailed metrics on execution times and success rates
- **Scalable Architecture**: Handles multiple concurrent directives with priority queuing
- **No Browser Dependencies**: Works entirely within Claude's MCP environment

### ⚠️ Limitations

- **Manual Initiation**: User must start the monitoring conversation
- **Single Conversation**: Only works within one Claude conversation thread
- **User Interruption**: Any user message can break the polling loop
- **Memory Constraints**: Very long conversations may hit token limits
- **No Background Processing**: Claude can't run monitoring in background
- **Session Dependency**: Monitoring stops if conversation ends

### 🔧 Best Practices

1. **Start monitoring in dedicated conversation**: Don't mix with other tasks
2. **Use clear directive language**: Be specific about expected outcomes
3. **Implement proper error handling**: Always include try/catch in external integrations
4. **Monitor system health**: Set up alerts for failed directives or system downtime
5. **Use webhooks for important results**: Don't rely only on polling for critical updates
6. **Implement result validation**: Verify Claude's results before taking automated actions

This implementation provides a robust, production-ready system for orchestrating Claude AI through MCP with complete result feedback and advanced workflow capabilities.
