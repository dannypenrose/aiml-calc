"""Search algorithms with step-by-step traces (AIMA chapter 3).

Conventions (AIMA's defaults made explicit; every one can be changed by a parameter):

* One step = take a node off the frontier, goal test it, and if it isn't a goal, expand it.
* Goal test when selected for every algorithm except BFS, which tests when a node is generated.
* Graph search: a child is not added if its state is already in the frontier or explored set.
  UCS and A* additionally replace a frontier node when a cheaper path to the same state is found.
* Tree search: no explored set, so states (including the parent) can come back.
* Children are generated in alphabetical (natural) order unless child_order="given".
* Ties in a priority queue are broken alphabetically by state unless tie_break says otherwise,
  and every tie is reported so you can see where an "arbitrary" choice changes the result.
"""

from __future__ import annotations

import heapq
import itertools
import math
from dataclasses import dataclass
from typing import Any, Optional

from .common import fmt, md_table, natural_key

INF = math.inf


# ---------------------------------------------------------------------------
# Problem set-up
# ---------------------------------------------------------------------------

def build_graph(
    edges: list[list[Any]],
    directed: bool = False,
    child_order: str = "alphabetical",
) -> dict[str, list[tuple[str, float]]]:
    """Turn [[from, to, cost], ...] into an adjacency list. Cost defaults to 1."""
    best: dict[tuple[str, str], float] = {}
    order: list[tuple[str, str]] = []
    nodes: list[str] = []

    def add(a: str, b: str, c: float) -> None:
        if (a, b) not in best:
            order.append((a, b))
            best[(a, b)] = c
        else:
            best[(a, b)] = min(best[(a, b)], c)

    for e in edges:
        if len(e) < 2:
            raise ValueError(f"Edge {e!r} needs at least [from, to]")
        a, b = str(e[0]), str(e[1])
        c = float(e[2]) if len(e) > 2 and e[2] is not None else 1.0
        for n in (a, b):
            if n not in nodes:
                nodes.append(n)
        add(a, b, c)
        if not directed:
            add(b, a, c)

    adj: dict[str, list[tuple[str, float]]] = {n: [] for n in nodes}
    for a, b in order:
        adj[a].append((b, best[(a, b)]))
    if child_order == "alphabetical":
        for k in adj:
            adj[k].sort(key=lambda t: natural_key(t[0]))
    elif child_order != "given":
        raise ValueError("child_order must be 'alphabetical' or 'given'")
    return adj


@dataclass
class Node:
    state: str
    parent: Optional["Node"]
    g: float
    depth: int

    def path(self) -> list[str]:
        n: Optional[Node] = self
        out: list[str] = []
        while n is not None:
            out.append(n.state)
            n = n.parent
        return out[::-1]


def _h(h: dict[str, float], s: str) -> float:
    return float(h.get(s, 0.0))


ALGORITHMS = ("bfs", "dfs", "ucs", "greedy", "astar", "dls", "ids", "idastar")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_search(
    algorithm: str,
    edges: list[list[Any]],
    start: str,
    goal: str | list[str],
    heuristic: Optional[dict[str, float]] = None,
    mode: str = "graph",
    directed: bool = False,
    child_order: str = "alphabetical",
    tie_break: str = "alphabetical",
    goal_test: str = "default",
    depth_limit: int = 3,
    max_depth: int = 10,
    max_steps: int = 200,
) -> dict[str, Any]:
    """Run a search and return {'answer', 'path', 'cost', 'expanded', 'steps', 'markdown'}."""
    algorithm = algorithm.lower().replace("*", "star").replace("-", "").replace("_", "")
    aliases = {"a": "astar", "gbfs": "greedy", "greedybestfirst": "greedy", "uniformcost": "ucs",
               "breadthfirst": "bfs", "depthfirst": "dfs", "iterativedeepening": "ids",
               "depthlimited": "dls", "ida": "idastar"}
    algorithm = aliases.get(algorithm, algorithm)
    if algorithm not in ALGORITHMS:
        raise ValueError(f"algorithm must be one of {ALGORITHMS}")
    if mode not in ("graph", "tree"):
        raise ValueError("mode must be 'graph' or 'tree'")
    if tie_break not in ("alphabetical", "fifo", "lifo"):
        raise ValueError("tie_break must be 'alphabetical', 'fifo' or 'lifo'")
    goals = {str(g) for g in (goal if isinstance(goal, list) else [goal])}
    h = {str(k): float(v) for k, v in (heuristic or {}).items()}
    adj = build_graph(edges, directed=directed, child_order=child_order)
    start = str(start)
    if start not in adj:
        adj[start] = []

    if algorithm in ("bfs", "dfs"):
        res = _uninformed_queue(algorithm, adj, start, goals, mode, goal_test, max_steps)
    elif algorithm in ("ucs", "greedy", "astar"):
        res = _best_first(algorithm, adj, start, goals, h, mode, tie_break, goal_test, max_steps)
    elif algorithm == "dls":
        res = _dls_trace(adj, start, goals, depth_limit, max_steps)
    elif algorithm == "ids":
        res = _ids_trace(adj, start, goals, max_depth, max_steps)
    else:
        res = _idastar_trace(adj, start, goals, h, max_steps)

    header = [
        f"## {algorithm.upper()} ({mode + ' search' if algorithm in ('bfs', 'dfs', 'ucs', 'greedy', 'astar') else 'tree search, depth-first'}) from {start} to {', '.join(sorted(goals, key=natural_key))}",
        "",
        f"**Answer:** {res['answer']}",
        "",
    ]
    res["markdown"] = "\n".join(header) + res["markdown"]
    res["algorithm"] = algorithm
    return res


