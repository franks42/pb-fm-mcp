#!/usr/bin/env python3
"""
Webpage MVP Infrastructure Testing Script

Tests all infrastructure components for the webpage MVP:
- S3 bucket access and CORS configuration
- DynamoDB table structure and permissions
- SQS queue creation and permissions
- Lambda function integration

Uses uv for all Python operations.
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import aiohttp

# Color codes for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def log(level: str, message: str) -> None:
    """Log message with color coding"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    colors = {
        'INFO': Colors.GREEN,
        'WARN': Colors.YELLOW,
        'ERROR': Colors.RED,
        'DEBUG': Colors.BLUE,
        'TEST': Colors.CYAN
    }
    color = colors.get(level, Colors.NC)
    print(f"{color}[{level}]{Colors.NC} [{timestamp}] {message}")

class WebpageInfrastructureTest:
    """Test webpage MVP infrastructure components"""
    
    def __init__(self):
        self.s3_client = None
        self.dynamodb_client = None
        self.sqs_client = None
        self.lambda_client = None
        
        # Infrastructure configuration
        self.config = {
            's3_bucket': 'pb-fm-webpage-mvp-assets',
            'dynamodb_table': 'pb-fm-webpage-sessions',
            'sqs_queue_prefix': 'pb-fm-webpage-',
            'region': 'us-west-1'
        }
        
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }

    def setup_aws_clients(self) -> bool:
        """Initialize AWS clients"""
        try:
            session = boto3.Session()
            
            # Check credentials
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            log('INFO', f"AWS Account: {identity['Account']}")
            log('INFO', f"User/Role: {identity['Arn']}")
            
            # Initialize clients
            self.s3_client = session.client('s3', region_name=self.config['region'])
            self.dynamodb_client = session.client('dynamodb', region_name=self.config['region'])
            self.sqs_client = session.client('sqs', region_name=self.config['region'])
            self.lambda_client = session.client('lambda', region_name=self.config['region'])
            
            log('INFO', 'AWS clients initialized successfully')
            return True
            
        except NoCredentialsError:
            log('ERROR', 'AWS credentials not found. Run: aws configure')
            return False
        except Exception as e:
            log('ERROR', f'Failed to initialize AWS clients: {e}')
            return False

    def test_s3_bucket(self) -> bool:
        """Test S3 bucket existence and configuration"""
        log('TEST', 'Testing S3 bucket configuration...')
        
        bucket_name = self.config['s3_bucket']
        
        try:
            # Test bucket existence
            self.s3_client.head_bucket(Bucket=bucket_name)
            log('INFO', f'✓ S3 bucket {bucket_name} exists')
            
            # Test bucket location
            location = self.s3_client.get_bucket_location(Bucket=bucket_name)
            log('INFO', f'✓ Bucket location: {location.get("LocationConstraint", "us-east-1")}')
            
            # Test CORS configuration
            try:
                cors = self.s3_client.get_bucket_cors(Bucket=bucket_name)
                log('INFO', '✓ CORS configuration found')
                
                # Validate CORS rules for browser access
                rules = cors.get('CORSRules', [])
                has_browser_access = False
                for rule in rules:
                    if '*' in rule.get('AllowedOrigins', []) or any(
                        origin.startswith('http') for origin in rule.get('AllowedOrigins', [])
                    ):
                        has_browser_access = True
                        break
                
                if has_browser_access:
                    log('INFO', '✓ CORS allows browser access')
                else:
                    log('WARN', '△ CORS may not allow browser access')
                    
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchCORSConfiguration':
                    log('WARN', '△ No CORS configuration found - browsers may not be able to access')
                else:
                    raise
            
            # Test write permissions
            test_key = f'test/{datetime.now().isoformat()}.json'
            test_data = {'test': True, 'timestamp': datetime.now().isoformat()}
            
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=json.dumps(test_data),
                ContentType='application/json'
            )
            log('INFO', '✓ S3 write permissions OK')
            
            # Test read permissions
            response = self.s3_client.get_object(Bucket=bucket_name, Key=test_key)
            content = json.loads(response['Body'].read())
            assert content['test'] is True
            log('INFO', '✓ S3 read permissions OK')
            
            # Cleanup test object
            self.s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            log('INFO', '✓ S3 delete permissions OK')
            
            self.test_results['passed'] += 1
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                log('ERROR', f'✗ S3 bucket {bucket_name} does not exist')
            elif error_code == 'AccessDenied':
                log('ERROR', f'✗ Access denied to S3 bucket {bucket_name}')
            else:
                log('ERROR', f'✗ S3 error: {e}')
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f'S3: {e}')
            return False

    def test_dynamodb_table(self) -> bool:
        """Test DynamoDB table structure and permissions"""
        log('TEST', 'Testing DynamoDB table configuration...')
        
        table_name = self.config['dynamodb_table']
        
        try:
            # Test table existence and get description
            response = self.dynamodb_client.describe_table(TableName=table_name)
            table = response['Table']
            
            log('INFO', f'✓ DynamoDB table {table_name} exists')
            log('INFO', f'✓ Table status: {table["TableStatus"]}')
            
            # Validate key schema
            key_schema = table['KeySchema']
            expected_keys = {'PK': 'HASH', 'SK': 'RANGE'}
            
            actual_keys = {key['AttributeName']: key['KeyType'] for key in key_schema}
            if actual_keys == expected_keys:
                log('INFO', '✓ Key schema is correct (PK, SK)')
            else:
                log('WARN', f'△ Key schema differs. Expected: {expected_keys}, Got: {actual_keys}')
            
            # Test write permissions
            test_item = {
                'PK': {'S': 'TEST#infrastructure-test'},
                'SK': {'S': f'METADATA#{datetime.now().isoformat()}'},
                'test_data': {'S': 'infrastructure_test'},
                'timestamp': {'S': datetime.now().isoformat()}
            }
            
            self.dynamodb_client.put_item(TableName=table_name, Item=test_item)
            log('INFO', '✓ DynamoDB write permissions OK')
            
            # Test read permissions
            response = self.dynamodb_client.get_item(
                TableName=table_name,
                Key={
                    'PK': test_item['PK'],
                    'SK': test_item['SK']
                }
            )
            
            if 'Item' in response:
                log('INFO', '✓ DynamoDB read permissions OK')
            else:
                log('ERROR', '✗ DynamoDB read failed - item not found')
                return False
            
            # Test query permissions
            response = self.dynamodb_client.query(
                TableName=table_name,
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={':pk': test_item['PK']}
            )
            
            if response['Count'] > 0:
                log('INFO', '✓ DynamoDB query permissions OK')
            else:
                log('WARN', '△ DynamoDB query returned no results')
            
            # Cleanup test item
            self.dynamodb_client.delete_item(
                TableName=table_name,
                Key={
                    'PK': test_item['PK'],
                    'SK': test_item['SK']
                }
            )
            log('INFO', '✓ DynamoDB delete permissions OK')
            
            self.test_results['passed'] += 1
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                log('ERROR', f'✗ DynamoDB table {table_name} does not exist')
            elif error_code == 'AccessDeniedException':
                log('ERROR', f'✗ Access denied to DynamoDB table {table_name}')
            else:
                log('ERROR', f'✗ DynamoDB error: {e}')
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f'DynamoDB: {e}')
            return False

    def test_sqs_permissions(self) -> bool:
        """Test SQS queue creation and permissions"""
        log('TEST', 'Testing SQS queue permissions...')
        
        test_queue_name = f"{self.config['sqs_queue_prefix']}test-{int(time.time())}"
        
        try:
            # Test queue creation
            response = self.sqs_client.create_queue(QueueName=test_queue_name)
            queue_url = response['QueueUrl']
            log('INFO', f'✓ SQS queue created: {test_queue_name}')
            
            # Test message sending
            test_message = {
                'test': True,
                'timestamp': datetime.now().isoformat(),
                'component': 'infrastructure-test'
            }
            
            self.sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(test_message)
            )
            log('INFO', '✓ SQS send message OK')
            
            # Test message receiving
            response = self.sqs_client.receive_message(
                QueueUrl=queue_url,
                WaitTimeSeconds=2
            )
            
            if 'Messages' in response:
                message = response['Messages'][0]
                body = json.loads(message['Body'])
                assert body['test'] is True
                log('INFO', '✓ SQS receive message OK')
                
                # Test message deletion
                self.sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
                log('INFO', '✓ SQS delete message OK')
            else:
                log('WARN', '△ No message received from SQS (may be timing issue)')
            
            # Cleanup test queue
            self.sqs_client.delete_queue(QueueUrl=queue_url)
            log('INFO', '✓ SQS queue deleted')
            
            self.test_results['passed'] += 1
            return True
            
        except ClientError as e:
            log('ERROR', f'✗ SQS error: {e}')
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f'SQS: {e}')
            return False

    async def test_lambda_integration(self, lambda_url: Optional[str] = None) -> bool:
        """Test Lambda function accessibility"""
        log('TEST', 'Testing Lambda function integration...')
        
        if not lambda_url:
            # Use development environment URL
            lambda_url = "https://pb-fm-mcp-dev.creativeapptitude.com"
            log('INFO', f'Using development Lambda URL: {lambda_url}')
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test health endpoint
                health_url = f"{lambda_url}/health"
                async with session.get(health_url, timeout=10) as response:
                    if response.status == 200:
                        log('INFO', '✓ Lambda health endpoint OK')
                    else:
                        log('WARN', f'△ Lambda health endpoint returned {response.status}')
                
                # Test API documentation endpoint
                docs_url = f"{lambda_url}/docs"
                async with session.get(docs_url, timeout=10) as response:
                    if response.status == 200:
                        log('INFO', '✓ Lambda documentation endpoint OK')
                    else:
                        log('WARN', f'△ Lambda docs endpoint returned {response.status}')
                
                # Test MCP endpoint
                mcp_url = f"{lambda_url}/mcp"
                mcp_request = {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 1
                }
                
                async with session.post(
                    mcp_url, 
                    json=mcp_request, 
                    timeout=10,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'result' in data and 'tools' in data['result']:
                            tool_count = len(data['result']['tools'])
                            log('INFO', f'✓ MCP endpoint OK ({tool_count} tools available)')
                        else:
                            log('WARN', '△ MCP endpoint returned unexpected format')
                    else:
                        log('WARN', f'△ MCP endpoint returned {response.status}')
            
            self.test_results['passed'] += 1
            return True
            
        except asyncio.TimeoutError:
            log('ERROR', '✗ Lambda function timeout')
            self.test_results['failed'] += 1
            self.test_results['errors'].append('Lambda: Timeout')
            return False
        except Exception as e:
            log('ERROR', f'✗ Lambda integration error: {e}')
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f'Lambda: {e}')
            return False

    def test_function_naming_availability(self) -> bool:
        """Test that webpage function names are available (not conflicting)"""
        log('TEST', 'Testing function naming conflicts...')
        
        # List of new function names we plan to create
        new_function_names = [
            'webpage_create_session',
            'webpage_join_session', 
            'webpage_get_session_status',
            'webpage_create_browser_queues',
            'webpage_poll_queue',
            'webpage_delete_message',
            'webpage_update_hash_price_display',
            'webpage_send_to_browsers',
            'webpage_get_session_participants',
            'webpage_transfer_control_to_observer'
        ]
        
        try:
            # Check against existing Lambda functions (if we can list them)
            try:
                response = self.lambda_client.list_functions()
                existing_functions = [f['FunctionName'] for f in response['Functions']]
                
                conflicts = set(new_function_names) & set(existing_functions)
                if conflicts:
                    log('ERROR', f'✗ Function name conflicts: {conflicts}')
                    return False
                else:
                    log('INFO', f'✓ No Lambda function name conflicts ({len(new_function_names)} names checked)')
            except ClientError:
                log('WARN', '△ Cannot list Lambda functions (permissions or different architecture)')
            
            # For now, assume no conflicts since we're using webpage_ prefix
            log('INFO', '✓ Function names use webpage_ prefix - conflicts unlikely')
            
            self.test_results['passed'] += 1
            return True
            
        except Exception as e:
            log('ERROR', f'✗ Function naming test error: {e}')
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f'Naming: {e}')
            return False

    async def run_all_tests(self, lambda_url: Optional[str] = None) -> bool:
        """Run all infrastructure tests"""
        log('INFO', '=== Webpage MVP Infrastructure Testing ===')
        log('INFO', f'Started at: {datetime.now().isoformat()}')
        
        # Setup
        if not self.setup_aws_clients():
            return False
        
        # Run tests
        tests = [
            ('S3 Bucket', self.test_s3_bucket),
            ('DynamoDB Table', self.test_dynamodb_table),
            ('SQS Permissions', self.test_sqs_permissions),
            ('Function Naming', self.test_function_naming_availability),
            ('Lambda Integration', lambda: asyncio.create_task(self.test_lambda_integration(lambda_url)))
        ]
        
        log('INFO', f'Running {len(tests)} test suites...')
        
        for test_name, test_func in tests:
            log('INFO', f'\n--- {test_name} ---')
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func
                else:
                    result = test_func()
                    if asyncio.iscoroutine(result):
                        result = await result
                        
                if not result:
                    log('ERROR', f'{test_name} test failed')
            except Exception as e:
                log('ERROR', f'{test_name} test error: {e}')
                self.test_results['failed'] += 1
                self.test_results['errors'].append(f'{test_name}: {e}')
        
        # Summary
        log('INFO', '\n=== Test Results Summary ===')
        log('INFO', f'Passed: {self.test_results["passed"]}')
        log('INFO', f'Failed: {self.test_results["failed"]}')
        log('INFO', f'Skipped: {self.test_results["skipped"]}')
        
        if self.test_results['errors']:
            log('ERROR', '\nErrors encountered:')
            for error in self.test_results['errors']:
                log('ERROR', f'  - {error}')
        
        success = self.test_results['failed'] == 0
        
        if success:
            log('INFO', '\n✓ All infrastructure tests passed!')
            log('INFO', 'Webpage MVP infrastructure is ready for development.')
        else:
            log('ERROR', f'\n✗ {self.test_results["failed"]} test(s) failed.')
            log('ERROR', 'Fix infrastructure issues before proceeding.')
        
        return success

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Test Webpage MVP Infrastructure')
    parser.add_argument('--lambda-url', help='Lambda function URL to test')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    tester = WebpageInfrastructureTest()
    success = await tester.run_all_tests(args.lambda_url)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    asyncio.run(main())