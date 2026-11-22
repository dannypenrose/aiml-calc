"""Constraint satisfaction (AIMA chapter 6): backtracking search with MRV / degree / LCV heuristics,
forward checking or MAC, and the AC-3 arc-consistency algorithm.

Binary constraints are written [X, op, Y] with op one of != == < > <= >=, or [X, "!=", Y] pairs from a
neighbour list. map colouring: give `neighbours` as {"WA": ["NT", "SA"], ...} and every pair must differ.
"""

from __future__ import annotations

import operator
from typing import Any, Optional

from .common import md_table, natural_key

_OPS = {"!=": operator.ne, "≠": operator.ne, "==": operator.eq, "=": operator.eq, "<": operator.lt,
        ">": operator.gt, "<=": operator.le, ">=": operator.ge}
_FLIP = {"!=": "!=", "≠": "!=", "==": "==", "=": "==", "<": ">", ">": "<", "<=": ">=", ">=": "<="}


class CSP:
    def __init__(self, variables: list[str], domains: dict[str, list[Any]], constraints: Optional[list[list[Any]]] = None,
                 neighbours: Optional[dict[str, list[str]]] = None):
        self.variables = [str(v) for v in variables]
        self.domains = {str(v): list(domains[v] if v in domains else domains.get(str(v), [])) for v in self.variables}
        # arcs[(X, Y)] = list of predicates p(x_value, y_value)
        self.arcs: dict[tuple[str, str], list[tuple[str, Any]]] = {}
        for c in constraints or []:
            x, op, y = str(c[0]), str(c[1]), str(c[2])
            if op not in _OPS:
                raise ValueError(f"Unknown operator {op!r}")
            self._add(x, op, y)
        for x, ys in (neighbours or {}).items():
            for y in ys:
                if (str(x), str(y)) not in self.arcs:
                    self._add(str(x), "!=", str(y))
        for v in self.variables:
            if not self.domains[v]:
                raise ValueError(f"Variable {v} has an empty domain")

    def _add(self, x: str, op: str, y: str) -> None:
        self.arcs.setdefault((x, y), []).append(op)
        self.arcs.setdefault((y, x), []).append(_FLIP[op])

    def neighbours(self, x: str) -> list[str]:
        return sorted({b for a, b in self.arcs if a == x}, key=natural_key)

    def consistent(self, x: str, vx: Any, y: str, vy: Any) -> bool:
        return all(_OPS[op](vx, vy) for op in self.arcs.get((x, y), []))

    def edges(self) -> list[tuple[str, str, str]]:
        seen, out = set(), []
        for (a, b), ops in self.arcs.items():
            if (b, a) in seen:
                continue
            seen.add((a, b))
            out.append((a, b, " ∧ ".join(ops)))
        return out


def _fmt_domains(d: dict[str, list[Any]], order: list[str]) -> str:
    return "; ".join(f"{v}: {{{', '.join(str(x) for x in d[v])}}}" for v in order)


def ac3(variables, domains, constraints=None, neighbours=None) -> dict[str, Any]:
    """AC-3: make every arc X → Y consistent by deleting values of X that have no support in Y."""
    csp = CSP(variables, domains, constraints, neighbours)
    d = {v: list(vals) for v, vals in csp.domains.items()}
    queue = sorted(csp.arcs, key=lambda a: (natural_key(a[0]), natural_key(a[1])))
    rows = []
    revisions = 0
    ok = True
    while queue:
        x, y = queue.pop(0)
        removed = [vx for vx in d[x] if not any(csp.consistent(x, vx, y, vy) for vy in d[y])]
        if removed:
            revisions += 1
            d[x] = [v for v in d[x] if v not in removed]
            added = [(z, x) for z in csp.neighbours(x) if z != y and (z, x) not in queue]
            queue.extend(added)
            rows.append([f"{x} → {y}", ", ".join(map(str, removed)), "{" + ", ".join(map(str, d[x])) + "}",
                         ", ".join(f"{a}→{b}" for a, b in added) or "–"])
            if not d[x]:
                ok = False
                break
        else:
            rows.append([f"{x} → {y}", "–", "{" + ", ".join(map(str, d[x])) + "}", "–"])
    md = ["## AC-3 arc consistency", "",
          f"**Answer:** {'arc consistent' if ok else 'inconsistent: a domain became empty, so there is no solution'}. "
          f"Final domains: {_fmt_domains(d, csp.variables)}", "",
          f"Initial domains: {_fmt_domains(csp.domains, csp.variables)}", "",
          md_table(["Arc checked", "Values removed from left", "Left domain now", "Arcs added back to queue"], rows), "",
          f"{len(rows)} arc checks, {revisions} revisions. When X loses a value, every arc Z → X (Z ≠ Y) is re-queued, "
          "because Z's values may have lost their support."]
    if ok and all(len(v) == 1 for v in d.values()):
        md.append("\nEvery domain has one value left, so AC-3 alone has solved the problem.")
    return {"consistent": ok, "domains": d, "markdown": "\n".join(md)}


