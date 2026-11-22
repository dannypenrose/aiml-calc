"""Generate a standalone Python program for each algorithm, with the UI's current values built in.

    from aiml_calc.codegen import generate
    source = generate("search_trace", algorithm="astar", edges=[...], ...)

Each template in `templates/` is a complete program that runs as it is; generation replaces only its inputs
block, so the code you read is the algorithm with your numbers in it.
"""

from __future__ import annotations

from importlib import resources

from .literals import block, splice
from .specs import SPECS


def template(key: str) -> str:
    return resources.files(__package__).joinpath("templates", f"{key}.py").read_text(encoding="utf-8")


def generate(key: str, **params) -> str:
    """The Python program for a view, with its inputs set from params."""
    return splice(template(key), block(SPECS[key](**params)))


__all__ = ["generate", "template", "SPECS"]
