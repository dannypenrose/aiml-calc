"""Graphviz DOT builders for the web UI (rendered in the browser, so no system Graphviz install is needed)."""

from __future__ import annotations

from typing import Any, Iterable, Optional

from .common import fmt

INK = "#1F2937"
MUTED = "#9CA3AF"
ACCENT = "#2563EB"
ACCENT_FILL = "#DBEAFE"
VISITED_FILL = "#F3F4F6"
GOOD = "#059669"
GOOD_FILL = "#D1FAE5"
WARN_FILL = "#FEF3C7"

_BASE = (f'bgcolor="transparent"; fontname="Helvetica"; '
         f'node [fontname="Helvetica", fontsize=11, color="{INK}", fontcolor="{INK}", style="filled", fillcolor="white"]; '
         f'edge [fontname="Helvetica", fontsize=10, color="{MUTED}", fontcolor="#4B5563"];')


def _q(s: Any) -> str:
    return '"' + str(s).replace('"', '\\"') + '"'


def search_graph(edges: list[list[Any]], directed: bool, start: str, goals: Iterable[str],
                 path: Optional[list[str]] = None, expanded: Optional[list[str]] = None,
                 heuristic: Optional[dict[str, float]] = None) -> str:
    goals = {str(g) for g in goals}
    path = [str(p) for p in (path or [])]
    order: dict[str, int] = {}
    for s in expanded or []:
        order.setdefault(str(s), len(order) + 1)
    path_edges = set(zip(path, path[1:]))
    nodes: list[str] = []
    for e in edges:
        for n in (str(e[0]), str(e[1])):
            if n not in nodes:
                nodes.append(n)
    lines = [f'{"digraph" if directed else "graph"} G {{ {_BASE} layout="neato"; overlap=false; splines=true; sep="+12";']
    for n in nodes:
        label = n
        if heuristic and n in heuristic:
            label += f"\\nh={fmt(float(heuristic[n]))}"
        if n in order:
            label += f"\\n#{order[n]}"
        attrs = [f"label={_q(label)}", "shape=circle", "width=0.55", "fixedsize=false"]
        if n in path:
            attrs += [f'fillcolor="{ACCENT_FILL}"', f'color="{ACCENT}"', "penwidth=2"]
        elif n in order:
            attrs += [f'fillcolor="{VISITED_FILL}"']
        if n in goals:
            attrs += ["shape=doublecircle", f'color="{GOOD}"']
        if n == str(start):
            attrs += ["penwidth=2.5"]
        lines.append(f"{_q(n)} [{', '.join(attrs)}];")
    seen = set()
    conn = "->" if directed else "--"
    for e in edges:
        a, b = str(e[0]), str(e[1])
        key = (a, b) if directed else tuple(sorted((a, b)))
        if key in seen:
            continue
        seen.add(key)
        cost = e[2] if len(e) > 2 else None
        on = (a, b) in path_edges or (not directed and (b, a) in path_edges)
        attrs = []
        if cost is not None:
            attrs.append(f"label={_q(fmt(float(cost)))}")
        if on:
            attrs += [f'color="{ACCENT}"', "penwidth=3", f'fontcolor="{ACCENT}"']
        lines.append(f"{_q(a)} {conn} {_q(b)} [{', '.join(attrs)}];")
    lines.append("}")
    return "\n".join(lines)


def game_tree(tree, values: dict[str, float], pruned: Iterable[str] = (), best: Optional[str] = None) -> str:
    pruned = set(pruned)
    shapes = {"max": "triangle", "min": "invtriangle", "chance": "circle", "leaf": "box"}
    lines = [f"digraph T {{ {_BASE} rankdir=TB; nodesep=0.25; ranksep=0.45;"]
    for n, typ in tree.types.items():
        v = values.get(n)
        if typ == "leaf":
            label = _q(f"{n} = {fmt(tree.values[n])}")
        else:
            label = _q(f"{n}\\n{fmt(v)}" if v is not None else n)
        attrs = [f"label={label}", f"shape={shapes[typ]}"]
        if typ != "leaf":
            attrs += ["width=0.8", "height=0.7", "fixedsize=true", "fontsize=10"]
        if n in pruned:
            attrs += ['style="dashed"', f'color="{MUTED}"', f'fontcolor="{MUTED}"']
        elif n == tree.root:
            attrs += [f'fillcolor="{ACCENT_FILL}"', f'color="{ACCENT}"', "penwidth=2"]
        elif typ == "max":
            attrs += [f'fillcolor="{GOOD_FILL}"']
        elif typ == "min":
            attrs += [f'fillcolor="{WARN_FILL}"']
        lines.append(f"{_q(n)} [{', '.join(attrs)}];")
    for p, kids in tree.children.items():
        probs = tree.probs.get(p)
        for i, c in enumerate(kids):
            attrs = []
            if probs:
                attrs.append(f"label={_q(fmt(probs[i]))}")
            if c in pruned:
                attrs += ['style="dashed"', f'color="{MUTED}"']
            elif p == tree.root and c == best:
                attrs += [f'color="{ACCENT}"', "penwidth=3"]
            lines.append(f"{_q(p)} -> {_q(c)} [{', '.join(attrs)}];")
    lines.append("}")
    return "\n".join(lines)


