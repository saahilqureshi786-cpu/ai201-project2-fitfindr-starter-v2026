"""
The FitFindr planning loop.

Unit 4:
- search_listings runs through MCP
- every tool call is traceable
- model failures return an actionable user message
- an empty size-constrained search retries once without the size filter
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
        "notice": None,
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
        description = description.replace(
            price_match.group(0),
            "",
        )

    if size_match:
        description = description.replace(
            size_match.group(0),
            "",
        )

    description = re.sub(
        r"\s+",
        " ",
        description,
    ).strip(" ,.-")

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """Run the FitFindr planning loop and return the finished session."""

    session = new_session(
        query,
        wardrobe,
    )

    session["parsed"] = parse_query(query)

    step = "search"
    count = 0

    while True:
        count += 1
        trace.check_iterations(count)

        if step == "search":
            parsed = session["parsed"]

            search_inputs = {
                "description": parsed["description"],
                "size": parsed["size"],
                "max_price": parsed["max_price"],
            }

            session["search_results"] = call_tool(
                "search_listings",
                search_inputs,
            )

            # Stretch feature:
            # If a size-constrained search returns nothing,
            # retry once without the size filter.
            if (
                not session["search_results"]
                and parsed["size"] is not None
            ):
                dropped_size = parsed["size"]

                trace.step(
                    "search_listings (via MCP)",
                    inputs=search_inputs,
                    returned=session["search_results"],
                    note=(
                        "no matches; retrying once without "
                        f"the size filter '{dropped_size}'"
                    ),
                )

                retry_inputs = {
                    "description": parsed["description"],
                    "size": None,
                    "max_price": parsed["max_price"],
                }

                session["search_results"] = call_tool(
                    "search_listings",
                    retry_inputs,
                )

                session["notice"] = (
                    f"No matches were found in size {dropped_size}, "
                    "so I retried without the size filter."
                )

                trace.step(
                    "search_listings retry (via MCP)",
                    inputs=retry_inputs,
                    returned=session["search_results"],
                    note=(
                        f"dropped size constraint '{dropped_size}'"
                    ),
                )

                if not session["search_results"]:
                    session["error"] = (
                        "I couldn't find a matching item. "
                        f"I retried without the size filter "
                        f"(dropped size {dropped_size}) and still "
                        "found nothing. Try changing the description "
                        "or maximum price."
                    )
                    return session

                session["selected_item"] = (
                    session["search_results"][0]
                )

                step = "outfit"
                continue

            # Standard empty-search branch when there was
            # no size constraint to loosen.
            if not session["search_results"]:
                trace.step(
                    "search_listings (via MCP)",
                    inputs=search_inputs,
                    returned=session["search_results"],
                    note=(
                        "branch: no matches, stopping before "
                        "suggest_outfit"
                    ),
                )

                session["error"] = (
                    "I couldn't find a matching item. "
                    "Try changing the description, size, "
                    "or maximum price."
                )
                return session

            trace.step(
                "search_listings (via MCP)",
                inputs=search_inputs,
                returned=session["search_results"],
                note=(
                    "matches found; selecting the first result"
                ),
            )

            session["selected_item"] = (
                session["search_results"][0]
            )

            step = "outfit"

        elif step == "outfit":
            outfit_inputs = {
                "new_item": session["selected_item"],
                "wardrobe_items": len(
                    session["wardrobe"].get(
                        "items",
                        [],
                    )
                ),
            }

            try:
                session["outfit_suggestion"] = suggest_outfit(
                    session["selected_item"],
                    session["wardrobe"],
                )

            except ModelUnavailable as exc:
                trace.step(
                    "suggest_outfit",
                    inputs=outfit_inputs,
                    returned="ModelUnavailable",
                    note=str(exc),
                )

                session["error"] = (
                    "The AI model couldn't be reached, "
                    "so I couldn't create an outfit suggestion. "
                    "Check your API key or internet connection, "
                    "then try again."
                )
                return session

            trace.step(
                "suggest_outfit",
                inputs=outfit_inputs,
                returned=session["outfit_suggestion"],
            )

            step = "fit_card"

        elif step == "fit_card":
            fit_card_inputs = {
                "outfit": session["outfit_suggestion"],
                "new_item": session["selected_item"],
            }

            try:
                session["fit_card"] = create_fit_card(
                    session["outfit_suggestion"],
                    session["selected_item"],
                )

            except ModelUnavailable as exc:
                trace.step(
                    "create_fit_card",
                    inputs=fit_card_inputs,
                    returned="ModelUnavailable",
                    note=str(exc),
                )

                session["error"] = (
                    "The AI model couldn't be reached while "
                    "creating the fit card. Check your API key "
                    "or internet connection, then try again."
                )
                return session

            trace.step(
                "create_fit_card",
                inputs=fit_card_inputs,
                returned=session["fit_card"],
            )

            return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["notice"]:
        print(f"  note: {session['notice']}")

    if session["error"]:
        print(f"  stopped: {session['error']}")
        return

    item = session["selected_item"] or {}

    print(
        f"  found:    {item.get('title')} — "
        f"${item.get('price')} on "
        f"{item.get('platform')}"
    )

    print(
        f"  outfit:   "
        f"{session['outfit_suggestion']}"
    )

    print(
        f"  fit card: "
        f"{session['fit_card']}"
    )


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")

    _show(
        run_agent(
            query=(
                "looking for a vintage "
                "graphic tee under $30"
            ),
            wardrobe=get_example_wardrobe(),
        )
    )

    print("\n=== A query it can't ===")

    _show(
        run_agent(
            query=(
                "designer ballgown "
                "size XXS under $5"
            ),
            wardrobe=get_example_wardrobe(),
        )
    )