# ---------------------------------------------------------------------------
# BFS / DFS
# ---------------------------------------------------------------------------

def _uninformed_queue(alg, adj, start, goals, mode, goal_test, max_steps):
    test_on_gen = (goal_test == "generation") or (goal_test == "default" and alg == "bfs")
    root = Node(start, None, 0.0, 0)
    conventions = [
        f"Frontier is a {'FIFO queue' if alg == 'bfs' else 'LIFO stack'}.",
        f"Goal test when a node is {'generated' if test_on_gen else 'selected for expansion'}.",
        "Graph search: children already in the frontier or explored set are not added."
        if mode == "graph" else "Tree search: no explored set, so states can repeat.",
    ]
    if alg == "dfs":
        conventions.append("Children are pushed in reverse so the first child (alphabetically) is expanded first.")

    steps: list[dict[str, Any]] = []
    if start in goals:
        return _finish(root, steps, conventions, "start is a goal")

    frontier: list[Node] = [root]
    explored: list[str] = []
    found: Optional[Node] = None
    step = 0
    while frontier and step < max_steps:
        step += 1
        node = frontier.pop(0) if alg == "bfs" else frontier.pop()
        rec: dict[str, Any] = {"step": step, "selected": node.state, "g": node.g, "depth": node.depth,
                               "added": [], "skipped": []}
        if not test_on_gen and node.state in goals:
            rec["goal"] = True
            rec["frontier"] = [n.state for n in frontier]
            rec["explored"] = list(explored)
            steps.append(rec)
            found = node
            break
        if mode == "graph":
            explored.append(node.state)
        children = [Node(s, node, node.g + c, node.depth + 1) for s, c in adj.get(node.state, [])]
        to_add: list[Node] = []
        for ch in children:
            if mode == "graph" and (ch.state in explored or any(n.state == ch.state for n in frontier)
                                    or any(n.state == ch.state for n in to_add)):
                why = "explored" if ch.state in explored else "already in frontier"
                rec["skipped"].append(f"{ch.state} ({why})")
                continue
            to_add.append(ch)
            rec["added"].append(ch.state)
            if test_on_gen and ch.state in goals:
                found = ch
                break
        if alg == "bfs":
            frontier.extend(to_add)
        else:
            frontier.extend(reversed(to_add))
        rec["frontier"] = [n.state for n in frontier] if alg == "bfs" else [n.state for n in reversed(frontier)]
        rec["explored"] = list(explored)
        if found is not None:
            rec["goal_generated"] = found.state
        steps.append(rec)
        if found is not None:
            break

    return _finish(found, steps, conventions, None, frontier_label="Frontier after (next to be taken first)")