_COLOURS = {"red": "#FCA5A5", "green": "#86EFAC", "blue": "#93C5FD", "yellow": "#FDE68A", "orange": "#FDBA74",
            "purple": "#C4B5FD", "pink": "#F9A8D4", "grey": "#D1D5DB", "gray": "#D1D5DB", "cyan": "#67E8F9"}


def constraint_graph(variables: list[str], edges: list[tuple[str, str, str]], solution: Optional[dict[str, Any]] = None) -> str:
    lines = [f'graph C {{ {_BASE} layout="neato"; overlap=false; sep="+15";']
    for v in variables:
        val = (solution or {}).get(v)
        label = v if val is None else f"{v}\\n{val}"
        fill = _COLOURS.get(str(val).lower(), ACCENT_FILL if val is not None else "white")
        lines.append(f'{_q(v)} [label={_q(label)}, shape=ellipse, fillcolor="{fill}"];')
    for a, b, op in edges:
        lab = "" if op == "!=" else f"label={_q(op)}"
        lines.append(f"{_q(a)} -- {_q(b)} [{lab}];")
    lines.append("}")
    return "\n".join(lines)


def bayes_net(parents: dict[str, list[str]], query: Optional[str] = None, evidence: Optional[dict[str, Any]] = None) -> str:
    evidence = evidence or {}
    lines = [f"digraph B {{ {_BASE} rankdir=TB; nodesep=0.4;"]
    for n in parents:
        attrs = ["shape=ellipse"]
        label = n
        if n in evidence:
            v = evidence[n]
            label += f"\\n= {'true' if v in (True, 'T', 'true', 1) else 'false'}"
            attrs += [f'fillcolor="{VISITED_FILL}"', "style=\"filled,bold\""]
        if n == query:
            attrs += [f'fillcolor="{ACCENT_FILL}"', f'color="{ACCENT}"', "penwidth=2"]
            label += "\\n(query)"
        lines.append(f"{_q(n)} [label={_q(label)}, {', '.join(attrs)}];")
    for n, ps in parents.items():
        for p in ps:
            lines.append(f'{_q(p)} -> {_q(n)} [color="{INK}"];')
    lines.append("}")
    return "\n".join(lines)


def network(layers: list[list[list[float]]], n_inputs: int, activations: Optional[list[list[float]]] = None) -> str:
    """Feed-forward network diagram with weights on the edges (bias weights shown inside each unit)."""
    lines = [f"digraph N {{ {_BASE} rankdir=LR; nodesep=0.5; ranksep=1.4; splines=line;"]
    cols = [[f"x{i + 1}" for i in range(n_inputs)]]
    for l, layer in enumerate(layers):
        cols.append([f"L{l + 1}u{j + 1}" for j in range(len(layer))])
    for i, name in enumerate(cols[0]):
        a = activations[0][i] if activations else None
        lab = name + (f"\\n{fmt(a, 3)}" if a is not None else "")
        lines.append(f'{_q(name)} [label={_q(lab)}, shape=circle, fillcolor="{VISITED_FILL}"];')
    for l, layer in enumerate(layers):
        out = l == len(layers) - 1
        for j, w in enumerate(layer):
            name = cols[l + 1][j]
            a = activations[l + 1][j] if activations else None
            lab = f"{'out' if out else 'h'}{j + 1}\\nb={fmt(w[0], 3)}" + (f"\\na={fmt(a, 3)}" if a is not None else "")
            fill = ACCENT_FILL if out else "white"
            lines.append(f'{_q(name)} [label={_q(lab)}, shape=circle, fillcolor="{fill}"];')
            for i, wi in enumerate(w[1:]):
                colour = ACCENT if wi >= 0 else "#DC2626"
                lines.append(f'{_q(cols[l][i])} -> {_q(name)} [label={_q(fmt(wi, 3))}, color="{colour}", '
                             f'penwidth={0.6 + min(abs(wi), 3):.2f}];')
    lines.append("}")
    return "\n".join(lines)


def implication_graph(rules: list[tuple[list[str], str]], facts: Iterable[str], proved: Iterable[str] = (),
                      query: Optional[str] = None) -> str:
    """AND-OR graph for propositional definite clauses (AIMA Fig 7.16 style)."""
    facts, proved = set(facts), set(proved)
    syms = set(facts)
    for prem, c in rules:
        syms |= set(prem) | {c}
    lines = [f"digraph R {{ {_BASE} rankdir=BT; nodesep=0.35;"]
    for s in sorted(syms):
        attrs = ["shape=ellipse"]
        if s in facts:
            attrs.append(f'fillcolor="{GOOD_FILL}"')
        elif s in proved:
            attrs.append(f'fillcolor="{ACCENT_FILL}"')
        if s == query:
            attrs += ["penwidth=2.5", f'color="{ACCENT}"']
        lines.append(f"{_q(s)} [{', '.join(attrs)}];")
    for i, (prem, c) in enumerate(rules):
        if len(prem) == 1:
            lines.append(f'{_q(prem[0])} -> {_q(c)} [color="{INK}"];')
        else:
            j = f"and{i}"
            lines.append(f'{j} [label="∧", shape=circle, width=0.25, height=0.25, fixedsize=true, fontsize=9];')
            for p in prem:
                lines.append(f'{_q(p)} -> {j} [arrowhead=none, color="{INK}"];')
            lines.append(f'{j} -> {_q(c)} [color="{INK}"];')
    lines.append("}")
    return "\n".join(lines)
