#!/usr/bin/env python3
"""
Example demonstrating how to use path-aware test data generation for jqpy.

This shows how developers can easily create test data with embedded path
information to make jq operations completely transparent and debuggable.
"""

# Import the path-aware utilities from jqpy
from src.jqpy.traverse_utils import make_path_aware, PATH_AWARE_TEST_DATA
from src.jqpy import get_path
import json


def demonstrate_basic_usage():
    """Show basic path-aware data creation and usage."""
    print("=== BASIC PATH-AWARE USAGE ===\n")
    
    # Create your test data as usual
    my_data = {
        "company": "TechCorp",
        "employees": [
            {"name": "Alice", "department": "Engineering", "salary": 90000},
            {"name": "Bob", "department": "Marketing", "salary": 75000},
            {"name": "Charlie", "department": "Engineering", "salary": 85000}
        ]
    }
    
    print("Original data:")
    print(json.dumps(my_data, indent=2))
    
    # Transform to path-aware format - this is all you need to do!
    path_aware_data = make_path_aware(my_data)
    
    print("\nPath-aware version:")
    print(json.dumps(path_aware_data, indent=2))
    

def demonstrate_jq_operations():
    """Show how path-aware data makes jq operations transparent."""
    print("\n=== JQ OPERATIONS WITH PATH TRACING ===\n")
    
    # Create path-aware test data
    data = make_path_aware({
        "teams": [
            {
                "name": "Backend",
                "members": [
                    {"name": "Alice", "role": "Senior", "active": True},
                    {"name": "Bob", "role": "Junior", "active": False}
                ]
            },
            {
                "name": "Frontend", 
                "members": [
                    {"name": "Charlie", "role": "Lead", "active": True}
                ]
            }
        ]
    })
    
    # Operation 1: Get all team names
    print("1. Get team names: .teams[].name")
    team_names = list(get_path(data, '.teams[].name'))
    print(f"   Result: {team_names}")
    
    # Operation 2: Get team objects to see their paths
    print("\n2. Get team objects: .teams[]")
    teams = list(get_path(data, '.teams[]'))
    for team in teams:
        print(f"   Team '{team['name']}' found at path: {team['path']}")
    
    # Operation 3: Complex filtering
    print("\n3. Filter active senior members: .teams[].members[] | select(.active and .role == \"Senior\")")
    active_seniors = list(get_path(data, '.teams[].members[] | select(.active == true and .role == "Senior")'))
    for member in active_seniors:
        print(f"   {member['name']} ({member['role']}) at path: {member['path']}")
    
    # Operation 4: Array construction
    print("\n4. Collect all member names: [.teams[].members[].name]")
    all_names = list(get_path(data, '[.teams[].members[].name]'))
    print(f"   Collected names: {all_names[0]}")


def demonstrate_debugging_benefits():
    """Show how path-aware data helps with debugging."""
    print("\n=== DEBUGGING BENEFITS ===\n")
    
    # Create problematic test case
    data = make_path_aware({
        "departments": [
            {
                "name": "Engineering",
                "projects": [
                    {"name": "Project A", "status": "active"},
                    {"name": "Project B", "status": "completed"}
                ]
            },
            {
                "name": "Marketing",
                "projects": [
                    {"name": "Campaign X", "status": "active"}
                ]
            }
        ]
    })
    
    # Suppose we want only active projects
    print("Looking for active projects: .departments[].projects[] | select(.status == \"active\")")
    active_projects = list(get_path(data, '.departments[].projects[] | select(.status == "active")'))
    
    print("Active projects found:")
    for project in active_projects:
        print(f"   Project: {project['name']}")
        print(f"   Path: {project['path']} <- Shows exactly where this came from!")
        print(f"   Department: {project['path'].split('.')[2]} <- Easy to extract department index")
        print()
    
    print("🎯 With path-aware data, you can immediately see:")
    print("   ✅ Which specific objects were selected")
    print("   ✅ What path expression led to each result")
    print("   ✅ How to manually verify the operation")
    print("   ✅ Where to look if something goes wrong")


def demonstrate_prebuilt_datasets():
    """Show how to use pre-built test datasets."""
    print("\n=== PRE-BUILT TEST DATASETS ===\n")
    
    print("Available pre-built datasets:")
    for name in PATH_AWARE_TEST_DATA.keys():
        print(f"   - {name}")
    
    # Use a complex pre-built dataset
    print(f"\nUsing 'complex_nested' dataset:")
    complex_data = PATH_AWARE_TEST_DATA["complex_nested"]
    
    # Show its structure
    print("Structure preview:")
    print(f"   Root path: {complex_data['path']}")
    company = complex_data["company"]
    print(f"   Company path: {company['path']}")
    
    # Use it for testing
    all_teams = list(get_path(complex_data, '.company.departments[].teams[]'))
    print(f"\nFound {len(all_teams)} teams:")
    for team in all_teams:
        print(f"   {team['name']} at {team['path']}")


def main():
    """Run all demonstrations."""
    print("🚀 JQPY PATH-AWARE TEST DATA UTILITIES")
    print("=" * 60)
    
    demonstrate_basic_usage()
    demonstrate_jq_operations()
    demonstrate_debugging_benefits()
    demonstrate_prebuilt_datasets()
    
    print("\n" + "=" * 60)
    print("✨ SUMMARY")
    print("=" * 60)
    print("Path-aware test data makes jq operations completely transparent!")
    print()
    print("🔧 Quick Start:")
    print("   from src.jqpy.traverse_utils import make_path_aware")
    print("   path_aware_data = make_path_aware(your_test_data)")
    print()
    print("📚 Benefits:")
    print("   ✅ See exactly which objects are accessed")
    print("   ✅ Trace complex nested operations step-by-step")
    print("   ✅ Debug failures with complete visibility")
    print("   ✅ Learn jq syntax through clear examples")
    print("   ✅ Verify operations at both data and path levels")


if __name__ == "__main__":
    main()