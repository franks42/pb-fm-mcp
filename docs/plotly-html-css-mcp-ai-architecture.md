# Plotly + HTML/CSS + MCP + AI: Architecture to Make the Whole Greater Than the Sum of the Parts

## Executive Summary

This document defines a hybrid web application architecture that combines the strengths of multiple technologies to create AI-orchestrated, high-performance dashboards for blockchain and financial data visualization.

**Core Principle**: Separation of concerns with declarative AI control, enabling rapid dashboard creation while maintaining performance and design flexibility.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI Orchestration Layer                     │
│                        (via MCP)                              │
├─────────────────────────────────────────────────────────────────┤
│  Stage 1: Layout Specification    │  Stage 2: Data Flow      │
│  • Dashboard structure            │  • Direct Server→Browser  │
│  • Panel configurations           │  • Real-time updates      │
│  • UI component placement         │  • Bypass AI bottleneck   │
└──────────────┬─────────────────────┴───────────────┬──────────────┘
               │                                     │
               ▼                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Browser Layer                             │
├─────────────────────┬──────────────────┬─────────────────────┤
│    HTML Structure   │   CSS Layout     │   Plotly Panels    │
│  • Semantic markup  │ • CSS Grid       │ • Data visualization│
│  • Form controls    │ • Responsive     │ • Empty containers  │
│  • Navigation       │ • Positioning    │ • Progressive data  │
│  • Figma designs    │ • Theming        │ • Chart interactions│
└─────────────────────┴──────────────────┴─────────────────────┘
               │                                     │
               ▼                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Lambda REST API                             │
│  • Data transformation    • Blockchain integration              │
│  • Format conversion      • Performance optimization            │
│  • Aggregation logic      • Caching strategies                 │
└─────────────────────────────────────────────────────────────────┘
```

## Design Decisions & Rationale

### 1. Technology Separation of Responsibilities

**HTML/CSS Domain:**
- Page structure and layout management
- Form controls and user input
- Navigation and static UI elements
- Figma design integration
- Responsive design and theming

**Plotly Domain:**
- Data visualization within assigned panels
- Chart interactions and animations
- Scientific/financial plotting capabilities
- Progressive data loading

**AI/MCP Domain:**
- Dashboard orchestration and composition
- Layout specification via JSON
- User intent interpretation
- Dynamic panel configuration

**Lambda REST API Domain:**
- Data transformation and cleanup
- Blockchain API integration
- Performance optimization
- Format standardization

### 2. Two-Phase Data Architecture

**Phase 1: AI Sets the Stage (via MCP)**
```json
{
  "action": "create_dashboard",
  "layout": {
    "grid_template": "1fr 1fr / 2fr 1fr",
    "panels": [
      {
        "id": "hash-stats-chart",
        "position": {"row": 1, "column": "1/3"},
        "type": "plotly",
        "config": {
          "title": "Hash Statistics Over Time",
          "xaxis": {"title": "Time", "type": "date"},
          "yaxis": {"title": "Hash Rate"},
          "template": "plotly_dark"
        }
      }
    ]
  },
  "data_sources": [
    {
      "panel_id": "hash-stats-chart",
      "endpoint": "/api/fetch_chart_ready_hash_stats",
      "refresh_interval": 30000
    }
  ]
}
```

**Phase 2: Direct Data Pipeline**
```javascript
// Browser fetches optimized data directly
fetch('/api/fetch_chart_ready_hash_stats')
  .then(response => response.json())
  .then(data => {
    Plotly.addTraces('hash-stats-chart', data.traces);
  });