def _finish(found, steps, conventions, note, frontier_label="Frontier after"):
    rows = []
    for r in steps:
        sel = r["selected"]
        if r.get("goal"):
            sel += " ✓ goal"
        added = ", ".join(r["added"]) or "–"
        if r.get("goal_generated"):
            added += f" (goal {r['goal_generated']} found on generation)"
        rows.append([str(r["step"]), sel, added, ", ".join(r["skipped"]) or "–",
                     " ".join(r["frontier"]) or "∅", " ".join(r["explored"]) or "–"])
    md = []
    if note:
        md.append(f"_{note}_\n")
    md.append(md_table(["Step", "Selected", "Children added", "Not added", frontier_label, "Explored"], rows))
    md.append("")
    md.append("**Conventions used:** " + " ".join(conventions))
    if found is None:
        answer = "no solution found" + (" (step limit reached)" if steps else "")
        return {"answer": answer, "path": None, "cost": None,
                "expanded": [r["selected"] for r in steps], "steps": steps, "markdown": "\n".join(md)}
    path = found.path()
    answer = f"path {' → '.join(path)}, cost {fmt(found.g)}, {len(steps)} step(s)"
    return {"answer": answer, "path": path, "cost": found.g,
            "expanded": [r["selected"] for r in steps if not r.get("goal")],
            "steps": steps, "markdown": "\n".join(md)}


# ---------------------------------------------------------------------------
# UCS / Greedy / A*
# ---------------------------------------------------------------------------

def _best_first(alg, adj, start, goals, h, mode, tie_break, goal_test, max_steps):
    counter = itertools.count()
    test_on_gen = goal_test == "generation"

    def f_of(n: Node) -> float:
        if alg == "ucs":
            return n.g
        if alg == "greedy":
            return _h(h, n.state)
        return n.g + _h(h, n.state)

    def key(n: Node, c: int):
        if tie_break == "alphabetical":
            return (f_of(n), natural_key(n.state), c)
        if tie_break == "fifo":
            return (f_of(n), c)
        return (f_of(n), -c)

    fname = {"ucs": "g", "greedy": "h", "astar": "f = g + h"}[alg]
    conventions = [
        f"Priority queue ordered by {fname}.",
        "Goal test when a node is selected (not when generated)." if not test_on_gen
        else "Goal test when a node is generated (non-standard for best-first search).",
        f"Ties broken {'alphabetically' if tie_break == 'alphabetical' else ('first-in-first-out' if tie_break == 'fifo' else 'last-in-first-out')}.",
    ]
    if mode == "graph":
        conventions.append("Graph search: children in the explored set are not added; children already in the frontier are not added"
                           + (" unless the new path is cheaper, in which case the frontier entry is replaced." if alg in ("ucs", "astar") else "."))
    else:
        conventions.append("Tree search: no explored set, so the parent and other repeated states come back into the frontier.")

    root = Node(start, None, 0.0, 0)
    entries: list[tuple[Any, int, Node]] = []  # heap of (key, id, node)
    alive: dict[int, Node] = {}
    by_state: dict[str, int] = {}  # graph mode: state -> id in frontier

    def push(n: Node) -> int:
        c = next(counter)
        heapq.heappush(entries, (key(n, c), c, n))
        alive[c] = n
        if mode == "graph":
            by_state[n.state] = c
        return c

    def frontier_view() -> list[Node]:
        return [n for k, c, n in sorted(entries) if c in alive]

    push(root)
    explored: list[str] = []
    steps: list[dict[str, Any]] = []
    found: Optional[Node] = None
    step = 0
    if test_on_gen and start in goals:
        found = root
    while found is None and alive and step < max_steps:
        while entries and entries[0][1] not in alive:
            heapq.heappop(entries)
        k, c, node = heapq.heappop(entries)
        del alive[c]
        if mode == "graph":
            by_state.pop(node.state, None)
        step += 1
        rest = frontier_view()
        fv = f_of(node)
        ties = [n.state for n in rest if abs(f_of(n) - fv) < 1e-12]
        why_parts = [f"{fname.split(' ')[0]} = {fmt(fv)} is lowest"]
        if ties:
            why_parts = [f"tie at {fmt(fv)} with {', '.join(ties)}, broken {'alphabetically' if tie_break == 'alphabetical' else tie_break.upper()}"]
        elif not rest:
            why_parts = ["only node in frontier"]
        rec: dict[str, Any] = {"step": step, "selected": node.state, "g": node.g, "h": _h(h, node.state),
                               "f": fv, "why": why_parts[0], "added": [], "skipped": [], "tie": bool(ties)}
        if not test_on_gen and node.state in goals:
            rec["goal"] = True
            rec["frontier"] = [(n.state, f_of(n)) for n in rest]
            rec["explored"] = list(explored)
            steps.append(rec)
            found = node
            break
        if mode == "graph":
            explored.append(node.state)
        for s, cost in adj.get(node.state, []):
            ch = Node(s, node, node.g + cost, node.depth + 1)
            label = _child_label(alg, ch, h)
            if mode == "graph":
                if s in explored:
                    rec["skipped"].append(f"{s} (explored)")
                    continue
                if s in by_state:
                    old = alive[by_state[s]]
                    if alg in ("ucs", "astar") and ch.g < old.g - 1e-12:
                        del alive[by_state[s]]
                        push(ch)
                        rec["added"].append(f"{label} replaces {s} (g {fmt(old.g)} → {fmt(ch.g)})")
                    else:
                        rec["skipped"].append(f"{s} (already in frontier)")
                    continue
            push(ch)
            rec["added"].append(label)
            if test_on_gen and s in goals:
                found = ch
                rec["goal_generated"] = s
                break
        rec["frontier"] = [(n.state, f_of(n)) for n in frontier_view()]
        rec["explored"] = list(explored)
        steps.append(rec)

    rows = []
    for r in steps:
        sel = f"{r['selected']} ({fname.split(' ')[0]} = {fmt(r['f'])})"
        if r.get("goal"):
            sel += " ✓ goal"
        fr = ", ".join(f"{s}({fmt(v)})" for s, v in r["frontier"]) or "∅"
        compact = "".join(sorted((s for s, _ in r["frontier"]), key=natural_key))
        rows.append([str(r["step"]), sel, r["why"], ", ".join(r["added"]) or "–",
                     ", ".join(r["skipped"]) or "–", f"{fr}  [{compact}]" if fr != "∅" else "∅",
                     " ".join(r["explored"]) or ("–" if mode == "graph" else "n/a")])
    md = [md_table(["Step", "Selected", "Why", "Children added", "Not added", "Frontier after (in priority order) [alphabetical]",
                    "Explored"], rows), ""]
    if any(r["tie"] for r in steps):
        md.append("⚠ **Ties occurred.** A different tie-break rule could change the order of expansion; try the tie_break option.\n")
    md.append("**Conventions used:** " + " ".join(conventions))

    if found is None:
        answer = "no solution found" + (" (step limit reached; tree search may be looping)" if step >= max_steps else "")
        return {"answer": answer, "path": None, "cost": None, "expanded": [r["selected"] for r in steps],
                "steps": steps, "markdown": "\n".join(md)}
    path = found.path()
    answer = f"path {' → '.join(path)}, cost {fmt(found.g)}, found at step {len(steps)}"
    return {"answer": answer, "path": path, "cost": found.g,
            "expanded": [r["selected"] for r in steps if not r.get("goal")],
            "steps": steps, "markdown": "\n".join(md)}


