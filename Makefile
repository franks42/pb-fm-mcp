build-McpFunction:
	# Copy only essential source files
	mkdir -p $(ARTIFACTS_DIR)/src
	cp -r src/hastra.py src/utils.py src/logger.py src/exceptions.py src/hastra_types.py $(ARTIFACTS_DIR)/src/
	cp lambda_handler.py $(ARTIFACTS_DIR)/
	cp async_wrapper.py $(ARTIFACTS_DIR)/
	# Install minimal dependencies
	pip install --target $(ARTIFACTS_DIR) httpx==0.28.1 structlog==25.4.0 typing-extensions certifi
	# Copy MCP handler from our working venv
	cp -r .venv/lib/python3.12/site-packages/awslabs $(ARTIFACTS_DIR)/
	cp -r .venv/lib/python3.12/site-packages/mcp $(ARTIFACTS_DIR)/
	# Clean up unnecessary files to reduce size
	find $(ARTIFACTS_DIR) -name "*.pyc" -delete
	find $(ARTIFACTS_DIR) -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find $(ARTIFACTS_DIR) -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true
	find $(ARTIFACTS_DIR) -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true
	# Exclude boto3/botocore since they're provided by Lambda runtime
	rm -rf $(ARTIFACTS_DIR)/boto* $(ARTIFACTS_DIR)/botocore* $(ARTIFACTS_DIR)/s3transfer*