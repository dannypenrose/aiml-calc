"""Probabilistic reasoning (AIMA chapters 13–14, 20): Bayes' rule, inference from a full joint distribution,
exact inference in Bayesian networks by enumeration, and naive Bayes classification.

All random variables are Boolean in the Bayes-net and joint-distribution tools (true/false).
"""

from __future__ import annotations

import itertools
import math
from collections import Counter, defaultdict
from typing import Any, Optional

from .common import fmt, md_table, natural_key


def _tf(v: Any) -> bool:
    return v if isinstance(v, bool) else str(v).strip().lower() in ("t", "true", "1", "yes", "+")


def _lit(var: str, val: bool) -> str:
    return var if val else "¬" + var


# ---------------------------------------------------------------------------
# Bayes' rule
# ---------------------------------------------------------------------------

def bayes_rule(prior: float, likelihood: float, false_positive_rate: float, hypothesis: str = "H",
               evidence: str = "E") -> dict[str, Any]:
    """P(H | E) = P(E | H) P(H) / P(E), with P(E) from total probability. Checked with natural frequencies."""
    pe = likelihood * prior + false_positive_rate * (1 - prior)
    post = likelihood * prior / pe
    n = 10000
    tp = likelihood * prior * n
    fp = false_positive_rate * (1 - prior) * n
    md = ["## Bayes' rule", "",
          f"**Answer:** P({hypothesis} | {evidence}) = **{fmt(post)}** ({fmt(post * 100, 2)}%)", "",
          "### Method 1: formula",
          f"P({evidence}) = P({evidence}|{hypothesis})P({hypothesis}) + P({evidence}|¬{hypothesis})P(¬{hypothesis}) "
          f"= {fmt(likelihood)}×{fmt(prior)} + {fmt(false_positive_rate)}×{fmt(1 - prior)} = {fmt(pe)}",
          f"P({hypothesis}|{evidence}) = P({evidence}|{hypothesis})P({hypothesis}) / P({evidence}) = "
          f"{fmt(likelihood * prior)} / {fmt(pe)} = **{fmt(post)}**", "",
          "### Method 2: natural frequencies (imagine 10,000 cases)",
          f"- {fmt(prior * n, 1)} have {hypothesis}; of those, {fmt(tp, 1)} show {evidence}.",
          f"- {fmt((1 - prior) * n, 1)} don't; of those, {fmt(fp, 1)} still show {evidence}.",
          f"- So of {fmt(tp + fp, 1)} cases showing {evidence}, {fmt(tp, 1)} really have {hypothesis}: "
          f"{fmt(tp, 1)} / {fmt(tp + fp, 1)} = **{fmt(tp / (tp + fp))}**", "",
          f"Prior {fmt(prior)} → posterior {fmt(post)}: the evidence multiplied the odds by the likelihood ratio "
          f"{fmt(likelihood / false_positive_rate) if false_positive_rate else '∞'}."]
    return {"posterior": post, "p_evidence": pe, "markdown": "\n".join(md)}


# ---------------------------------------------------------------------------
# Full joint distribution
# ---------------------------------------------------------------------------

