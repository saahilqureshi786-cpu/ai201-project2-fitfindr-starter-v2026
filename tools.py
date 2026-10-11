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


# ── Search helpers ────────────────────────────────────────────────────────────

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


_ITEM_TYPES = {
    "tee",
    "tshirt",
    "shirt",
    "top",
    "tank",
    "blouse",
    "hoodie",
    "sweater",
    "cardigan",
    "jacket",
    "coat",
    "blazer",
    "vest",
    "jeans",
    "pants",
    "trousers",
    "cargo",
    "skirt",
    "shorts",
    "dress",
    "gown",
    "sneakers",
    "shoes",
    "boots",
    "loafers",
    "heels",
    "hat",
    "cap",
    "beanie",
    "bag",
    "belt",
}


def _keywords(text: str) -> set[str]:
    """Return useful lowercase words for keyword matching."""

    words = re.findall(
        r"[a-z0-9]+",
        (text or "").lower(),
    )

    return {
        word
        for word in words
        if word not in _STOPWORDS
        and len(word) > 1
    }


def _size_tokens(size: str) -> set[str]:
    """Normalize a clothing size into comparable tokens."""

    cleaned = re.sub(
        r"\([^)]*\)",
        "",
        size or "",
    )

    parts = re.split(
        r"[/,\s]+",
        cleaned.upper(),
    )

    return {
        part.strip()
        for part in parts
        if part.strip()
    }


def _size_matches(
    wanted: str,
    listing_size: str,
) -> bool:
    """
    Compare clothing sizes using normalized whole tokens.

    This allows M to match S/M while preventing S from matching
    unrelated text such as US 9.
    """

    if not wanted:
        return True

    wanted_tokens = _size_tokens(wanted)
    listing_tokens = _size_tokens(listing_size)

    if any(
        token.startswith("ONE")
        for token in listing_tokens
    ):
        return True

    return bool(
        wanted_tokens
        & listing_tokens
    )


def _item_type_words(
    description: str,
) -> set[str]:
    """Return clothing/item-type words explicitly named in the query."""

    return {
        word
        for word in _keywords(description)
        if word in _ITEM_TYPES
    }


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search listings using description keywords and optional filters.

    Item-type words such as jacket, dress, tee, or sneakers receive
    extra weight so a query like "90s track jacket" prefers jackets
    instead of unrelated items that only happen to match "90s".

    Returns matching listing dictionaries ordered by relevance.
    Returns [] when nothing matches.
    """

    listings = load_listings()

    query_words = _keywords(description)
    type_words = _item_type_words(description)

    scored: list[tuple[int, dict]] = []

    for listing in listings:

        # Maximum-price filter
        if (
            max_price is not None
            and listing["price"] > max_price
        ):
            continue

        # Size filter
        if (
            size is not None
            and not _size_matches(
                size,
                listing["size"],
            )
        ):
            continue

        title_words = _keywords(
            listing.get(
                "title",
                "",
            )
        )

        description_words = _keywords(
            listing.get(
                "description",
                "",
            )
        )

        category_words = _keywords(
            listing.get(
                "category",
                "",
            )
        )

        style_words = _keywords(
            " ".join(
                listing.get(
                    "style_tags",
                    [],
                )
            )
        )

        color_words = _keywords(
            " ".join(
                listing.get(
                    "colors",
                    [],
                )
            )
        )

        brand_words = _keywords(
            listing.get("brand")
            or ""
        )

        platform_words = _keywords(
            listing.get(
                "platform",
                "",
            )
        )

        important_words = (
            title_words
            | category_words
            | style_words
        )

        all_words = (
            title_words
            | description_words
            | category_words
            | style_words
            | color_words
            | brand_words
            | platform_words
        )

        # If the user explicitly names an item type,
        # require that type in an important listing field.
        if (
            type_words
            and not (
                type_words
                & important_words
            )
        ):
            continue

        score = 0

        # Weighted matching.
        score += (
            4
            * len(
                query_words
                & title_words
            )
        )

        score += (
            3
            * len(
                query_words
                & category_words
            )
        )

        score += (
            3
            * len(
                query_words
                & style_words
            )
        )

        score += len(
            query_words
            & description_words
        )

        # Strong bonus for matching the requested item type.
        score += (
            6
            * len(
                type_words
                & important_words
            )
        )

        normalized_query = (
            description
            or ""
        ).strip().lower()

        if (
            normalized_query
            and normalized_query
            in listing.get(
                "title",
                "",
            ).lower()
        ):
            score += 10

        elif (
            normalized_query
            and normalized_query
            in listing.get(
                "description",
                "",
            ).lower()
        ):
            score += 4

        # Bonus when all query words appear somewhere.
        if (
            query_words
            and query_words.issubset(
                all_words
            )
        ):
            score += 5

        if score > 0:
            scored.append(
                (
                    score,
                    listing,
                )
            )

    scored.sort(
        key=lambda pair: (
            pair[0],
            -pair[1]["price"],
        ),
        reverse=True,
    )

    return [
        listing
        for _, listing
        in scored[
            : config.SEARCH_RESULT_LIMIT
        ]
    ]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(
    new_item: dict,
    wardrobe: dict,
) -> str:
    """
    Suggest one or two outfits using the thrifted item and the user's wardrobe.

    If the wardrobe is empty, return general styling advice instead.
    """

    items = wardrobe.get(
        "items",
        [],
    )

    item_details = (
        f"Item: "
        f"{new_item.get('title', 'Unknown item')}\n"
        f"Category: "
        f"{new_item.get('category', '')}\n"
        f"Colors: "
        f"{', '.join(new_item.get('colors', []))}\n"
        f"Style tags: "
        f"{', '.join(new_item.get('style_tags', []))}\n"
        f"Price: "
        f"${new_item.get('price', 0):.2f}\n"
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
            f"| category: "
            f"{item.get('category', '')} "
            f"| colors: "
            f"{', '.join(item.get('colors', []))} "
            f"| style: "
            f"{', '.join(item.get('style_tags', []))}"
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

def create_fit_card(
    outfit: str,
    new_item: dict,
) -> str:
    """
    Create a short social-style caption about the thrift find.

    Returns a two-to-four sentence caption.
    If outfit is empty or whitespace, returns a descriptive message
    instead of raising an exception.
    """

    if not outfit or not outfit.strip():
        return (
            f"I found "
            f"{new_item.get('title', 'this thrifted item')}, "
            "but I do not have an outfit suggestion "
            "to turn into a fit card yet."
        )

    title = new_item.get(
        "title",
        "this thrift find",
    )

    price = new_item.get(
        "price",
        0,
    )

    platform = new_item.get(
        "platform",
        "the resale platform",
    )

    exact_price = (
        f"${price:.2f}"
    )

    prompt = f"""
Write a short social-media-style caption someone would actually post about
this thrift find.

The following listing details must be preserved exactly:

Exact item title: {title}
Exact price: {exact_price}
Exact platform: {platform}

Outfit suggestion:
{outfit}

Requirements:
- Write 2 to 4 sentences.
- Include the exact item title "{title}" exactly as written.
- Include the exact price "{exact_price}" exactly once.
- Include the exact platform "{platform}" exactly once.
- Do not shorten, paraphrase, rename, or reformat those three listing details.
- Describe the vibe of the outfit.
- Make it sound like a real personal post, not a product listing.
"""

    return generate(prompt)