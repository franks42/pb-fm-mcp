"""
Test script to simulate the documentation update functionality.

This script can be run manually to test the documentation update logic
without requiring EventBridge permissions.
"""

import json
import sys
import os

# Add the docs-updater directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'docs-updater'))

from update_docs import validate_api_health, update_external_documentation

def test_documentation_update():
    """Test the documentation update functionality."""
    print("🧪 Testing Documentation Update Functionality")
    print("=" * 60)
    
    # Test API URL
    api_url = "https://869vaymeul.execute-api.us-west-1.amazonaws.com/Prod"
    
    # Test API health validation
    print("1️⃣ Testing API health validation...")
    if validate_api_health(api_url):
        print("✅ API health check passed!")
    else:
        print("❌ API health check failed!")
        return False
    
    # Test documentation updates
    print("\n2️⃣ Testing documentation updates...")
    update_results = update_external_documentation(api_url)
    
    print(f"📊 Update Results:")
    for service, result in update_results.items():
        status = "✅" if "success" in result else "❌"
        print(f"  {status} {service}: {result}")
    
    # Show final URLs
    print(f"\n🔗 Documentation URLs:")
    print(f"  📖 OpenAPI Spec: {api_url}/openapi.json")
    print(f"  📚 Swagger UI: https://generator3.swagger.io/index.html?url={api_url}/openapi.json")
    print(f"  📋 API Docs: {api_url}/docs")
    
    print("\n🎉 Documentation update test completed!")
    return True

if __name__ == "__main__":
    success = test_documentation_update()
    sys.exit(0 if success else 1)