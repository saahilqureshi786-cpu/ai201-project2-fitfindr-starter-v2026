"""
Evaluation scenarios for FitFindr — Unit 4.

The first five scenarios map directly to the five acceptance criteria
written in criteria.md during Unit 3.

The final scenario is a Unit 4 diagnostic/stretch scenario used to measure
the retry-without-size behavior and the search-ranking improvement.
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
        # An impossible query should stop before suggest_outfit.
        "name": "impossible query stops before second tool",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # Criterion 3:
        # The selected search result should remain the same item
        # when it moves through session state.
        "name": "selected item preserved through session state",
        "query": "90s track jacket in size M",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Criterion 4:
        # The fit card should contain the selected item,
        # price, and platform.
        "name": "fit card includes key listing details",
        "query": "denim jacket under $50",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # Criterion 5:
        # Every result must respect the user's maximum price.
        "name": "search respects maximum price",
        "query": "graphic tee under $25",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        # Unit 4 stretch / diagnostic:
        #
        # There is a 90s track jacket in the data, but not in XS.
        # The first search should return no results.
        #
        # The agent should then retry once without the size filter.
        # After the search-ranking improvement, the selected item
        # should be:
        #
        # 90s Track Jacket — Navy/White Stripe
        #
        # This is intentionally not one of the original five criteria.
        "name": "retry without size selects requested item type",
        "query": "90s track jacket size XS",
        "wardrobe": "example",
        "criterion": None,
    },
]


WARDROBES = (
    "example",
    "empty",
)


def validate() -> list[str]:
    """
    Validate the evaluation scenarios before running the full test.

    The original five grading criteria must each appear exactly once.

    Additional diagnostic scenarios are allowed when criterion is None.
    """

    problems = []
    seen_criteria = set()

    for i, scenario in enumerate(
        SCENARIOS,
        1,
    ):
        if not scenario.get(
            "name",
            "",
        ).strip():
            problems.append(
                f"scenario {i} has no name"
            )

        if not scenario.get(
            "query",
            "",
        ).strip():
            problems.append(
                f"scenario {i} has no query"
            )

        if scenario.get(
            "wardrobe"
        ) not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe "
                f"{scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )

        criterion = scenario.get(
            "criterion"
        )

        # None is allowed for diagnostic scenarios.
        if criterion is None:
            continue

        if criterion not in {
            1,
            2,
            3,
            4,
            5,
        }:
            problems.append(
                f"scenario {i} has invalid "
                f"criterion {criterion!r}"
            )

            continue

        if criterion in seen_criteria:
            problems.append(
                f"criterion {criterion} "
                "appears more than once"
            )

        else:
            seen_criteria.add(
                criterion
            )

    missing = (
        {1, 2, 3, 4, 5}
        - seen_criteria
    )

    for criterion in sorted(
        missing
    ):
        problems.append(
            f"criterion {criterion} "
            "has no evaluation scenario"
        )

    return problems