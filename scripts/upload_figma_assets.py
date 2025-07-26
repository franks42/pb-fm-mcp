#!/usr/bin/env python3
"""
Figma Assets Upload Script for PB-FM MCP Dashboard

This script uploads Figma-exported design assets to the S3 WebAssets bucket
for immediate use in the dashboard without requiring Lambda redeployment.

Usage:
    python scripts/upload_figma_assets.py --source ./figma-exports
    python scripts/upload_figma_assets.py --source ./figma-exports --bucket pb-fm-mcp-dev-web-assets-289426936662
    python scripts/upload_figma_assets.py --help
"""

import argparse
import boto3
import os
import sys
from pathlib import Path
from typing import Dict, List
import mimetypes

# MIME type mappings for web assets
MIME_TYPES = {
    '.css': 'text/css',
    '.js': 'text/javascript',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
    '.otf': 'font/otf',
    '.html': 'text/html',
    '.json': 'application/json'
}

def get_s3_bucket_name() -> str:
    """
    Get the WebAssets S3 bucket name from CloudFormation stack.
    """
    try:
        import boto3
        cf = boto3.client('cloudformation')
        
        response = cf.describe_stacks(StackName='pb-fm-mcp-dev')
        stack = response['Stacks'][0]
        
        for output in stack.get('Outputs', []):
            if output['OutputKey'] == 'WebAssetsBucketName':
                return output['OutputValue']
        
        # Fallback - construct from known pattern
        account_id = boto3.client('sts').get_caller_identity()['Account']
        return f"pb-fm-mcp-dev-web-assets-{account_id}"
        
    except Exception as e:
        print(f"Warning: Could not get bucket name from CloudFormation: {e}")
        print("Using default bucket name pattern...")
        account_id = boto3.client('sts').get_caller_identity()['Account']
        return f"pb-fm-mcp-dev-web-assets-{account_id}"

def upload_file_to_s3(file_path: Path, bucket_name: str, s3_key: str) -> bool:
    """
    Upload a single file to S3 with appropriate content type.
    """
    try:
        s3 = boto3.client('s3')
        
        # Determine content type
        content_type = MIME_TYPES.get(file_path.suffix.lower())
        if not content_type:
            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                content_type = 'application/octet-stream'
        
        # Upload with metadata
        extra_args = {
            'ContentType': content_type,
            'CacheControl': 'public, max-age=3600',  # 1 hour cache
        }
        
        # Enable compression for text files
        if content_type.startswith(('text/', 'application/javascript', 'application/json')):
            extra_args['ContentEncoding'] = 'gzip'
            # TODO: Implement gzip compression if needed
        
        s3.upload_file(str(file_path), bucket_name, s3_key, ExtraArgs=extra_args)
        print(f"✅ Uploaded: {s3_key} ({content_type})")
        return True
        
    except Exception as e:
        print(f"❌ Failed to upload {s3_key}: {e}")
        return False

def upload_figma_assets(source_dir: Path, bucket_name: str, dry_run: bool = False) -> Dict[str, List[str]]:
    """
    Upload Figma assets from source directory to S3 bucket.
    
    Expected directory structure:
    source_dir/
    ├── design-tokens/
    │   ├── colors.css
    │   ├── typography.css
    │   └── spacing.css
    ├── components/
    │   ├── buttons/
    │   └── cards/
    ├── icons/
    │   ├── wallet.svg
    │   └── chart.svg
    └── images/
        └── logo.png
    """
    results = {
        'successful': [],
        'failed': [],
        'skipped': []
    }
    
    if not source_dir.exists():
        print(f"❌ Source directory does not exist: {source_dir}")
        return results
    
    print(f"📁 Scanning source directory: {source_dir}")
    print(f"🪣 Target S3 bucket: {bucket_name}")
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be uploaded")
    
    # Scan all files recursively
    files_to_upload = []
    for file_path in source_dir.rglob('*'):
        if file_path.is_file():
            # Generate S3 key (preserve directory structure under figma/ prefix)
            relative_path = file_path.relative_to(source_dir)
            s3_key = f"figma/{relative_path}".replace('\\', '/')  # Ensure forward slashes
            files_to_upload.append((file_path, s3_key))
    
    print(f"📋 Found {len(files_to_upload)} files to upload")
    
    if not files_to_upload:
        print("⚠️  No files found to upload")
        return results
    
    # Upload files
    for file_path, s3_key in files_to_upload:
        if dry_run:
            print(f"🔍 Would upload: {s3_key}")
            results['successful'].append(s3_key)
        else:
            if upload_file_to_s3(file_path, bucket_name, s3_key):
                results['successful'].append(s3_key)
            else:
                results['failed'].append(s3_key)
    
    return results

