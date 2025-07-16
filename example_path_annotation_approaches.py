#!/usr/bin/env python3
"""
Example showing different approaches to adding path annotations to data structures.

This demonstrates how jqpy's modular design allows for elegant solutions
by combining existing utilities.
"""

from src.jqpy.traverse_utils import (
    add_path_annotations, 
    add_path_annotations_using_set_path,
    create_path_map
)
from src.jqpy import get_path, set_path
import json


def demonstrate_manual_set_path_approach():
    """Show how to manually add path annotations using set_path()."""
    print("=== MANUAL set_path() APPROACH ===\n")
    
    data = {
        "team": "Engineering",
        "members": [
            {"name": "Alice", "role": "Senior"},
            {"name": "Bob", "role": "Junior"}
        ]
    }
    
    print("Original data:")
    print(json.dumps(data, indent=2))
    
    # Step 1: Find all paths
    paths = create_path_map(data)
    print(f"\nFound {len(paths)} paths:")
    for path in sorted(paths.keys()):
        if isinstance(paths[path], dict):
            print(f"   {path} -> dict")
    
    # Step 2: Use set_path to add annotations
    result = data
    for path, value in paths.items():
        if isinstance(value, dict):
            annotation_path = f"{path}._jq_path" if path != "." else "._jq_path"
            set_result = list(set_path(result, annotation_path, path))
            if set_result:
                result = set_result[0]
    
    print("\nAfter manual set_path annotations:")
    print(json.dumps(result, indent=2))
    
    return result


def demonstrate_utility_function_approach():
    """Show the utility function approach."""
    print("\n=== UTILITY FUNCTION APPROACH ===\n")
    
    data = {
        "team": "Engineering", 
        "members": [
            {"name": "Alice", "role": "Senior"},
            {"name": "Bob", "role": "Junior"}
        ]
    }
    
    # Using the utility function (which internally uses set_path)
    annotated = add_path_annotations_using_set_path(data)
    
    print("Using add_path_annotations_using_set_path():")
    print(json.dumps(annotated, indent=2))
    
    return annotated


def demonstrate_custom_annotation_workflow():
    """Show how to create custom annotation workflows."""
    print("\n=== CUSTOM ANNOTATION WORKFLOW ===\n")
    
    data = {
        "projects": [
            {"name": "Project A", "status": "active", "team": "backend"},
            {"name": "Project B", "status": "completed", "team": "frontend"}
        ]
    }
    
    print("Original data:")
    print(json.dumps(data, indent=2))
    
    # Custom workflow: Add multiple types of annotations
    result = data
    paths = create_path_map(data)
    
    for path, value in paths.items():
        if isinstance(value, dict):
            # Add path annotation
            path_annotation = f"{path}._debug_path" if path != "." else "._debug_path"
            set_result = list(set_path(result, path_annotation, path))
            if set_result:
                result = set_result[0]
            
            # Add type annotation
            type_annotation = f"{path}._type" if path != "." else "._type"
            set_result = list(set_path(result, type_annotation, "object"))
            if set_result:
                result = set_result[0]
            
            # Add depth annotation
            depth = path.count('.') + path.count('[')
            depth_annotation = f"{path}._depth" if path != "." else "._depth"
            set_result = list(set_path(result, depth_annotation, depth))
            if set_result:
                result = set_result[0]
    
    print("\nWith custom annotations (path, type, depth):")
    print(json.dumps(result, indent=2))
    
    return result


def demonstrate_filtering_with_paths():
    """Show how path annotations help with filtering and debugging."""
    print("\n=== FILTERING WITH PATH ANNOTATIONS ===\n")
    
    # Use annotated data for filtering
    data = add_path_annotations_using_set_path({
        "departments": [
            {
                "name": "Engineering",
                "employees": [
                    {"name": "Alice", "active": True},
                    {"name": "Bob", "active": False}
                ]
            },
            {
                "name": "Sales",
                "employees": [
                    {"name": "Charlie", "active": True}
                ]
            }
        ]
    })
    
    # Find all active employees
    active_employees = list(get_path(data, '.departments[].employees[] | select(.active == true)'))
    
    print("Active employees found:")
    for emp in active_employees:
        print(f"   {emp['name']} at path: {emp['_jq_path']}")
        # Extract department from path
        dept_index = emp['_jq_path'].split('.departments[')[1].split(']')[0]
        print(f"     -> Department index: {dept_index}")
    
    # Find departments with all active employees
    all_departments = list(get_path(data, '.departments[]'))
    print("\nDepartment analysis:")
    for dept in all_departments:
        dept_employees = list(get_path(dept, '.employees[]'))
        active_count = len([e for e in dept_employees if e.get('active', False)])
        total_count = len(dept_employees)
        print(f"   {dept['name']} (at {dept['_jq_path']}): {active_count}/{total_count} active")


def main():
    """Run all demonstrations."""
    print("🛠️  JQPY PATH ANNOTATION APPROACHES")
    print("=" * 60)
    
    demonstrate_manual_set_path_approach()
    demonstrate_utility_function_approach()
    demonstrate_custom_annotation_workflow()
    demonstrate_filtering_with_paths()
    
    print("\n" + "=" * 60)
    print("🎯 KEY INSIGHTS")
    print("=" * 60)
    print("\n✨ The set_path() approach is superior because:")
    print("   ✅ Reuses existing, well-tested jqpy functionality")
    print("   ✅ Demonstrates jqpy's modular, composable design")
    print("   ✅ More flexible - can add any type of annotation")
    print("   ✅ Shows the power of combining create_path_map() + set_path()")
    print("   ✅ Follows the Unix philosophy: do one thing well, then combine")
    
    print("\n🔧 Best Practice:")
    print("   Use create_path_map() to find all paths, then set_path() to annotate")
    print("   This approach scales to any type of data structure modification!")
    
    print("\n📚 Available utilities:")
    print("   • create_path_map() - See all available paths")
    print("   • add_path_annotations_using_set_path() - Automated path annotation")
    print("   • extract_paths_from_results() - Get paths from annotated results")
    print("   • set_path() - The fundamental building block for data modification")


if __name__ == "__main__":
    main()