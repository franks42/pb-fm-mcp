from registry import api_function

@api_function(protocols=["mcp", "rest"])
def test_function(test_param: str) -> dict:
    return {"result": test_param}
EOF < /dev/null