#!/usr/bin/env python3
"""
CloudFormation Template Update Script for Webpage MVP

Safely adds webpage MVP resources to existing template-unified.yaml:
- S3 bucket: pb-fm-webpage-mvp-assets
- DynamoDB table: pb-fm-webpage-sessions  
- SQS permissions for pb-fm-webpage-* queues
- Required IAM permissions

Uses uv for execution and creates backup before modification.
"""

import os
import sys
import yaml
import json
from datetime import datetime
from typing import Dict, Any
import argparse
import shutil
import re

def log(level: str, message: str) -> None:
    """Log message with color coding"""
    colors = {
        'INFO': '\033[0;32m',
        'WARN': '\033[1;33m', 
        'ERROR': '\033[0;31m',
        'DEBUG': '\033[0;34m'
    }
    color = colors.get(level, '\033[0m')
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"{color}[{level}]\033[0m [{timestamp}] {message}")

class CloudFormationUpdater:
    """Updates CloudFormation template with webpage MVP resources"""
    
    def __init__(self, template_path: str):
        self.template_path = template_path
        self.backup_path = f"{template_path}.backup.{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.template = None
        
    def load_template(self) -> bool:
        """Load existing CloudFormation template (handle CF intrinsic functions)"""
        try:
            if not os.path.exists(self.template_path):
                log('ERROR', f'Template file not found: {self.template_path}')
                return False
                
            # Read template as raw text first to handle CloudFormation functions
            with open(self.template_path, 'r') as f:
                self.template_text = f.read()
                
            # Try to parse with custom YAML loader that handles CloudFormation functions
            try:
                # Create custom YAML loader for CloudFormation
                class CFLoader(yaml.SafeLoader):
                    pass
                
                # Add constructors for CloudFormation functions
                def cf_constructor(loader, tag_suffix, node):
                    """Handle CloudFormation intrinsic functions"""
                    if isinstance(node, yaml.ScalarNode):
                        return {tag_suffix: loader.construct_scalar(node)}
                    elif isinstance(node, yaml.SequenceNode):
                        return {tag_suffix: loader.construct_sequence(node)}
                    elif isinstance(node, yaml.MappingNode):
                        return {tag_suffix: loader.construct_mapping(node)}
                    return {tag_suffix: node.value}
                
                # Register constructors for common CF functions
                CFLoader.add_multi_constructor('!', cf_constructor)
                
                self.template = yaml.load(self.template_text, Loader=CFLoader)
                
            except Exception as yaml_error:
                log('WARN', f'CloudFormation YAML parsing failed: {yaml_error}')
                log('INFO', 'Will manually append to template file instead')
                # For now, just parse what we can and manually append later
                self.template = None
                return True
                
            log('INFO', f'Loaded template: {self.template_path}')
            
            # Validate basic structure if we parsed successfully
            if self.template and 'Resources' not in self.template:
                log('ERROR', 'Template missing Resources section')
                return False
                
            return True
            
        except Exception as e:
            log('ERROR', f'Error loading template: {e}')
            return False
    
    def create_backup(self) -> bool:
        """Create backup of original template"""
        try:
            shutil.copy2(self.template_path, self.backup_path)
            log('INFO', f'Created backup: {self.backup_path}')
            return True
        except Exception as e:
            log('ERROR', f'Failed to create backup: {e}')
            return False
    
    def check_existing_resources(self) -> Dict[str, bool]:
        """Check if webpage MVP resources already exist"""
        resources = self.template.get('Resources', {})
        
        existing = {
            's3_bucket': False,
            'dynamodb_table': False,
            'sqs_permissions': False
        }
        
        # Check for S3 bucket
        for resource_name, resource in resources.items():
            if resource.get('Type') == 'AWS::S3::Bucket':
                bucket_name = resource.get('Properties', {}).get('BucketName', '')
                if bucket_name == 'pb-fm-webpage-mvp-assets':
                    existing['s3_bucket'] = True
                    log('INFO', f'Found existing S3 bucket resource: {resource_name}')
        
        # Check for DynamoDB table
        for resource_name, resource in resources.items():
            if resource.get('Type') == 'AWS::DynamoDB::Table':
                table_name = resource.get('Properties', {}).get('TableName', '')
                if table_name == 'pb-fm-webpage-sessions':
                    existing['dynamodb_table'] = True
                    log('INFO', f'Found existing DynamoDB table resource: {resource_name}')
        
        # Check for SQS permissions (approximate check)
        for resource_name, resource in resources.items():
            if resource.get('Type') == 'AWS::IAM::Policy':
                policy_doc = resource.get('Properties', {}).get('PolicyDocument', {})
                statements = policy_doc.get('Statement', [])
                for statement in statements:
                    resources_list = statement.get('Resource', [])
                    if isinstance(resources_list, list):
                        for res in resources_list:
                            if 'pb-fm-webpage-' in str(res):
                                existing['sqs_permissions'] = True
                                log('INFO', f'Found existing SQS permissions in: {resource_name}')
                                break
        
        return existing
    
    def add_s3_bucket(self) -> None:
        """Add S3 bucket resource for webpage assets"""
        bucket_resource = {
            'Type': 'AWS::S3::Bucket',
            'Properties': {
                'BucketName': 'pb-fm-webpage-mvp-assets',
                'PublicReadPolicy': False,
                'CorsConfiguration': {
                    'CorsRules': [
                        {
                            'AllowedOrigins': ['*'],
                            'AllowedMethods': ['GET', 'HEAD'],
                            'AllowedHeaders': ['*'],
                            'MaxAge': 3600
                        }
                    ]
                },
                'LifecycleConfiguration': {
                    'Rules': [
                        {
                            'Id': 'DeleteIncompleteMultipartUploads',
                            'Status': 'Enabled',
                            'AbortIncompleteMultipartUpload': {
                                'DaysAfterInitiation': 7
                            }
                        },
                        {
                            'Id': 'DeleteSessionDataAfter30Days',
                            'Status': 'Enabled',
                            'Filter': {
                                'Prefix': 'sessions/'
                            },
                            'ExpirationInDays': 30
                        }
                    ]
                }
            }
        }
        
        self.template['Resources']['WebpageMvpAssetsBucket'] = bucket_resource
        log('INFO', 'Added S3 bucket resource: WebpageMvpAssetsBucket')
    
    def add_dynamodb_table(self) -> None:
        """Add DynamoDB table for webpage sessions"""
        table_resource = {
            'Type': 'AWS::DynamoDB::Table',
            'Properties': {
                'TableName': 'pb-fm-webpage-sessions',
                'BillingMode': 'PAY_PER_REQUEST',
                'AttributeDefinitions': [
                    {
                        'AttributeName': 'PK',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'SK', 
                        'AttributeType': 'S'
                    }
                ],
                'KeySchema': [
                    {
                        'AttributeName': 'PK',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'SK',
                        'KeyType': 'RANGE'
                    }
                ],
                'TimeToLiveSpecification': {
                    'AttributeName': 'ttl',
                    'Enabled': True
                },
                'PointInTimeRecoverySpecification': {
                    'PointInTimeRecoveryEnabled': False
                }
            }
        }
        
        self.template['Resources']['WebpageSessionsTable'] = table_resource
        log('INFO', 'Added DynamoDB table resource: WebpageSessionsTable')
    
    def add_iam_permissions(self) -> None:
        """Add IAM permissions for webpage MVP resources"""
        
        # Find existing Lambda execution role
        lambda_role_name = None
        for resource_name, resource in self.template['Resources'].items():
            if resource.get('Type') == 'AWS::IAM::Role':
                assume_policy = resource.get('Properties', {}).get('AssumeRolePolicyDocument', {})
                if 'lambda.amazonaws.com' in str(assume_policy):
                    lambda_role_name = resource_name
                    break
        
        if not lambda_role_name:
            log('WARN', 'Could not find Lambda execution role - will create new policy')
            lambda_role_name = 'WebpageMvpLambdaRole'
        
        # Add webpage-specific permissions policy
        webpage_policy = {
            'Type': 'AWS::IAM::Policy',
            'Properties': {
                'PolicyName': 'WebpageMvpPermissions',
                'PolicyDocument': {
                    'Version': '2012-10-17',
                    'Statement': [
                        {
                            'Effect': 'Allow',
                            'Action': [
                                's3:GetObject',
                                's3:PutObject',
                                's3:DeleteObject'
                            ],
                            'Resource': 'arn:aws:s3:::pb-fm-webpage-mvp-assets/*'
                        },
                        {
                            'Effect': 'Allow',
                            'Action': [
                                's3:ListBucket'
                            ],
                            'Resource': 'arn:aws:s3:::pb-fm-webpage-mvp-assets'
                        },
                        {
                            'Effect': 'Allow',
                            'Action': [
                                'dynamodb:GetItem',
                                'dynamodb:PutItem',
                                'dynamodb:UpdateItem',
                                'dynamodb:DeleteItem',
                                'dynamodb:Query',
                                'dynamodb:Scan'
                            ],
                            'Resource': {
                                'Fn::GetAtt': ['WebpageSessionsTable', 'Arn']
                            }
                        },
                        {
                            'Effect': 'Allow',
                            'Action': [
                                'sqs:CreateQueue',
                                'sqs:DeleteQueue',
                                'sqs:SendMessage',
                                'sqs:ReceiveMessage',
                                'sqs:DeleteMessage',
                                'sqs:GetQueueAttributes',
                                'sqs:SetQueueAttributes'
                            ],
                            'Resource': 'arn:aws:sqs:*:*:pb-fm-webpage-*'
                        }
                    ]
                },
                'Roles': [
                    {'Ref': lambda_role_name}
                ]
            }
        }
        
        self.template['Resources']['WebpageMvpPolicy'] = webpage_policy
        log('INFO', f'Added IAM policy: WebpageMvpPolicy (attached to {lambda_role_name})')
    
    def add_outputs(self) -> None:
        """Add CloudFormation outputs for webpage MVP resources"""
        if 'Outputs' not in self.template:
            self.template['Outputs'] = {}
        
        outputs = {
            'WebpageMvpS3Bucket': {
                'Description': 'S3 bucket for webpage MVP assets',
                'Value': {'Ref': 'WebpageMvpAssetsBucket'},
                'Export': {
                    'Name': {'Fn::Sub': '${AWS::StackName}-webpage-s3-bucket'}
                }
            },
            'WebpageSessionsTableName': {
                'Description': 'DynamoDB table for webpage sessions',
                'Value': {'Ref': 'WebpageSessionsTable'},
                'Export': {
                    'Name': {'Fn::Sub': '${AWS::StackName}-webpage-sessions-table'}
                }
            }
        }
        
        self.template['Outputs'].update(outputs)
        log('INFO', 'Added CloudFormation outputs for webpage MVP resources')
    
    def save_template(self) -> bool:
        """Save updated template"""
        try:
            with open(self.template_path, 'w') as f:
                if self.template_text:
                    # Save raw template text (preserves CloudFormation functions)
                    f.write(self.template_text)
                else:
                    # Fallback to YAML dump if we have parsed template
                    yaml.dump(self.template, f, default_flow_style=False, sort_keys=False)
            
            log('INFO', f'Updated template saved: {self.template_path}')
            return True
            
        except Exception as e:
            log('ERROR', f'Failed to save template: {e}')
            return False
    
    def manually_append_resources(self) -> bool:
        """Manually append webpage MVP resources to template"""
        log('INFO', 'Manually appending webpage MVP resources to template...')
        
        # Define the resources to append as YAML text
        resources_yaml = """
# Webpage MVP Resources (Added automatically)
  WebpageMvpAssetsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: pb-fm-webpage-mvp-assets
      PublicAccessBlockConfiguration:
        BlockPublicAcls: false
        BlockPublicPolicy: false
        IgnorePublicAcls: false
        RestrictPublicBuckets: false
      CorsConfiguration:
        CorsRules:
          - AllowedOrigins: ['*']
            AllowedMethods: [GET, HEAD]
            AllowedHeaders: ['*']
            MaxAge: 3600
      LifecycleConfiguration:
        Rules:
          - Id: DeleteSessionDataAfter30Days
            Status: Enabled
            Filter:
              Prefix: sessions/
            ExpirationInDays: 30

  WebpageSessionsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: pb-fm-webpage-sessions
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK
          AttributeType: S
      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE
      TimeToLiveSpecification:
        AttributeName: ttl
        Enabled: true

  WebpageMvpPolicy:
    Type: AWS::IAM::Policy
    Properties:
      PolicyName: WebpageMvpPermissions
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Action:
              - s3:GetObject
              - s3:PutObject
              - s3:DeleteObject
            Resource: arn:aws:s3:::pb-fm-webpage-mvp-assets/*
          - Effect: Allow
            Action:
              - s3:ListBucket
            Resource: arn:aws:s3:::pb-fm-webpage-mvp-assets
          - Effect: Allow
            Action:
              - dynamodb:GetItem
              - dynamodb:PutItem
              - dynamodb:UpdateItem
              - dynamodb:DeleteItem
              - dynamodb:Query
              - dynamodb:Scan
            Resource: !GetAtt WebpageSessionsTable.Arn
          - Effect: Allow
            Action:
              - sqs:CreateQueue
              - sqs:DeleteQueue
              - sqs:SendMessage
              - sqs:ReceiveMessage
              - sqs:DeleteMessage
              - sqs:GetQueueAttributes
              - sqs:SetQueueAttributes
            Resource: arn:aws:sqs:*:*:pb-fm-webpage-*
      Roles:
        - !Ref LambdaExecutionRole

# Webpage MVP Outputs (Added automatically)
Outputs:
  WebpageMvpS3Bucket:
    Description: S3 bucket for webpage MVP assets
    Value: !Ref WebpageMvpAssetsBucket
    Export:
      Name: !Sub "${AWS::StackName}-webpage-s3-bucket"
      
  WebpageSessionsTableName:
    Description: DynamoDB table for webpage sessions
    Value: !Ref WebpageSessionsTable
    Export:
      Name: !Sub "${AWS::StackName}-webpage-sessions-table"
"""
        
        # Check if resources already exist
        if 'pb-fm-webpage-mvp-assets' in self.template_text:
            log('INFO', 'Webpage MVP resources already exist in template')
            return True
        
        # Find where to insert (before the last line or before existing Outputs)
        lines = self.template_text.split('\n')
        
        # Look for existing Outputs section
        outputs_line = -1
        resources_end = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith('Outputs:'):
                outputs_line = i
                break
            elif line.strip() and not line.startswith(' ') and not line.startswith('#'):
                # This is a top-level section
                if 'Resources:' in self.template_text[:self.template_text.find(line)]:
                    resources_end = i
        
        # Insert the resources
        if outputs_line > 0:
            # Insert before Outputs
            lines.insert(outputs_line, resources_yaml.strip())
        else:
            # Append to end
            lines.append(resources_yaml.strip())
        
        # Update template text
        self.template_text = '\n'.join(lines)
        
        return True

    def update_template(self, force: bool = False) -> bool:
        """Main function to update template with webpage MVP resources"""
        log('INFO', 'Starting CloudFormation template update for Webpage MVP')
        
        if not self.load_template():
            return False
        
        if not self.create_backup():
            return False
        
        # Check if resources already exist (simple text search)
        if 'pb-fm-webpage-mvp-assets' in self.template_text and not force:
            log('WARN', 'Webpage MVP resources appear to already exist in template')
            log('INFO', 'Use --force to update anyway')
            return True
        
        # Since CloudFormation YAML is complex, manually append resources
        if not self.manually_append_resources():
            return False
        
        # Save updated template
        if not self.save_template():
            return False
        
        log('INFO', '✓ CloudFormation template updated successfully!')
        log('INFO', f'Backup created: {self.backup_path}')
        log('INFO', '\nNext steps:')
        log('INFO', '  1. Review the updated template')
        log('INFO', '  2. Run: ./deploy.sh dev --clean --test')
        log('INFO', '  3. Test infrastructure: uv run python scripts/test_webpage_infrastructure.py')
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Update CloudFormation template for Webpage MVP')
    parser.add_argument('--template', '-t', default='template-unified.yaml', 
                       help='Path to CloudFormation template (default: template-unified.yaml)')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force update even if resources exist')
    
    args = parser.parse_args()
    
    # Resolve template path
    if not os.path.isabs(args.template):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(os.path.dirname(script_dir), args.template)
    else:
        template_path = args.template
    
    updater = CloudFormationUpdater(template_path)
    success = updater.update_template(args.force)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()