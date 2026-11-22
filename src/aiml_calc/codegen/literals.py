"""Render Python values as source code and splice them into program templates.

Each template is a complete, runnable program with one block between the markers

    # --- inputs ---
    ...
    # --- end inputs ---

The generator replaces that block with the values from the UI, so the program always matches the page.
"""

from __future__ import annotations

START, END = "# --- inputs ---", "# --- end inputs ---"


class Raw:
    """Source code to insert as it is (e.g. an expression-tree constructor call)."""

    def __init__(self, code: str):
        self.code = code


def literal(v, width: int = 100) -> str:
    """A Python literal, one item per line when it would be long."""
    flat = _flat(v)
    if len(flat) <= width or not isinstance(v, (list, tuple, dict)):
        return flat
    if isinstance(v, dict):
        return "{\n" + "".join(f"    {_flat(k)}: {_flat(x)},\n" for k, x in v.items()) + "}"
    o, c = ("[", "]") if isinstance(v, list) else ("(", ")")
    return o + "\n" + "".join(f"    {_flat(x)},\n" for x in v) + c


def _flat(v) -> str:
    if isinstance(v, Raw):
        return v.code
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, dict):
        return "{" + ", ".join(f"{_flat(k)}: {_flat(x)}" for k, x in v.items()) + "}"
    if isinstance(v, tuple):
        return "(" + ", ".join(_flat(x) for x in v) + ("," if len(v) == 1 else "") + ")"
    if isinstance(v, list):
        return "[" + ", ".join(_flat(x) for x in v) + "]"
    return repr(v)


def block(items: list[tuple[str, object, str]]) -> str:
    """items: (NAME, value, comment) -> 'NAME = value  # comment' lines."""
    out = []
    for name, value, comment in items:
        line = f"{name} = {literal(value)}"
        if comment and "\n" not in line and len(line) + len(comment) < 110:
            line += f"   # {comment}"
        elif comment:
            out.append(f"# {comment}")
        out.append(line)
    return "\n".join(out)


def splice(template: str, inputs: str) -> str:
    i, j = template.index(START), template.index(END)
    return template[: i + len(START)] + "\n" + inputs + "\n" + template[j:]
