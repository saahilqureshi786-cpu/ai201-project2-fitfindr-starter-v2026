"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""
import re
import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


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
# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """Run the FitFindr planning loop and return the finished session."""

    session = new_session(query, wardrobe)

    # Parse the user's query and store it in session state.
    session["parsed"] = parse_query(query)

    step = "search"
    count = 0

    while True:
        count += 1
        trace.check_iterations(count)

        if step == "search":
            parsed = session["parsed"]

            session["search_results"] = search_listings(
                parsed["description"],
                parsed["size"],
                parsed["max_price"],
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
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
