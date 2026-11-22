"""Small helpers shared by every module: number formatting, natural sort, markdown tables."""

from __future__ import annotations

import math
import re
from typing import Any, Iterable, Sequence


def natural_key(s: Any) -> list[Any]:
    """Sort key that orders 'A2' before 'A10' and '2' before '10'."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(s))]


def fmt(x: Any, dp: int = 4) -> str:
    """Format a number for display: integers without decimals,
    everything else rounded to `dp` decimal places with trailing zeros trimmed."""
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, (int,)):
        return str(x)
    if isinstance(x, float):
        if math.isinf(x):
            return "∞" if x > 0 else "−∞"
        if math.isnan(x):
            return "NaN"
        if abs(x - round(x)) < 1e-9:
            return str(int(round(x)))
        s = f"{x:.{dp}f}".rstrip("0").rstrip(".")
        return s
    return str(x)


def md_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    """Render a markdown table. Cells are converted with fmt()."""
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(fmt(c) if not isinstance(c, str) else c for c in r) + " |")
    return "\n".join(out)