def _child_label(alg, ch: Node, h) -> str:
    if alg == "ucs":
        return f"{ch.state}(g {fmt(ch.g)})"
    if alg == "greedy":
        return f"{ch.state}(h {fmt(_h(h, ch.state))})"
    return f"{ch.state}(g {fmt(ch.g)}, f {fmt(ch.g + _h(h, ch.state))})"


# ---------------------------------------------------------------------------
# Depth-limited, iterative deepening and IDA*
# ---------------------------------------------------------------------------

def _dls_core(adj, node: Node, goals, limit, visits, budget):
    """AIMA recursive depth-limited search (tree search). Returns Node, 'cutoff' or None."""
    if len(visits) >= budget:
        return "cutoff"
    visits.append((node.state, node.depth))
    if node.state in goals:
        return node
    if node.depth == limit:
        return "cutoff"
    cutoff = False
    for s, c in adj.get(node.state, []):
        r = _dls_core(adj, Node(s, node, node.g + c, node.depth + 1), goals, limit, visits, budget)
        if r == "cutoff":
            cutoff = True
        elif r is not None:
            return r
    return "cutoff" if cutoff else None


def _dls_trace(adj, start, goals, limit, max_steps):
    visits: list[tuple[str, int]] = []
    r = _dls_core(adj, Node(start, None, 0.0, 0), goals, limit, visits, max_steps)
    order = " → ".join(f"{s}" for s, _ in visits)
    md = [f"**Visit order (limit {limit}):** {order}", "",
          md_table(["#", "Node", "Depth"], [[str(i + 1), s, str(d)] for i, (s, d) in enumerate(visits)]), "",
          "**Conventions used:** recursive depth-limited tree search (AIMA); goal test when a node is visited; "
          "children visited alphabetically; nodes at the depth limit are not expanded (cutoff)."]
    if isinstance(r, Node):
        p = r.path()
        ans = f"path {' → '.join(p)}, cost {fmt(r.g)}"
        return {"answer": ans, "path": p, "cost": r.g, "expanded": [s for s, _ in visits], "steps": visits,
                "markdown": "\n".join(md)}
    ans = "cutoff (no goal within the depth limit)" if r == "cutoff" else "failure (no goal reachable)"
    return {"answer": ans, "path": None, "cost": None, "expanded": [s for s, _ in visits], "steps": visits,
            "markdown": "\n".join(md)}


