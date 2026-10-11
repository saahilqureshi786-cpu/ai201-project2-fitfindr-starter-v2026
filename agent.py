"""
The FitFindr planning loop.

Unit 4 moves search_listings behind MCP. The other two tools remain direct
Python calls.

The agent:
1. Parses the user's query.
2. Searches listings through MCP.
3. Stops early if nothing matches.
4. Stores the selected item in session state.
5. Generates an outfit suggestion.
6. Generates a fit card.
"""

import re

import trace
from generate import ModelUnavailable
from mcp_client import call_tool
from tools import suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """Create a fresh session for one user interaction."""

    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


def parse_query(query: str) -> dict:
    """Extract description, size, and maximum price from a user query."""

    text = query.strip()

    price_match = re.search(
        r"(?:under|below|up to)\s*\$?(\d+(?:\.\d+)?)",
        text,
        re.IGNORECASE,
    )

    size_match = re.search(
        r"\bsize\s+([A-Za-z0-9/]+)",
        text,
        re.IGNORECASE,
    )

    max_price = float(price_match.group(1)) if price_match else None
    size = size_match.group(1) if size_match else None

    description = text

    if price_match:
        description = description.replace(price_match.group(0), "")

    if size_match:
        description = description.replace(size_match.group(0), "")

    description = re.sub(r"\s+", " ", description).strip(" ,.-")

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """Run the FitFindr planning loop and return the finished session."""

    session = new_session(query, wardrobe)

    session["parsed"] = parse_query(query)

    step = "search"
    count = 0

    while True:
        count += 1
        trace.check_iterations(count)

        if step == "search":
            parsed = session["parsed"]

            # Unit 4: search_listings now runs through MCP.
            session["search_results"] = call_tool(
                "search_listings",
                {
                    "description": parsed["description"],
                    "size": parsed["size"],
                    "max_price": parsed["max_price"],
                },
            )

            # Branch: stop if the search returned nothing.
            if not session["search_results"]:
                session["error"] = (
                    "I couldn't find a matching item. "
                    "Try changing the description, size, or maximum price."
                )
                return session

            session["selected_item"] = session["search_results"][0]
            step = "outfit"

        elif step == "outfit":
            session["outfit_suggestion"] = suggest_outfit(
                session["selected_item"],
                session["wardrobe"],
            )
            step = "fit_card"

        elif step == "fit_card":
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"],
                session["selected_item"],
            )
            return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(
            f"  fit_card is {session['fit_card']!r} "
            "— it should still be None here"
        )
        return

    item = session["selected_item"] or {}

    print(
        f"  found:    {item.get('title')} — "
        f"${item.get('price')} on {item.get('platform')}"
    )
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(
        run_agent(
            query="looking for a vintage graphic tee under $30",
            wardrobe=get_example_wardrobe(),
        )
    )

    print("\n=== A query it can't ===")
    _show(
        run_agent(
            query="designer ballgown size XXS under $5",
            wardrobe=get_example_wardrobe(),
        )
    )

    print(
        "\nThe second one should stop before the fit card. "
        "If both paths look the same,\n"
        "the branch isn't doing anything yet."
    )