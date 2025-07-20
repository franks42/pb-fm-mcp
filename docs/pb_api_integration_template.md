# PB-API Integration Template

Use this template when integrating a new Provenance Blockchain API endpoint.

## API Information

**API Endpoint:** `https://service-explorer.provenance.io/api/v3/example`
**HTTP Method:** GET/POST
**Purpose:** [Describe what this API provides]
**Integration Date:** [YYYY-MM-DD]
**Integrator:** [Your name]

## Phase 1: Discovery ✅

### 1.1 API Details
```yaml
api_endpoint:
  url: "https://service-explorer.provenance.io/api/v3/example"
  method: "GET"
  parameters:
    - name: "param1"
      type: "string"
      required: true
      description: "Description of param1"
    - name: "param2" 
      type: "integer"
      required: false
      default: 10
      description: "Description of param2"
  authentication: "none"
  rate_limits: "unknown"
```

### 1.2 Raw Response Capture
- [ ] Raw response saved to `docs/raw_api_responses/[endpoint_name]_raw.json`
- [ ] Multiple parameter combinations tested
- [ ] Error responses documented
- [ ] Edge cases identified

### 1.3 Base64 Expansion
- [ ] base64expand() applied to raw responses
- [ ] Expanded response saved to `docs/raw_api_responses/[endpoint_name]_expanded.json`
- [ ] Hidden data documented (if any)

## Phase 2: Attribute Analysis ✅

### 2.1 Attribute Catalog
For each response attribute, complete this analysis:

```yaml
attribute_analysis:
  attribute_name_1:
    source_path: "path.in.response"
    data_type: "string|integer|float|boolean|object|array"
    sample_values: ["sample1", "sample2", "sample3"]
    value_range: "description of typical range"
    null_handling: "never_null|can_be_null|sometimes_empty"
    purpose: "Business purpose of this attribute"
    units: "nhash|usd|percentage|count|timestamp|etc"
    calculation: "raw_blockchain_data|calculated_by_api|derived_field"
    relationship: "Parent/child/sibling relationships to other attributes"
    temporal: "How often does this change?"
    business_importance: "critical|high|medium|low|none"
    communication_value: "high|medium|low|none"
    bandwidth_impact: "large|medium|small"
    ai_usefulness: "essential|useful|optional|noise"
    
  attribute_name_2:
    # ... repeat for each attribute
```

### 2.2 Data Dictionary Integration
- [ ] Checked existing field registry for similar concepts
- [ ] Checked denomination registry for unit types
- [ ] Reviewed logical groups for related attributes
- [ ] Created new field registry entries (if needed)
- [ ] Updated denomination registry (if needed)

### 2.3 Standardized Field Names
```yaml
field_name_mapping:
  # old_name: new_standardized_name
  "currentSupply": "current_supply_nhash"
  "maxSupply": "max_supply_nhash"
  "lastUpdated": null  # Filtered out
```

## Phase 3: Transformation Design ✅

### 3.1 Field Mappings
```yaml
field_mappings:
  - source_path: "currentSupply.amount"
    target_path: "current_supply_nhash"
    transform: "string_to_int"
    dependencies: []
    validation: "must_be_positive_integer"
    
  - source_path: "maxSupply.amount"
    target_path: "max_supply_nhash"
    transform: "string_to_int"
    dependencies: []
    validation: "must_be_positive_integer"

calculated_fields:
  - target_path: "locked_supply_nhash"
    formula: "current_supply_nhash - circulating_supply_nhash"
    dependencies: ["current_supply_nhash", "circulating_supply_nhash"]
    validation: "must_be_non_negative"

excluded_fields:
  - "lastUpdated"  # API metadata, not business data
  - "pagination"   # API structure, not useful for AI
  - "@type"        # Internal type information
```

### 3.2 Logical Grouping
```yaml
logical_groups:
  [group_name]:
    description: "Complete [business concept] information"
    attributes:
      - standardized_field_1
      - standardized_field_2
      - calculated_field_1
    reasoning: "These fields must be understood together because..."
    required_together: true|false
    use_cases:
      - "Use case 1 description"
      - "Use case 2 description"
```

### 3.3 Error Handling Strategy
```yaml
error_handling:
  missing_required_fields:
    action: "return_error"
    message: "Required field {field_name} missing from API response"
    
  missing_optional_fields:
    action: "use_default"
    defaults:
      optional_field_1: 0
      optional_field_2: null
      
  invalid_data_types:
    action: "attempt_conversion_or_error"
    conversions:
      string_to_int: "try int() conversion, error if fails"
      
  api_failures:
    network_timeout: "return timeout error message"
    http_4xx: "return client error message"
    http_5xx: "return server error message"
```

## Phase 4: Implementation ✅

### 4.1 Primitive Function
- [ ] Created `fetch_[name]()` function in `pb_primitive_apis.py`
- [ ] Follows established async pattern
- [ ] Includes comprehensive docstring
- [ ] Handles all error scenarios
- [ ] Returns standardized field names

### 4.2 Configuration Files
- [ ] Added endpoint mapping to `pb_api_endpoint_mappings.yaml`
- [ ] Updated attribute groups in `pb_api_attribute_groups.yaml`
- [ ] Updated denomination registry (if needed)

