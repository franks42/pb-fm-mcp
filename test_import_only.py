#!/usr/bin/env python3
"""
Test just the import path for the stats function
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), 'src')))

try:
    print("🧪 Testing Function Import")
    print("=" * 30)
    
    # Test function import directly
    print("📦 Importing stats function...")
    from src.functions.stats_functions import fetch_current_hash_statistics
    print("✅ Function imported successfully")
    
    # Test registry import
    print("📦 Importing registry...")
    from src.registry.registry import get_registry
    print("✅ Registry imported successfully")
    
    # Test registry content
    registry = get_registry()
    print(f"📊 Registry has {len(registry)} functions")
    
    # List functions
    for name, meta in registry.get_all_functions().items():
        print(f"✅ {name}: {[p.value for p in meta.protocols]}")
        
    print("\n🎉 Import test passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()