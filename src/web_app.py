"""
FastAPI application for AWS Lambda Web Adapter deployment.
Simplified version without Mangum complexity.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from registry import get_registry, FastAPIIntegration
from version import get_version_string, get_full_version_info

# Create FastAPI app without Lambda-specific configuration
app = FastAPI(
    title="PB-FM API",
    description="REST API for Provenance Blockchain and Figure Markets data",
    version=get_version_string(),
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Health check endpoint for Lambda Web Adapter
@app.get("/health")
async def health_check():
    """Health check endpoint for container readiness."""
    return {"status": "healthy", "version": get_version_string()}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    version_info = get_full_version_info()
    return {
        "name": "PB-FM API",
        "version": version_info["version"],
        "build_number": version_info["build_number"],
        "build_datetime": version_info["build_datetime"],
        "environment": version_info["deployment_environment"],
        "description": "REST API for Provenance Blockchain and Figure Markets data",
        "endpoints": {
            "docs": "/docs",
            "openapi": "/openapi.json",
            "health": "/health"
        }
    }

# Register all @api_function decorated functions as routes
print("🔧 Registering API functions...")
registry = get_registry()
FastAPIIntegration.register_rest_routes(app, registry)
print(f"✅ Registered {len(registry.get_rest_functions())} REST endpoints")

# Update OpenAPI schema
FastAPIIntegration.update_openapi_schema(app, registry)
print("📝 Updated OpenAPI schema with registry documentation")