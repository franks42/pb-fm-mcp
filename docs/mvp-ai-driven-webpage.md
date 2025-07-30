# MVP: AI-Driven Webpage Architecture

## Overview

This document defines the MVP (Minimum Viable Product) for an AI-driven webpage system where an AI agent orchestrates dynamic web displays through declarative directives. The system uses SQS as a generic message bus for async communication between components.

## Core Architecture Concept

**Vision**: AI (like Claude) receives high-level user instructions/questions and has complete freedom to decide what and how things are displayed on a webpage. The AI orchestrates layout, content, visualizations, and data presentation through a message-based architecture.

## Component Architecture

### 1. SQS as Generic Message Bus
- **Purpose**: Async communication between all system components
- **Message Format**: JSON
- **Behavior**: Each component can poll/wait for messages and send messages to any other component
- **Pattern**: Low-latency polling without resource waste

### 2. AI-Agent (Orchestrator)
- **Role**: Master orchestrator for webpage experience
- **Input**: High-level user instructions/questions
- **Output**: Coordinated webpage layout, content, and visualizations
- **Freedom**: Complete autonomy in determining presentation approach
- **Responsibilities**:
  - Understand coarse layout requirements
  - Design different panels and components
  - Coordinate text/labels/form fields
  - Prepare Plotly panels and components
  - Direct datasets to appropriate Plotly components

### 3. AI-Queue-Handler (MCP Functions)
- **Implementation**: MCP functions for AI to interact with SQS
- **Capabilities**:
  - Put messages on queue
  - Receive messages from queue
  - **Wait functionality**: Can wait inside function call with configurable timeout
- **AI Polling Responsibility**: AI must regularly check for messages (only way AI receives input)
- **Existing Code**: Already implemented in `src/functions/sqs_traffic_light.py`
  - Functions: `wait_for_user_input()`, `send_response_to_browser()`

### 4. Browser-JS (Renderer)
- **Role**: Webpage rendering and user interaction
- **Behavior**: Polls for messages directed at webpage components
- **Component Types**:
  - `layout-manager` → HTML/CSS layout updates
  - `plotly-panel-{id}` → Individual Plotly chart components
  - `dataset-router` → Routes datasets to appropriate Plotly components
  - `text-component-{id}` → Labels, forms, text content

### 5. WebBrowser-Queue-Handler (WebServer Functions)
- **Purpose**: Browser JS interface to SQS
- **Capabilities**:
  - Send messages (put on queue)
  - Receive messages for page components
- **Message Dispatching Options** (TBD):
  - **Option A**: Local JS-orchestrator dispatches to components
  - **Option B**: Each component polls individually
  - **Trade-off**: Individual polling enables auto-cleanup when components removed, but requires more polling calls

### 6. Component Addressing System
- **Concept**: Every webpage component has a unique address for message routing
- **Message Routing**: Messages contain addressing information to direct data to correct handler
- **Examples**:
  - Messages to `layout-manager` → HTML/CSS layout updates
  - Messages to `plotly-panel-1` → Specific chart configuration
  - Messages to `plotly-panel-2` → Different chart configuration
  - Messages to `dataset-router` → Dataset routing to appropriate components

### 7. S3 (Persistent Storage)
- **Rule**: Anything larger than a few characters stored in S3
- **Storage Types**:
  - HTML/CSS layouts
  - Plotly component configurations
  - Plotly layout specifications
  - Datasets (price data, trading volumes, blockchain data)
- **Reference Pattern**: S3 content referenced by identifiers in queue messages

### 8. S3-Queue-Handler (Bulk Data Management)
- **Principle**: **No bulk data through SQS** - only S3 identifiers/references
- **Workflow**:
  1. AI prepares webpage layout/component
  2. Stores content in S3 bucket
  3. Sends S3 reference via SQS message
  4. Browser retrieves content from S3 using reference
- **S3 Registry Required**: Catalog system for stored layouts, Plotly components, datasets
- **Reusability**: System can reuse and prepare standard layouts and components

### 9. DynamoDB (Role TBD)
- **Purpose**: Staging/caching (specific role to be determined)
- **Potential Uses**: Message routing tables, component registry, session state

## Message Flow Architecture

```
User Input → AI-Agent → SQS Message Bus → Browser Components
                ↓                              ↓
            S3 Storage ← S3 Registry → S3 Content Retrieval
```

**Detailed Message Flow**:
1. **User Input**: High-level instruction/question to AI
2. **AI Processing**: AI decides layout, components, visualizations
3. **Content Creation**: AI creates/selects layouts, Plotly configs, datasets
4. **S3 Storage**: Large content stored in S3 with unique identifiers
5. **SQS Messaging**: S3 references sent via SQS to appropriate browser components
6. **Browser Polling**: Components poll SQS for messages
7. **Content Retrieval**: Components fetch content from S3 using references
8. **Rendering**: Browser renders content and awaits next instructions

## Polling Pattern (Low Latency Communication)

**Pattern**: 
- Call webserver → wait for message (few seconds timeout) → return → call again
- **Benefit**: Guarantees low latency without resource waste
- **Implementation**: Consistent across all polling components

## Technical Implementation Notes

### Existing Infrastructure
- **Working Foundation**: SQS traffic light pattern already implemented
- **Performance**: ~663ms browser→AI, ~475ms AI→browser response times
- **Event Replay**: Multi-browser synchronization through event sourcing
- **Current Functions**: `wait_for_user_input()`, `send_response_to_browser()` in `sqs_traffic_light.py`

### Architecture Decisions Pending
1. **Browser Message Dispatching**: Central orchestrator vs individual component polling
2. **DynamoDB Usage**: Specific role in staging/caching pipeline
3. **S3 Registry Structure**: Organization and indexing of reusable components
4. **Component Lifecycle**: Creation, updating, and cleanup of webpage components

## MVP Scope (To Be Completed)

**Current Status**: Architecture definition in progress
**Next Steps**: 
1. Complete component specification
2. Define MVP feature set
3. Create implementation roadmap
4. Begin development phase

---

**Document Status**: Architecture definition in progress (Session ended for dinner/reboot)
**Last Updated**: July 30, 2025
**Next Session**: Continue with MVP feature definition and implementation planning