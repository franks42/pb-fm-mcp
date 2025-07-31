from registry import api_function

@api_function(
    protocols=["mcp", "rest"],
    description="Test function with broken decorator",
    parameters={
        "test_param": {"type": "string", "description": "Test parameter"}
    }
)
def test_function_with_params(test_param: str) -> dict:
    return {"result": test_param}

@api_function(protocols=["mcp", "rest"])
def test_function_clean(test_param: str) -> dict:
    return {"result": test_param}
EOF < /dev/null