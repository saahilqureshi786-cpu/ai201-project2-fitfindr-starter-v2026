"""
FitFindr MCP server.

Unit 4 moves one FitFindr tool behind MCP so the agent calls it through
a standard tool interface instead of importing the function directly.

The tool exposed here is search_listings.
"""

from mcp.server.fastmcp import FastMCP

from tools import search_listings as _search_listings_impl


mcp = FastMCP("fitfindr", log_level="WARNING")


@mcp.tool()
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search FitFindr thrift listings for items matching a clothing description.

    Args:
        description: Clothing description or keywords to search for.
        size: Optional clothing size to require.
        max_price: Optional maximum price in dollars.

    Returns:
        A list of matching listing dictionaries ordered by relevance.
        Returns an empty list when no listings match the requested constraints.
    """
    return _search_listings_impl(
        description,
        size,
        max_price,
    )


if __name__ == "__main__":
    mcp.run()