def joint_query(variables: list[str], table: list[list[Any]], query: str,
                evidence: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """P(query | evidence) from a full joint table. Each row: [value of each variable..., probability]."""
    evidence = {str(k): _tf(v) for k, v in (evidence or {}).items()}
    rows = [([_tf(v) for v in r[:-1]], float(r[-1])) for r in table]
    total = sum(p for _, p in rows)
    idx = {v: i for i, v in enumerate(variables)}
    unnorm = {True: 0.0, False: 0.0}
    terms = {True: [], False: []}
    for vals, p in rows:
        if all(vals[idx[e]] == ev for e, ev in evidence.items()):
            q = vals[idx[query]]
            unnorm[q] += p
            terms[q].append(fmt(p))
    z = unnorm[True] + unnorm[False]
    ev_str = ", ".join(_lit(k, v) for k, v in evidence.items())
    cond = f" | {ev_str}" if ev_str else ""
    md = ["## Inference from the full joint distribution", ""]
    if z == 0:
        md.append("**Answer:** the evidence has probability 0, so the query is undefined.")
        return {"distribution": None, "markdown": "\n".join(md)}
    pt, pf = unnorm[True] / z, unnorm[False] / z
    md += [f"**Answer:** P({query}{cond}) = **⟨{fmt(pt)}, {fmt(pf)}⟩** (true, false)", "",
           f"Sum the rows that match the evidence, split by {query}:",
           f"- {_lit(query, True)}{', ' + ev_str if ev_str else ''}: {' + '.join(terms[True]) or '0'} = {fmt(unnorm[True])}",
           f"- {_lit(query, False)}{', ' + ev_str if ev_str else ''}: {' + '.join(terms[False]) or '0'} = {fmt(unnorm[False])}",
           f"- Normalise: α = 1 / ({fmt(unnorm[True])} + {fmt(unnorm[False])}) = 1 / {fmt(z)}, giving ⟨{fmt(pt)}, {fmt(pf)}⟩", ""]
    if abs(total - 1) > 1e-6:
        md.append(f"⚠ The table sums to {fmt(total)}, not 1.")
    md.append(md_table(variables + ["P"], [["T" if v else "F" for v in vals] + [fmt(p)] for vals, p in rows]))
    return {"distribution": {"true": pt, "false": pf}, "markdown": "\n".join(md)}


# ---------------------------------------------------------------------------
# Bayesian networks
# ---------------------------------------------------------------------------

class BayesNet:
    """nodes: {"Alarm": {"parents": ["Burglary", "Earthquake"], "cpt": {"T,T": 0.95, "T,F": 0.94, ...}}, ...}
    The CPT gives P(node = true | parent values); keys are comma-separated T/F in parent order ("" for no parents)."""

    def __init__(self, nodes: dict[str, dict[str, Any]]):
        self.parents = {str(n): [str(p) for p in d.get("parents", [])] for n, d in nodes.items()}
        self.cpt: dict[str, dict[tuple, float]] = {}
        for n, d in nodes.items():
            table = {}
            raw = d.get("cpt", d.get("p"))
            if isinstance(raw, (int, float)):
                raw = {"": raw}
            for k, v in raw.items():
                key = tuple(_tf(x) for x in str(k).split(",")) if str(k).strip() else ()
                table[key] = float(v)
            if len(table) != 2 ** len(self.parents[str(n)]):
                raise ValueError(f"{n}: CPT needs {2 ** len(self.parents[str(n)])} rows, got {len(table)}")
            self.cpt[str(n)] = table
        self.order = self._topological()

    def _topological(self) -> list[str]:
        order, seen = [], set()

        def visit(n, stack=()):
            if n in seen:
                return
            if n in stack:
                raise ValueError("The network has a cycle")
            for p in self.parents[n]:
                visit(p, stack + (n,))
            seen.add(n)
            order.append(n)

        for n in sorted(self.parents, key=natural_key):
            visit(n)
        return order

    def p(self, var: str, val: bool, assignment: dict[str, bool]) -> float:
        pt = self.cpt[var][tuple(assignment[p] for p in self.parents[var])]
        return pt if val else 1 - pt


def bayes_net_query(nodes: dict[str, dict[str, Any]], query: str, evidence: Optional[dict[str, Any]] = None,
                    show_terms: int = 8) -> dict[str, Any]:
    """ENUMERATION-ASK (AIMA Fig 14.9), checked against the full joint distribution built from the chain rule."""
    bn = BayesNet(nodes)
    evidence = {str(k): _tf(v) for k, v in (evidence or {}).items()}
    hidden = [v for v in bn.order if v != query and v not in evidence]
    ev_str = ", ".join(_lit(k, v) for k, v in evidence.items())
    md = ["## Bayesian network inference by enumeration", ""]
    unnorm = {}
    term_lines = []
    for qv in (True, False):
        total = 0.0
        shown = 0
        for hv in itertools.product([True, False], repeat=len(hidden)):
            a = {**evidence, query: qv, **dict(zip(hidden, hv))}
            factors = [(f"P({_lit(v, a[v])}" + (f" | {', '.join(_lit(p, a[p]) for p in bn.parents[v])})" if bn.parents[v] else ")"),
                        bn.p(v, a[v], a)) for v in bn.order]
            prod = math.prod(f for _, f in factors)
            total += prod
            if shown < show_terms:
                term_lines.append(f"- {_lit(query, qv)}" + (f", {', '.join(_lit(h, a[h]) for h in hidden)}" if hidden else "")
                                  + f": {' × '.join(fmt(f) for _, f in factors)} = {fmt(prod, 6)}")
                shown += 1
        unnorm[qv] = total
        term_lines.append(f"- **Σ for {_lit(query, qv)} = {fmt(total, 6)}**")
    z = unnorm[True] + unnorm[False]
    pt, pf = unnorm[True] / z, unnorm[False] / z

    # Method 2: build the full joint with the chain rule and sum it (independent code path)
    joint = {}
    for vals in itertools.product([True, False], repeat=len(bn.order)):
        a = dict(zip(bn.order, vals))
        joint[vals] = math.prod(bn.p(v, a[v], a) for v in bn.order)
    num = sum(p for vals, p in joint.items() if dict(zip(bn.order, vals))[query]
              and all(dict(zip(bn.order, vals))[e] == ev for e, ev in evidence.items()))
    den = sum(p for vals, p in joint.items() if all(dict(zip(bn.order, vals))[e] == ev for e, ev in evidence.items()))
    check = num / den

    cond = f" | {ev_str}" if ev_str else ""
    md += [f"**Answer:** P({query}{cond}) = **⟨{fmt(pt)}, {fmt(pf)}⟩** (true, false)", "",
           "### Method 1: enumeration",
           f"P({query}{cond}) = α Σ over hidden variables {{{', '.join(hidden) or 'none'}}} of the product of each node's CPT entry "
           f"(nodes in topological order: {', '.join(bn.order)}).", "", *term_lines, "",
           f"α = 1 / ({fmt(unnorm[True], 6)} + {fmt(unnorm[False], 6)}) → ⟨{fmt(pt)}, {fmt(pf)}⟩", "",
           "### Method 2: full joint distribution",
           f"Built all {2 ** len(bn.order)} joint entries with the chain rule P(x₁,…,xₙ) = Π P(xᵢ | parents(Xᵢ)) and summed: "
           f"P({query}{cond}) = {fmt(num, 6)} / {fmt(den, 6)} = {fmt(check)} {'✓ agrees' if abs(check - pt) < 1e-9 else '✗ disagrees'}."]
    return {"distribution": {"true": pt, "false": pf}, "order": bn.order, "parents": bn.parents,
            "markdown": "\n".join(md)}


# ---------------------------------------------------------------------------
# Naive Bayes
# ---------------------------------------------------------------------------

def naive_bayes(attributes: list[str], data: list[list[Any]], query: dict[str, Any], laplace: float = 0.0) -> dict[str, Any]:
    """Naive Bayes classifier from categorical data. Each data row is [attribute values..., class].
    laplace = k adds k to every count (Laplace smoothing; 0 = raw frequencies)."""
    classes = Counter(str(r[-1]) for r in data)
    n = len(data)
    values = {a: sorted({str(r[i]) for r in data} | ({str(query[a])} if a in query else set()), key=natural_key)
              for i, a in enumerate(attributes)}
    counts: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for r in data:
        for i, a in enumerate(attributes):
            counts[(a, str(r[-1]))][str(r[i])] += 1
    scores = {}
    lines = []
    for c in sorted(classes, key=natural_key):
        prior = classes[c] / n
        parts = [f"P({c}) = {classes[c]}/{n}"]
        s = prior
        for a, v in query.items():
            num = counts[(a, c)][str(v)] + laplace
            den = classes[c] + laplace * len(values[a])
            s *= num / den
            parts.append(f"P({a}={v} | {c}) = {fmt(num)}/{fmt(den)}")
        scores[c] = s
        lines.append(f"- **{c}:** " + " × ".join(parts) + f" = **{fmt(s, 6)}**")
    z = sum(scores.values())
    post = {c: (s / z if z else 0.0) for c, s in scores.items()}
    best = max(scores, key=lambda c: scores[c])
    md = ["## Naive Bayes", "",
          f"**Answer:** predicted class **{best}** (P = {fmt(post[best])})", "",
          "Assumes attributes are independent given the class: P(c | x) ∝ P(c) Π P(xᵢ | c).", "", *lines, "",
          "Normalised: " + ", ".join(f"P({c} | x) = {fmt(p)}" for c, p in post.items())]
    if laplace == 0 and any(s == 0 for s in scores.values()):
        md.append("\n⚠ A zero count wiped out a class's score entirely. Laplace smoothing (laplace = 1) avoids this.")
    return {"prediction": best, "posterior": post, "markdown": "\n".join(md)}
