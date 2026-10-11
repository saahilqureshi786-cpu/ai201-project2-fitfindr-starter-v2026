#!/usr/bin/env python3
"""
FitFindr — command line.

Examples:

    python app.py ask 'vintage graphic tee under $30'
    python app.py ask
    python app.py ask --empty-wardrobe
    python app.py listings
    python app.py fields
    python app.py examples

Add --trace to any ask command to print the planning loop step by step.
"""

import argparse
import sys

import config


EXAMPLE_QUERIES = [
    "vintage graphic tee under $30",
    "90s track jacket in size M",
    "silk slip dress in midi length under $40",
    "platform sneakers size 8",
    "denim jacket under $50",
    "designer ballgown size XXS under $5",
]


def cmd_fields(args):
    """Show fields available in listings and wardrobe data."""

    from utils.data_loader import (
        load_listings,
        get_example_wardrobe,
    )

    listing = load_listings()[0]

    print("A listing has these fields:\n")

    for key, value in listing.items():
        shown = str(value)

        if len(shown) > 58:
            shown = shown[:58] + "…"

        print(
            f"  {key:<14} "
            f"{type(value).__name__:<6} "
            f"{shown}"
        )

    item = get_example_wardrobe()["items"][0]

    print("\nA wardrobe item has these fields:\n")

    for key, value in item.items():
        shown = str(value)

        if len(shown) > 58:
            shown = shown[:58] + "…"

        print(
            f"  {key:<14} "
            f"{type(value).__name__:<6} "
            f"{shown}"
        )


def cmd_listings(args):
    """Browse listing data."""

    from utils.data_loader import load_listings

    listings = load_listings()

    if args.full:
        import json

        for listing in listings[: args.n]:
            print(
                json.dumps(
                    listing,
                    indent=2,
                )
            )
            print()

        return

    print(f"{len(listings)} listings.\n")

    print(
        f"{'id':<6}"
        f"{'price':>8}  "
        f"{'size':<22}"
        f"{'platform':<11}"
        "title"
    )

    print("-" * 92)

    for listing in listings[: args.n]:
        print(
            f"{str(listing['id']):<6}"
            f"{listing['price']:>8.2f}  "
            f"{str(listing['size']):<22}"
            f"{listing['platform']:<11}"
            f"{listing['title'][:38]}"
        )

    if len(listings) > args.n:
        print(
            f"\n… {len(listings) - args.n} more. "
            f"Use -n {len(listings)} to see them all."
        )


def cmd_examples(args):
    """Print useful example queries."""

    print("Queries worth trying:\n")

    for query in EXAMPLE_QUERIES[:-1]:
        print(
            f"  python app.py ask '{query}'"
        )

    print(
        "\nAnd one the data cannot match "
        "— this is the empty-search branch:\n"
    )

    print(
        f"  python app.py ask "
        f"'{EXAMPLE_QUERIES[-1]}'"
    )


def _ask_one(
    query,
    wardrobe,
    use_trace,
):
    """Run one FitFindr query."""

    from agent import run_agent
    import trace as trace_module

    if use_trace:
        trace_module.start_trace()

    session = run_agent(
        query,
        wardrobe,
    )

    print()

    # Unit 4 stretch:
    # Tell the user when a constraint was automatically loosened.
    if session.get("notice"):
        print(
            f"  Note: {session['notice']}"
        )
        print()

    if session["error"]:
        print(
            f"  {session['error']}"
        )

    else:
        item = (
            session["selected_item"]
            or {}
        )

        print(
            f"  Found:    "
            f"{item.get('title')} — "
            f"${item.get('price')} on "
            f"{item.get('platform')}"
        )

        print()

        print(
            f"  Outfit:   "
            f"{session['outfit_suggestion']}"
        )

        print()

        print(
            f"  Fit card: "
            f"{session['fit_card']}"
        )

    print()

    if use_trace:
        text = trace_module.get_trace()

        if not text:
            print(
                "  (--trace printed nothing. "
                "No trace steps were recorded.)\n"
            )

    return session


def cmd_ask(args):
    """Run FitFindr."""

    from utils.data_loader import (
        get_example_wardrobe,
        get_empty_wardrobe,
    )

    import generate

    wardrobe = (
        get_empty_wardrobe()
        if args.empty_wardrobe
        else get_example_wardrobe()
    )

    if args.empty_wardrobe:
        print(
            "(running with an empty wardrobe)"
        )

    try:
        if args.query:
            _ask_one(
                args.query,
                wardrobe,
                args.trace,
            )

        else:
            print(
                "Ask for something, or press Enter "
                "on an empty line to quit.\n"
            )

            while True:
                try:
                    query = input("> ").strip()

                except (
                    EOFError,
                    KeyboardInterrupt,
                ):
                    print()
                    break

                if not query:
                    break

                _ask_one(
                    query,
                    wardrobe,
                    args.trace,
                )

    finally:
        print(
            generate.usage()
        )


def build_parser():
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(
        prog="app.py",
        description="FitFindr",
        formatter_class=(
            argparse.RawDescriptionHelpFormatter
        ),
        epilog=__doc__,
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    p_fields = sub.add_parser(
        "fields",
        help="show fields in the project data",
    )

    p_fields.set_defaults(
        func=cmd_fields,
    )

    p_list = sub.add_parser(
        "listings",
        help="browse the listings data",
    )

    p_list.add_argument(
        "-n",
        type=int,
        default=15,
        help="how many listings to show",
    )

    p_list.add_argument(
        "--full",
        action="store_true",
        help="print complete listing records",
    )

    p_list.set_defaults(
        func=cmd_listings,
    )

    p_ex = sub.add_parser(
        "examples",
        help="show example queries",
    )

    p_ex.set_defaults(
        func=cmd_examples,
    )

    p_ask = sub.add_parser(
        "ask",
        help="run the FitFindr agent",
    )

    p_ask.add_argument(
        "query",
        nargs="?",
    )

    p_ask.add_argument(
        "--trace",
        action="store_true",
        help="print the loop step by step",
    )

    p_ask.add_argument(
        "--empty-wardrobe",
        action="store_true",
        help=(
            "run as a user with nothing "
            "saved in their wardrobe"
        ),
    )

    p_ask.set_defaults(
        func=cmd_ask,
    )

    return parser


def main():
    """FitFindr CLI entry point."""

    args = (
        build_parser()
        .parse_args()
    )

    try:
        args.func(args)

    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(130)

    except Exception as exc:
        print(
            f"\n{type(exc).__name__}: "
            f"{exc}\n",
            file=sys.stderr,
        )

        sys.exit(1)


if __name__ == "__main__":
    main()