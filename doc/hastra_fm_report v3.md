# Hastra FM MCP Server - Next Steps

## Current State Assessment

### Code Maturity
- Current implementation is pre-beta proof-of-concept code
- Successfully demonstrates viability and core functionality
- Code is messy and reflects iterative learning process
- Sufficient functionality to validate the effort's worthiness

### API Foundation Issues
- Built on existing PB&FM internal APIs used by Explorer and FM-exchange web apps
- APIs have evolved over years with multiple developers contributing
- Inconsistent naming conventions across functions, variables, and attributes
- Inconsistent datatypes usage throughout the system
- APIs work well for internal developers who have:
  - Context understanding of UI implementation
  - Access to corporate institutional knowledge
  - Colleague support for clarification

## Current Implementation Problems

### AI Integration Challenges
- First iteration directly exposed internal APIs to AI as MCP APIs
- Partial success due to AI's contextual inference capabilities
- Significant confusion and iteration cycles caused by:
  - Ambiguous attribute names
  - Inconsistent naming patterns
  - Lack of clear data type definitions
- AI frequently draws incorrect conclusions from ambiguous context

### Current Mitigation Strategy
- Providing AI with prompt-context documentation before API calls
- Iteratively updating context documentation when inconsistencies are discovered
- Process is cumbersome and time-consuming
- AI can suggest context improvements when asked to analyze reasoning inconsistencies

## Key Lessons Learned

### API Design for AI Consumption
- Direct exposure of internal APIs to AI creates confusion
- Context ambiguity leads to incorrect AI reasoning
- Iterative context refinement is inefficient for production use

### Documentation Strategy
- Prompt-context approach works but requires constant maintenance
- AI can help identify and suggest fixes for context inconsistencies
- Clear, unambiguous documentation is critical for AI integration

## Data Dictionary Approach - Key Discovery

### Benefits of Data Dictionary Implementation
- **Significant improvement in AI comprehension**: Data dictionary helps AI connect dots and infer correct context
- **Reduced error rates**: Confusion and misunderstandings drop dramatically
- **Better data interpretation**: AI can properly understand data meaning and relationships
- **Consistent data types**: Eliminates type inconsistencies that cause AI confusion

### Implementation Challenges
- **Increased code complexity**: MCP server glue-code becomes more sophisticated
- **Translation layer required**: Must map internal API attributes to data dictionary names
- **Naming scheme design**: Creating consistent, intuitive naming conventions (classic computer science challenge)
- **Data type standardization**: Ensuring consistent data types across all attributes
- **Development overhead**: Additional abstraction layer adds implementation complexity

### Trade-off Analysis
- **Cost**: More complex MCP server implementation and maintenance
- **Benefit**: Substantial reduction in AI confusion and iteration cycles
- **Net result**: Investment in data dictionary pays off through improved AI reliability

## Data Filtering Strategy

### Information Overload Challenge
- **Problem**: Internal APIs often return more data than needed for specific MCP API purposes
- **AI confusion risk**: Extra irrelevant information can confuse AI reasoning
- **Processing overhead**: AI wastes cycles on non-relevant data
- **Recommendation**: Limit data to what's actually needed for the intended use case

### Unexpected Benefits vs. Confusion Trade-offs
- **Positive example**: Feeding full account API results led to unexpected KYC status discovery
  - AI decoded base64 blob and found clear KYC status indicators
  - Provided valuable unexpected insights about account holders
- **Negative impact**: Many more cases where extra information caused confusion
- **Net assessment**: Extra effort dealing with AI confusion outweighs occasional insights
- **Best practice**: Filter data to essential information only

## Development and Testing Strategy

### Iterative Development Approach
- **Small incremental steps**: Work with manageable chunks when implementing new MCP APIs
- **Test question methodology**: Develop reasonable number of test questions for each new API
- **Manual testing burden**: Current approach requires manual verification of AI responses

### Test Automation Opportunity
- **Current gap**: No automated testing for MCP API AI interactions
- **Potential solution**: Automated prompt-based testing system
  - Save prompts that set proper context
  - Include test questions with expected answers
  - Automated verification of AI responses
- **Next action item**: Explore automated testing implementation with Claude

