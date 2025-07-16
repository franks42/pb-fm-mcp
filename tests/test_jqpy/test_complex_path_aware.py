"""
Path-aware tests for complex jqpy operations.

This demonstrates how path-aware test data makes complex operations
much easier to understand and debug.
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.jqpy import get_path, parse_path
from src.jqpy.traverse_utils import make_path_aware, PATH_AWARE_TEST_DATA as PATH_AWARE_DATA


def test_complex_filtering_path_aware():
    """Test complex filtering with multiple conditions using path-aware data."""
    # Original complex dataset
    data = make_path_aware({
        "employees": [
            {"name": "Alice", "department": "Engineering", "salary": 90000, "active": True},
            {"name": "Bob", "department": "Engineering", "salary": 75000, "active": False}, 
            {"name": "Charlie", "department": "Sales", "salary": 80000, "active": True},
            {"name": "Diana", "department": "Marketing", "salary": 85000, "active": True},
            {"name": "Eve", "department": "Engineering", "salary": 95000, "active": True}
        ]
    })
    
    print("\\n=== Complex Filtering Demo ===")
    print("Dataset paths:")
    employees = list(get_path(data, '.employees[]'))
    for emp in employees:
        print(f"  {emp['path']}: {emp['name']} ({emp['department']}, ${emp['salary']}, active: {emp['active']})")
    
    # Filter: Engineering employees with high salary who are active
    result = list(get_path(data, '.employees[] | select(.department == "Engineering" and .salary > 80000 and .active == true)'))
    
    print("\\nFilter: Engineering + salary > 80k + active")
    print("Selected employees:")
    for emp in result:
        print(f"  {emp['path']}: {emp['name']} (${emp['salary']})")
    
    # Should get Alice and Eve
    expected_names = ["Alice", "Eve"]
    result_names = [emp["name"] for emp in result]
    assert sorted(result_names) == sorted(expected_names)


def test_nested_array_construction_path_aware():
    """Test nested array construction with path-aware data."""
    data = make_path_aware({
        "regions": [
            {
                "name": "North",
                "countries": [
                    {"name": "Canada", "cities": ["Toronto", "Vancouver"]},
                    {"name": "USA", "cities": ["New York", "Los Angeles"]}
                ]
            },
            {
                "name": "South", 
                "countries": [
                    {"name": "Brazil", "cities": ["São Paulo", "Rio"]}
                ]
            }
        ]
    })
    
    print("\\n=== Nested Array Construction Demo ===")
    
    # Show the structure with paths
    regions = list(get_path(data, '.regions[]'))
    for region in regions:
        print(f"Region {region['path']}: {region['name']}")
        countries = list(get_path(region, '.countries[]'))
        for country in countries:
            print(f"  Country {country['path']}: {country['name']} -> cities: {country['cities']}")
    
    # Collect all city names using array construction
    result = list(get_path(data, '[.regions[].countries[].cities[]]'))
    expected = [["Toronto", "Vancouver", "New York", "Los Angeles", "São Paulo", "Rio"]]
    assert result == expected
    
    print(f"\\nArray construction [.regions[].countries[].cities[]] collected: {result[0]}")
    
    # Collect country names grouped by region
    country_result = list(get_path(data, '[.regions[].countries[].name]'))
    expected_countries = [["Canada", "USA", "Brazil"]]
    assert country_result == expected_countries
    
    print(f"Country names [.regions[].countries[].name]: {country_result[0]}")


def test_object_construction_path_aware():
    """Test object construction with path-aware data."""
    data = make_path_aware({
        "products": [
            {"id": 1, "name": "laptop", "price": 1000, "category": "electronics"},
            {"id": 2, "name": "book", "price": 20, "category": "education"},
            {"id": 3, "name": "phone", "price": 800, "category": "electronics"}
        ]
    })
    
    print("\\n=== Object Construction Demo ===")
    
    # Show original products with paths
    products = list(get_path(data, '.products[]'))
    for product in products:
        print(f"Product {product['path']}: {product['name']} (${product['price']})")
    
    # Construct new objects with transformed data
    result = list(get_path(data, '.products[] | {product_name: .name, cost_usd: .price, type: .category}'))
    
    print("\\nObject construction result:")
    for i, obj in enumerate(result):
        print(f"  Object {i}: {obj}")
    
    expected = [
        {"product_name": "laptop", "cost_usd": 1000, "type": "electronics"},
        {"product_name": "book", "cost_usd": 20, "type": "education"},
        {"product_name": "phone", "cost_usd": 800, "type": "electronics"}
    ]
    assert result == expected


def test_multi_level_aggregation_path_aware():
    """Test multi-level aggregation operations with path-aware data."""
    data = make_path_aware({
        "sales": {
            "quarters": [
                {
                    "name": "Q1",
                    "months": [
                        {"name": "Jan", "revenue": 100000},
                        {"name": "Feb", "revenue": 120000},
                        {"name": "Mar", "revenue": 110000}
                    ]
                },
                {
                    "name": "Q2",
                    "months": [
                        {"name": "Apr", "revenue": 130000},
                        {"name": "May", "revenue": 125000},
                        {"name": "Jun", "revenue": 135000}
                    ]
                }
            ]
        }
    })
    
    print("\\n=== Multi-Level Aggregation Demo ===")
    
    # Show structure with paths
    quarters = list(get_path(data, '.sales.quarters[]'))
    for quarter in quarters:
        print(f"Quarter {quarter['path']}: {quarter['name']}")
        months = list(get_path(quarter, '.months[]'))
        for month in months:
            print(f"  Month {month['path']}: {month['name']} -> ${month['revenue']}")
    
    # Aggregate all monthly revenues
    total_result = list(get_path(data, '[.sales.quarters[].months[].revenue] | add'))
    expected_total = sum([100000, 120000, 110000, 130000, 125000, 135000])
    assert total_result == [expected_total]
    
    print(f"\\nTotal revenue across all months: ${total_result[0]}")
    
    # Get highest revenue month
    max_result = list(get_path(data, '[.sales.quarters[].months[].revenue] | max'))
    expected_max = 135000
    assert max_result == [expected_max]
    
    print(f"Highest monthly revenue: ${max_result[0]}")
    
    # Get quarterly totals using more complex construction
    quarterly_totals = []
    for quarter in quarters:
        quarter_total = list(get_path(quarter, '[.months[].revenue] | add'))
        quarterly_totals.append({
            "quarter": quarter["name"],
            "total": quarter_total[0],
            "quarter_path": quarter["path"]
        })
    
    print("\\nQuarterly totals:")
    for qt in quarterly_totals:
        print(f"  {qt['quarter']} (from {qt['quarter_path']}): ${qt['total']}")


def test_path_tracing_complex_operations():
    """Test that shows how paths help trace complex operations."""
    data = make_path_aware({
        "university": {
            "colleges": [
                {
                    "name": "Engineering",
                    "departments": [
                        {
                            "name": "Computer Science",
                            "courses": [
                                {"code": "CS101", "students": 45},
                                {"code": "CS201", "students": 32}
                            ]
                        },
                        {
                            "name": "Electrical Engineering", 
                            "courses": [
                                {"code": "EE101", "students": 38}
                            ]
                        }
                    ]
                },
                {
                    "name": "Liberal Arts",
                    "departments": [
                        {
                            "name": "History",
                            "courses": [
                                {"code": "HIST101", "students": 28}
                            ]
                        }
                    ]
                }
            ]
        }
    })
    
    print("\\n=== Path Tracing Complex Operations ===")
    
    # Trace a complex path to see exactly what gets selected
    print("Tracing path: .university.colleges[].departments[].courses[]")
    
    # First level: colleges
    colleges = list(get_path(data, '.university.colleges[]'))
    print("\\nColleges found:")
    for college in colleges:
        print(f"  {college['path']}: {college['name']}")
    
    # Second level: departments
    departments = list(get_path(data, '.university.colleges[].departments[]'))
    print("\\nDepartments found:")
    for dept in departments:
        print(f"  {dept['path']}: {dept['name']}")
    
    # Third level: courses
    courses = list(get_path(data, '.university.colleges[].departments[].courses[]'))
    print("\\nCourses found:")
    for course in courses:
        print(f"  {course['path']}: {course['code']} ({course['students']} students)")
    
    # Now do operations that would be hard to trace without paths
    large_classes = list(get_path(data, '.university.colleges[].departments[].courses[] | select(.students > 30)'))
    print("\\nLarge classes (> 30 students):")
    for course in large_classes:
        print(f"  {course['path']}: {course['code']} ({course['students']} students)")
    
    # Array construction with filtering
    large_class_codes = list(get_path(data, '[.university.colleges[].departments[].courses[] | select(.students > 30) | .code]'))
    print(f"\\nLarge class codes collected: {large_class_codes[0]}")
    
    expected_codes = ["CS101", "CS201", "EE101"]
    assert large_class_codes[0] == expected_codes


if __name__ == "__main__":
    print("=== PATH-AWARE COMPLEX OPERATIONS DEMO ===")
    
    test_complex_filtering_path_aware()
    test_nested_array_construction_path_aware() 
    test_object_construction_path_aware()
    test_multi_level_aggregation_path_aware()
    test_path_tracing_complex_operations()
    
    print("\\n=== All complex operations traced successfully with paths! ===")