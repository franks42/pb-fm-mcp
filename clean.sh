#!/bin/bash
# Complete cleanup script for pb-fm-mcp deployment artifacts

set -e

echo "🧹 Cleaning all deployment artifacts and caches..."

# Remove SAM build artifacts
echo "  - Removing SAM build directory..."
rm -rf .aws-sam/

# Remove Python cache files
echo "  - Removing Python bytecode files..."
find . -name "*.pyc" -delete

echo "  - Removing Python cache directories..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove other cache directories
echo "  - Removing Ruff cache..."
rm -rf .ruff_cache/

# Remove SAM configuration
echo "  - Removing SAM config files..."
rm -f samconfig.toml

# Remove old Cloudflare Workers artifacts
echo "  - Removing old Cloudflare Workers artifacts..."
rm -rf .venv-workers/ .wrangler/

# Remove any temporary files
echo "  - Removing temporary files..."
rm -f /tmp/test_sqs_timing_*.py 2>/dev/null || true

echo "✅ Cleanup complete! Ready for fresh deployment."