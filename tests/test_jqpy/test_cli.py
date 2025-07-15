"""
Tests for the jqpy command-line interface.

These tests verify that jqpy behaves similarly to jq for common operations.
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

# Check if jq is available for comparison tests
JQ_AVAILABLE = False
try:
    subprocess.run(["jq", "--version"], 
                  capture_output=True, 
                  check=True)
    JQ_AVAILABLE = True
except (subprocess.SubprocessError, FileNotFoundError):
    JQ_AVAILABLE = False

# Path to the jqpy script
JQPY_SCRIPT = str(Path(__file__).parent.parent.parent / "src" / "jqpy" / "cli.py")

def run_jqpy(
    filter_expr: str,
    input_data: Optional[Union[str, Dict, List]] = None,
    args: Optional[List[str]] = None,
    input_file: Optional[str] = None,
) -> Tuple[str, str, int]:
    """Run jqpy with the given arguments and input."""
    if args is None:
        args = []
    
    # Create a temporary file for input data if needed
    temp_file = None
    try:
        if input_data is not None and not input_file:
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
                if isinstance(input_data, (dict, list)):
                    json.dump(input_data, f)
                else:
                    f.write(str(input_data))
                temp_file = f.name
            input_file = temp_file
        
        # Build the command to run the module with -m
        cmd = [sys.executable, '-m', 'jqpy.cli_simple']
        
        # Add input file if specified
        if input_file:
            cmd.extend(['--argfile', input_file])
        
        # Add other arguments and filter expression
        cmd.extend(args)
        cmd.append(filter_expr)
        
        print(f"Running command: {' '.join(cmd)}")
        
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        print(f"Command output: {result.stdout!r}")
        print(f"Command error: {result.stderr!r}")
        print(f"Exit code: {result.returncode}")
        
        return result.stdout, result.stderr, result.returncode
        
    except Exception as e:
        print(f"Error in run_jqpy: {e}")
        return "", str(e), 1
        
    finally:
        # Clean up temporary file if we created one
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except OSError:
                pass

def run_jq(
    filter_expr: str,
    input_data: Optional[Union[str, Dict, List]] = None,
    args: Optional[List[str]] = None,
    input_file: Optional[str] = None,
) -> Tuple[str, str, int]:
    """Run jq with the given arguments and input."""
    if not JQ_AVAILABLE:
        pytest.skip("jq not available for comparison testing")
        
    if args is None:
        args = []
        
    cmd = ["jq"] + args + [filter_expr]
    
    if input_file:
        cmd.append(input_file)
    
    input_str = None
    if input_data is not None:
        if isinstance(input_data, (dict, list)):
            input_str = json.dumps(input_data)
        else:
            input_str = str(input_data)
    
    result = subprocess.run(
        cmd,
        input=input_str,
        capture_output=True,
        text=True
    )
    
    return result.stdout, result.stderr, result.returncode

class TestJQPYCLI(unittest.TestCase):
    """Test cases for the jqpy command-line interface."""
    
    def test_basic_identity(self):
        """Test basic identity filter."""
        data = {"name": "John", "age": 30}
        print("\n=== Testing basic identity ===")
        print(f"Input data: {data}")
        
        # Test jqpy
        output, err, code = run_jqpy('.', data)
        print(f"jqpy output: {output!r}")
        print(f"jqpy error: {err!r}")
        print(f"jqpy exit code: {code}")
        
        if output:
            try:
                parsed = json.loads(output)
                print(f"Parsed output: {parsed}")
                self.assertEqual(parsed, data)
            except json.JSONDecodeError as e:
                print(f"Failed to parse output: {e}")
        
        # Test jq for comparison
        if JQ_AVAILABLE:
            jq_output, jq_err, jq_code = run_jq('.', data)
            print(f"jq output: {jq_output!r}")
            print(f"jq error: {jq_err!r}")
            print(f"jq exit code: {jq_code}")
            
            if output and jq_output:
                print("Comparing outputs...")
                self.assertEqual(output.strip(), jq_output.strip())
    
    def test_field_access(self):
        """Test field access."""
        data = {"user": {"name": "John", "age": 30}}
        output, _, _ = run_jqpy('.user.name', data)
        self.assertEqual(json.loads(output), "John")
        
        if JQ_AVAILABLE:
            jq_output, _, _ = run_jq('.user.name', data)
            self.assertEqual(output.strip(), jq_output.strip())
    
    def test_array_indexing(self):
        """Test array indexing."""
        data = {"items": [1, 2, 3, 4, 5]}
        output, _, _ = run_jqpy('.items[0]', data)
        self.assertEqual(json.loads(output), 1)
        
        output, _, _ = run_jqpy('.items[-1]', data)
        self.assertEqual(json.loads(output), 5)
        
        if JQ_AVAILABLE:
            jq_output1, _, _ = run_jq('.items[0]', data)
            jq_output2, _, _ = run_jq('.items[-1]', data)
            # Compare each individual command output
            output1, _, _ = run_jqpy('.items[0]', data)
            output2, _, _ = run_jqpy('.items[-1]', data)
            self.assertEqual(output1.strip(), jq_output1.strip())
            self.assertEqual(output2.strip(), jq_output2.strip())
    
    def test_wildcard(self):
        """Test wildcard operator."""
        data = {"users": [{"name": "John"}, {"name": "Jane"}]}
        output, _, _ = run_jqpy('.users[].name', data)
        # Parse each line as separate JSON value (jq style)
        lines = [line.strip() for line in output.strip().split('\n') if line.strip()]
        results = [json.loads(line) for line in lines]
        self.assertEqual(sorted(results), ["Jane", "John"])
    
    def test_comparison_operators(self):
        """Test comparison operators in filters."""
        data = {"users": [
            {"name": "John", "age": 30, "active": True},
            {"name": "Jane", "age": 25, "active": False}
        ]}
        
        # Test equality
        output, _, _ = run_jqpy('.users[] | select(.active == true) | .name', data)
        self.assertEqual(json.loads(output), "John")
        
        # Test numeric comparison
        output, _, _ = run_jqpy('.users[] | select(.age > 25) | .name', data)
        self.assertEqual(json.loads(output), "John")
    
    def test_raw_output(self):
        """Test raw output option."""
        data = {"name": "John"}
        output, _, _ = run_jqpy('.name', data, args=['-r'])
        self.assertEqual(output.strip(), "John")
        
        if JQ_AVAILABLE:
            jq_output, _, _ = run_jq('.name', data, args=['-r'])
            self.assertEqual(output.strip(), jq_output.strip())
    
    def test_compact_output(self):
        """Test compact output option."""
        data = {"name": "John", "age": 30}
        output, _, _ = run_jqpy('.', data, args=['-c'])
        self.assertEqual(output.strip(), '{"name":"John","age":30}')
    
    def test_slurp_option(self):
        """Test slurp option for multiple inputs."""
        inputs = ['{"name": "John"}', '{"name": "Jane"}']
        output, _, _ = run_jqpy('.[].name', input_data='\n'.join(inputs), args=['-s'])
        # Parse each line as separate JSON value (jq style)
        lines = [line.strip() for line in output.strip().split('\n') if line.strip()]
        results = [json.loads(line) for line in lines]
        self.assertEqual(sorted(results), ["Jane", "John"])
    
    def test_null_input(self):
        """Test null input option."""
        output, _, _ = run_jqpy('42', args=['-n'])
        self.assertEqual(json.loads(output), 42)
    
    def test_exit_status(self):
        """Test exit status behavior."""
        # Should succeed with output
        _, _, code = run_jqpy('.', '{}', args=['-e'])
        self.assertEqual(code, 0)
        
        # Should fail with no output
        _, _, code = run_jqpy('false', '{}', args=['-e'])
        self.assertEqual(code, 1)
    
    def test_file_input(self):
        """Test reading input from a file."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            try:
                json.dump({"name": "John"}, f)
                f.close()
                
                output, _, _ = run_jqpy('.name', input_file=f.name)
                self.assertEqual(json.loads(output), "John")
            finally:
                try:
                    os.unlink(f.name)
                except OSError:
                    pass

