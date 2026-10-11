"""
A trace: a printed record of what the agent did, step by step, in order.

Tracing is activated by start_trace(). Normal runs stay quiet.
"""

import config

_lines: list[str] = []
_step_number = 0
_enabled = False


def start_trace() -> None:
    """Clear and enable tracing for one run."""
    global _step_number, _enabled

    _lines.clear()
    _step_number = 0
    _enabled = True


def step(name: str, inputs=None, returned=None, note: str = "") -> None:
    """Record one step of the agent loop."""

    global _step_number

    if not _enabled:
        return

    _step_number += 1

    line = f"[{_step_number}] {name}"

    if inputs is not None:
        line += f"\n      in:  {_short(inputs)}"

    if returned is not None:
        line += f"\n      out: {_short(returned)}"

    if note:
        line += f"\n      →    {note}"

    _lines.append(line)
    print(line, flush=True)


def get_trace() -> str:
    """Return the complete trace as text."""
    return "\n".join(_lines)


def _short(value, limit: int = 110) -> str:
    """Keep trace values readable."""

    if isinstance(value, list):
        if not value:
            return "[] (empty)"

        head = value[0]

        if isinstance(head, dict) and "title" in head:
            titles = ", ".join(
                str(v.get("title", "?"))
                for v in value[:3]
            )
            more = (
                f" … +{len(value) - 3} more"
                if len(value) > 3
                else ""
            )
            return f"{len(value)} items: {titles}{more}"

        return f"{len(value)} items: {str(head)[:60]}…"

    if isinstance(value, dict):
        if "title" in value:
            return (
                f"{value.get('title')} "
                f"(${value.get('price')}, {value.get('platform')})"
            )

        keys = ", ".join(list(value)[:6])
        return f"dict with keys: {keys}"

    text = str(value).replace("\n", " ")

    return text if len(text) <= limit else text[:limit] + "…"


def check_iterations(count: int) -> None:
    """Stop the planning loop if it runs too many times."""

    if count > config.MAX_ITERATIONS:
        raise RuntimeError(
            f"The loop ran {count} times, past MAX_ITERATIONS "
            f"({config.MAX_ITERATIONS}) in config.py.\n"
            "That usually means a branch is not ending."
        )