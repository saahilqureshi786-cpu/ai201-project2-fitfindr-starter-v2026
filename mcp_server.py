"""
FitFindr MCP server.

Unit 4 exposes two FitFindr tools through MCP:

1. search_listings
2. create_fit_card

The agent calls these tools through mcp_client instead of importing their
implementations directly.
"""

from mcp.server.fastmcp import FastMCP

from tools import (
    search_listings as _search_listings_impl,
    create_fit_card as _create_fit_card_impl,
)


mcp = FastMCP(
    "fitfindr",
    log_level="WARNING",
)


@mcp.tool()
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search FitFindr thrift listings.

    Args:
        description: Clothing description or keywords to search for.
        size: Optional clothing size to require.
        max_price: Optional maximum price in dollars.

    Returns:
        Matching listing dictionaries ordered by relevance.
        Returns an empty list when nothing matches.
    """

    return _search_listings_impl(
        description,
        size,
        max_price,
    )


@mcp.tool()
def create_fit_card(
    outfit: str,
    new_item: dict,
) -> str:
    """
    Create a short social-style FitFindr caption.

    Args:
        outfit: The generated outfit suggestion.
        new_item: The selected thrift listing dictionary.

    Returns:
        A two-to-four sentence fit-card caption containing the selected
        item's title, price, platform, and outfit vibe.

        If the outfit is empty, returns a descriptive fallback message.
    """

    return _create_fit_card_impl(
        outfit,
        new_item,
    )


if __name__ == "__main__":
    mcp.run()