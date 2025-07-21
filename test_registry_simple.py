#!/usr/bin/env python3
"""
Simple test for registry without FastAPI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("🧪 Testing Registry Core")
    print("=" * 30)
    
    # Test registry core
    from src.registry.registry import get_registry
    from src.functions.stats_functions import fetch_current_hash_statistics
    
    registry = get_registry()
    print(f"📊 Registry has {len(registry)} functions")
    
    # List functions
    for name, meta in registry.get_all_functions().items():
        print(f"✅ {name}: {[p.value for p in meta.protocols]}")
        print(f"   Path: {meta.rest_path}")
        print(f"   Method: {meta.rest_method}")
        print(f"   Tags: {meta.tags}")
        
    print("\n🎉 Registry core working!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()