## Performance and Latency Issues

### API Call Latency
- **Observable delays**: MCP API calls and AI inference take noticeable time (sub-second to second range)
- **Complex data scenarios**: Hash account balance requires multiple calls:
  - Wallet account info (1 call)
  - All delegated hash (4 calls)  
  - Vesting information (1 call)
  - Committed hash (1 call)
- **Total impact**: 7 separate API calls for complete account picture

### API Consolidation Strategy
- **Current approach**: Multiple granular internal API calls reflecting piecemeal data architecture
- **Optimization opportunity**: Bundle multiple internal calls into single MCP API call
- **Benefits for AI**:
  - Single API call instead of multiple
  - Easier inference with data from same context
  - Reduced complexity in AI reasoning
- **Implementation trade-offs**:
  - More complex MCP server implementation
  - Longer response times as MCP server waits for multiple internal calls
  - Potential timeout issues (already observed in beta environment)
- **Proof of concept**: Current bundling of 4 delegation calls shows promise

## Infrastructure and Deployment Considerations

### Current Technology Stack and Platform Choices
- **Current implementation**: Written in Python
- **Language choices for MCP servers**: Python and (much more prevalent) JavaScript
- **Hosting preference**: JavaScript clearly preferred, difficult to find fully supported Python hosting that integrates well with MCP-specific deployment
- **Platform selection**: We chose Cloudflare (CF) Workers for MCP server hosting
- **CF Workers experience**: No prior experience, but CF had significant traction and examples for MCP server hosting
- **Python support discovery**: CF Python support is very recent, not as well supported as JS, and very much in beta
- **Implementation outcome**: We made it work after jumping through some hoops

### Production Infrastructure Recommendations
- **Alternative hosting**: For production Hastra-FM-MCP server, there may be better choices - requires further investigation and input from SE
- **Language reconsideration**: Python vs JS choice could be revisited - current MCP server code is not large, porting to JS may be viable (although we personally prefer Python over JS)
- **Account ownership**: If remaining with CF Workers, Hastra should own the associated CF account for billing ($5/month currently, but no load yet)
- **Subdomain strategy**: Host workers in Hastra subdomain like "cf-mcp.hastra.com" for user security assurance
- **Subdomain support**: Many current MCP-hosting services don't support subdomains, but CF does

### Architecture Benefits and Performance Considerations
- **CF architecture advantages**: Each MCP request spawns its own CF worker - very lightweight, stateless, sandboxed JS-VM
- **Concurrent access**: Makes multi-user access very easy when all access is public and unauthenticated
- **Caching limitations**: No caching and truly stateless, possibly causing unnecessary overhead on internal API calls
- **Performance optimization**: If sticking with CF Workers, caching with Durable Object workers could provide benefits
- **Investigation needed**: Requires further investigation and testing

### Code Repository and Deployment Pipeline
- **Current repository**: Code resides in a personal GitHub repo and should be moved to an official Hastra account
- **Current deployment method**: Deployment of MCP server to CF Workers currently working from checked-out code on developer's machine
- **Automated deployment**: CF supports automatic deployment after GitHub commit, which should be the recommended approach
- **Implementation challenge**: We were unable to make automated deployment work for Python-based server - may be developer issue or CF limitation, needs investigation

## Security Model and Limitations

### Public Data Architecture
- **Data accessibility**: All data retrieved from Hastra, Provenance Blockchain (PB), and Figure Markets is publicly available
- **Blockchain nature**: PB is a public blockchain with inherently open data
- **API authentication**: None of the APIs require authentication
- **Security focus**: Primary concerns are integrity and privacy rather than access control
- **CF Workers privacy**: Stateless architecture with new worker for every request guarantees no cross-user data exposure and provides privacy for user interactions with MCP server

### Data Integrity Assurance
- **MCP server control**: We can assure that data retrieved through MCP APIs is correct
- **Direct verification**: Data integrity can be validated against blockchain sources
- **Controlled scope**: Limited to the accuracy of data retrieval and transformation

