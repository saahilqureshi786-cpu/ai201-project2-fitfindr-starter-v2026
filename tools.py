"""
The three FitFindr tools.

Each tool can be called and tested independently:

    search_listings(description, size, max_price)  -> list[dict]
    suggest_outfit(new_item, wardrobe)             -> str
    create_fit_card(outfit, new_item)              -> str
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

_STOPWORDS = {
    "a",
    "an",
    "and",
    "the",
    "for",
    "with",
    "under",
    "over",
    "in",
    "of",
}


def _keywords(text: str) -> set[str]:
    """Return useful lowercase words for keyword matching."""
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {word for word in words if word not in _STOPWORDS and len(word) > 1}


def _size_tokens(size: str) -> set[str]:
    """Normalize a clothing size into comparable tokens."""
    cleaned = re.sub(r"\([^)]*\)", "", size or "")
    parts = re.split(r"[/,\s]+", cleaned.upper())

    return {part.strip() for part in parts if part.strip()}


def _size_matches(wanted: str, listing_size: str) -> bool:
    """
    Check sizes using whole tokens.

    This allows M to match S/M, but prevents S from accidentally
    matching something like US 9.
    """
    if not wanted:
        return True

    wanted_tokens = _size_tokens(wanted)
    listing_tokens = _size_tokens(listing_size)

    if any(token.startswith("ONE") for token in listing_tokens):
        return True

    return bool(wanted_tokens & listing_tokens)


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings for items matching a description and optional filters.

    Returns matching listing dictionaries, best match first.
    Returns [] when no listing matches.
    """

    listings = load_listings()
    query_words = _keywords(description)

    scored: list[tuple[int, dict]] = []

    for listing in listings:

        # Maximum-price filter
        if max_price is not None and listing["price"] > max_price:
            continue

        # Size filter
        if size is not None and not _size_matches(size, listing["size"]):
            continue

        searchable_text = " ".join(
            [
                listing.get("title", ""),
                listing.get("description", ""),
                listing.get("category", ""),
                " ".join(listing.get("style_tags", [])),
                " ".join(listing.get("colors", [])),
                listing.get("brand") or "",
                listing.get("platform", ""),
            ]
        )

        listing_words = _keywords(searchable_text)

        # Count how many query keywords appear in this listing.
        score = len(query_words & listing_words)

        # Do not return unrelated listings.
        if score == 0:
            continue

        scored.append((score, listing))

    # Highest-scoring listings first.
    scored.sort(key=lambda pair: pair[0], reverse=True)

    return [
        listing
        for _, listing in scored[: config.SEARCH_RESULT_LIMIT]
    ]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Suggest one or two outfits using the thrifted item and the user's wardrobe.

    If the wardrobe is empty, return general styling advice instead.
    """

    items = wardrobe.get("items", [])

    item_details = (
        f"Item: {new_item.get('title', 'Unknown item')}\n"
        f"Category: {new_item.get('category', '')}\n"
        f"Colors: {', '.join(new_item.get('colors', []))}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', []))}\n"
        f"Price: ${new_item.get('price', 0):.2f}\n"
    )

    if not items:
        prompt = f"""
You are helping someone style a thrifted clothing item.

{item_details}

The user does not have any wardrobe items available.

Suggest one or two practical ways to style this item using general clothing
categories such as shoes, bottoms, tops, or accessories.

Keep the answer concise and useful.
"""

        return generate(prompt)

    wardrobe_text = "\n".join(
        (
            f"- {item.get('name', 'Unnamed item')} "
            f"| category: {item.get('category', '')} "
            f"| colors: {', '.join(item.get('colors', []))} "
            f"| style: {', '.join(item.get('style_tags', []))}"
        )
        for item in items
    )

    prompt = f"""
You are helping someone create an outfit around a thrifted item.

Thrifted item:
{item_details}

The user's existing wardrobe:
{wardrobe_text}

Suggest one or two outfits.

Use and name specific pieces from the user's wardrobe.
Explain briefly why the pieces work together.
Keep the answer concise and practical.
"""

    return generate(prompt)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Create a short social-style caption about the thrift find.

    Returns a two-to-four sentence caption.
    If outfit is empty or whitespace, returns a descriptive message
    rather than raising an exception.
    """

    if not outfit or not outfit.strip():
        return (
            f"I found {new_item.get('title', 'this thrifted item')}, "
            "but I do not have an outfit suggestion to turn into a fit card yet."
        )

    title = new_item.get("title", "this thrift find")
    price = new_item.get("price", 0)
    platform = new_item.get("platform", "the resale platform")

    prompt = f"""
Write a short social-media-style caption someone would actually post about
this thrift find.

Item: {title}
Price: ${price:.2f}
Platform: {platform}

Outfit suggestion:
{outfit}

Requirements:
- Write 2 to 4 sentences.
- Mention the item.
- Mention the price exactly once.
- Mention the platform exactly once.
- Describe the vibe of the outfit.
- Make it sound like a real personal post, not a product listing.
"""

    return generate(prompt)