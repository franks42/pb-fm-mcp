#!/bin/bash
cd /Users/franksiebenlist/Documents/GitHub/hastra-fm-mcp
uv run pytest tests/test_jqpy/test_traversal.py::test_wildcard_dict_access -v