### 4.3 Registry Updates
- [ ] Added to `PRIMITIVE_FUNCTIONS` registry
- [ ] Added to function exposure configuration
- [ ] Updated categories in `list_available_functions()`

### 4.4 Tests Created
- [ ] Unit tests for primitive function
- [ ] Integration tests with real API
- [ ] Error scenario tests
- [ ] Performance tests

## Phase 5: Validation ✅

### 5.1 Data Accuracy Verification
```yaml
validation_tests:
  - test_name: "Basic data accuracy"
    description: "Verify transformed data matches raw API data"
    status: "pass|fail|pending"
    notes: "Any issues or observations"
    
  - test_name: "Calculation verification"
    description: "Verify calculated fields are correct"
    status: "pass|fail|pending"
    notes: "Manual calculation verification"
    
  - test_name: "Error handling"
    description: "Test all error scenarios"
    status: "pass|fail|pending"
    notes: "Edge cases tested"
```

### 5.2 Performance Metrics
```yaml
performance_results:
  response_time:
    avg_ms: 0
    p95_ms: 0
    p99_ms: 0
  concurrent_performance:
    requests_per_second: 0
    max_concurrent: 0
  bandwidth_efficiency:
    raw_response_size_kb: 0
    transformed_response_size_kb: 0
    compression_ratio: 0
```

### 5.3 Documentation
- [ ] Function docstring complete with examples
- [ ] API mapping documentation written
- [ ] Business logic explained
- [ ] Usage examples provided
- [ ] Troubleshooting guide created

## Phase 6: Integration ✅

### 6.1 Test Server Integration
- [ ] Function accessible via test web server
- [ ] curl examples tested
- [ ] Error responses tested
- [ ] Performance acceptable

### 6.2 MCP Integration
- [ ] Added to `mcpworker.py` (if needed for MCP exposure)
- [ ] Docstring synchronization working
- [ ] MCP client testing completed

### 6.3 AI Agent Testing
- [ ] Pandas DataFrame creation tested
- [ ] NumPy array compatibility verified
- [ ] Visualization library integration tested
- [ ] AI usage patterns documented

## Quality Checklist ✅

Final verification before integration:

### Technical Quality
- [ ] All error scenarios handled gracefully
- [ ] Performance meets requirements
- [ ] Memory usage acceptable
- [ ] Concurrent access working
- [ ] Base64 expansion integrated

### Data Quality
- [ ] All attributes properly analyzed
- [ ] Field names follow conventions
- [ ] Calculations verified manually
- [ ] Logical groupings make sense
- [ ] No redundant data included

### Documentation Quality
- [ ] Docstrings complete and accurate
- [ ] Examples provided and tested
- [ ] Business logic explained
- [ ] Integration guide written
- [ ] Troubleshooting documented

### Integration Quality
- [ ] Function registry updated
- [ ] Configuration files updated
- [ ] Tests comprehensive
- [ ] Web server integration working
- [ ] MCP integration working (if applicable)

### AI-Friendliness
- [ ] Data formats optimized for AI processing
- [ ] Metadata useful for AI agents
- [ ] Usage patterns documented
- [ ] Bandwidth optimized
- [ ] Field names self-documenting

## Post-Integration Notes

### Performance Observations
- Actual response times: [document real performance]
- Bottlenecks identified: [any performance issues]
- Optimization opportunities: [potential improvements]

### Usage Patterns
- Most common use cases: [how is this function used?]
- Integration with other functions: [commonly used together]
- AI agent feedback: [any feedback from AI usage]

### Maintenance Notes
- API stability: [how often does the source API change?]
- Dependencies: [what other functions depend on this?]
- Future enhancements: [planned improvements]

## Integration Approval

**Technical Reviewer:** [Name] ✅/❌ Date: [YYYY-MM-DD]
**Business Reviewer:** [Name] ✅/❌ Date: [YYYY-MM-DD]
**AI Agent Testing:** [Name] ✅/❌ Date: [YYYY-MM-DD]

**Final Approval:** ✅/❌ Date: [YYYY-MM-DD]

**Integration Status:** Draft | In Progress | Testing | Complete | Deployed

---

## Example Implementation

Here's a complete example for reference:

### API: HASH Token Supply Statistics

```yaml
api_endpoint:
  url: "https://service-explorer.provenance.io/api/v3/utility_token/stats"
  method: "GET"
  parameters: []
  
field_mappings:
  - source_path: "maxSupply.amount"
    target_path: "max_supply_nhash"
    transform: "string_to_int"
    
  - source_path: "currentSupply.amount"
    target_path: "current_supply_nhash"
    transform: "string_to_int"

calculated_fields:
  - target_path: "locked_nhash"
    formula: "current_supply_nhash - circulating_supply_nhash - community_pool_nhash - bonded_nhash"
    dependencies: ["current_supply_nhash", "circulating_supply_nhash", "community_pool_nhash", "bonded_nhash"]

logical_groups:
  hash_supply_complete:
    description: "Complete HASH token supply and distribution information"
    attributes:
      - max_supply_nhash
      - current_supply_nhash
      - circulating_supply_nhash
      - locked_nhash
      - burned_nhash
      - community_pool_nhash
      - bonded_nhash
    reasoning: "All fields needed to understand HASH tokenomics and supply distribution"
    required_together: true
```

This template ensures every integration follows the same rigorous process and maintains consistent quality across all PB-API integrations.