# Use standard Python image for web app
FROM python:3.12-slim

# Add AWS Lambda Web Adapter (for Lambda deployment)
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.7.1 /lambda-adapter /opt/extensions/

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies using pip (uv not available in Lambda container)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY lambda_handler.py .
COPY async_wrapper.py .
COPY version.json .
COPY version.py .

# Environment variables for Lambda Web Adapter
ENV PORT=8080
ENV AWS_LWA_READINESS_CHECK_PATH="/health"
ENV AWS_LWA_READINESS_CHECK_PROTOCOL="http"

# Add src directory to Python path so imports work naturally
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Run with Uvicorn (Lambda Web Adapter format) - unified app
CMD ["uvicorn", "src.web_app_unified:app", "--host", "0.0.0.0", "--port", "8080"]