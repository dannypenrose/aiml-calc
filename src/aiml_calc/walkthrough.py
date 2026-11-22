"""Plain-language, step-by-step accounts of how each algorithm reached its answer.

Each function takes the algorithm's result and the inputs that produced it, and returns a list of markdown steps
that use the actual numbers. The app shows them, numbered, under the answer. They are written so a learner can see
the method from the "How it works" panel being applied to this exact problem.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from itertools import product
from typing import Any, Callable

from . import fol, logic
from .common import fmt

MAX_LISTED = 8  # long traces: narrate this many steps, then point to the full working


def _join(items, last="and") -> str:
    items = [str(i) for i in items]
    if not items:
        return "nothing"
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + f" {last} " + items[-1]


def _more(n_total: int) -> str:
    return f"…and {n_total - MAX_LISTED} more step(s) the same way (every one is in the full working below)."


def _answer_line(md: str) -> str:
    m = re.search(r"\*\*Answer:\*\*\s*(.+)", md)
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

_RULES = {
    "bfs": "Breadth-first search always expands the **shallowest** node in the frontier (the oldest one added), "
           "and checks for the goal as soon as a node is generated.",
    "dfs": "Depth-first search always expands the **deepest** node in the frontier (the newest one added).",
    "ucs": "Uniform-cost search always expands the node with the **lowest path cost g(n)** so far.",
    "greedy": "Greedy best-first search always expands the node with the **lowest h(n)**, the estimated cost still to "
              "go. It ignores the cost already paid.",
    "astar": "A\\* always expands the node with the **lowest f(n) = g(n) + h(n)**: cost so far plus estimated cost "
             "still to go.",
    "dls": "Depth-limited search is depth-first search that never expands a node at the depth limit.",
    "ids": "Iterative deepening runs depth-limited search with limit 0, then 1, then 2 and so on, until a limit is "
           "deep enough to reach the goal.",
    "idastar": "IDA\\* runs depth-first search but cuts off any node whose f = g + h is above a threshold. Each new "
               "round raises the threshold to the smallest f that went over it last time.",
}
_WHY = {
    "astar": "A\\* is guaranteed to return the cheapest path when h never overestimates (is admissible). You can check "
             "that on the *Check a heuristic* page.",
    "ucs": "Because uniform-cost search always expands the cheapest path first, the first time it selects the goal, "
           "that path is the cheapest one.",
    "bfs": "BFS finds the path with the **fewest steps**. That is only the cheapest path when every step costs the "
           "same, so compare its cost with uniform-cost search.",
    "dfs": "DFS returns the first path it reaches. It is not guaranteed to be the shortest or the cheapest.",
    "greedy": "Greedy search follows the heuristic, so it is often quick, but it is not guaranteed to find the cheapest "
              "path.",
    "dls": "This is the first path found within the depth limit; it isn't guaranteed to be the cheapest.",
    "ids": "Like BFS, iterative deepening finds the path with the fewest steps, while using only DFS's memory.",
    "idastar": "With an admissible heuristic, IDA\\* returns the cheapest path, like A\\*, using far less memory.",
}


def search_trace(r, algorithm, start, goal, tie_break="alphabetical", depth_limit=3, **_) -> list[str]:
    alg = algorithm
    out = [f"**The rule.** {_RULES[alg]}"]
    steps = r.get("steps") or []
    if alg in ("bfs", "dfs", "ucs", "greedy", "astar"):
        out.append(f"**Start.** The frontier holds only **{start}**.")
        for s in steps[:MAX_LISTED]:
            if alg == "astar":
                score = f"f = g + h = {fmt(s['g'])} + {fmt(s['h'])} = {fmt(s['f'])}"
            elif alg == "ucs":
                score = f"g = {fmt(s['g'])}"
            elif alg == "greedy":
                score = f"h = {fmt(s['h'])}"
            else:
                score = f"depth {s.get('depth', '?')}"
            why = s.get("why")
            reason = f"{score}; {why}" if why else score
            tie = f" There was a tie, broken {tie_break}." if s.get("tie") else ""
            added = [a for a in s["added"] if " replaces " not in a]
            cheaper = [re.match(r"(\S+?)\(.*?\) replaces \S+ \((.+)\)", a) for a in s["added"] if " replaces " in a]
            line = (f"**Step {s['step']}.** Expand **{s['selected']}** ({reason}).{tie} "
                    f"Add {_join(added) if added else 'nothing new'} to the frontier.")
            for m in filter(None, cheaper):
                line += f" It also found a cheaper path to {m.group(1)} ({m.group(2)}), so that frontier entry is replaced."
            if s.get("skipped"):
                line += f" Skip {_join(s['skipped'])}."
            out.append(line)
        if len(steps) > MAX_LISTED:
            out.append(_more(len(steps)))
    elif alg == "dls":
        visited = ", ".join(f"{n} (depth {d})" for n, d in steps[:12]) + (" …" if len(steps) > 12 else "")
        out.append(f"**Explore.** With limit {depth_limit}, it goes as deep as it can along the first branch, then backs "
                   f"up. Nodes visited in order: {visited}.")
    elif alg == "ids":
        for row in steps[:MAX_LISTED]:
            limit, nodes, count, outcome = row[:4]
            out.append(f"**Limit {limit}.** Visit {nodes} ({count} node(s)): {outcome}.")
    elif alg == "idastar":
        for row in steps[:MAX_LISTED]:
            thr, expanded, over, nxt = (list(row) + ["", "", "", ""])[:4]
            line = f"**Threshold {thr}.** Expand {expanded or 'nothing'}."
            if over:
                line += f" Cut off {over} (f above {thr})."
            if nxt and re.fullmatch(r"[\d.]+", str(nxt)):
                line += f" The smallest f that went over is {nxt}, so that becomes the next threshold."
            elif nxt:
                line += f" {str(nxt)[:1].upper()}{str(nxt)[1:]}."
            out.append(line)
    if r.get("path"):
        path = " → ".join(r["path"])
        when = "generated" if alg == "bfs" else "selected for expansion"
        out.append(f"**Goal reached.** {goal} is {when}, so the search stops. Following each node's parent back to the "
                   f"start gives **{path}**, with total cost **{fmt(r['cost'])}**.")
        out.append(f"**Why this answer.** {_WHY[alg]}")
    else:
        out.append(f"**No path.** The search ran out of nodes to try (or hit its limit) without reaching {goal}.")
    return out


def search_heuristic(r, edges, goal, heuristic, directed=False, **_) -> list[str]:
    hs = r["h_star"]
    h = lambda n: float(heuristic.get(n, 0.0))  # noqa: E731
    out = ["**True costs first.** Run uniform-cost search outward from the goal to find h\\*(n), the real cheapest "
           "cost from each node to " + goal + ": " + ", ".join(f"h\\*({n}) = {fmt(v)}" for n, v in hs.items()) + "."]
    over = [f"h({n}) = {fmt(h(n))} > h\\*({n}) = {fmt(v)}" for n, v in hs.items() if h(n) > v + 1e-9]
    out.append("**Admissible?** A heuristic is admissible if it never overestimates: h(n) ≤ h\\*(n) for every node. "
               + (f"It fails at {_join(over)}." if over else "Every node passes."))
    arcs = [(e[0], e[1], float(e[2]) if len(e) > 2 else 1.0) for e in edges]
    if not directed:
        arcs += [(b, a, c) for a, b, c in arcs]
    bad = [f"{a}→{b}: h({a}) = {fmt(h(a))} > {fmt(c)} + h({b}) = {fmt(c + h(b))}" for a, b, c in arcs
           if h(a) > c + h(b) + 1e-9]
    out.append("**Consistent?** Along every edge n → n′ with cost c, the estimate must not drop by more than the step "
               "costs: h(n) ≤ c + h(n′). "
               + (f"It fails on {_join(bad[:4])}" + (f" and {len(bad) - 4} more" if len(bad) > 4 else "") + "."
                  if bad else "Every edge passes."))
    verdict = ("admissible and consistent, so A\\* is optimal with both tree and graph search"
               if r["admissible"] and r["consistent"] else
               "admissible but not consistent, so A\\* tree search is optimal, but graph search may need to reopen nodes"
               if r["admissible"] else
               "not admissible, so A\\* may return a path that isn't the cheapest")
    out.append(f"**So** the heuristic is {verdict}.")
    return out


# ---------------------------------------------------------------------------
# Propositional logic
# ---------------------------------------------------------------------------

def truth_table(r, formulas, **_) -> list[str]:
    syms, total = r["symbols"], r["total"]
    out = [f"**List every model.** {len(syms)} symbol(s) ({_join(syms)}) give 2^{len(syms)} = {total} rows, one for "
           "each way of setting them true or false.",
           "**Work out each formula in each row**, from the innermost brackets outwards, using the tables for ¬, ∧, ∨, "
           "⇒ and ⇔. Remember A ⇒ B is false only when A is true and B is false."]
    for f, c in r["counts"].items():
        kind = ("**valid** (true in every model)" if c == total else
                "**unsatisfiable** (true in no model)" if c == 0 else "**satisfiable** (true in some models)")
        out.append(f"**Count.** `{f}` is true in {c} of {total} rows, so it is {kind}.")
    return out


def cnf(r, formula, **_) -> list[str]:
    md = r["markdown"]
    out = [f"**Start** with `{formula}`. CNF means an AND of clauses, where each clause is an OR of literals."]
    rules = re.findall(r"^\d+\.\s+(.+)$", md.split("### Method 2")[0], re.M)
    for line in rules:
        out.append(f"**{line.split(':', 1)[0]}.** {line.split(':', 1)[1].strip() if ':' in line else ''}")
    out.append(f"**Read off the clauses:** {_answer_line(md).split('Compact')[0].strip()}")
    out.append("**Check.** Building the truth table of the original and the CNF shows they agree on every row"
               + (", so the conversion is correct." if r.get("equivalent") else ". They don't, so something is wrong."))
    return out


def entailment(r, kb, query, **_) -> list[str]:
    ent, res = r
    syms = set()
    for s in list(kb) + [query]:
        syms |= logic.symbols(logic.parse(s))
    n = len(syms)
    out = [f"**Model checking.** List all 2^{n} = {2 ** n} models of the {n} symbols ({_join(sorted(syms))}).",
           f"**Keep the models of the knowledge base:** {ent['kb_models']} model(s) make every KB sentence true.",
           f"**Check the query** `{query}` in each of those. "
           + ("It is true in all of them, so **KB ⊨ α**." if ent["entails"] else
              "It is false in at least one, so the KB does **not** entail it: that model is a counterexample."),
           f"**Resolution, a second method.** Add the negated query ¬({query}) to the KB and convert everything to "
           "clauses. If KB ⊨ α, then KB ∧ ¬α must be a contradiction.",
           "**Resolve** pairs of clauses that contain a symbol and its negation, cancelling that pair to make a new "
           "clause. " + ("This eventually produces the **empty clause**, a contradiction, so the query is proved."
                         if res["proved"] else
                         "No new clauses can be made and the empty clause never appears, so the query isn't proved."),
           "**Both methods agree**." if res["proved"] == ent["entails"] else "**The two methods disagree**: check the input."]
    return out


def _horn(rules):
    out = []
    for rule in rules:
        lhs, rhs = rule.replace("⇒", "=>").split("=>")
        out.append(([p.strip() for p in re.split(r"&|∧", lhs) if p.strip()], rhs.strip(), rule))
    return out


def chaining(r, rules, facts, query, **_) -> list[str]:
    fc, bc = r
    parsed = _horn(rules)
    known = list(dict.fromkeys(facts))
    out = [f"**Forward chaining starts from the facts:** {_join(known)}. It fires any rule whose premises are all "
           "known, and adds the conclusion."]
    for sym in fc["inferred"]:
        if sym in known:
            continue
        rule = next((rl for prem, concl, rl in parsed if concl == sym and all(p in known for p in prem)), None)
        known.append(sym)
        if rule:
            out.append(f"`{rule}`: all premises are known, so add **{sym}**.")
        if sym == query:
            break
    out.append(f"**Forward result:** {query} " + ("is derived." if fc["entails"] else
                                                   "is never derived; no more rules can fire."))
    proof: list[str] = []

    def prove(q, active):
        """Return the explanation lines for a successful proof of q, or None."""
        if q in facts:
            return []
        if q in active:
            return None  # would go round in a circle
        for prem, concl, rl in parsed:
            if concl != q:
                continue
            sub, ok = [], True
            for p_ in prem:
                got = prove(p_, active | {q})
                if got is None:
                    ok = False
                    break
                sub += got
            if ok:
                given = [p_ for p_ in prem if p_ in facts]
                note = f" ({_join(given)} given)" if given else ""
                return sub + [f"**{q}** via `{rl}`{note}"]
        return None

    found = prove(query, frozenset())
    if found is not None:
        proof = list(dict.fromkeys(found))
        out.append(f"**Backward chaining works from the goal instead.** To prove {query} it looks for a rule that "
                   "concludes it, then tries to prove that rule's premises the same way, until it reaches given facts. "
                   "Branches that would go round in a circle are abandoned. The proof it finds, from the bottom up: "
                   + "; ".join(proof) + ".")
    else:
        out.append(f"**Backward chaining works from the goal instead**, looking for a rule that concludes {query} and "
                   "trying to prove its premises, but every route either needs an unknown symbol or goes round in a "
                   "circle.")
    out.append(f"**Backward result:** {query} " + ("is proved. Both directions agree." if bc["entails"] else
                                                    "can't be proved from the facts."))
    return out


# ---------------------------------------------------------------------------
# SAT
# ---------------------------------------------------------------------------

def dpll(r, clauses, symbol_order=None, use_pure_symbols=True, true_first=True, **_) -> list[str]:
    out = ["**Simplify before guessing.** " + (
        "A *pure symbol* appears with only one sign in the remaining clauses, so it can safely be set to make those "
        "clauses true. " if use_pure_symbols else "The pure symbol rule is turned off here. ")
           + "A *unit clause* has only one unassigned literal left, so that literal must be true.",
           f"**Then branch.** When neither rule applies, take the next symbol in order "
           f"({_join(symbol_order) if symbol_order else 'alphabetical'}) and try "
           f"{'true' if true_first else 'false'} first."]
    summ = r.get("step_summary") or []
    for line in summ[:MAX_LISTED]:
        label, _, body = line.partition(":")
        parts = [p.strip() for p in body.split(",")]
        outcome = parts[-1] if parts and "=" not in parts[-1] else ""
        assign = ", ".join(p for p in parts if "=" in p)
        expl = (" A clause has every literal false, so this branch fails: back up and try the other value."
                if outcome == "fail" else " Every clause is now satisfied." if outcome else "")
        out.append(f"**{label.replace('Step', 'Try')}.** {assign}.{expl}")
    if len(summ) > MAX_LISTED:
        out.append(_more(len(summ)))
    if r["satisfiable"]:
        model = ", ".join(f"{k}={'true' if v else 'false'}" for k, v in (r.get("model") or {}).items())
        out.append(f"**Satisfiable.** The model {model} makes every clause true.")
    else:
        out.append("**Unsatisfiable.** Every branch ended in a false clause, so no assignment satisfies all the "
                   "clauses.")
    return out


def walksat_step(r, clauses, model, p, clause_index=0, **_) -> list[str]:
    falses = r.get("false_clauses") or []
    m = ", ".join(f"{k}={v}" for k, v in model.items())
    if not falses:
        return [f"**Check the model** {m} against every clause: all are true.",
                "**Done.** The model already satisfies everything, so WalkSAT stops here."]
    out = [f"**Check the model** {m} against every clause. False: "
           + _join([f"c{i} `{clauses[i - 1]}`" for i in falses]) + ".",
           (f"**Pick a false clause.** Clause c{clause_index} is fixed here." if clause_index else
            "**Pick a false clause** at random from those."),
           f"**Choose what to flip.** With probability p = {fmt(p)}, flip a random symbol from that clause (a random "
           f"walk). Otherwise, with probability 1 − p = {fmt(1 - p)}, flip the symbol whose flip leaves the fewest "
           "clauses false (greedy)."]
    reach = r.get("reachable") or {}
    out.append("**Possible moves:** " + _join([f"flip {s} ({' or '.join(ways)})" for s, ways in reach.items()]) + ".")
    return out


def walksat_run(r, clauses, p, max_flips, seed, **_) -> list[str]:
    rows = re.findall(r"^\|\s*(\d+)\s*\|\s*(c\d+)\s*\|\s*(\w+)\s*\|\s*(\w+)\s*\|", r["markdown"], re.M)
    out = [f"**Start** from a random complete assignment (seed {seed}, so the run repeats exactly).",
           f"**Each flip:** pick a false clause at random. With probability p = {fmt(p)} flip a random symbol in it; "
           "otherwise flip the symbol that leaves the fewest clauses false."]
    for n, c, mode, sym in rows[:MAX_LISTED]:
        out.append(f"**Flip {n}.** Clause {c} is false; {mode} choice: flip **{sym}**.")
    if len(rows) > MAX_LISTED:
        out.append(_more(len(rows)))
    if r["solved"]:
        model = ", ".join(f"{k}={'true' if v else 'false'}" for k, v in r["model"].items())
        out.append(f"**Solved** after {len(rows)} flip(s): {model} makes every clause true.")
    else:
        out.append(f"**Gave up** after {max_flips} flips. WalkSAT can't prove a problem has no solution; it only stops "
                   "looking.")
    return out


# ---------------------------------------------------------------------------
# First-order logic
# ---------------------------------------------------------------------------

def unify(r, x, y, **_) -> list[str]:
    md = r["markdown"]
    out = [f"**Compare from the outside in.** `{x}` and `{y}` must have the same predicate or function name and the "
           "same number of arguments; then unify the arguments one at a time, left to right."]
    for line in md.splitlines():
        line = line.strip(" -")
        m = re.match(r"bind \*\*(\w+)/(.+?)\*\*", line)
        if m:
            out.append(f"**Bind {m.group(1)} to {m.group(2)}.** A variable can stand for any term that doesn't "
                       f"contain it (the occur check). Substitute it everywhere before carrying on.")
        elif re.search(r"fail|clash|occur", line, re.I) and "Answer" not in line:
            out.append(f"**Stop.** {line}")
    if r.get("unifier") is not None:
        out.append(f"**Result.** {_answer_line(md)} This is the *most general* unifier: it binds only what it has to.")
    else:
        ans = _answer_line(md) or "they do not unify."
        out.append(f"**Result.** {ans[:1].upper()}{ans[1:]}")
    return out


def fol_chaining(r, kb, query, **_) -> list[str]:
    fc, bc = r
    given = [s.strip() for s in kb if "=>" not in s and "⇒" not in s]
    rules = [s for s in kb if "=>" in s or "⇒" in s]
    new = [f for f in fc["facts"] if f not in given]
    out = [f"**Forward chaining starts from the {len(given)} given fact(s).** In each round, every rule is matched "
           "against the known facts. Any substitution that makes all its premises known facts adds the conclusion, "
           "with that substitution applied.",
           f"**Derived over {fc['rounds']} round(s):** {_join(new) if new else 'nothing new'}.",
           f"**Forward result:** {query} " + ("is among them, so it's proved." if fc["proved"] else "is never derived.")]
    for rule in rules:
        concl = re.split(r"=>|⇒", rule)[1].strip()
        u = fol.unify(concl, query).get("unifier")
        if u is not None:
            prem = re.split(r"=>|⇒", rule)[0].strip()
            theta = ", ".join(f"{k}/{v}" for k, v in u.items()) or "no bindings"
            out.append(f"**Backward chaining starts from the query.** `{query}` unifies with the conclusion of "
                       f"`{rule}` ({theta}), so it now has to prove `{prem}` with those bindings, one premise at a time. "
                       "Each time it uses a rule it renames the rule's variables first (standardising apart).")
            break
    out.append(f"**Backward result:** {query} " + ("is proved. Both directions agree." if bc["proved"] else
                                                    "can't be proved."))
    return out


# ---------------------------------------------------------------------------
# CSP
# ---------------------------------------------------------------------------

_INFER = {"forward_checking": "After each assignment, remove now-impossible values from the neighbours' domains "
                              "(forward checking). If a neighbour's domain empties, this choice is already a dead end.",
          "mac": "After each assignment, run AC-3 on the arcs into the variable just set (MAC), pruning further ahead.",
          "none": "There's no pruning ahead: a value is only rejected when it is tried and clashes with an assigned "
                  "neighbour."}


def csp_backtracking(r, variables, domains, constraints, variable_order="mrv", value_order="lcv",
                     inference="forward_checking", **_) -> list[str]:
    out = ["**Pick a variable.** " + (
        "MRV: the one with the fewest values left; ties go to the variable involved in the most constraints with "
        "unassigned variables (degree)." if variable_order == "mrv" else "In the order listed."),
           "**Pick a value.** " + ("Least constraining value: the one that removes the fewest options from the "
                                   "neighbours." if value_order == "lcv" else "In the order listed."),
           f"**Look ahead.** {_INFER[inference]}",
           "**Back up on a dead end.** If a variable has no values left, undo the most recent choice and try its next "
           "value."]
    out.append(f"**Here** it made {r['assignments']} assignment(s) and backtracked {r['backtracks']} time(s).")
    if r["solution"]:
        order = " (in the order assigned)" if r["backtracks"] == 0 else ""
        out.append(f"**Solution{order}:** " + ", ".join(f"{k} = {v}" for k, v in r["solution"].items())
                   + ". Every constraint is satisfied.")
    else:
        out.append("**No solution.** Every option ran into a dead end.")
    return out


def csp_ac3(r, variables, domains, constraints, **_) -> list[str]:
    out = ["**Fill a queue with every arc.** Each constraint between X and Y gives two arcs, (X, Y) and (Y, X).",
           "**Revise each arc (X, Y):** remove any value of X that has no compatible value left in Y. If X lost a "
           "value, put the arcs (Z, X) back in the queue for X's other neighbours, because their support may have "
           "gone."]
    for v in variables:
        removed = [x for x in domains[v] if x not in r["domains"].get(v, [])]
        if removed:
            out.append(f"**{v}** loses {_join(removed)}, leaving {{{', '.join(str(x) for x in r['domains'][v]) or '∅'}}}.")
    if r["consistent"]:
        out.append("**The queue empties** with no domain empty, so the problem is arc consistent. That narrows the "
                   "search but doesn't always solve it: backtracking finishes the job.")
    else:
        out.append("**A domain became empty**, so the problem has no solution.")
    return out


# ---------------------------------------------------------------------------
# Games
# ---------------------------------------------------------------------------

def games(r, tree, use_alpha_beta=True, **_) -> list[str]:
    t, vals = r["tree"], r["values"]
    pruned = set(r.get("pruned") or [])
    has_chance = "chance" in t.types.values()
    out = ["**Leaves** hold the utility for MAX. Values are passed up the tree: a MAX node takes its **largest** "
           "child, a MIN node its **smallest**" + (", and a chance node the probability-weighted **average**"
                                                   if has_chance else "") + "."]
    order = []

    def post(n):
        for c in t.children.get(n, []):
            post(c)
        if t.children.get(n):
            order.append(n)

    post(t.root)
    order = [n for n in order if n in vals]  # a whole subtree can be pruned
    for n in order[:MAX_LISTED + 2]:
        kids = [c for c in t.children[n] if c in vals]
        typ = t.types.get(n, "max")
        shown = ", ".join(f"{c} = {fmt(vals[c])}" for c in kids)
        skipped = [c for c in t.children[n] if c not in vals]
        if typ == "chance":
            probs = t.probs.get(n, [])
            calc = " + ".join(f"{fmt(p)}×{fmt(vals[c])}" for p, c in zip(probs, t.children[n]) if c in vals)
            line = f"**{n}** (chance) = {calc} = **{fmt(vals[n])}**."
        else:
            word = "largest" if typ == "max" else "smallest"
            line = f"**{n}** ({typ.upper()}) sees {shown} and takes the {word}: **{fmt(vals[n])}**."
        if skipped:
            parent = next((q for q, cs in t.children.items() if n in cs), None)
            before = []
            if parent:
                sibs = t.children[parent]
                before = [vals[c] for c in sibs[:sibs.index(n)] if c in vals]
            if before and typ == "min":
                line += (f" Once it sees {fmt(vals[n])}, {n} is worth at most {fmt(vals[n])}, but MAX already has "
                         f"{fmt(max(before))} from an earlier move (α = {fmt(max(before))}), so {_join(skipped)} can't "
                         f"change the decision and {'is' if len(skipped) == 1 else 'are'} pruned.")
            elif before and typ == "max":
                line += (f" Once it sees {fmt(vals[n])}, {n} is worth at least {fmt(vals[n])}, but MIN already has "
                         f"{fmt(min(before))} from an earlier move (β = {fmt(min(before))}), so {_join(skipped)} can't "
                         f"change the decision and {'is' if len(skipped) == 1 else 'are'} pruned.")
            else:
                line += f" {_join(skipped)} pruned: they can't change the decision."
        out.append(line)
    best = r.get("best_move") or next((c for c in t.children.get(t.root, []) if vals.get(c) == r["value"]), None)
    out.append(f"**Decision.** The root is worth **{fmt(r['value'])}**, so MAX's best move is **{best}**.")
    if use_alpha_beta:
        out.append("**Why pruning is safe.** α is the best value MAX can already guarantee and β the best MIN can. "
                   "Once a MIN node finds a child worth ≤ α, MAX will never let play reach it, so its remaining "
                   "children can't change the decision. "
                   + (f"Here {_join(sorted(pruned))} were never evaluated, and the answer is the same as plain minimax."
                      if pruned else "Here nothing could be pruned, because no branch was ruled out early."))
    return out


# ---------------------------------------------------------------------------
# Probability
# ---------------------------------------------------------------------------

def bayes_rule(r, prior, likelihood, false_positive_rate, **_) -> list[str]:
    pe, post = r["p_evidence"], r["posterior"]
    a, b = likelihood * prior, false_positive_rate * (1 - prior)
    return [f"**Start with the prior:** P(H) = {fmt(prior)}, so P(¬H) = {fmt(1 - prior)}.",
            f"**How likely is the evidence overall?** P(E) = P(E|H)P(H) + P(E|¬H)P(¬H) = {fmt(likelihood)}×{fmt(prior)}"
            f" + {fmt(false_positive_rate)}×{fmt(1 - prior)} = {fmt(a)} + {fmt(b)} = **{fmt(pe)}**.",
            f"**Apply Bayes' rule:** P(H|E) = P(E|H)P(H) / P(E) = {fmt(a)} / {fmt(pe)} = **{fmt(post)}**.",
            f"**In counts.** Picture 1,000 cases: about {fmt(1000 * prior)} have H, and {fmt(1000 * a)} of those show "
            f"E. Of the {fmt(1000 * (1 - prior))} without H, {fmt(1000 * b)} also show E. So of everyone showing E, the "
            f"share with H is {fmt(1000 * a)} / {fmt(1000 * pe)} ≈ {fmt(post)}."]


def bayes_net(r, nodes, query, evidence, **_) -> list[str]:
    hidden = [v for v in r["order"] if v != query and v not in evidence]
    ev = ", ".join(f"{k}={'true' if v else 'false'}" for k, v in evidence.items()) or "no evidence"
    sums = re.findall(r"Σ for ¬?" + re.escape(query) + r" = ([0-9.e-]+)", r["markdown"])
    term = next((l[2:] for l in r["markdown"].splitlines() if l.startswith("- ") and "×" in l), "")
    out = [f"**Set up.** We want P({query} | {ev}). The other variables, {_join(hidden) if hidden else 'none'}, are "
           "hidden, so we sum over every combination of their values.",
           "**Each term is a product of table entries** (the chain rule): P(x₁, …, xₙ) = Π P(xᵢ | parents(xᵢ)), one "
           "entry from each node's table." + (f" For example: {term}." if term else "")]
    if hidden:
        out.append(f"**Sum** that product over the {2 ** len(hidden)} combinations of {_join(hidden)}, once with "
                   f"{query} = true and once with {query} = false.")
    if len(sums) >= 2:
        t, f = sums[0], sums[1]
        out.append(f"**The two sums:** {t} for {query} = true and {f} for {query} = false. These aren't "
                   "probabilities yet: they still include P(evidence).")
        out.append(f"**Normalise** so they add to 1: P({query} = true | evidence) = {t} / ({t} + {f}) "
                   f"= **{fmt(r['distribution']['true'])}**.")
    else:
        out.append(f"**Normalise** so the two values add to 1: P({query} = true | evidence) = "
                   f"**{fmt(r['distribution']['true'])}**.")
    return out


def joint(r, variables, table, query, evidence, **_) -> list[str]:
    qi = variables.index(query)
    match = lambda row: all(str(row[variables.index(k)]).upper().startswith("T") == bool(v)  # noqa: E731
                            for k, v in evidence.items())
    rows = [row for row in table if match(row)]
    a = sum(row[-1] for row in rows if str(row[qi]).upper().startswith("T"))
    b = sum(row[-1] for row in rows if not str(row[qi]).upper().startswith("T"))
    ev = ", ".join(f"{k}={'true' if v else 'false'}" for k, v in evidence.items()) or "no evidence"
    return [f"**Keep the rows that match the evidence** ({ev}): {len(rows)} of {len(table)} rows. Their total, "
            f"{fmt(a + b)}, is P(evidence).",
            f"**Split them by {query}:** rows with {query} = true add up to {fmt(a)}; rows with {query} = false add up "
            f"to {fmt(b)}.",
            f"**Normalise:** P({query} = true | evidence) = {fmt(a)} / {fmt(a + b)} = **{fmt(r['distribution']['true'])}**"
            f", and false = {fmt(b)} / {fmt(a + b)} = {fmt(r['distribution']['false'])}."]


def naive_bayes(r, attributes, data, query, laplace=0.0, **_) -> list[str]:
    classes = Counter(row[-1] for row in data)
    n = len(data)
    values = {a: {str(row[i]) for row in data} for i, a in enumerate(attributes)}
    out = [f"**Priors from class frequencies:** " + ", ".join(f"P({c}) = {k}/{n}" for c, k in classes.items()) + ".",
           "**Assume the attributes are independent given the class** (the 'naive' part), so P(class | x) is "
           "proportional to P(class) × P(x₁ | class) × P(x₂ | class) × …"
           + (f" Laplace k = {fmt(laplace)} is added to every count so no value gets probability 0." if laplace else "")]
    for c, k in classes.items():
        parts, score = [f"{k}/{n}"], k / n
        for a, v in query.items():
            if a not in attributes:
                continue
            i = attributes.index(a)
            num = sum(1 for row in data if row[-1] == c and str(row[i]) == str(v)) + laplace
            den = k + laplace * len(values[a])
            parts.append(f"{fmt(num)}/{fmt(den)}")
            score *= num / den if den else 0.0
        out.append(f"**Score for {c}:** {' × '.join(parts)} = {fmt(score)}.")
    post = r["posterior"]
    out.append("**Normalise** the scores so they add to 1: " + ", ".join(f"P({c} | x) = {fmt(p)}" for c, p in post.items())
               + f". The most probable class is **{r['prediction']}**.")
    return out


# ---------------------------------------------------------------------------
# Machine learning
# ---------------------------------------------------------------------------

def _pt(p):
    return "(" + ", ".join(fmt(v) for v in p) + ")"


def kmeans(r, points, centres, metric="euclidean", max_iterations=1, **_) -> list[str]:
    names = [chr(65 + i) for i in range(len(centres))]
    prev = centres
    out = [f"**Start** with {len(centres)} centres: " + ", ".join(f"{n} at {_pt(c)}" for n, c in zip(names, centres))
           + f". Each round has two steps: assign, then update. Distance is {metric}."]
    for i, h in enumerate(r["history"][:4], 1):
        groups = {n: [_pt(p) for p, a in zip(points, h["assignment"]) if a == n] for n in names}
        out.append(f"**Round {i}, assign.** Each point joins its nearest centre: "
                   + "; ".join(f"{n} gets {_join(g) if g else 'no points'}" for n, g in groups.items()) + ".")
        out.append(f"**Round {i}, update.** Move each centre to the mean of its points: "
                   + ", ".join(f"{n} {_pt(a)} → {_pt(b)}" for n, a, b in zip(names, prev, h["centres"])) + ".")
        prev = h["centres"]
    if len(r["history"]) < max_iterations:
        out.append("**Stop.** The centres didn't move in the last round, so the clusters are stable.")
    else:
        out.append(f"**Stop** after the {max_iterations} round(s) requested. More rounds may still move the centres.")
    return out


def knn(r, train, query, k, normalise=False, **_) -> list[str]:
    X = [[float(v) for v in row[:-1]] for row in train]
    q = [float(v) for v in query]
    if normalise:
        cols = list(zip(*X, q))
        lo, hi = [min(c) for c in cols], [max(c) for c in cols]
        nz = lambda v: [(x - a) / (b - a) if b > a else 0.0 for x, a, b in zip(v, lo, hi)]  # noqa: E731
        X, q = [nz(x) for x in X], nz(q)
    ranked = sorted((math.dist(x, q), i) for i, x in enumerate(X))
    top = ranked[:k]
    votes = Counter(train[i][-1] for _, i in top)
    out = []
    if normalise:
        out.append("**Normalise** each attribute to the range 0 to 1, so no attribute dominates just because of its units.")
    out.append(f"**Measure** the straight-line distance from {_pt(query)} to every training example: "
               + ", ".join(f"{_pt(train[i][:-1])} → {fmt(d)}" for d, i in ranked[:6]) + (" …" if len(ranked) > 6 else "")
               + ".")
    out.append(f"**Take the {k} nearest:** " + _join([f"{_pt(train[i][:-1])} ({train[i][-1]})" for _, i in top]) + ".")
    out.append("**Vote:** " + ", ".join(f"{c}: {v}" for c, v in votes.items())
               + f". The prediction is **{r['prediction']}**.")
    return out


def linear_regression(r, xs, ys, **_) -> list[str]:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    w0, w1 = r["weights"]
    return [f"**Means:** x̄ = {fmt(mx)}, ȳ = {fmt(my)}.",
            f"**Slope:** w₁ = Σ(x − x̄)(y − ȳ) / Σ(x − x̄)² = {fmt(sxy)} / {fmt(sxx)} = **{fmt(w1)}**. It measures how "
            "much y rises, on average, for each unit of x.",
            f"**Intercept:** w₀ = ȳ − w₁x̄ = {fmt(my)} − {fmt(w1)}×{fmt(mx)} = **{fmt(w0)}**, so the line passes "
            "through the point of means.",
            f"**Loss:** the sum of squared residuals, Σ(y − (w₀ + w₁x))², is {fmt(r['loss'])}. No other straight line "
            "makes it smaller."]


def gradient_descent(r, xs, ys, weights, alpha, steps, mode="batch", **_) -> list[str]:
    L = r["losses"]
    w0, w1 = weights
    errs = [y - (w0 + w1 * x) for x, y in zip(xs, ys)]
    out = [f"**Start** at w = [{fmt(w0)}, {fmt(w1)}], where the loss Σ(y − h(x))² is {fmt(L[0])}."]
    if mode == "batch":
        g0, g1 = sum(errs), sum(e * x for e, x in zip(errs, xs))
        out.append(f"**First update (batch).** Errors y − h(x) are {', '.join(fmt(e) for e in errs)}. "
                   f"w₀ ← w₀ + α Σ(y − h) = {fmt(w0)} + {fmt(alpha)}×{fmt(g0)} = {fmt(w0 + alpha * g0)}; "
                   f"w₁ ← w₁ + α Σ(y − h)x = {fmt(w1)} + {fmt(alpha)}×{fmt(g1)} = {fmt(w1 + alpha * g1)}.")
    else:
        e, x = errs[0], xs[0]
        out.append(f"**First update (stochastic, one example at a time).** For x = {fmt(x)}: error {fmt(e)}, so "
                   f"w₀ ← {fmt(w0)} + {fmt(alpha)}×{fmt(e)} = {fmt(w0 + alpha * e)} and "
                   f"w₁ ← {fmt(w1)} + {fmt(alpha)}×{fmt(e)}×{fmt(x)} = {fmt(w1 + alpha * e * x)}.")
    out.append("**Each update moves the weights downhill** on the loss surface, by a step proportional to α. "
               "The 2 from differentiating the square is folded into α, as in AIMA.")
    picks = sorted({0, 1, 2, min(5, len(L) - 1), len(L) - 1})
    out.append("**Loss as it trains:** " + ", ".join(f"update {i}: {fmt(L[i])}" for i in picks if i < len(L)) + ".")
    trend = ("It keeps falling" if L[-1] < L[0] else "It grows: α is too large and every step overshoots")
    out.append(f"**Result.** {trend}. After {steps} update(s) w = [{', '.join(fmt(v) for v in r['weights'])}]; "
               "with more steps it approaches the least-squares line from the *Linear regression* page.")
    return out


def logistic(r, weights, x, y=1.0, alpha=0.1, **_) -> list[str]:
    z, h = r["linear"], r["probability"]
    return [f"**Linear score:** z = w₀ + w₁x = {fmt(weights[0])} + {fmt(weights[1])}×{fmt(x)} = {fmt(z)}.",
            f"**Squash it into a probability** with the logistic function: h = 1 / (1 + e^(−z)) = **{fmt(h)}**. "
            f"Above 0.5 means class 1, so this predicts class {1 if h >= 0.5 else 0}.",
            f"**One learning step** with target y = {fmt(y)} and α = {fmt(alpha)}. The error is y − h = {fmt(y - h)}.",
            f"**AIMA's rule** (gradient of squared error): wᵢ ← wᵢ + α(y − h)·h(1 − h)·xᵢ gives "
            f"[{', '.join(fmt(v) for v in r['aima_update'])}].",
            f"**Log-likelihood rule** (the usual one in practice): wᵢ ← wᵢ + α(y − h)·xᵢ gives "
            f"[{', '.join(fmt(v) for v in r['log_likelihood_update'])}]. Both move the weights so h gets closer to y."]


def neuron(r, inputs, weights, **_) -> list[str]:
    terms = " + ".join([fmt(weights[0])] + [f"{fmt(w)}×{fmt(x)}" for w, x in zip(weights[1:], inputs)])
    o = r["outputs"]
    return [f"**Weighted sum:** in = w₀ + Σ wᵢxᵢ = {terms} = **{fmt(r['linear'])}**. The bias w₀ shifts where the "
            "neuron switches on.",
            "**Apply an activation function** to get the output: "
            + ", ".join(f"{name} → {fmt(v)}" for name, v in o.items() if name != "linear") + ".",
            f"**Reading it.** The threshold unit fires (outputs 1) because in {'≥' if r['linear'] >= 0 else '<'} 0"
            + ("" if r["linear"] >= 0 else ", so it outputs 0 instead") + ". The others give a graded output instead "
            "of a hard yes or no."]


def perceptron(r, examples, weights, alpha, epochs, **_) -> list[str]:
    w = [float(v) for v in weights]
    out = [f"**Start** with w = [{', '.join(fmt(v) for v in w)}]. For each example, predict h = 1 if "
           "w₀ + w₁x₁ + w₂x₂ ≥ 0, otherwise 0. If the prediction is wrong, update wᵢ ← wᵢ + α(y − h)xᵢ (with x₀ = 1)."]
    updates, converged = [], None
    for ep in range(1, epochs + 1):
        changed = False
        for ex in examples:
            x, y = [1.0] + [float(v) for v in ex[:-1]], float(ex[-1])
            h = 1.0 if sum(a * b for a, b in zip(w, x)) >= 0 else 0.0
            if h != y:
                w = [wi + alpha * (y - h) * xi for wi, xi in zip(w, x)]
                changed = True
                updates.append(f"**Epoch {ep}, example {_pt(ex[:-1])}:** predicted {fmt(h)}, target {fmt(y)}, so "
                               f"w → [{', '.join(fmt(v) for v in w)}].")
        if not changed:
            converged = ep
            break
    out += updates[:MAX_LISTED]
    if len(updates) > MAX_LISTED:
        out.append(f"…and {len(updates) - MAX_LISTED} more update(s).")
    if converged:
        out.append(f"**Epoch {converged}** gets every example right, so learning stops: the weights "
                   f"[{', '.join(fmt(v) for v in r['weights'])}] define a line that separates the two classes.")
    else:
        out.append(f"**After {epochs} epoch(s)** there are still mistakes, so the weights keep changing. If they never "
                   "settle, the classes can't be separated by a straight line (XOR is the classic example).")
    return out


def network(r, inputs, layers, targets, alpha, **_) -> list[str]:
    sig = lambda z: 1 / (1 + math.exp(-z))  # noqa: E731
    acts, out = [list(inputs)], []
    for li, layer in enumerate(layers, 1):
        a_prev, layer_a, parts = acts[-1], [], []
        for j, w in enumerate(layer, 1):
            z = w[0] + sum(a * b for a, b in zip(w[1:], a_prev))
            layer_a.append(sig(z))
            parts.append(f"unit {j}: in = {fmt(z)}, a = σ(in) = {fmt(layer_a[-1])}")
        acts.append(layer_a)
        name = "Output layer" if li == len(layers) else f"Layer {li}"
        out.append(f"**Forward, {name.lower()}.** Weighted sum then logistic: " + "; ".join(parts) + ".")
    d = r["deltas"]
    out.append("**Output error.** Δ = (y − a)·a(1 − a): "
               + ", ".join(f"({fmt(t)} − {fmt(a)})×{fmt(a)}×{fmt(1 - a)} = {fmt(dk)}"
                           for t, a, dk in zip(targets, acts[-1], d[-1])) + ".")
    if len(d) > 1:
        out.append("**Pass the error back.** Each hidden unit's Δⱼ = aⱼ(1 − aⱼ) Σₖ wⱼₖΔₖ, blaming it in proportion to "
                   "its weight into the next layer: " + ", ".join(fmt(v) for v in d[-2]) + ".")
    new_out = r["new_layers"][-1][0]
    out.append(f"**Update every weight:** wᵢⱼ ← wᵢⱼ + α·aᵢ·Δⱼ with α = {fmt(alpha)}. The output unit's weights become "
               f"[{', '.join(fmt(v) for v in new_out)}], nudging the output towards the target.")
    return out


def cnn(r, input_shape, filter_size, n_filters, stride, padding, **_) -> list[str]:
    A, B, C = input_shape
    P, Q = filter_size
    W, H, D = r["output"]
    per = P * Q * C + 1
    return [f"**Width:** (A − P + 2·padding) / stride + 1 = ({A} − {P} + 2×{padding}) / {stride} + 1 = **{W}**. "
            "That's how many positions the filter fits across.",
            f"**Height:** ({B} − {Q} + 2×{padding}) / {stride} + 1 = **{H}**.",
            f"**Depth:** one output layer per filter, so **{D}**.",
            f"**Neurons:** {W} × {H} × {D} = **{r['neurons']:,}**, one per output value.",
            f"**Weights:** each filter has {P}×{Q}×{C} = {P * Q * C} weights plus 1 bias = {per}, and they're **shared** "
            f"across every position. So {n_filters} × {per} = **{r['weights']:,}** in total, far fewer than one per "
            "connection."]


STEPS: dict[str, Callable[..., list[str]]] = {
    "search_trace": search_trace, "search_heuristic": search_heuristic, "truth_table": truth_table, "cnf": cnf,
    "entailment": entailment, "chaining": chaining, "dpll": dpll, "walksat_step": walksat_step,
    "walksat_run": walksat_run, "unify": unify, "fol_chaining": fol_chaining, "csp_backtracking": csp_backtracking,
    "csp_ac3": csp_ac3, "games": games, "bayes_rule": bayes_rule, "bayes_net": bayes_net, "joint": joint,
    "naive_bayes": naive_bayes, "kmeans": kmeans, "knn": knn, "linear_regression": linear_regression,
    "gradient_descent": gradient_descent, "logistic": logistic, "neuron": neuron, "perceptron": perceptron,
    "network": network, "cnn": cnn,
}


def steps(key: str, result: Any, **params) -> list[str]:
    return STEPS[key](result, **params)
