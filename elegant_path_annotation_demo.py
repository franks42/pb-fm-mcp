#!/usr/bin/env python3
"""
Demonstration of the elegant path annotation approach.

This shows the three-step process:
1. Get the paths for all the objects in the data
2. Iterate over those paths to add key-value pairs  
3. Where the key name and value are derived from the paths that matched individual objects

This approach leverages jqpy's existing set_path() functionality beautifully.
"""

from src.jqpy.traverse_utils import (
    create_path_map, 
    annotate_objects_with_paths, 
    annotate_with_custom_values
)
from src.jqpy import get_path, set_path
import json


def demonstrate_three_step_process():
    """Show the elegant three-step approach step by step."""
    print("🎯 THE ELEGANT THREE-STEP APPROACH")
    print("=" * 50)
    
    data = {
        "teams": [
            {
                "name": "Backend",
                "members": [
                    {"name": "Alice", "seniority": "Senior"},
                    {"name": "Bob", "seniority": "Junior"}
                ]
            },
            {
                "name": "Frontend", 
                "lead": {"name": "Charlie", "seniority": "Lead"}
            }
        ],
        "company": {"name": "TechCorp", "founded": 2020}
    }
    
    print("\nOriginal data:")
    print(json.dumps(data, indent=2))
    
    print("\n📍 STEP 1: Get the paths for all the objects in the data")
    all_paths = create_path_map(data)
    object_paths = {path: value for path, value in all_paths.items() if isinstance(value, dict)}
    
    print(f"Found {len(object_paths)} objects at these paths:")
    for path in sorted(object_paths.keys()):
        print(f"   {path}")
    
    print("\n🔄 STEP 2: Iterate over those paths to add key-value pairs")
    print("(using set_path for each object path)")
    
    result = data
    import copy
    result = copy.deepcopy(data)
    
    for path, value in object_paths.items():
        # STEP 3: Key name and value derived from the path
        annotation_path = f"{path}._jq_path" if path != "." else "._jq_path"
        annotation_value = path  # Value derived from the path itself
        
        print(f"   Adding {annotation_path} = '{annotation_value}'")
        set_result = list(set_path(result, annotation_path, annotation_value))
        if set_result:
            result = set_result[0]
    
    print("\n✨ RESULT: All objects now have path annotations")
    print(json.dumps(result, indent=2))
    
    return result


def demonstrate_utility_wrapper():
    """Show how the utility function encapsulates the three-step process."""
    print("\n" + "=" * 50)
    print("🛠️  UTILITY FUNCTION WRAPPER")
    print("=" * 50)
    
    data = {
        "projects": [
            {"name": "Project A", "status": "active"},
            {"name": "Project B", "status": "completed", 
             "details": {"budget": 10000, "team_size": 5}}
        ]
    }
    
    print("\nOriginal data:")
    print(json.dumps(data, indent=2))
    
    print("\nUsing annotate_objects_with_paths() - encapsulates the 3 steps:")
    annotated = annotate_objects_with_paths(data, annotation_key="location")
    print(json.dumps(annotated, indent=2))
    
    print("\nTesting jq operations:")
    results = list(get_path(annotated, '.projects[]'))
    for project in results:
        print(f"   Project '{project['name']}' found at: {project['location']}")
    
    return annotated


