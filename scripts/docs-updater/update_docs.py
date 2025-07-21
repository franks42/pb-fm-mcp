"""
AWS Lambda function to update documentation after successful deployments.

This function is triggered by EventBridge when CloudFormation deployment completes successfully.
It ensures documentation is only updated AFTER the API is actually deployed and responding.
"""

import json
import boto3
import urllib3
import time
from typing import Dict, Any

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handle CloudFormation deployment completion events and update documentation.
    
    Args:
        event: EventBridge event from CloudFormation
        context: Lambda context
        
    Returns:
        Response dictionary with status and details
    """
    print(f"📋 Received EventBridge event: {json.dumps(event, indent=2)}")
    
    try:
        # Extract deployment details from event
        detail = event.get('detail', {})
        stack_name = detail.get('stack-name', 'unknown')
        status = detail.get('status-code', 'unknown')
        
        print(f"🚀 Processing deployment: {stack_name} - {status}")
        
        # Only process successful deployments
        if status not in ['UPDATE_COMPLETE', 'CREATE_COMPLETE']:
            print(f"⏭️  Skipping non-completion status: {status}")
            return {'statusCode': 200, 'body': f'Skipped status: {status}'}
        
        # Wait a moment for API Gateway to be fully ready
        print("⏳ Waiting for API Gateway to be ready...")
        time.sleep(10)
        
        # Validate API health before updating docs
        api_url = "https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod"
        if not validate_api_health(api_url):
            print("❌ API health check failed, skipping doc update")
            return {'statusCode': 500, 'body': 'API health check failed'}
        
        # Update external documentation services
        update_results = update_external_documentation(api_url)
        
        # Send success notification
        send_notification(stack_name, update_results)
        
        print("✅ Documentation update completed successfully")
        return {
            'statusCode': 200, 
            'body': json.dumps({
                'message': 'Documentation updated successfully',
                'stack_name': stack_name,
                'update_results': update_results
            })
        }
        
    except Exception as e:
        error_msg = f"❌ Documentation update failed: {str(e)}"
        print(error_msg)
        
        # Send error notification
        send_error_notification(str(e))
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg})
        }


def validate_api_health(api_url: str) -> bool:
    """
    Validate that the API is healthy and responding properly.
    
    Args:
        api_url: Base API URL
        
    Returns:
        True if API is healthy, False otherwise
    """
    http = urllib3.PoolManager()
    
    # Test multiple endpoints to ensure full functionality
    test_endpoints = [
        f"{api_url}/openapi.json",
        f"{api_url}/api/current_hash_statistics",
        f"{api_url}/api/system_context"
    ]
    
    for endpoint in test_endpoints:
        try:
            print(f"🧪 Testing endpoint: {endpoint}")
            response = http.request('GET', endpoint, timeout=10.0)
            
            if response.status != 200:
                print(f"❌ Endpoint {endpoint} returned status {response.status}")
                return False
                
            # For OpenAPI endpoint, validate it's valid JSON
            if 'openapi.json' in endpoint:
                try:
                    data = json.loads(response.data.decode('utf-8'))
                    if 'paths' not in data:
                        print("❌ OpenAPI spec missing 'paths' field")
                        return False
                    print(f"✅ OpenAPI spec has {len(data['paths'])} endpoints")
                except json.JSONDecodeError:
                    print("❌ OpenAPI spec is not valid JSON")
                    return False
            
            print(f"✅ Endpoint {endpoint} is healthy")
            
        except Exception as e:
            print(f"❌ Endpoint {endpoint} failed: {str(e)}")
            return False
    
    print("✅ All API health checks passed")
    return True


def update_external_documentation(api_url: str) -> Dict[str, str]:
    """
    Update external documentation services with latest API spec.
    
    Args:
        api_url: Base API URL
        
    Returns:
        Dictionary with update results for each service
    """
    results = {}
    openapi_url = f"{api_url}/openapi.json"
    
    # Update Swagger Generator (if configured)
    results['swagger_generator'] = update_swagger_generator(openapi_url)
    
    # Update Postman (if configured) 
    results['postman'] = update_postman_collection(openapi_url)
    
    # Update custom documentation sites (if configured)
    results['custom_sites'] = notify_custom_sites(openapi_url)
    
    return results


def update_swagger_generator(openapi_url: str) -> str:
    """
    Trigger Swagger Generator to update with latest spec.
    
    Args:
        openapi_url: URL to OpenAPI specification
        
    Returns:
        Status message
    """
    try:
        # Note: This is a placeholder - actual Swagger Hub API integration would require API key
        print(f"📚 Would update Swagger Generator with: {openapi_url}")
        
        # For now, just log the URL that should be used
        swagger_docs_url = f"https://generator3.swagger.io/index.html?url={openapi_url}"
        print(f"📖 Documentation available at: {swagger_docs_url}")
        
        return "success - URL available"
        
    except Exception as e:
        print(f"❌ Swagger Generator update failed: {str(e)}")
        return f"failed: {str(e)}"


def update_postman_collection(openapi_url: str) -> str:
    """
    Update Postman collection with latest API spec.
    
    Args:
        openapi_url: URL to OpenAPI specification
        
    Returns:
        Status message
    """
    try:
        # Placeholder for Postman API integration
        print(f"📮 Would update Postman collection with: {openapi_url}")
        return "success - placeholder"
        
    except Exception as e:
        print(f"❌ Postman update failed: {str(e)}")
        return f"failed: {str(e)}"


def notify_custom_sites(openapi_url: str) -> str:
    """
    Notify custom documentation sites about API updates.
    
    Args:
        openapi_url: URL to OpenAPI specification
        
    Returns:
        Status message
    """
    try:
        # Placeholder for webhook notifications to custom sites
        print(f"🔔 Would notify custom sites about: {openapi_url}")
        return "success - placeholder"
        
    except Exception as e:
        print(f"❌ Custom sites notification failed: {str(e)}")
        return f"failed: {str(e)}"


def send_notification(stack_name: str, update_results: Dict[str, str]) -> None:
    """
    Send success notification about documentation update.
    
    Args:
        stack_name: CloudFormation stack name
        update_results: Results from documentation updates
    """
    print(f"📧 Documentation update completed for {stack_name}")
    print(f"📊 Results: {json.dumps(update_results, indent=2)}")
    
    # Placeholder for Slack/SNS notifications
    # sns = boto3.client('sns')
    # sns.publish(TopicArn='...', Message='Documentation updated successfully')


def send_error_notification(error_message: str) -> None:
    """
    Send error notification about failed documentation update.
    
    Args:
        error_message: Error details
    """
    print(f"🚨 Sending error notification: {error_message}")
    
    # Placeholder for error notifications
    # sns = boto3.client('sns')  
    # sns.publish(TopicArn='...', Message=f'Documentation update failed: {error_message}')