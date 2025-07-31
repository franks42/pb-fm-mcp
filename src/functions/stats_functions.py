"""
Statistics Functions for Provenance Blockchain

Functions for fetching blockchain statistics and token metrics.
All functions are decorated with @api_function to be automatically
exposed via both MCP and REST protocols.
"""

from typing import Any

import structlog

from registry import api_function
from utils import async_http_get_json, JSONType

# Set up logging
logger = structlog.get_logger()


@api_function(
    protocols=["mcp", "rest"],
    description="Fetch current HASH token statistics including supply, circulation, and staking data",
)
async def fetch_current_hash_statistics() -> JSONType:
    """
    Fetch the current overall statistics for the Provenance Blockchain's utility token HASH.

    Provides comprehensive statistics including supply, circulation, staking, and
    community pool data.
    Pie chart visualization also available at: https://explorer.provenance.io/network/token-stats

    Returns:
        Dictionary containing HASH statistics with the following attributes:
        - maxSupply: The total initial amount of all HASH minted
        - burned: The total amount of all burned HASH
        - currentSupply: Current total supply (maxSupply - burned)
        - circulation: Total amount of HASH in circulation
        - communityPool: HASH managed by Provenance Foundation for community
        - bonded: Total HASH delegated/staked with validators
        - locked: HASH locked in vesting schedules (calculated field)

    Raises:
        HTTPError: If the Provenance blockchain API is unavailable
    """
    url = "https://service-explorer.provenance.io/api/v3/utility_token/stats"
    response = await async_http_get_json(url)

    if response.get("MCP-ERROR"):
        return response

    # Calculate locked amount: currentSupply - circulation - communityPool - bonded
    try:
        locked_amount = (
            int(response["currentSupply"]["amount"])
            - int(response["circulation"]["amount"])
            - int(response["communityPool"]["amount"])
            - int(response["bonded"]["amount"])
        )

        response["locked"] = {"amount": locked_amount, "denom": "nhash"}
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Could not calculate locked amount: {e}")
        # Return response without locked field rather than failing

    return response


@api_function(
    protocols=["mcp", "rest"],
    path="/api/get_system_context",
    method="GET",
    tags=["system", "context"],
    description="Get essential system context for Figure Markets Exchange and Provenance Blockchain",
)
async def get_system_context() -> JSONType:
    """
    REQUIRED READING: Essential system context for the Figure Markets Exchange
    and the Provenance Blockchain that MUST be read before using any tools.

    Contains critical usage guidelines, data handling protocols, and server capabilities.

    Returns:
        Dictionary with attribute 'context' containing the markdown-formatted context description

    Raises:
        HTTPError: If the context documentation is unavailable
    """
    try:
        url = "https://raw.githubusercontent.com/franks42/FigureMarkets-MCP-Server/refs/heads/main/FigureMarketsContext.md"

        # Run sync HTTP call in thread pool to avoid event loop conflicts
        import httpx

        # Fetch context text using async httpx client
        async with httpx.AsyncClient() as client:
            client.headers["accept-encoding"] = "identity"
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            context_text = response.text

        return {"context": context_text}

    except Exception as e:
        logger.error(f"Could not fetch system context: {e}")
        return {"MCP-ERROR": f"System context fetch error: {e!s}"}