```

### 3. Declarative Programming Model

All dashboard modifications are controlled through JSON specifications:
- **Layout changes**: CSS Grid configurations
- **Panel creation**: Plotly initialization parameters
- **Data binding**: REST endpoint mappings
- **Styling**: Theme and responsive breakpoints

## Architectural Benefits (Pros)

### Performance Advantages
- **Direct Data Flow**: Large datasets bypass AI conversation limits
- **Progressive Rendering**: Empty plot containers provide immediate visual feedback
- **Optimized Pipelines**: Lambda pre-processes data for browser consumption
- **Real-time Updates**: Direct server-browser connection for live data

### Development Benefits
- **Figma Integration**: HTML/CSS naturally supports design handoffs
- **Declarative Control**: AI can specify entire dashboards via JSON
- **Technology Specialization**: Each tool handles what it does best
- **Maintainable Separation**: Clear boundaries between components

### User Experience Benefits
- **Immediate Responsiveness**: Layout renders before data arrives
- **Rich Interactions**: HTML forms + Plotly charts + CSS animations
- **Professional Design**: Figma workflows for polished interfaces
- **Adaptive Layouts**: CSS Grid for responsive behavior

## Architectural Challenges (Cons)

### Complexity Overhead
- **Coordination Logic**: Managing state between HTML, CSS, and Plotly
- **Multiple Technologies**: Team needs expertise across different domains
- **Integration Points**: More surfaces for potential failures

### Limited Plotly UI
- **No Text Inputs**: Complex forms require HTML fallback
- **Styling Constraints**: Plotly theming vs CSS design systems
- **Mobile Limitations**: Touch interactions may need custom handling

### Development Workflow
- **Build Process**: Coordinating asset compilation and deployment
- **Testing Complexity**: Multiple layers require comprehensive test strategies
- **Debugging**: Issues may span technology boundaries

## Path to MVP: Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
1. **Enhanced Dashboard Engine**
   - Extend existing dashboard serving to support panel specifications
   - Implement CSS Grid layout generation from JSON configs
   - Create Plotly container initialization system

2. **Data Pipeline Optimization**
   - Add chart-ready REST endpoints for existing MCP functions
   - Implement JavaScript-optimized data formats
   - Create progressive loading patterns

### Phase 2: AI Integration (Weeks 3-4)
3. **MCP Dashboard Orchestration**
   - New MCP functions for dashboard creation/modification
   - JSON schema for layout specifications
   - Integration with existing browser automation functions

4. **Performance Optimization**
   - Implement empty plot container pre-rendering
   - Add data streaming capabilities
   - Create caching strategies for repeated requests

### Phase 3: Enhancement (Weeks 5-6)
5. **Advanced Features**
   - Theme system with Figma integration pathway
   - Mobile-responsive breakpoints
   - Interactive dashboard editing

6. **Production Readiness**
   - Comprehensive testing suite
   - Performance monitoring
   - Documentation and deployment guides

## Immediate Next Steps (MVP Todo List)

### Week 1: Core Infrastructure
1. **Create enhanced dashboard template system**
   - Extend `src/web_app_unified.py` dashboard routes
   - Add JSON-to-CSS Grid conversion utilities
   - Implement Plotly container management

2. **Add chart-ready REST endpoints**
   - Create `/api/chart/hash_statistics` endpoint
   - Implement JavaScript timestamp formatting
   - Add Plotly-optimized data structures

3. **Build dashboard specification engine**
   - JSON schema for dashboard layouts
   - CSS Grid generation from specifications
   - Plotly initialization from configuration

### Week 2: MCP Integration
4. **Implement MCP dashboard functions**
   - `create_dashboard(layout_spec)`
   - `modify_dashboard_panel(panel_id, config)`
   - `bind_data_source(panel_id, endpoint)`

5. **Test end-to-end flow**
   - AI creates dashboard via MCP
   - Browser renders empty containers
   - Data flows directly from Lambda to Plotly

6. **Performance validation**
   - Measure data pipeline performance
   - Validate progressive loading behavior
   - Test real-time update capabilities

## Success Metrics

- **Performance**: Dashboard loads in <2 seconds, data updates in <500ms
- **Usability**: AI can create functional dashboards with single MCP call
- **Maintainability**: Clear separation allows independent development of each layer
- **Scalability**: Architecture supports multiple concurrent dashboard sessions

## Future Enhancements

- **Advanced AI Capabilities**: Natural language dashboard modification
- **Real-time Collaboration**: Multiple users sharing dashboard configurations  
- **Mobile Optimization**: Touch-first interactions and responsive design
- **Template Library**: Pre-built dashboard patterns for common use cases

---

*This architecture leverages the existing pb-fm-mcp infrastructure while adding sophisticated dashboard capabilities that combine AI orchestration with high-performance data visualization.*