def demonstrate_custom_derivations():
    """Show how we can derive different key-value pairs from paths."""
    print("\n" + "=" * 50)  
    print("🎨 CUSTOM KEY-VALUE DERIVATIONS")
    print("=" * 50)
    
    data = {
        "departments": [
            {
                "name": "Engineering",
                "teams": [
                    {"name": "Backend", "size": 8},
                    {"name": "Frontend", "size": 6}
                ]
            },
            {
                "name": "Marketing",
                "campaigns": [
                    {"name": "Summer Sale", "budget": 5000}
                ]
            }
        ]
    }
    
    print("\nOriginal data:")
    print(json.dumps(data, indent=2))
    
    # Custom derivation 1: Extract department index from path
    def derive_department_info(path):
        if ".departments[" in path:
            dept_index = path.split(".departments[")[1].split("]")[0]
            return f"dept_{dept_index}"
        return "root_level"
    
    dept_annotated = annotate_with_custom_values(data, derive_department_info, "dept_id")
    print("\nWith department ID derived from path:")
    print(json.dumps(dept_annotated, indent=2))
    
    # Custom derivation 2: Path hierarchy level
    def derive_hierarchy_level(path):
        if path == ".":
            return "organization"
        elif ".departments[" in path and ".teams[" not in path and ".campaigns[" not in path:
            return "department"
        elif ".teams[" in path or ".campaigns[" in path:
            return "team_or_campaign"
        else:
            return "unknown"
    
    hierarchy_annotated = annotate_with_custom_values(data, derive_hierarchy_level, "level")
    print("\nWith hierarchy level derived from path:")
    print(json.dumps(hierarchy_annotated, indent=2))


def demonstrate_practical_use_case():
    """Show a practical debugging use case."""
    print("\n" + "=" * 50)
    print("🐛 PRACTICAL DEBUGGING USE CASE")
    print("=" * 50)
    
    # Complex nested data that might be hard to debug
    data = {
        "api_responses": [
            {
                "endpoint": "/users",
                "results": [
                    {"user_id": 1, "data": {"profile": {"active": True}}},
                    {"user_id": 2, "data": {"profile": {"active": False}}}
                ]
            },
            {
                "endpoint": "/orders",
                "results": [
                    {"order_id": 100, "data": {"status": "completed"}}
                ]
            }
        ]
    }
    
    print("Complex nested API response data:")
    print(json.dumps(data, indent=2))
    
    # Add debugging annotations
    debug_annotated = annotate_objects_with_paths(data, "_debug_path")
    
    print("\nNow let's filter for active users and see exactly where they came from:")
    active_profiles = list(get_path(debug_annotated, '.api_responses[].results[].data.profile | select(.active == true)'))
    
    for profile in active_profiles:
        path = profile["_debug_path"]
        print(f"   Active profile found at: {path}")
        # Extract useful info from the path
        api_index = path.split('.api_responses[')[1].split(']')[0]
        result_index = path.split('.results[')[1].split(']')[0] 
        print(f"     -> API response #{api_index}, result #{result_index}")
    
    print("\n🎯 With path annotations, debugging complex nested data becomes trivial!")


def main():
    """Run all demonstrations."""
    print("🌟 ELEGANT PATH ANNOTATION APPROACH")
    print("Using jqpy's set_path() for maximum elegance")
    print("=" * 60)
    
    demonstrate_three_step_process()
    demonstrate_utility_wrapper()
    demonstrate_custom_derivations()
    demonstrate_practical_use_case()
    
    print("\n" + "=" * 60)
    print("✨ KEY INSIGHTS")
    print("=" * 60)
    print("\n🎯 The Three-Step Process:")
    print("   1️⃣  Get paths for all objects in the data")
    print("   2️⃣  Iterate over those paths to add key-value pairs")
    print("   3️⃣  Key name and value derived from paths that matched individual objects")
    
    print("\n🛠️  Why this approach is elegant:")
    print("   ✅ Leverages existing set_path() functionality")
    print("   ✅ Demonstrates jqpy's modular, composable design")
    print("   ✅ Key names and values are completely customizable")
    print("   ✅ Path information drives the annotation process")
    print("   ✅ Works with any level of nesting complexity")
    
    print("\n📚 Available utilities:")
    print("   • create_path_map() - Step 1: Get all object paths")
    print("   • annotate_objects_with_paths() - Complete 3-step process")
    print("   • annotate_with_custom_values() - Custom key-value derivation")
    print("   • set_path() - The fundamental building block")


if __name__ == "__main__":
    main()