def generate_sample_structure(output_dir: Path):
    """
    Generate a sample Figma export directory structure for testing.
    """
    print(f"📋 Creating sample Figma export structure in: {output_dir}")
    
    # Create directory structure
    directories = [
        'design-tokens',
        'components/buttons',
        'components/cards',
        'components/panels',
        'icons',
        'images',
        'fonts'
    ]
    
    for dir_path in directories:
        (output_dir / dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create sample files
    sample_files = {
        'design-tokens/colors.css': '''/* Figma Design Tokens - Colors */
:root {
  --color-primary: #00ff88;
  --color-secondary: #00ccff;
  --color-accent: #ff6b6b;
  --color-background: #1e1e1e;
  --color-surface: #2a2a2a;
  --color-text: #ffffff;
  --color-text-muted: #888888;
}''',
        'design-tokens/typography.css': '''/* Figma Design Tokens - Typography */
:root {
  --font-family-primary: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  --font-family-mono: 'Courier New', monospace;
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-md: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 24px;
  --font-size-2xl: 32px;
  --font-weight-normal: 400;
  --font-weight-bold: 700;
}''',
        'design-tokens/spacing.css': '''/* Figma Design Tokens - Spacing */
:root {
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-2xl: 48px;
  --border-radius-sm: 4px;
  --border-radius-md: 8px;
  --border-radius-lg: 12px;
}''',
        'components/buttons/button-primary.css': '''.figma-button-primary {
  padding: var(--spacing-md);
  background: linear-gradient(45deg, var(--color-primary), var(--color-secondary));
  color: black;
  border: none;
  border-radius: var(--border-radius-md);
  font-weight: var(--font-weight-bold);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.figma-button-primary:hover {
  transform: translateY(-2px);
}''',
        'components/cards/dashboard-card.css': '''.figma-dashboard-card {
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}''',
        'icons/wallet.svg': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M21 18V6H3V18H21Z" stroke="currentColor" stroke-width="2"/>
<path d="M18 12H15V10H18V12Z" fill="currentColor"/>
</svg>''',
        'icons/chart.svg': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M3 17L9 11L13 15L21 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
</svg>'''
    }
    
    for file_path, content in sample_files.items():
        full_path = output_dir / file_path
        full_path.write_text(content)
        print(f"  📄 Created: {file_path}")
    
    print(f"✅ Sample structure created! You can now run:")
    print(f"   python scripts/upload_figma_assets.py --source {output_dir}")

def main():
    parser = argparse.ArgumentParser(
        description='Upload Figma-exported design assets to S3 WebAssets bucket',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Upload from figma-exports directory (auto-detect bucket)
  python scripts/upload_figma_assets.py --source ./figma-exports
  
  # Upload to specific bucket
  python scripts/upload_figma_assets.py --source ./figma-exports --bucket my-bucket
  
  # Dry run to see what would be uploaded
  python scripts/upload_figma_assets.py --source ./figma-exports --dry-run
  
  # Generate sample export structure
  python scripts/upload_figma_assets.py --generate-sample ./sample-figma-exports
        '''
    )
    
    parser.add_argument(
        '--source', '-s',
        type=Path,
        help='Path to Figma exports directory'
    )
    
    parser.add_argument(
        '--bucket', '-b',
        type=str,
        help='S3 bucket name (auto-detected if not specified)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be uploaded without actually uploading'
    )
    
    parser.add_argument(
        '--generate-sample',
        type=Path,
        help='Generate a sample Figma export directory structure'
    )
    
    args = parser.parse_args()
    
    # Generate sample structure
    if args.generate_sample:
        generate_sample_structure(args.generate_sample)
        return
    
    # Validate arguments
    if not args.source:
        parser.error("--source is required (or use --generate-sample)")
    
    # Get bucket name
    bucket_name = args.bucket
    if not bucket_name:
        print("🔍 Auto-detecting S3 bucket name...")
        try:
            bucket_name = get_s3_bucket_name()
            print(f"✅ Found bucket: {bucket_name}")
        except Exception as e:
            print(f"❌ Failed to auto-detect bucket: {e}")
            print("Please specify bucket name with --bucket")
            sys.exit(1)
    
    # Upload assets
    print(f"\n🚀 Starting Figma assets upload...")
    results = upload_figma_assets(args.source, bucket_name, args.dry_run)
    
    # Print results
    print(f"\n📊 Upload Results:")
    print(f"  ✅ Successful: {len(results['successful'])}")
    print(f"  ❌ Failed: {len(results['failed'])}")
    print(f"  ⏭️  Skipped: {len(results['skipped'])}")
    
    if results['failed']:
        print(f"\n❌ Failed uploads:")
        for failed_file in results['failed']:
            print(f"  - {failed_file}")
        sys.exit(1)
    
    if not args.dry_run and results['successful']:
        print(f"\n🎉 All assets uploaded successfully!")
        print(f"Assets are now available at:")
        print(f"https://{bucket_name}.s3.us-west-1.amazonaws.com/figma/")
        print(f"\nTo use in dashboard, reference files like:")
        print(f"<link rel=\"stylesheet\" href=\"https://{bucket_name}.s3.us-west-1.amazonaws.com/figma/design-tokens/colors.css\">")

if __name__ == '__main__':
    main()