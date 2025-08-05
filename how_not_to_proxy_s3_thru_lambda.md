# How NOT to Proxy S3 Through Lambda

**Date**: July 31, 2025  
**Issue**: Despite yesterday's work to avoid Lambda proxy for S3 content, the implementation still routes all S3 downloads through Lambda, causing unnecessary costs and latency.

## 🚨 Current (Problematic) Implementation

### What Actually Happens Today
1. **User Request**: `https://pb-fm-mcp-dev.creativeapptitude.com/s3/sessions/xyz/index.html`
2. **API Gateway**: Routes `/s3/{proxy+}` to Lambda function
3. **Lambda Proxy**: `handle_s3_proxy()` function processes request
4. **Lambda Downloads**: Lambda makes HTTP request to CloudFront 
5. **Lambda Memory**: Content loaded into Lambda memory (up to 512MB)
6. **Response**: Lambda returns content back through API Gateway to user

### Performance & Cost Problems
- **Double Network Latency**: User → Lambda → CloudFront → S3 → CloudFront → Lambda → User
- **Lambda Execution Cost**: Every S3 download triggers billable Lambda execution time
- **Memory Usage**: Lambda loads entire file content into memory
- **Timeout Risk**: Large files could hit 30-second Lambda timeout
- **No CDN Benefits**: CloudFront caching bypassed by Lambda proxy

## 📋 Evidence of Lambda Proxy Still Active

### Template Configuration (`template-unified.yaml`)
```yaml
# Lines 152-157: S3 proxy route still defined
S3ProxyRoute:
  Type: Api
  Properties:
    RestApiId: !Ref MyServerlessApi
    Path: /s3/{proxy+}
    Method: ANY
```

### Lambda Handler (`lambda_handler_unified.py`)
```python
# Lines 231-232: S3 proxy routing still active
elif path.startswith("/s3/"):
    return handle_s3_proxy(event, context)

# Lines 1040+: Lambda proxy function still implemented
def handle_s3_proxy(event, context):
    """Proxy /s3/* requests to CloudFront distribution"""
    # ... downloads content through Lambda ...
```

### Session Creation Functions
```python
# webpage_orchestration.py & webpage_session_management.py
# Still return wrong domain: pb-fm-webpage.com (doesn't exist)
# Should return CloudFront URLs directly
```

## 🎯 What Should Have Been Implemented

### Direct CloudFront Access
- **User Request**: Direct to `https://d2q2unco9ewdt0.cloudfront.net/sessions/xyz/index.html`
- **CloudFront**: Serves directly from S3 with global CDN caching
- **No Lambda**: Zero Lambda execution cost for content delivery

### Session URLs Should Return
```python
# CORRECT: Direct CloudFront URL
session_url = f"https://d2q2unco9ewdt0.cloudfront.net/sessions/{session_id}/index.html"

# WRONG: Lambda proxy URL (current implementation)
session_url = f"https://pb-fm-mcp-dev.creativeapptitude.com/s3/sessions/{session_id}/index.html"

# WRONG: Non-existent domain (also current in code)
session_url = f"https://pb-fm-webpage.com/session/{session_id}"
```

## 💸 Cost Impact Analysis

### Current Lambda Proxy Costs
- **Lambda Invocation**: $0.0000002 per request
- **Lambda Duration**: $0.0000166667 per GB-second
- **API Gateway**: $3.50 per million requests
- **Data Transfer**: Through Lambda adds latency and processing overhead

### Direct CloudFront Costs
- **CloudFront**: $0.085 per GB for first 10TB (US/Europe)
- **S3 Requests**: $0.0004 per 1,000 GET requests
- **No Lambda costs**: Zero execution time or memory usage

**Example**: 1,000 webpage views of 100KB content
- **Lambda Proxy**: ~$0.50 (Lambda + API Gateway + processing time)
- **Direct CloudFront**: ~$0.15 (CloudFront + S3 only)
- **Savings**: ~70% cost reduction + much faster delivery

## 🔧 Immediate Fixes Needed

### 1. Remove Lambda S3 Proxy Routes
```yaml
# DELETE from template-unified.yaml:
S3ProxyRoute:
  Type: Api
  # ... remove entire section
```

### 2. Remove Lambda Proxy Function
```python
# DELETE from lambda_handler_unified.py:
def handle_s3_proxy(event, context):
    # ... remove entire function

# DELETE routing logic:
elif path.startswith("/s3/"):
    return handle_s3_proxy(event, context)
```

### 3. Fix Session URL Generation
```python
# webpage_orchestration.py & webpage_session_management.py
# CHANGE FROM:
session_url = f"https://pb-fm-webpage.com/session/{session_id}"

# CHANGE TO:
CLOUDFRONT_URL = os.environ.get("WEBPAGE_MVP_CLOUDFRONT_URL", "https://d2q2unco9ewdt0.cloudfront.net")
session_url = f"{CLOUDFRONT_URL}/sessions/{session_id}/index.html"
```

