"""
Path-aware tests for the jqpy command-line interface.

This is a copy of test_cli.py but using test data with embedded path information
to make it easier to understand which elements are being processed and returned
by CLI operations. Compare with test_cli.py to see the difference in readability.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pytest

from src.jqpy.traverse_utils import make_path_aware, PATH_AWARE_TEST_DATA as PATH_AWARE_DATA

# Check if jq is available for comparison tests
JQ_AVAILABLE = False
try:
    subprocess.run(["jq", "--version"], 
                  capture_output=True, 
                  check=True)
    JQ_AVAILABLE = True
except (subprocess.SubprocessError, FileNotFoundError):
    JQ_AVAILABLE = False


def run_jqpy_path_aware(
    filter_expr: str,
    input_data: Optional[Union[str, Dict, List]] = None,
    args: Optional[List[str]] = None,
    input_file: Optional[str] = None,
) -> Tuple[str, str, int]:
    """Run jqpy with path-aware input data."""
    if args is None:
        args = []
    
    # Convert input data to path-aware format
    if isinstance(input_data, (dict, list)):
        input_data = make_path_aware(input_data)
    
    # Create a temporary file for input data if needed
    temp_file = None
    try:
        if input_data is not None and not input_file:
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as f:
                if isinstance(input_data, (dict, list)):
                    json.dump(input_data, f)
                else:
                    f.write(str(input_data))
                temp_file = f.name
            input_file = temp_file
        
        # Build the command
        cmd = [sys.executable, '-m', 'jqpy']
        
        # Add input file if specified
        if input_file:
            cmd.extend(['--argfile', input_file])
        
        # Add other arguments and filter expression
        cmd.extend(args)
        cmd.append(filter_expr)
        
        print(f"\\n=== Path-Aware CLI Test ===")
        print(f"Filter: {filter_expr}")
        print(f"Input data paths: {json.dumps(input_data, indent=2) if isinstance(input_data, (dict, list)) else input_data}")
        print(f"Command: {' '.join(cmd)}")
        
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        print(f"Output: {result.stdout!r}")
        if result.stderr:
            print(f"Error: {result.stderr!r}")
        print(f"Exit code: {result.returncode}")
        
        return result.stdout, result.stderr, result.returncode
        
    except Exception as e:
        print(f"Error in run_jqpy_path_aware: {e}")
        return "", str(e), 1
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)


class TestJQPYCLIPathAware(unittest.TestCase):
    """Test jqpy CLI with path-aware data for better debugging."""
    
    def test_basic_identity_path_aware(self):
        """Test basic identity filter with path-aware data."""
        # Original: {"name": "John", "age": 30}
        input_data = {"name": "John", "age": 30}
        
        stdout, stderr, code = run_jqpy_path_aware('.', input_data)
        
        self.assertEqual(code, 0, f"Command failed: {stderr}")
        result = json.loads(stdout.strip())
        
        # Result should be the path-aware version
        expected = {"path": ".", "name": "John", "age": 30}
        self.assertEqual(result, expected)
        
        print(f"Identity returned object with path: {result['path']}")
    
    def test_field_access_path_aware(self):
        """Test field access with path-aware data."""
        # Original: {"user": {"name": "John", "age": 30}}
        input_data = {
            "user": {
                "name": "John",
                "age": 30
            }
        }
        
        # Test accessing the user object
        stdout, stderr, code = run_jqpy_path_aware('.user', input_data)
        self.assertEqual(code, 0, f"Command failed: {stderr}")
        
        result = json.loads(stdout.strip())
        expected = {"path": ".user", "name": "John", "age": 30}
        self.assertEqual(result, expected)
        
        print(f"Field access .user returned object at path: {result['path']}")
        
        # Test accessing a nested field
        stdout, stderr, code = run_jqpy_path_aware('.user.name', input_data)
        self.assertEqual(code, 0, f"Command failed: {stderr}")
        
        result = stdout.strip().strip('"')  # Remove JSON quotes
        self.assertEqual(result, "John")
        
        print(f"Field access .user.name returned: {result}")
    
    def test_array_operations_path_aware(self):
        """Test array operations with path-aware data."""
        # Original: {"items": [1, 2, 3, 4, 5]}
        input_data = {"items": [1, 2, 3, 4, 5]}
        
        # Test array indexing
        stdout, stderr, code = run_jqpy_path_aware('.items[0]', input_data)
        self.assertEqual(code, 0, f"Command failed: {stderr}")
        
        result = int(stdout.strip())
        self.assertEqual(result, 1)
        print(f"Array index .items[0] returned: {result}")
        
        # Test array splat (streaming)
        stdout, stderr, code = run_jqpy_path_aware('.items[]', input_data)
        self.assertEqual(code, 0, f"Command failed: {stderr}")
        
        # Parse multiple JSON values from streaming output
        results = [int(line.strip()) for line in stdout.strip().split('\\n') if line.strip()]
        expected = [1, 2, 3, 4, 5]
        self.assertEqual(results, expected)
        print(f"Array splat .items[] returned streaming: {results}")
    
    def test_object_array_path_aware(self):
        """Test operations on arrays of objects with path-aware data."""
        # Original: {"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}
        input_data = {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ]
        }
        
        # Test getting user objects (streaming)
        stdout, stderr, code = run_jqpy_path_aware('.users[]', input_data)
        self.assertEqual(code, 0, f"Command failed: {stderr}")
        
        # Parse streaming JSON objects
        lines = [line.strip() for line in stdout.strip().split('\\n') if line.strip()]
        results = [json.loads(line) for line in lines]
        
        expected = [
            {"path": ".users[0]", "name": "Alice", "age": 30},
            {"path": ".users[1]", "name": "Bob", "age": 25}
        ]
        self.assertEqual(results, expected)
        
        print("User objects found at paths:")
        for user in results:
            print(f"  Path: {user['path']}, Name: {user['name']}")
        
        # Test getting just names (streaming)
        stdout, stderr, code = run_jqpy_path_aware('.users[].name', input_data)
        self.assertEqual(code, 0, f"Command failed: {stderr}")
        
        names = [line.strip().strip('"') for line in stdout.strip().split('\\n') if line.strip()]
        self.assertEqual(sorted(names), ["Alice", "Bob"])
        print(f"User names extracted: {names}")
    
    def test_array_construction_path_aware(self):
        """Test array construction with path-aware data."""
        # Original: {"numbers": [10, 20, 30], "users": [{"name": "Alice"}, {"name": "Bob"}]}
        input_data = {
            "numbers": [10, 20, 30],
            "users": [{"name": "Alice"}, {"name": "Bob"}]
        }
        
        # Test simple array construction
        stdout, stderr, code = run_jqpy_path_aware('[.numbers[]]', input_data)
        self.assertEqual(code, 0, f"Command failed: {stderr}")
        
        result = json.loads(stdout.strip())
        expected = [10, 20, 30]
        self.assertEqual(result, expected)
        print(f"Array construction [.numbers[]] collected: {result}")
        
        # Test mixed array construction
        stdout, stderr, code = run_jqpy_path_aware('[.numbers[0], .users[0].name]', input_data)
        self.assertEqual(code, 0, f"Command failed: {stderr}")
        
        result = json.loads(stdout.strip())
        expected = [10, "Alice"]
        self.assertEqual(result, expected)
        print(f"Mixed array construction collected: {result}")
    
    def test_filtering_path_aware(self):
        """Test filtering operations with path-aware data."""
        # Original: [{"name": "Alice", "age": 30, "active": true}, {"name": "Bob", "age": 25, "active": false}]
        input_data = [
            {"name": "Alice", "age": 30, "active": True},
            {"name": "Bob", "age": 25, "active": False},
            {"name": "Charlie", "age": 35, "active": True}
        ]
        
        # Test age filtering
        stdout, stderr, code = run_jqpy_path_aware('.[] | select(.age > 28)', input_data)
        self.assertEqual(code, 0, f"Command failed: {stderr}")
        
        # Parse streaming results
        lines = [line.strip() for line in stdout.strip().split('\\n') if line.strip()]
        results = [json.loads(line) for line in lines]
        
        # Should get Alice and Charlie
        expected_names = ["Alice", "Charlie"]
        result_names = [obj["name"] for obj in results]
        self.assertEqual(sorted(result_names), sorted(expected_names))
        
        print("Age filter (> 28) selected objects at paths:")
        for obj in results:
            print(f"  Path: {obj['path']}, Name: {obj['name']}, Age: {obj['age']}")
        
        # Test boolean filtering  
        stdout, stderr, code = run_jqpy_path_aware('.[] | select(.active)', input_data)
        self.assertEqual(code, 0, f"Command failed: {stderr}")
        
        lines = [line.strip() for line in stdout.strip().split('\\n') if line.strip()]
        active_results = [json.loads(line) for line in lines]
        
        active_names = [obj["name"] for obj in active_results]
        self.assertEqual(sorted(active_names), ["Alice", "Charlie"])
        
        print("Active filter selected objects at paths:")
        for obj in active_results:
            print(f"  Path: {obj['path']}, Name: {obj['name']}, Active: {obj['active']}")
    
    def test_deeply_nested_path_aware(self):
        """Test deeply nested access with path-aware data."""
        input_data = {
            "company": {
                "departments": [
                    {
                        "name": "Engineering",
                        "teams": [
                            {"name": "Backend", "members": ["Alice", "Bob"]},
                            {"name": "Frontend", "members": ["Charlie"]}
                        ]
                    },
                    {
                        "name": "Sales", 
                        "teams": [
                            {"name": "Enterprise", "members": ["Diana"]}
                        ]
                    }
                ]
            }
        }
        
        # Test deep nested access
        stdout, stderr, code = run_jqpy_path_aware('.company.departments[].teams[].name', input_data)
        self.assertEqual(code, 0, f"Command failed: {stderr}")
        
        team_names = [line.strip().strip('"') for line in stdout.strip().split('\\n') if line.strip()]
        expected = ["Backend", "Frontend", "Enterprise"]
        self.assertEqual(sorted(team_names), sorted(expected))
        
        print(f"Deep nested access found team names: {team_names}")
        
        # Test getting team objects to see their paths
        stdout, stderr, code = run_jqpy_path_aware('.company.departments[].teams[]', input_data)
        self.assertEqual(code, 0, f"Command failed: {stderr}")
        
        lines = [line.strip() for line in stdout.strip().split('\\n') if line.strip()]
        teams = [json.loads(line) for line in lines]
        
        print("Team objects found at paths:")
        for team in teams:
            print(f"  Path: {team['path']}, Team: {team['name']}")
    
    def test_aggregation_path_aware(self):
        """Test aggregation operations with path-aware data."""
        # Original: {"scores": [85, 92, 78, 96, 88]}
        input_data = {"scores": [85, 92, 78, 96, 88]}
        
        # Test array construction with aggregation
        stdout, stderr, code = run_jqpy_path_aware('[.scores[]] | add', input_data)
        self.assertEqual(code, 0, f"Command failed: {stderr}")
        
        result = int(stdout.strip())
        expected = sum([85, 92, 78, 96, 88])
        self.assertEqual(result, expected)
        print(f"Array construction + add: {result} (sum of .scores[])")
        
        # Test sorting
        stdout, stderr, code = run_jqpy_path_aware('[.scores[]] | sort', input_data)
        self.assertEqual(code, 0, f"Command failed: {stderr}")
        
        result = json.loads(stdout.strip())
        expected = sorted([85, 92, 78, 96, 88])
        self.assertEqual(result, expected)
        print(f"Array construction + sort: {result}")


def test_path_aware_readability_demo():
    """Demonstrate the readability improvement of path-aware tests."""
    print("\\n" + "="*60)
    print("PATH-AWARE TEST READABILITY DEMONSTRATION")
    print("="*60)
    
    # Show how path-aware data makes operations transparent
    input_data = {
        "departments": [
            {
                "name": "Engineering",
                "employees": [
                    {"name": "Alice", "role": "Senior"},
                    {"name": "Bob", "role": "Junior"}
                ]
            },
            {
                "name": "Sales",
                "employees": [
                    {"name": "Charlie", "role": "Manager"}
                ]
            }
        ]
    }
    
    print("\\nOriginal data structure:")
    print(json.dumps(input_data, indent=2))
    
    print("\\nPath-aware version:")
    path_aware_data = make_path_aware(input_data)
    print(json.dumps(path_aware_data, indent=2))
    
    print("\\nNow when we run: .departments[].employees[].name")
    print("We can see exactly which paths are being traversed!")


if __name__ == "__main__":
    # Run the readability demo
    test_path_aware_readability_demo()
    
    # Run specific tests
    test_suite = unittest.TestSuite()
    test_suite.addTest(TestJQPYCLIPathAware('test_basic_identity_path_aware'))
    test_suite.addTest(TestJQPYCLIPathAware('test_object_array_path_aware'))
    test_suite.addTest(TestJQPYCLIPathAware('test_filtering_path_aware'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)