"""DPLL and WalkSAT (AIMA §7.6) with a step-by-step summary and a detailed trace.

DPLL conventions (AIMA Fig 7.17, made deterministic):
  * check for early termination (all clauses true → success, any clause false → fail);
  * pure symbol rule first, then the unit clause rule (unit clauses found in clause order);
  * otherwise branch on the next symbol in the given order, trying true before false;
  * each summary "Step" runs from a branching decision to the next success or fail.
"""

from __future__ import annotations

import random
from typing import Any, Optional

from .common import md_table, natural_key
from .logic import clause_compact, clause_str, parse_clause


def _clauses(clauses: list[Any]) -> list[frozenset]:
    return [parse_clause(c) for c in clauses]


def _clause_value(c, model: dict[str, bool]) -> Optional[bool]:
    """True if some literal is true, False if every literal is false, None if undecided."""
    undecided = False
    for s, v in c:
        if s in model:
            if model[s] == v:
                return True
        else:
            undecided = True
    return None if undecided else False


def _symbols(clauses) -> list[str]:
    return sorted({s for c in clauses for s, _ in c}, key=natural_key)


def dpll(
    clauses: list[Any],
    symbol_order: Optional[list[str]] = None,
    use_pure_symbols: bool = True,
    true_first: bool = True,
) -> dict[str, Any]:
    cls = _clauses(clauses)
    order = [str(s) for s in symbol_order] if symbol_order else _symbols(cls)
    for s in _symbols(cls):
        if s not in order:
            order.append(s)

    log: list[str] = []          # detailed trace lines
    step_summary: list[list[str]] = [[]]

    def cur(model):
        return "{" + ", ".join(f"{s}={'T' if v else 'F'}" for s, v in model.items()) + "}"

    def record(sym, val, reason, depth):
        step_summary[-1].append(f"{sym}={'true' if val else 'false'}")
        log.append(f"{'  ' * depth}- {reason}: **{sym} = {'true' if val else 'false'}**")

    def find_pure(model):
        signs: dict[str, set] = {}
        for c in cls:
            if _clause_value(c, model) is True:
                continue
            for s, v in c:
                if s not in model:
                    signs.setdefault(s, set()).add(v)
        for s in order:
            if s in signs and len(signs[s]) == 1:
                return s, next(iter(signs[s]))
        return None

    def find_unit(model):
        for i, c in enumerate(cls):
            if _clause_value(c, model) is not None:
                continue
            unassigned = [(s, v) for s, v in c if s not in model]
            if len(unassigned) == 1:
                return i, unassigned[0]
        return None

    def solve(model: dict[str, bool], depth: int) -> Optional[dict[str, bool]]:
        vals = [_clause_value(c, model) for c in cls]
        if all(v is True for v in vals):
            step_summary[-1].append("success")
            log.append(f"{'  ' * depth}- every clause is true → **success** {cur(model)}")
            return model
        false = [i for i, v in enumerate(vals) if v is False]
        if false:
            step_summary[-1].append("fail")
            log.append(f"{'  ' * depth}- clause c{false[0] + 1} ({clause_str(cls[false[0]])}) is false → **fail**")
            return None
        if use_pure_symbols:
            p = find_pure(model)
            if p:
                record(p[0], p[1], f"pure symbol {p[0]}", depth)
                return solve({**model, p[0]: p[1]}, depth)
        u = find_unit(model)
        if u:
            i, (s, v) = u
            record(s, v, f"unit clause c{i + 1} ({clause_str(cls[i])})", depth)
            return solve({**model, s: v}, depth)
        sym = next(s for s in order if s not in model)
        first, second = (True, False) if true_first else (False, True)
        record(sym, first, f"branch on {sym} (next in order)", depth)
        r = solve({**model, sym: first}, depth + 1)
        if r is not None:
            return r
        step_summary.append([])
        log.append(f"{'  ' * depth}- backtrack to {sym}")
        record(sym, second, f"branch on {sym}, other value", depth)
        return solve({**model, sym: second}, depth + 1)

    result = solve({}, 0)
    summary = [f"Step {i + 1}: " + ", ".join(s) for i, s in enumerate(step_summary) if s]
    md = ["## DPLL", "",
          f"**Answer:** {'satisfiable, model ' + ', '.join(f'{s}={str(v).lower()}' for s, v in sorted(result.items(), key=lambda kv: natural_key(kv[0]))) if result else 'unsatisfiable'}",
          "", "**Step summary:**", *[f"- {e}" for e in summary], "",
          "Clauses: " + "; ".join(f"c{i + 1}: {clause_str(c)}" for i, c in enumerate(cls)), "",
          "**Detailed trace:**", *log, "",
          f"**Conventions used:** symbol order {'-'.join(order)}; {'true' if true_first else 'false'} tried first; "
          f"{'pure symbol rule before unit clause rule' if use_pure_symbols else 'pure symbol rule off'}; "
          "unit clauses taken in clause order. Unassigned symbols left at the end can take either value."]
    return {"satisfiable": result is not None, "model": result, "step_summary": summary, "markdown": "\n".join(md)}


