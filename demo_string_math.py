#!/usr/bin/env python3
"""
Demo script showcasing the new string and math operations in jqpy.
"""

from src.jqpy import get_path

def demo_string_operations():
    print("🔤 STRING OPERATIONS DEMO")
    print("=" * 50)
    
    # Split operation
    data = "apple,banana,cherry,date"
    result = list(get_path(data, 'split(",")'))
    print(f'"{data}" | split(",") → {result}')
    
    # Join operation
    data = ["apple", "banana", "cherry"]
    result = list(get_path(data, 'join(" & ")'))
    print(f'{data} | join(" & ") → {result}')
    
    # Case operations
    data = "Hello World"
    result = list(get_path(data, 'lowercase'))
    print(f'"{data}" | lowercase → {result}')
    
    result = list(get_path(data, 'uppercase'))
    print(f'"{data}" | uppercase → {result}')
    
    # String tests
    data = "Hello World"
    result = list(get_path(data, 'startswith("Hello")'))
    print(f'"{data}" | startswith("Hello") → {result}')
    
    result = list(get_path(data, 'endswith("World")'))
    print(f'"{data}" | endswith("World") → {result}')
    
    result = list(get_path(data, 'contains("llo")'))
    print(f'"{data}" | contains("llo") → {result}')
    
    # Trim operation
    data = "  Hello World  "
    result = list(get_path(data, 'trim'))
    print(f'"{data}" | trim → {result}')
    
    print()

def demo_math_operations():
    print("🔢 MATH OPERATIONS DEMO")
    print("=" * 50)
    
    # Add operation - numbers
    data = [1, 2, 3, 4, 5]
    result = list(get_path(data, 'add'))
    print(f'{data} | add → {result}')
    
    # Add operation - strings
    data = ["Hello", " ", "World", "!"]
    result = list(get_path(data, 'add'))
    print(f'{data} | add → {result}')
    
    # Add operation - arrays
    data = [[1, 2], [3, 4], [5, 6]]
    result = list(get_path(data, 'add'))
    print(f'{data} | add → {result}')
    
    # Min/Max operations
    data = [3, 1, 4, 1, 5, 9, 2, 6]
    result = list(get_path(data, 'min'))
    print(f'{data} | min → {result}')
    
    result = list(get_path(data, 'max'))
    print(f'{data} | max → {result}')
    
    # Sort operation
    data = [3, 1, 4, 1, 5, 9, 2, 6]
    result = list(get_path(data, 'sort'))
    print(f'{data} | sort → {result}')
    
    # Reverse operation
    data = [1, 2, 3, 4, 5]
    result = list(get_path(data, 'reverse'))
    print(f'{data} | reverse → {result}')
    
    # Unique operation
    data = [1, 2, 2, 3, 1, 4, 3, 5]
    result = list(get_path(data, 'unique'))
    print(f'{data} | unique → {result}')
    
    # Flatten operation
    data = [[1, 2], [3, 4], [5, 6]]
    result = list(get_path(data, 'flatten'))
    print(f'{data} | flatten → {result}')
    
    # Flatten with depth
    data = [[[1, 2]], [[3, 4]], [[5, 6]]]
    result = list(get_path(data, 'flatten(2)'))
    print(f'{data} | flatten(2) → {result}')
    
    print()

def demo_chained_operations():
    print("⛓️  CHAINED OPERATIONS DEMO")
    print("=" * 50)
    
    # String processing chain
    data = "  apple,banana,cherry,date  "
    result = list(get_path(data, 'trim | split(",") | sort'))
    print(f'"{data}" | trim | split(",") | sort → {result}')
    
    # Math processing chain
    data = [[1, 2], [3, 4], [5, 6]]
    result = list(get_path(data, 'flatten | add'))
    print(f'{data} | flatten | add → {result}')
    
    # Complex data processing
    data = {
        "users": [
            {"name": "Alice", "scores": [85, 92, 78]},
            {"name": "Bob", "scores": [90, 88, 95]},
            {"name": "Charlie", "scores": [82, 87, 91]}
        ]
    }
    result = list(get_path(data, 'users[].scores | flatten | sort | reverse'))
    print(f'Complex data | users[].scores | flatten | sort | reverse → {result}')
    
    print()

def demo_real_world_use_cases():
    print("🌍 REAL-WORLD USE CASES")
    print("=" * 50)
    
    # Data cleaning
    data = {
        "records": [
            {"name": "  John Doe  ", "email": "JOHN@EXAMPLE.COM"},
            {"name": "Jane Smith", "email": "jane@example.com"},
            {"name": "  Bob Johnson  ", "email": "BOB@EXAMPLE.COM"}
        ]
    }
    
    # Clean names
    result = list(get_path(data, 'records[].name | trim'))
    print(f'Clean names: {result}')
    
    # Normalize emails
    result = list(get_path(data, 'records[].email | lowercase'))
    print(f'Normalize emails: {result}')
    
    # CSV processing
    csv_data = "name,age,city\nJohn,30,NYC\nJane,25,LA\nBob,35,Chicago"
    result = list(get_path(csv_data, 'split("\n") | .[1:] | .[].split(",")'))
    print(f'Parse CSV data: {result}')
    
    # Statistical analysis
    scores = [85, 92, 78, 90, 88, 95, 82, 87, 91]
    result = list(get_path(scores, 'sort'))
    print(f'Sorted scores: {result}')
    
    result = list(get_path(scores, 'add'))
    total = result[0]
    average = total / len(scores)
    print(f'Total: {total}, Average: {average:.1f}')
    
    print()

if __name__ == "__main__":
    print("🎉 JQPY STRING & MATH OPERATIONS DEMO")
    print("=" * 50)
    print()
    
    demo_string_operations()
    demo_math_operations()
    demo_chained_operations()
    demo_real_world_use_cases()
    
    print("✅ Demo complete! These operations make jqpy much more powerful")
    print("   for real-world data processing and manipulation tasks.")