### AI Agent Variability Challenge
- **Multiple AI platforms**: Users can connect any AI agent to the MCP server (Claude, future MCP-compatible AIs)
- **Uncontrolled inference**: Different AIs have varying capabilities, personalities, and reasoning approaches
- **Interpretation differences**: Same data may lead to different conclusions across AI platforms
- **Version compatibility**: Context optimized for Claude 4.0 may not work equally well with other AI flavors or future Claude versions

### Inherent Architecture Limitations
- **Context dependency**: We can only control initial context to help AIs understand Hastra/PB/FM ecosystem
- **Testing scope**: We can test MCP API integrity and somewhat test with the specific AI we write the context for
- **Transparency requirement**: We should be transparent about these inherent limitations of AI + MCP architecture
- **User awareness**: Users need to understand that AI interpretation quality varies by platform and version

## User Onboarding and Experience

### Onboarding Challenges
- **Conversational interface learning curve**: Not always easy to use when users are new to the system
- **Unclear potential benefits**: Beginning users fail to grasp the potential benefit of AI assistant empowered with Hastra-FM-MCP service
- **Question formulation difficulty**: Users struggle with knowing what questions to ask initially

### Suggested Question Strategy
- **AI-initiated suggestions**: When AI agent recognizes user wants to communicate about Hastra/FM/PB, it can suggest example questions
- **MCP API for examples**: We could add MCP API that returns document with example questions and answers
- **Guided discovery**: Helps users understand the scope and capabilities of the system

### Future UI Enhancement Opportunities
- **Claude Artifacts potential**: Artifacts allow creation of interfaces that could help with onboarding
- **Interactive UI concept**: UI with predefined questions as buttons could help users understand possibilities
- **Current limitation**: Artifacts currently cannot access internet or MCP servers
- **Future capability**: This will change with next versions in the near future, enabling richer onboarding experiences

## Monitoring, Logging, and Feedback

### Current Monitoring Gaps
- **No logging implemented**: Currently no logging or monitoring in place
- **MCP SDK uncertainty**: There may be basic logging integrated in the MCP SDK, but this needs verification
- **Usage analytics missing**: No visibility into service usage, user count, or API call frequency
- **Performance blind spots**: Cannot identify bottlenecks or optimization opportunities

### Required Monitoring Metrics
- **Usage statistics**: How much the service is used and by how many users
- **API analytics**: Which MCP APIs were used how many times
- **Performance metrics**: Identify bottlenecks and determine where to move functionality from AI to MCP server to internal PB/FM server
- **Error tracking**: Monitor failures and response times

### Feedback Collection Strategy
- **Feedback API**: Define additional API where AI agent can provide feedback from user or AI for improvements or errors
- **Central storage**: MCP server could store feedback in central database
- **Developer access**: Enable developers to review valuable suggestions and error reports
- **Continuous improvement**: Create feedback loop for iterative system enhancement

## Data Consistency Challenges

### Blockchain State Consistency Problem
- **Root cause**: Related data retrieved through separate API calls may come from different committed blocks
- **Impact**: Inconsistent data as transfers, trades, staking, rewards, vesting occur unpredictably each block
- **Result**: AI and users receive potentially inconsistent information with visible abnormalities during big events
- **Mitigation**: Warn both AI and users about this inherent limitation

### Practical Impact Assessment
- **Minor inconsistencies**: Usually small percentage-wise (unvested amounts, rewards per block)
- **Detection strategy**: AI can likely notice large inconsistencies and request data refresh, AI can also notify user when inconsistency is apparent and suggest refresh
- **User experience**: Most small discrepancies go unnoticed and can be ignored

## Long-term Architecture Vision

### Ideal Implementation Goals
- **Perfect MCP-to-internal API mapping**: Internal APIs use same data dictionary as MCP APIs
- **Consolidated server-side processing**: Hastra/PB server handles multi-API consolidation
- **Guaranteed consistency**: All data retrieved from same transacted block
- **Simplified glue code**: Minimal translation layer between internal and MCP APIs