### 4. Add Environment Variable
```yaml
# template-unified.yaml Environment Variables:
WEBPAGE_MVP_CLOUDFRONT_URL: !Sub "https://${WebpageMvpCloudFrontDistribution.DomainName}"
```

## 🎯 Yesterday's Work Status

**Promised by Previous Claude**: "Lambda proxy removed, direct CloudFront access working"  
**Reality Today**: Lambda proxy still fully active and routing all S3 traffic  
**Conclusion**: The previous implementation did NOT actually remove the Lambda proxy despite assurances

## 📊 Testing Direct Access

### Direct CloudFront URL (Works)
- ✅ `https://d2q2unco9ewdt0.cloudfront.net/sessions/simple-price-mvp/index.html` → 200 OK
- Fast delivery, cached by CloudFront globally

### Lambda Proxy URL (Works but Expensive)  
- ❓ `https://pb-fm-mcp-dev.creativeapptitude.com/s3/sessions/simple-price-mvp/index.html` → Unknown (needs testing)
- Slow delivery, Lambda processing overhead

### Current Session URLs (Broken)
- ❌ `https://pb-fm-webpage.com/session/test-scenario-1` → Domain doesn't exist
- Functions return non-functional URLs

## 🚀 Next Steps

1. **Test Current Lambda Proxy**: Verify if it actually works
2. **Implement Direct CloudFront URLs**: Fix session creation functions  
3. **Remove Lambda Proxy**: Delete proxy routes and functions
4. **Deploy and Test**: Ensure direct CloudFront access works
5. **Cost Monitoring**: Compare before/after Lambda costs

## 📝 Lessons Learned

- **Always verify implementation**: Don't trust assurances without evidence
- **Check actual code**: Template and handler configurations tell the truth
- **Test real URLs**: Verify what actually works vs. what's claimed
- **Document findings**: Prevent repeat work on already "solved" problems

## 🌐 Domain Environment Variables Analysis

### Current Environment Variable Usage

**No domain environment variables are currently passed to Lambda!**

From `template-unified.yaml` lines 70-79, the Lambda Environment Variables section:
```yaml
Environment:
  Variables:
    API_GATEWAY_STAGE_PATH: /v1
    SESSIONS_TABLE: !Ref ConversationSessionsTable
    MESSAGES_TABLE: !Ref ConversationMessagesTable
    DASHBOARDS_TABLE: !Ref PersonalizedDashboardsTable
    SCREENSHOTS_BUCKET: !If [CreateScreenshotsBucket, !Ref ScreenshotBucket, !Ref ExistingScreenshotsBucket]
    WEB_ASSETS_BUCKET: !If [CreateWebAssetsBucket, !Ref WebAssetsBucket, !Ref ExistingWebAssetsBucket]
    WEBPAGE_MVP_ASSETS_BUCKET: !Ref WebpageMvpAssetsBucket
    WEBPAGE_MVP_SESSIONS_TABLE: !Ref WebpageMvpSessionsTable
    # ❌ MISSING: No domain or URL environment variables!
```

### Available CloudFormation Outputs (Not Passed to Lambda)
```yaml
# These exist as outputs but are NOT environment variables
CustomDomainUrl: 
  Value: !If [IsProduction, "https://pb-fm-mcp.${DomainName}/", "https://pb-fm-mcp-dev.${DomainName}/"]
  
WebpageMvpCloudFrontUrl:
  Value: !Sub "https://${WebpageMvpCloudFrontDistribution.DomainName}"
```

### Current Hardcoded Domain Usage

**Functions with Hardcoded Domains:**
```python
# ❌ WRONG: webpage_orchestration.py (line 191-193)
"session_url": f"https://pb-fm-mcp-dev.creativeapptitude.com/session/{actual_session_id}"

# ❌ WRONG: webpage_session_management.py (line 95)  
"session_url": f"https://pb-fm-mcp-dev.creativeapptitude.com/session/{session_id}"

# ❌ WRONG: Both functions also hardcode non-existent domain
"session_url": f"https://pb-fm-webpage.com/session/{session_id}"

# ✅ CORRECT: ai_terminal.py (lines 314, 339, 372)
"dev_url": f"https://pb-fm-mcp-dev.creativeapptitude.com/ai-terminal?session={session_id}"
"production_url": f"https://pb-fm-mcp.creativeapptitude.com/ai-terminal?session={session_id}"

# ✅ CORRECT: debug_functions.py (line 118)
f"https://pb-fm-mcp-dev.creativeapptitude.com/dashboard/{dashboard_id}"

# ❌ HARDCODED: lambda_handler_unified.py (line 1054)
cloudfront_url = os.environ.get("WEBPAGE_MVP_CLOUDFRONT_URL", "https://d2q2unco9ewdt0.cloudfront.net")
```

