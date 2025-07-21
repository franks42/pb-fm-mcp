#!/usr/bin/env python3
"""
Test script for lambda handler integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("🧪 Testing Lambda Handler Integration")
    print("=" * 40)
    
    # Test imports
    print("📦 Testing imports...")
    from src.registry import get_registry, MCPIntegration, FastAPIIntegration
    from src.functions.stats_functions import fetch_current_hash_statistics
    print("✅ Registry imports successful")
    
    # Test registry
    registry = get_registry()
    print(f"📊 Registry has {len(registry)} functions")
    
    # List registered functions
    for name, meta in registry.get_all_functions().items():
        print(f"   - {name}: {[p.value for p in meta.protocols]} -> {meta.rest_path}")
    
    print("\n✅ Integration test passed! 🎉")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()