def _ids_trace(adj, start, goals, max_depth, max_steps):
    rows = []
    md: list[str] = []
    result = None
    total = 0
    for limit in range(0, max_depth + 1):
        visits: list[tuple[str, int]] = []
        r = _dls_core(adj, Node(start, None, 0.0, 0), goals, limit, visits, max_steps)
        total += len(visits)
        rows.append([str(limit), " ".join(s for s, _ in visits), str(len(visits)),
                     "goal found" if isinstance(r, Node) else ("cutoff" if r == "cutoff" else "failure")])
        if isinstance(r, Node) or r is None:
            result = r
            break
    md.append(md_table(["Depth limit", "Nodes visited (in order)", "Count", "Result"], rows))
    md.append("")
    md.append(f"Total nodes visited across all iterations: **{total}**.")
    md.append("")
    md.append("**Conventions used:** repeated depth-limited tree search with limits 0, 1, 2, …; goal test when visited; "
              "children visited alphabetically.")
    if isinstance(result, Node):
        p = result.path()
        return {"answer": f"path {' → '.join(p)}, cost {fmt(result.g)}, found at depth limit {len(p) - 1}",
                "path": p, "cost": result.g, "expanded": [], "steps": rows, "markdown": "\n".join(md)}
    return {"answer": "no solution within max_depth", "path": None, "cost": None, "expanded": [], "steps": rows,
            "markdown": "\n".join(md)}


def _idastar_trace(adj, start, goals, h, max_steps):
    root = Node(start, None, 0.0, 0)
    threshold = _h(h, start)
    rows = []
    budget = [max_steps]

    def dfs(node: Node, bound: float, visits: list[str], pruned: list[str]):
        f = node.g + _h(h, node.state)
        if f > bound + 1e-12:
            pruned.append(f"{node.state}({fmt(f)})")
            return f, None
        budget[0] -= 1
        visits.append(f"{node.state}({fmt(f)})")
        if node.state in goals:
            return f, node
        if budget[0] <= 0:
            return INF, None
        mn = INF
        on_path = set(node.path())
        for s, c in adj.get(node.state, []):
            if s in on_path:
                continue  # avoid cycling back along the current path
            t, found = dfs(Node(s, node, node.g + c, node.depth + 1), bound, visits, pruned)
            if found is not None:
                return t, found
            mn = min(mn, t)
        return mn, None

    found = None
    while True:
        visits: list[str] = []
        pruned: list[str] = []
        t, found = dfs(root, threshold, visits, pruned)
        rows.append([fmt(threshold), " ".join(visits), ", ".join(pruned) or "–",
                     "goal found" if found else (fmt(t) if t < INF else "∞")])
        if found is not None or t == INF or budget[0] <= 0:
            break
        threshold = t
    md = [md_table(["f-cost threshold", "Nodes visited (f)", "Pruned (f > threshold)", "Next threshold / result"], rows), "",
          "**Conventions used:** IDA* (depth-first within an f-contour); the next threshold is the smallest f of any pruned node; "
          "children visited alphabetically; states already on the current path are skipped."]
    if found is not None:
        p = found.path()
        return {"answer": f"path {' → '.join(p)}, cost {fmt(found.g)}", "path": p, "cost": found.g,
                "expanded": [], "steps": rows, "markdown": "\n".join(md)}
    return {"answer": "no solution found", "path": None, "cost": None, "expanded": [], "steps": rows,
            "markdown": "\n".join(md)}


