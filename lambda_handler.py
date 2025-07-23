#!/usr/bin/env python3
"""
AWS Lambda handler for unified MCP + REST deployment.

This file is no longer used with AWS Lambda Web Adapter deployment.
The Web Adapter uses run.sh to start uvicorn directly.

For reference, this was the old mangum-based approach that had async issues.
"""

# This file is kept for reference but not used in Web Adapter deployment
# The actual application starts via: run.sh -> uvicorn src.web_app_unified:app