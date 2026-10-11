"""
Evaluation scenarios for FitFindr — Unit 4.

Each scenario maps directly to one acceptance criterion in criteria.md.

run_eval.py executes every scenario five times with caching disabled.
"""

SCENARIOS = [
    {
        # Criterion 1:
        # A matching query should complete the full three-tool path.
        "name": "matching query completes all three tools",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # Criterion 2:
        # An impossible query should stop after search_listings.
        "name": "impossible query stops before second tool",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # Criterion 3:
        # The selected search result should remain the same item
        # when it moves through session state to suggest_outfit.
        "name": "selected item preserved through session state",
        "query": "90s track jacket in size M",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Criterion 4:
        # The final fit card should mention the selected item,
        # its price, and its resale platform.
        "name": "fit card includes key listing details",
        "query": "denim jacket under $50",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # Criterion 5:
        # Every search result must respect the user's maximum price.
        "name": "search respects maximum price",
        "query": "graphic tee under $25",
        "wardrobe": "example",
        "criterion": 5,
    },
]


WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """
    Validate the evaluation scenarios before a long test run.

    Returns a list of problems. An empty list means the scenarios are valid.
    """

    problems = []

    seen_criteria = set()

    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name", "").strip():
            problems.append(f"scenario {i} has no name")

        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")

        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe "
                f"{scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )

        criterion = scenario.get("criterion")

        if criterion not in {1, 2, 3, 4, 5}:
            problems.append(
                f"scenario {i} has invalid criterion {criterion!r}"
            )
        elif criterion in seen_criteria:
            problems.append(
                f"criterion {criterion} appears more than once"
            )
        else:
            seen_criteria.add(criterion)

    missing = {1, 2, 3, 4, 5} - seen_criteria

    for criterion in sorted(missing):
        problems.append(
            f"criterion {criterion} has no evaluation scenario"
        )

    return problems