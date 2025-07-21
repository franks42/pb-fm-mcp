# AWS EventBridge Documentation Auto-Update Architecture

## Problem Statement
- GitHub Actions update docs immediately on commit, but deployment takes ~30 seconds
- Creates window where docs show features not yet deployed
- Users may see 404 errors for documented endpoints that aren't live yet

## Solution: EventBridge-Triggered Documentation Updates

### Architecture Flow
```
1. Developer commits → GitHub push
2. AWS SAM deploys → CloudFormation stack update
3. Deployment completes → CloudFormation SUCCESS event
4. EventBridge captures event → Triggers documentation update Lambda
5. Lambda validates API → Updates external documentation services
```

### EventBridge Rule Configuration
```yaml
# In template.yaml
DocumentationUpdateRule:
  Type: AWS::Events::Rule
  Properties:
    Description: "Trigger docs update after successful deployment"
    EventPattern:
      source: ["aws.cloudformation"]
      detail-type: ["CloudFormation Stack Status Change"]
      detail:
        stack-name: ["pb-fm-mcp-v2"]  # Our stack name
        status-code: ["UPDATE_COMPLETE", "CREATE_COMPLETE"]
    State: ENABLED
    Targets:
      - Arn: !GetAtt DocumentationUpdateFunction.Arn
        Id: "DocumentationUpdateTarget"

DocumentationUpdateFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: scripts/docs-updater/
    Handler: update_docs.lambda_handler
    Runtime: python3.12
    Timeout: 30
    Events:
      CloudFormationEvent:
        Type: CloudWatchEvent
        Properties:
          Rule: !Ref DocumentationUpdateRule
```

### Benefits
✅ **Perfect Timing**: Docs only update AFTER successful deployment
✅ **Guaranteed Sync**: No docs-ahead-of-deployment issues  
✅ **Automatic**: Zero manual intervention
✅ **Reliable**: Only triggers on actual deployment success
✅ **Rollback Safe**: Failed deployments don't trigger doc updates

### Lambda Function Responsibilities
1. **Validate API Health**: Test that new endpoints are actually responding
2. **Update External Services**: 
   - Swagger Hub API spec refresh
   - Postman collection updates
   - Custom documentation sites
3. **Notification**: Slack/email alerts about successful doc updates
4. **Error Handling**: Retry logic if external services are temporarily unavailable

### External Service Integration Options
- **Swagger Hub**: API key-based automatic spec updates
- **Postman**: Workspace API to update collections
- **GitHub Pages**: Commit updated OpenAPI spec to docs repo
- **Custom Sites**: Webhook notifications to your documentation sites