## 🔧 Suggested Environment Variable Fixes

### 1. Add Missing Environment Variables to Template
```yaml
# template-unified.yaml Environment Variables section:
Environment:
  Variables:
    # ... existing variables ...
    
    # Add domain environment variables
    CUSTOM_DOMAIN_BASE_URL: !If 
      - HasCustomDomain
      - !If [IsProduction, !Sub "https://pb-fm-mcp.${DomainName}", !Sub "https://pb-fm-mcp-dev.${DomainName}"]
      - ""
    
    WEBPAGE_MVP_CLOUDFRONT_URL: !Sub "https://${WebpageMvpCloudFrontDistribution.DomainName}"
    
    DEPLOYMENT_ENVIRONMENT: !Ref Environment
```

### 2. Create Domain Utility Function
```python
# src/functions/domain_utils.py (NEW FILE)
import os
from typing import Optional

def get_custom_domain_url() -> str:
    """Get the custom domain URL from environment or detect from version.json"""
    
    # First try environment variable (preferred)
    env_url = os.environ.get("CUSTOM_DOMAIN_BASE_URL")
    if env_url:
        return env_url.rstrip('/')
    
    # Fallback: detect from version.json
    try:
        from .version_functions import get_version_info
        version_info = get_version_info()
        env = version_info.get("deployment_environment", "dev")
        
        if env == "prod":
            return "https://pb-fm-mcp.creativeapptitude.com"
        else:
            return "https://pb-fm-mcp-dev.creativeapptitude.com"
    except Exception:
        # Final fallback
        return "https://pb-fm-mcp-dev.creativeapptitude.com"

def get_cloudfront_url() -> str:
    """Get CloudFront URL from environment with fallback"""
    return os.environ.get("WEBPAGE_MVP_CLOUDFRONT_URL", "https://d2q2unco9ewdt0.cloudfront.net")

def get_session_url(session_id: str, use_direct_cloudfront: bool = True) -> str:
    """Generate session URL - either direct CloudFront or through custom domain"""
    
    if use_direct_cloudfront:
        # Direct CloudFront access (faster, cheaper)
        cloudfront_url = get_cloudfront_url()
        return f"{cloudfront_url}/sessions/{session_id}/index.html"
    else:
        # Through custom domain (single domain, but slower/costlier if using Lambda proxy)
        custom_domain = get_custom_domain_url()
        return f"{custom_domain}/s3/sessions/{session_id}/index.html"
```

### 3. Update Session Creation Functions
```python
# webpage_orchestration.py & webpage_session_management.py
from .domain_utils import get_session_url

# REPLACE hardcoded URLs with:
"session_url": get_session_url(actual_session_id, use_direct_cloudfront=True)
"master_url": get_session_url(actual_session_id, use_direct_cloudfront=True)  
"observer_url": f"{get_session_url(actual_session_id, use_direct_cloudfront=True)}?role=observer"
```

### 4. Update Other Functions with Hardcoded Domains
```python
# visualization_functions.py (line 59)
from .domain_utils import get_custom_domain_url
base_url = get_custom_domain_url()

# All other functions should use domain_utils instead of hardcoded domains
```

## 🎯 Implementation Options

### Option A: Direct CloudFront (Recommended)
- **URL Pattern**: `https://d2q2unco9ewdt0.cloudfront.net/sessions/{id}/index.html`
- **Pros**: Fast, cheap, global CDN caching
- **Cons**: Different domain from main application
- **Cost**: ~70% cheaper than Lambda proxy

### Option B: Custom Domain S3 Proxy (Current, Expensive)
- **URL Pattern**: `https://pb-fm-mcp-dev.creativeapptitude.com/s3/sessions/{id}/index.html`
- **Pros**: Single domain consistency
- **Cons**: Expensive Lambda proxy, slower delivery
- **Cost**: 3x more expensive than direct CloudFront

### Option C: Custom Domain Direct (Best of Both Worlds)
- **URL Pattern**: `https://sessions-pb-fm-mcp-dev.creativeapptitude.com/sessions/{id}/index.html`
- **Implementation**: Create subdomain CNAME pointing to CloudFront
- **Pros**: Custom domain + direct CloudFront performance
- **Cons**: Requires additional DNS/certificate setup

## 🚀 Recommended Implementation Steps

1. **Add environment variables** to CloudFormation template
2. **Create domain utility functions** for dynamic URL generation
3. **Update all hardcoded domain references** to use utilities
4. **Choose direct CloudFront URLs** for session creation (Option A)
5. **Remove Lambda S3 proxy** entirely (separate task)
6. **Deploy and test** with both dev and prod environments

---

**Bottom Line**: The Lambda S3 proxy is still active and costing unnecessary money. Direct CloudFront access was the goal but was not actually implemented despite previous claims.