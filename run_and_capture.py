#!/usr/bin/env python3
"""
Execute the test and capture output to a file since bash is broken.
"""

import subprocess
import sys
import os

def run_test():
    try:
        # Change to project directory
        os.chdir('/Users/franksiebenlist/Documents/GitHub/hastra-fm-mcp')
        
        # Run the test script directly with Python
        result = subprocess.run([
            sys.executable, 'test_wildcard_fix.py'
        ], capture_output=True, text=True, timeout=30)
        
        # Write output to file
        with open('captured_output.txt', 'w') as f:
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\n\nSTDERR:\n")
            f.write(result.stderr)
            f.write(f"\n\nReturn code: {result.returncode}")
        
        print("Test executed and output captured to captured_output.txt")
        return result.returncode == 0
        
    except Exception as e:
        with open('captured_output.txt', 'w') as f:
            f.write(f"Error running test: {e}")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    run_test()