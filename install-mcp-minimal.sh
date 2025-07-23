#!/bin/bash
# Install MCP handler without boto3/botocore dependencies
pip install --no-deps awslabs-mcp-lambda-handler
pip install typing-extensions  # Required by MCP handler
pip install certifi  # Required by httpx