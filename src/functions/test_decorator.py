"""Test file for decorator syncing"""

from registry import api_function

@api_function(protocols=["mcp", "rest"])
def test_function_broken(test_param: str) -> dict:
    """Test function with broken decorator format"""
    return {"result": test_param}

@api_function(protocols=["mcp", "rest"])
def test_function_correct(test_param: str) -> dict:
    """Test function with correct decorator format"""
    return {"result": test_param}