def backtracking(variables, domains, constraints=None, neighbours=None, variable_order: str = "mrv",
                 value_order: str = "lcv", inference: str = "forward_checking", max_steps: int = 500) -> dict[str, Any]:
    """BACKTRACKING-SEARCH (AIMA Fig 6.5).

    variable_order: "static" (the order given) or "mrv" (minimum remaining values, ties by degree, then name).
    value_order: "static" or "lcv" (least constraining value first).
    inference: "none", "forward_checking" or "mac" (maintain arc consistency with AC-3)."""
    csp = CSP(variables, domains, constraints, neighbours)
    log: list[str] = []
    steps = {"assign": 0, "backtrack": 0}

    def select(assign, d):
        un = [v for v in csp.variables if v not in assign]
        if variable_order == "static":
            return un[0], "next in order"
        def degree(v):
            return sum(1 for n in csp.neighbours(v) if n not in assign)
        best = min(un, key=lambda v: (len(d[v]), -degree(v), csp.variables.index(v)))
        tied = [v for v in un if len(d[v]) == len(d[best])]
        why = f"MRV: {len(d[best])} value(s) left"
        if len(tied) > 1:
            why += f", tie with {', '.join(t for t in tied if t != best)} broken by degree ({degree(best)})"
        return best, why

    def order_values(var, assign, d):
        vals = list(d[var])
        if value_order != "lcv":
            return vals, ""
        def ruled_out(val):
            return sum(1 for n in csp.neighbours(var) if n not in assign
                       for vn in d[n] if not csp.consistent(var, val, n, vn))
        scored = sorted(vals, key=lambda v: (ruled_out(v), vals.index(v)))
        return scored, " (LCV: " + ", ".join(f"{v} rules out {ruled_out(v)}" for v in vals) + ")"

    def infer(var, val, assign, d):
        """Returns new domains or None on a wipe-out, and a description."""
        d2 = {k: list(v) for k, v in d.items()}
        d2[var] = [val]
        if inference == "none":
            return d2, ""
        pruned = []
        if inference == "forward_checking":
            for n in csp.neighbours(var):
                if n in assign:
                    continue
                keep = [vn for vn in d2[n] if csp.consistent(var, val, n, vn)]
                if len(keep) < len(d2[n]):
                    pruned.append(f"{n}−{{{', '.join(str(x) for x in d2[n] if x not in keep)}}}")
                d2[n] = keep
                if not keep:
                    return None, f"forward checking empties {n}'s domain"
            return d2, ("FC prunes " + ", ".join(pruned)) if pruned else "FC prunes nothing"
        # MAC: AC-3 starting from arcs (Z, var)
        queue = [(n, var) for n in csp.neighbours(var) if n not in assign]
        while queue:
            x, y = queue.pop(0)
            rem = [vx for vx in d2[x] if not any(csp.consistent(x, vx, y, vy) for vy in d2[y])]
            if rem:
                pruned.append(f"{x}−{{{', '.join(map(str, rem))}}}")
                d2[x] = [v for v in d2[x] if v not in rem]
                if not d2[x]:
                    return None, f"MAC empties {x}'s domain"
                queue.extend((z, x) for z in csp.neighbours(x) if z != y)
        return d2, ("MAC prunes " + ", ".join(pruned)) if pruned else "MAC prunes nothing"

    def bt(assign, d, depth):
        if len(assign) == len(csp.variables):
            return assign
        if steps["assign"] >= max_steps:
            return None
        var, why = select(assign, d)
        vals, lcv = order_values(var, assign, d)
        ind = "  " * depth
        log.append(f"{ind}- choose **{var}** ({why}); try {', '.join(map(str, vals))}{lcv}")
        for val in vals:
            if not all(csp.consistent(var, val, o, assign[o]) for o in assign if (var, o) in csp.arcs):
                log.append(f"{ind}  - {var} = {val} conflicts with an assignment ✗")
                continue
            steps["assign"] += 1
            d2, note = infer(var, val, assign, d)
            if d2 is None:
                log.append(f"{ind}  - {var} = {val}: {note} ✗")
                continue
            log.append(f"{ind}  - **{var} = {val}**" + (f"; {note}" if note else ""))
            r = bt({**assign, var: val}, d2, depth + 1)
            if r is not None:
                return r
            steps["backtrack"] += 1
            log.append(f"{ind}  - undo {var} = {val} (backtrack)")
        return None

    result = bt({}, csp.domains, 0)
    md = ["## Backtracking search", ""]
    if result:
        md.append("**Answer:** " + ", ".join(f"{v} = {result[v]}" for v in csp.variables))
    else:
        md.append("**Answer:** no solution" + (" (step limit reached)" if steps["assign"] >= max_steps else ""))
    md += ["", f"{steps['assign']} assignments tried, {steps['backtrack']} backtracks.", "", *log, "",
           f"Settings: variable order **{variable_order}**, value order **{value_order}**, inference **{inference}**."]
    if result:
        ok = all(csp.consistent(a, result[a], b, result[b]) for (a, b) in csp.arcs)
        md.append(f"\nCheck: every constraint holds in the final assignment {'✓' if ok else '✗'}.")
    return {"solution": result, "assignments": steps["assign"], "backtracks": steps["backtrack"],
            "edges": csp.edges(), "markdown": "\n".join(md)}
