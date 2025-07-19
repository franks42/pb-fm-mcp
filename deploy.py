#!/usr/bin/env python3
"""
AWS Lambda deployment script for pb-fm-mcp server
"""
import argparse
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

def create_deployment_package():
    """Create a deployment package for AWS Lambda"""
    print("Creating deployment package...")
    
    # Create a temporary directory for the package
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy source files
        source_files = [
            "lambda_handler.py",
            "src/utils.py", 
            "src/base64expand.py",
            "src/hastra_types.py",
            "src/hastra.py"
        ]
        
        for file in source_files:
            if Path(file).exists():
                dest = temp_path / Path(file).name
                dest.write_text(Path(file).read_text())
                print(f"Added {file}")
        
        # Install dependencies using uv
        print("Installing dependencies with uv...")
        subprocess.run([
            "uv", "pip", "install",
            "--target", str(temp_path),
            "awslabs-mcp-lambda-handler",
            "httpx",
            "structlog",
            "pyyaml"
        ], check=True)
        
        # Create zip file
        zip_path = Path("pb-fm-mcp-lambda.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in temp_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(temp_path)
                    zipf.write(file_path, arcname)
        
        print(f"Deployment package created: {zip_path}")
        return zip_path

def deploy_to_aws(function_name: str, role_arn: str, region: str = "us-east-1"):
    """Deploy the Lambda function to AWS"""
    zip_path = create_deployment_package()
    
    print(f"Deploying to AWS Lambda function: {function_name}")
    
    # Create or update Lambda function
    try:
        # Try to update existing function
        subprocess.run([
            "aws", "lambda", "update-function-code",
            "--function-name", function_name,
            "--zip-file", f"fileb://{zip_path}",
            "--region", region
        ], check=True)
        print(f"Updated existing Lambda function: {function_name}")
        
    except subprocess.CalledProcessError:
        # Create new function if update fails
        print("Function doesn't exist, creating new one...")
        subprocess.run([
            "aws", "lambda", "create-function",
            "--function-name", function_name,
            "--runtime", "python3.12",
            "--role", role_arn,
            "--handler", "lambda_handler.lambda_handler",
            "--zip-file", f"fileb://{zip_path}",
            "--timeout", "30",
            "--memory-size", "512",
            "--region", region
        ], check=True)
        print(f"Created new Lambda function: {function_name}")
    
    # Clean up
    zip_path.unlink()
    print("Deployment complete!")

def create_api_gateway(function_name: str, region: str = "us-east-1"):
    """Create API Gateway for the Lambda function"""
    print("Creating API Gateway...")
    
    # This would require more complex AWS SDK calls
    # For now, provide manual instructions
    print(f"""
    Manual API Gateway setup required:
    
    1. Go to AWS Console > API Gateway
    2. Create new HTTP API
    3. Add integration to Lambda function: {function_name}
    4. Add route: POST /mcp
    5. Enable CORS if needed
    6. Deploy API
    
    Or use AWS CDK/CloudFormation for automated setup.
    """)

def main():
    parser = argparse.ArgumentParser(description="Deploy pb-fm-mcp to AWS Lambda")
    parser.add_argument("--function-name", help="Lambda function name")
    parser.add_argument("--role-arn", help="IAM role ARN for Lambda")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--api-gateway", action="store_true", help="Setup API Gateway")
    parser.add_argument("--package-only", action="store_true", help="Only create deployment package")
    
    args = parser.parse_args()
    
    if args.package_only:
        create_deployment_package()
    else:
        if not args.function_name or not args.role_arn:
            parser.error("--function-name and --role-arn are required for deployment")
        deploy_to_aws(args.function_name, args.role_arn, args.region)
        
        if args.api_gateway:
            create_api_gateway(args.function_name, args.region)

if __name__ == "__main__":
    main()