# ---------------------------------------------------------------------------
# Heuristic analysis
# ---------------------------------------------------------------------------

def true_costs(adj, goals) -> dict[str, float]:
    """h*(n): cheapest real cost from every node to the nearest goal (Dijkstra on reversed edges)."""
    rev: dict[str, list[tuple[str, float]]] = {n: [] for n in adj}
    for a, lst in adj.items():
        for b, c in lst:
            rev.setdefault(b, []).append((a, c))
    dist = {n: INF for n in rev}
    pq: list[tuple[float, str]] = []
    for g in goals:
        dist[g] = 0.0
        heapq.heappush(pq, (0.0, g))
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, c in rev.get(u, []):
            if d + c < dist.get(v, INF):
                dist[v] = d + c
                heapq.heappush(pq, (d + c, v))
    return dist


def check_heuristic(
    edges: list[list[Any]],
    goal: str | list[str],
    heuristic: dict[str, float],
    directed: bool = False,
    compare_with: Optional[dict[str, float]] = None,
) -> dict[str, Any]:
    """Check admissibility (h ≤ h*) and consistency (h(n) ≤ c(n, n') + h(n')) and, optionally, dominance."""
    goals = {str(g) for g in (goal if isinstance(goal, list) else [goal])}
    adj = build_graph(edges, directed=directed)
    h = {str(k): float(v) for k, v in heuristic.items()}
    hstar = true_costs(adj, goals)
    rows = []
    adm_viol = []
    for n in sorted(adj, key=natural_key):
        hn = _h(h, n)
        ok = hn <= hstar.get(n, INF) + 1e-12
        if not ok:
            adm_viol.append(n)
        rows.append([n, fmt(hn), fmt(hstar.get(n, INF)), "✓" if ok else "✗ overestimates"])
    cons_rows = []
    cons_viol = []
    for a in sorted(adj, key=natural_key):
        for b, c in adj[a]:
            lhs, rhs = _h(h, a), c + _h(h, b)
            ok = lhs <= rhs + 1e-12
            if not ok:
                cons_viol.append(f"{a}→{b}")
            cons_rows.append([f"{a} → {b}", fmt(lhs), f"{fmt(c)} + {fmt(_h(h, b))} = {fmt(rhs)}", "✓" if ok else "✗"])
    goal_zero = all(abs(_h(h, g)) < 1e-12 for g in goals)
    md = ["## Heuristic check", "",
          f"**Answer:** admissible: **{'yes' if not adm_viol else 'no'}**"
          f"{'' if not adm_viol else ' (overestimates at ' + ', '.join(adm_viol) + ')'}; "
          f"consistent: **{'yes' if not cons_viol else 'no'}**"
          f"{'' if not cons_viol else ' (fails on ' + ', '.join(cons_viol) + ')'}"
          f"{'' if goal_zero else '; note h(goal) ≠ 0'}.", "",
          "### Admissibility: h(n) ≤ h*(n), the true cheapest cost to a goal",
          md_table(["Node", "h(n)", "h*(n)", "OK?"], rows), "",
          "### Consistency: h(n) ≤ c(n, n') + h(n') for every edge",
          md_table(["Edge", "h(n)", "c + h(n')", "OK?"], cons_rows), ""]
    if not cons_viol and adm_viol:
        md.append("_Consistent but not admissible can only happen if h(goal) > 0._")
    md.append("Reminder: every consistent heuristic is admissible (when h(goal) = 0), not the other way round. "
              "Tree-search A* needs admissible; graph-search A* needs consistent.")
    out = {"admissible": not adm_viol, "consistent": not cons_viol, "h_star": hstar}
    if compare_with:
        h2 = {str(k): float(v) for k, v in compare_with.items()}
        ge = all(_h(h2, n) >= _h(h, n) - 1e-12 for n in adj)
        le = all(_h(h2, n) <= _h(h, n) + 1e-12 for n in adj)
        verdict = ("the second heuristic dominates the first" if ge and not le else
                   "the first heuristic dominates the second" if le and not ge else
                   "they are identical" if ge and le else "neither dominates the other")
        md.append("")
        md.append(f"**Dominance:** {verdict} (h₂ dominates h₁ if h₂(n) ≥ h₁(n) for every n and both are admissible).")
        out["dominance"] = verdict
    out["markdown"] = "\n".join(md)
    return out