### Implementation Pathway
- **Short-term challenge**: Non-trivial implementation effort, difficult to achieve quickly
- **Long-term benefit**: Easier AI integration with improved consistency
- **Advanced possibilities**:
  - Auto-generate MCP server code from internal APIs
  - Direct AI calls to Hastra/PB server with native MCP protocol support
  - Follow industry patterns (e.g., Stripe's approach for customer-facing APIs)

### Industry Precedent
- **Early adopters**: Companies like Stripe already implementing this approach for external APIs
- **Validation**: Proven pattern for AI-first API design

## Current Implementation Analysis

### Context Documentation Strategy
- **Extensive system context**: Current implementation uses 50+ page detailed context document
- **Comprehensive data dictionary**: Includes detailed calculations, common mistakes, worked examples
- **AI guidance**: Step-by-step calculation sequences to prevent errors
- **Critical terminology**: Distinguishes between API data values vs calculated values
- **Real-world examples**: Worked examples showing correct vs incorrect calculations

### Documentation Maintenance Burden
- **Large context document**: Requires significant maintenance as APIs evolve
- **Complexity management**: 50+ page context shows scale of documentation needed
- **Knowledge transfer challenge**: New developers must understand extensive context
- **Version control**: Context updates must stay synchronized with API changes

### Current MCP Server Implementation Insights
Based on the system context, the current implementation reveals several production readiness gaps:

#### Complex Calculation Logic
- **Multi-step calculations**: HASH wallet analysis requires 6-step calculation sequence
- **Vesting coverage logic**: Complex logic for determining available vs restricted amounts
- **Error-prone calculations**: Common mistakes lead to negative spendable amounts
- **Validation requirements**: Multiple validation rules to ensure data consistency

#### Data Consistency Challenges (Confirmed)
- **Live blockchain system**: Data changes every 4 seconds with new blocks
- **API timing issues**: Different calls may return data from different blockchain blocks
- **Acceptable variance**: Minor inconsistencies (<1%) considered normal
- **Fresh data strategy**: Re-fetch when discrepancies >5% observed

#### AI Confusion Points (Detailed in Context)
- **Terminology confusion**: API field names vs calculated wallet amounts
- **Calculation order errors**: Wrong sequence leads to negative values
- **Vesting logic mistakes**: Common 24x overstatement errors in market analysis
- **Reward optimization**: AI doesn't understand which delegation states earn rewards

## Production Readiness Assessment

### Critical Production Barriers

#### Documentation Complexity
- **50+ page context requirement**: Indicates API abstraction layer needed
- **Maintenance overhead**: Context document requires constant updates
- **Developer onboarding**: Steep learning curve for new team members
- **AI confusion management**: Extensive error prevention documentation needed

#### Error Prevention Requirements
- **Complex validation logic**: Multiple validation rules needed to catch calculation errors
- **Common mistake patterns**: Well-documented recurring AI reasoning errors
- **Negative value detection**: System must detect and prevent impossible negative amounts
- **Data consistency monitoring**: Must detect and handle blockchain state differences

#### Performance and Reliability Concerns
- **Timeout issues**: Already observed in beta environment
- **Network latency**: Multiple API calls create cumulative delays
- **Beta environment limitations**: Difficult to isolate root causes of failures
- **Data refresh requirements**: Must handle inconsistent blockchain states

### Immediate Production Readiness Actions

#### Short-term Fixes (0-3 months)
- **API consolidation**: Implement single calls for multi-step data retrieval
- **Calculation validation**: Add automated negative value detection
- **Error handling**: Implement timeout retry logic and graceful degradation
- **Data consistency checks**: Add validation for blockchain state differences
- **Context optimization**: Reduce context document size through better API design

#### Medium-term Improvements (3-6 months)  
- **Data dictionary implementation**: Create consistent naming and data types
- **Automated testing**: Implement AI response validation system
- **Performance monitoring**: Add latency and timeout tracking
- **API versioning**: Establish versioning strategy for context changes
- **Documentation automation**: Generate context from API specifications

#### Long-term Architecture (6+ months)
- **Native MCP APIs**: Design internal APIs specifically for AI consumption
- **Server-side consolidation**: Move multi-API logic to Hastra/PB server
- **Blockchain consistency**: Implement single-block data retrieval
- **Auto-generated servers**: Generate MCP server code from API definitions
- **Industry alignment**: Follow Stripe-style AI-first API design patterns