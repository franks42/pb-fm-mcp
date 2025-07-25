"""
Consolidated HTTP utilities and type definitions for the registry system.
All functions should use this centralized async_http_get_json implementation.
"""
from typing import Any, Union
import httpx


# Union type for mixed JSON values
JSONType = Union[str, int, float, bool, None, dict[str, Any], list[Any]]


async def async_http_get_json(
    url: str,
    params: dict | None = None,
    timeout: float = 10.0,
    connect_timeout: float = 5.0
) -> JSONType:
    """Make an async HTTP GET request and return JSON response.

    Args:
        url: The URL to send the GET request to
        params: Query parameters to include
        timeout: Total request timeout in seconds
        connect_timeout: Connection timeout in seconds

    Returns:
        JSON response data on success, or error dict with 'MCP-ERROR' key on failure
    """

    if params is None:
        params = {}

    timeout_config = httpx.Timeout(timeout, connect=connect_timeout)
    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient(timeout=timeout_config) as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            # Validate content type
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                return {"MCP-ERROR": f"Expected JSON, got {content_type}"}

            return response.json()

        except httpx.TimeoutException:
            return {"MCP-ERROR": "Network Error: Request timed out"}
        except httpx.HTTPStatusError as e:
            return {"MCP-ERROR": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"MCP-ERROR": f"Request error: {e}"}
        except ValueError as e:
            return {"MCP-ERROR": f"Invalid JSON response: {e}"}
        except Exception as e:
            return {"MCP-ERROR": f"Unknown exception raised: {e}"}