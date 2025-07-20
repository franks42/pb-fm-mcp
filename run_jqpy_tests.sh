#!/bin/bash
# Run jqpy tests

# Change to the project root directory
cd "$(dirname "$0")"

# Run pytest on the jqpy test directory
python -m pytest tests/test_jqpy/ -v

# Exit with the pytest exit code
exit $?