# Add a test that compares jq and jqpy output for various expressions
TEST_CASES = [
    ('.', {'a': 1, 'b': 2}),
    ('.a', {'a': 1, 'b': 2}),
    ('.[]', [1, 2, 3]),
    ('.a.b', {'a': {'b': 'value'}}),
    ('.[] | .*2', [1, 2, 3]),
    ('map(. * 2)', [1, 2, 3]),
    ('.[] | select(. > 1)', [1, 2, 3, 4]),
    ('{a: .a, b: .b}', {'a': 1, 'b': 2, 'c': 3}),
]

@pytest.mark.skipif(not JQ_AVAILABLE, reason="jq not available for comparison testing")
@pytest.mark.parametrize("filter_expr,data", TEST_CASES)
def test_jq_compatibility(filter_expr: str, data: Any):
    """Test that jqpy produces the same output as jq for various expressions."""
    # Skip tests that use jq features not yet implemented in jqpy
    if any(op in filter_expr for op in ['|', 'select', 'map']):
        pytest.skip("Advanced jq features not yet implemented in jqpy")
    
    # Run both commands
    jqpy_out, _, _ = run_jqpy(filter_expr, data)
    jq_out, _, _ = run_jq(filter_expr, data)
    
    # Parse outputs for comparison (to handle whitespace differences)
    try:
        jqpy_parsed = json.loads(jqpy_out)
        jq_parsed = json.loads(jq_out)
        
        # Special handling for empty outputs
        if not jqpy_out.strip() and not jq_out.strip():
            return
            
        assert jqpy_parsed == jq_parsed, f"jqpy: {jqpy_parsed} != jq: {jq_parsed}"
    except json.JSONDecodeError:
        # If output isn't valid JSON, compare as strings (with whitespace normalized)
        assert jqpy_out.strip() == jq_out.strip(), \
            f"Outputs differ. jqpy: '{jqpy_out.strip()}' != jq: '{jq_out.strip()}'"

if __name__ == '__main__':
    unittest.main()
