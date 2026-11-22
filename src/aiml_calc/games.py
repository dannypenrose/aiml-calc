"""Adversarial search (AIMA chapter 5): minimax, alpha-beta pruning and expectiminimax on an explicit game tree.

A tree can be given two ways:
  * nested lists of leaf utilities, e.g. [[3, 12, 8], [2, 4, 6], [14, 5, 2]] (AIMA Fig 5.2), with levels alternating
    MAX, MIN, MAX, ... from the root; or
  * a dict {"children": {"A": ["B", "C"], ...}, "values": {"D": 3, ...}, "types": {"A": "max", "B": "chance", ...},
    "probabilities": {"B": [0.5, 0.5], ...}} for any shape, including chance nodes.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from .common import fmt, md_table, natural_key


class Tree:
    def __init__(self, spec: Any, root_type: str = "max"):
        self.children: dict[str, list[str]] = {}
        self.values: dict[str, float] = {}
        self.types: dict[str, str] = {}
        self.probs: dict[str, list[float]] = {}
        if isinstance(spec, list):
            self.root = "A"
            self._from_lists(spec, root_type)
        else:
            self.children = {str(k): [str(c) for c in v] for k, v in spec.get("children", {}).items()}
            self.values = {str(k): float(v) for k, v in spec.get("values", {}).items()}
            self.probs = {str(k): [float(p) for p in v] for k, v in spec.get("probabilities", {}).items()}
            child_set = {c for cs in self.children.values() for c in cs}
            roots = [n for n in self.children if n not in child_set]
            self.root = str(spec.get("root", roots[0] if roots else next(iter(self.values))))
            given = {str(k): str(v).lower() for k, v in spec.get("types", {}).items()}
            self._assign_types(self.root, root_type, given)

    def _from_lists(self, spec, root_type):
        names = _name_gen()
        queue = [(next(names), spec, root_type)]
        self.root = queue[0][0]
        while queue:
            name, sub, typ = queue.pop(0)
            if isinstance(sub, list):
                self.types[name] = typ
                kids = []
                for s in sub:
                    k = next(names)
                    kids.append(k)
                    queue.append((k, s, "min" if typ == "max" else "max"))
                self.children[name] = kids
            else:
                self.values[name] = float(sub)
                self.types[name] = "leaf"

    def _assign_types(self, node, default, given, last_player="min"):
        if node not in self.children:
            self.types[node] = "leaf"
            return
        t = given.get(node, default)
        self.types[node] = t
        if t == "chance":
            player = last_player            # who moved into this chance node
            nxt = "min" if player == "max" else "max"
        else:
            player = t
            nxt = "min" if t == "max" else "max"
        for c in self.children[node]:
            self._assign_types(c, nxt, given, player)

    def leaves(self) -> list[str]:
        return [n for n, t in self.types.items() if t == "leaf"]


def _name_gen():
    i = 0
    while True:
        n, s = i, ""
        while True:
            s = chr(ord("A") + n % 26) + s
            n = n // 26 - 1
            if n < 0:
                break
        yield s
        i += 1


def minimax(tree: Any, root_type: str = "max") -> dict[str, Any]:
    """Minimax (and expectiminimax if the tree has chance nodes): the backed-up value of every node."""
    t = Tree(tree, root_type)
    vals: dict[str, float] = {}
    rows = []

    def v(n):
        typ = t.types[n]
        if typ == "leaf":
            vals[n] = t.values[n]
            return vals[n]
        kids = [v(c) for c in t.children[n]]
        if typ == "max":
            vals[n] = max(kids)
            how = f"max({', '.join(fmt(k) for k in kids)})"
        elif typ == "min":
            vals[n] = min(kids)
            how = f"min({', '.join(fmt(k) for k in kids)})"
        else:
            ps = t.probs.get(n) or [1 / len(kids)] * len(kids)
            vals[n] = sum(p * k for p, k in zip(ps, kids))
            how = " + ".join(f"{fmt(p)}×{fmt(k)}" for p, k in zip(ps, kids))
        rows.append([n, typ.upper(), how, fmt(vals[n])])
        return vals[n]

    root_v = v(t.root)
    best_children = [c for c in t.children[t.root] if abs(vals[c] - root_v) < 1e-12] if t.types[t.root] != "chance" else []
    md = ["## Minimax" + (" (expectiminimax)" if "chance" in t.types.values() else ""), "",
          f"**Answer:** value of {t.root} = **{fmt(root_v)}**"
          + (f"; best move for {t.types[t.root].upper()}: **{t.root} → {best_children[0]}**" if best_children else ""), "",
          md_table(["Node", "Type", "Backed-up from children", "Value"], rows), "",
          "Values are backed up from the leaves: MAX takes the largest child value, MIN the smallest"
          + (", and a chance node the probability-weighted average." if "chance" in t.types.values() else ".")]
    return {"value": root_v, "values": vals, "best_move": best_children[0] if best_children else None,
            "tree": t, "markdown": "\n".join(md)}


def alphabeta(tree: Any, root_type: str = "max") -> dict[str, Any]:
    """Alpha-beta pruning: left-to-right, showing α and β at each node and which subtrees are never examined."""
    t = Tree(tree, root_type)
    if "chance" in t.types.values():
        raise ValueError("Alpha-beta as implemented here needs MAX/MIN nodes only (use minimax for chance nodes)")
    log: list[str] = []
    visited: list[str] = []
    pruned: list[str] = []
    vals: dict[str, float] = {}

    def subtree(n):
        out = [n]
        for c in t.children.get(n, []):
            out += subtree(c)
        return out

    def ab(n, alpha, beta, depth):
        visited.append(n)
        ind = "  " * depth
        typ = t.types[n]
        if typ == "leaf":
            vals[n] = t.values[n]
            log.append(f"{ind}- {n} = {fmt(vals[n])}")
            return vals[n]
        log.append(f"{ind}- {typ.upper()} {n}: enter with α = {fmt(alpha)}, β = {fmt(beta)}")
        kids = t.children[n]
        v = -math.inf if typ == "max" else math.inf
        for i, c in enumerate(kids):
            cv = ab(c, alpha, beta, depth + 1)
            if typ == "max":
                v = max(v, cv)
                if v >= beta:
                    skip = kids[i + 1:]
                    if skip:
                        for s in skip:
                            pruned.extend(subtree(s))
                        log.append(f"{ind}  - v = {fmt(v)} ≥ β = {fmt(beta)}: **prune** {', '.join(skip)} (MIN above will never allow this)")
                    vals[n] = v
                    return v
                alpha = max(alpha, v)
            else:
                v = min(v, cv)
                if v <= alpha:
                    skip = kids[i + 1:]
                    if skip:
                        for s in skip:
                            pruned.extend(subtree(s))
                        log.append(f"{ind}  - v = {fmt(v)} ≤ α = {fmt(alpha)}: **prune** {', '.join(skip)} (MAX above already has better)")
                    vals[n] = v
                    return v
                beta = min(beta, v)
            log.append(f"{ind}  - after {c}: v = {fmt(v)}, α = {fmt(alpha)}, β = {fmt(beta)}")
        vals[n] = v
        log.append(f"{ind}  - {n} returns {fmt(v)}")
        return v

    root_v = ab(t.root, -math.inf, math.inf, 0)
    mm = minimax(tree, root_type)
    leaves = t.leaves()
    pruned_leaves = [p for p in pruned if t.types[p] == "leaf"]
    md = ["## Alpha-beta pruning", "",
          f"**Answer:** value of {t.root} = **{fmt(root_v)}**; pruned: **{', '.join(sorted(set(pruned), key=natural_key)) or 'nothing'}** "
          f"({len(pruned_leaves)} of {len(leaves)} leaves never examined)", "",
          f"Order visited: {' '.join(visited)}", "", *log, "",
          f"Check: plain minimax gives {fmt(mm['value'])} {'✓ same value' if abs(mm['value'] - root_v) < 1e-12 else '✗ DIFFERENT'}. "
          "Pruning never changes the root's value, only how much of the tree is searched. "
          "Children are searched left to right; better move ordering prunes more."]
    return {"value": root_v, "pruned": sorted(set(pruned), key=natural_key), "visited": visited, "values": vals,
            "tree": t, "markdown": "\n".join(md)}