def walksat_step(
    clauses: list[Any],
    model: dict[str, Any],
    p: float = 0.5,
    clause_index: Optional[int] = None,
) -> dict[str, Any]:
    """Analyse one WalkSAT step: which clauses are false, and for each candidate clause what every flip does.

    clause_index is 1-based; leave it out to analyse every false clause (WalkSAT picks one at random).
    """
    cls = _clauses(clauses)
    m = {str(k): (v if isinstance(v, bool) else str(v).lower() in ("t", "true", "1")) for k, v in model.items()}

    def sat_count(mm):
        return sum(1 for c in cls if any(mm[s] == v for s, v in c))

    def status(mm):
        return ["T" if any(mm[s] == v for s, v in c) else "F" for c in cls]

    start_status = status(m)
    false_idx = [i for i, s in enumerate(start_status) if s == "F"]
    md = ["## WalkSAT step", ""]
    syms = sorted(m, key=natural_key)
    if not false_idx:
        md.insert(1, "**Answer:** every clause is already satisfied, so WalkSAT returns this model.")
        return {"reachable": [], "markdown": "\n".join(md)}
    candidates = [clause_index - 1] if clause_index else false_idx
    reachable: dict[str, set] = {}
    sections = []
    for ci in candidates:
        c = cls[ci]
        rows = [["(start)", ", ".join(f"{s}={'T' if m[s] else 'F'}" for s in syms)] + start_status + [str(sat_count(m))]]
        scores = {}
        for s, _ in sorted(c, key=lambda l: natural_key(l[0])):
            mm = {**m, s: not m[s]}
            scores[s] = sat_count(mm)
            rows.append([f"flip **{s}**", ", ".join(f"{x}={'T' if mm[x] else 'F'}" for x in syms)] + status(mm) + [f"**{scores[s]}**"])
        best = max(scores.values())
        greedy = [s for s, v in scores.items() if v == best]
        if p < 1:
            for s in greedy:
                reachable.setdefault(s, set()).add("greedy")
        if p > 0:
            for s in scores:
                reachable.setdefault(s, set()).add("random walk")
        sections.append(f"### If WalkSAT picks clause c{ci + 1}: {clause_str(c)}\n\n"
                        + md_table(["Flip", "Model"] + [f"c{i + 1}" for i in range(len(cls))] + ["# satisfied"], rows)
                        + f"\n\nGreedy choice (max satisfied = {best}): **{', '.join(greedy)}**"
                        + (" (tie: either can be chosen)" if len(greedy) > 1 else ""))
    def flipped_model(s):
        return ", ".join(f"{x}={'true' if (not m[x] if x == s else m[x]) else 'false'}" for x in syms)
    reach_lines = [f"- flip {s} → {flipped_model(s)} (via {' and '.join(sorted(v))})" for s, v in
                   sorted(reachable.items(), key=lambda kv: natural_key(kv[0]))]
    md.insert(1, f"**Answer:** false clauses: {', '.join('c' + str(i + 1) for i in false_idx)}. "
                 f"With p = {p}, one step can reach:\n" + "\n".join(reach_lines) + "\n")
    md.extend(sections)
    md.append("")
    md.append("**Conventions used:** with probability p flip a random symbol from the chosen false clause (random walk); "
              "otherwise flip the symbol that maximises the number of satisfied clauses (greedy). "
              "p = 0 means always greedy; p = 1 means always random. Only symbols in the chosen clause can flip.")
    return {"false_clauses": [i + 1 for i in false_idx],
            "reachable": {s: sorted(v) for s, v in reachable.items()}, "markdown": "\n".join(md)}


def walksat_run(clauses: list[Any], p: float = 0.5, max_flips: int = 100, seed: int = 0,
                model: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Full randomised WalkSAT run (for practice; a seed makes it repeatable)."""
    cls = _clauses(clauses)
    rng = random.Random(seed)
    syms = _symbols(cls)
    m = ({str(k): (v if isinstance(v, bool) else str(v).lower() in ("t", "true", "1")) for k, v in model.items()}
         if model else {s: rng.random() < 0.5 for s in syms})
    rows = []
    for flip in range(1, max_flips + 1):
        false = [i for i, c in enumerate(cls) if not any(m[s] == v for s, v in c)]
        if not false:
            break
        ci = rng.choice(false)
        if rng.random() < p:
            s = rng.choice(sorted(x for x, _ in cls[ci]))
            how = "random"
        else:
            best, s = -1, None
            for x, _ in sorted(cls[ci]):
                mm = {**m, x: not m[x]}
                sc = sum(1 for c in cls if any(mm[y] == v for y, v in c))
                if sc > best:
                    best, s = sc, x
            how = "greedy"
        m[s] = not m[s]
        rows.append([str(flip), f"c{ci + 1}", how, s, ", ".join(f"{x}={'T' if m[x] else 'F'}" for x in syms)])
    solved = all(any(m[s] == v for s, v in c) for c in cls)
    md = ["## WalkSAT run", "", f"**Answer:** {'solved: ' + ', '.join(f'{x}={str(m[x]).lower()}' for x in syms) if solved else 'no model found within max_flips (WalkSAT cannot prove unsatisfiability)'}",
          "", md_table(["Flip", "Clause picked", "Mode", "Flipped", "Model after"], rows)]
    return {"solved": solved, "model": m, "markdown": "\n".join(md)}


def clauses_compact_form(clauses: list[Any]) -> list[str]:
    return [clause_compact(parse_clause(c)) for c in clauses]
