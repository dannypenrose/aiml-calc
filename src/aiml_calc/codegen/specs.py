"""Per-view input specs: turn the UI's current values into the inputs block of each program.

Each spec returns [(NAME, value, comment)]. Values are plain data, or Raw source for expression trees and terms.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from .. import fol as fol_mod
from .. import games as games_mod
from .. import logic as logic_mod
from ..probability import BayesNet, _tf
from .literals import Raw


def num(x: Any) -> Any:
    """Show 15.0 as 15 in generated code; keep real fractions."""
    if isinstance(x, bool):
        return x
    x = float(x)
    return int(x) if x.is_integer() and abs(x) < 1e15 else x


def _list(items: list[str]) -> Raw:
    flat = "[" + ", ".join(items) + "]"
    return Raw(flat if len(flat) <= 90 else "[\n" + "".join(f"    {i},\n" for i in items) + "]")


# ---------------------------------------------------------------------------
# Expression trees (propositional logic) and terms (first-order logic)
# ---------------------------------------------------------------------------

_OPS = {"and": "And", "or": "Or", "imp": "Imp", "iff": "Iff"}


def expr(t) -> str:
    if t[0] == "sym":
        return f'Sym("{t[1]}")'
    if t[0] == "const":
        return "TRUE" if t[1] else "FALSE"
    if t[0] == "not":
        return f"Not({expr(t[1])})"
    return f"{_OPS[t[0]]}({expr(t[1])}, {expr(t[2])})"


def term(t) -> str:
    if isinstance(t, fol_mod.Var):
        return f'Var("{t.name}")'
    return f'Fn("{t.op}"' + "".join(", " + term(a) for a in t.args) + ")"


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def _edges(edges):
    return [(str(e[0]), str(e[1]), num(e[2] if len(e) > 2 else 1)) for e in edges]


def search_trace(algorithm="astar", edges=(), start="", goal="", heuristic=None, mode="graph", directed=False,
                 tie_break="alphabetical", depth_limit=3, max_steps=200, **_):
    return [("ALGORITHM", algorithm, "bfs, dfs, ucs, greedy, astar, dls, ids or idastar"),
            ("MODE", mode, '"graph" keeps an explored set; "tree" does not'),
            ("TIE_BREAK", tie_break, "alphabetical, fifo or lifo"),
            ("DIRECTED", bool(directed), ""), ("START", str(start), ""), ("GOAL", str(goal), ""),
            ("DEPTH_LIMIT", int(depth_limit), "used by depth-limited search"),
            ("MAX_STEPS", int(max_steps), "tree search can loop forever on a graph with cycles, so stop here"),
            ("EDGES", _edges(edges), "(from, to, step cost)"),
            ("H", {str(k): num(v) for k, v in (heuristic or {}).items()}, "estimated cost from each state to the goal")]


def search_heuristic(edges=(), goal="", heuristic=None, directed=False, **_):
    return [("DIRECTED", bool(directed), ""), ("GOAL", str(goal), ""), ("EDGES", _edges(edges), "(from, to, step cost)"),
            ("H", {str(k): num(v) for k, v in (heuristic or {}).items()}, "the heuristic to check")]


# ---------------------------------------------------------------------------
# Propositional logic and SAT
# ---------------------------------------------------------------------------

def truth_table(formulas=(), extra_symbols=None, **_):
    return [("FORMULAS", _list([expr(logic_mod.parse(f)) for f in formulas]), ""),
            ("EXTRA_SYMBOLS", list(extra_symbols or []), "symbols in the problem that don't appear in the formulas")]


def cnf(formula="", **_):
    return [("FORMULA", Raw(expr(logic_mod.parse(formula))), formula)]


def entailment(kb=(), query="", **_):
    trees = [logic_mod.parse(s) for s in kb]
    q = logic_mod.parse(query)
    clauses: list = []
    for t in trees + [("not", q)]:
        for c in logic_mod.tree_to_clauses(logic_mod._distribute(logic_mod._push_not(
                logic_mod._elim_imp(logic_mod._elim_iff(t))))):
            if c not in clauses:
                clauses.append(c)
    cl = [[("" if v else "-") + s for s, v in sorted(c, key=lambda l: (l[0], not l[1]))] for c in clauses]
    return [("KB", _list([expr(t) for t in trees]), ""), ("QUERY", Raw(expr(q)), ""),
            ("CLAUSES", cl, 'clauses of KB & ~QUERY in CNF (see the CNF view); "-X" means not X')]


def chaining(rules=(), facts=(), query="", **_):
    parsed, facts = logic_mod._parse_definite(list(rules), list(facts))
    return [("RULES", [(list(p), c) for p, c, _ in parsed], "(premises, conclusion)"),
            ("FACTS", list(facts), ""), ("QUERY", query, "")]


_COMPACT = re.compile(r"-?[A-Z][A-Z0-9_]*(v-?[A-Z][A-Z0-9_]*)*")


def _clauses(clauses) -> list[list[str]]:
    """Clauses as lists of literals ("-X" = not X), in the order the user typed them."""
    out = []
    for c in clauses:
        text = str(c).strip()
        if _COMPACT.fullmatch(text):
            out.append(text.split("v"))
            continue
        parsed = logic_mod.parse_clause(text)
        order = logic_mod.appearance_order(text)
        lits = sorted(parsed, key=lambda l: (order.get(l[0], 10**6), l[0], not l[1]))
        out.append([("" if v else "-") + s for s, v in lits])
    return out


def dpll(clauses=(), symbol_order=None, use_pure_symbols=True, true_first=True, **_):
    return [("CLAUSES", _clauses(clauses), '"-X" means not X'), ("SYMBOL_ORDER", list(symbol_order or []), ""),
            ("USE_PURE_SYMBOLS", bool(use_pure_symbols), ""), ("TRUE_FIRST", bool(true_first), "")]


def walksat_step(clauses=(), model=None, p=0.5, clause_index=None, **_):
    m = {str(k): (v if isinstance(v, bool) else str(v).lower() in ("t", "true", "1")) for k, v in (model or {}).items()}
    return [("CLAUSES", _clauses(clauses), '"-X" means not X'), ("MODEL", m, "the current complete assignment"),
            ("P", float(p), "probability of a random-walk move"),
            ("CLAUSE_INDEX", int(clause_index or 0), "the false clause WalkSAT picks (from 1); 0 = every false clause")]


def walksat_run(clauses=(), p=0.5, max_flips=100, seed=0, **_):
    return [("CLAUSES", _clauses(clauses), '"-X" means not X'), ("P", float(p), "probability of a random-walk move"),
            ("MAX_FLIPS", int(max_flips), ""), ("SEED", int(seed), "the same seed gives the same run")]


# ---------------------------------------------------------------------------
# First-order logic
# ---------------------------------------------------------------------------

def unify(x="", y="", **_):
    return [("X", Raw(term(fol_mod.parse_term(x))), x), ("Y", Raw(term(fol_mod.parse_term(y))), y)]


def fol_chaining(kb=(), query="", **_):
    rules = [fol_mod.parse_rule(r) for r in kb]
    lines = [f"([{', '.join(term(p) for p in prem)}], {term(c)})" for prem, c in rules]
    return [("KB", Raw("[\n" + "".join(f"    {r},\n" for r in lines) + "]"), "(premises, conclusion); facts have no premises"),
            ("QUERY", Raw(term(fol_mod.parse_term(query))), "")]


# ---------------------------------------------------------------------------
# Constraint satisfaction
# ---------------------------------------------------------------------------

def _csp(variables, domains, constraints):
    vs = [str(v) for v in variables]
    return [("VARIABLES", vs, ""), ("DOMAINS", {v: list(domains[v]) for v in vs}, ""),
            ("CONSTRAINTS", [(str(a), str(op), str(b)) for a, op, b in constraints], "(X, operator, Y)")]


def csp_backtracking(variables=(), domains=None, constraints=(), variable_order="mrv", value_order="lcv",
                     inference="forward_checking", **_):
    return _csp(variables, domains or {}, constraints) + [
        ("VARIABLE_ORDER", variable_order, '"mrv" or "static" (as listed)'),
        ("VALUE_ORDER", value_order, '"lcv" or "static"'),
        ("INFERENCE", inference, '"none", "forward_checking" or "mac"')]


def csp_ac3(variables=(), domains=None, constraints=(), **_):
    return _csp(variables, domains or {}, constraints)


# ---------------------------------------------------------------------------
# Games
# ---------------------------------------------------------------------------

def games(tree=None, use_alpha_beta=True, **_):
    t = games_mod.Tree(tree)
    return [("ROOT", t.root, ""), ("CHILDREN", {k: list(v) for k, v in t.children.items()}, ""),
            ("VALUES", {k: num(v) for k, v in t.values.items()}, "leaf utilities for MAX"),
            ("TYPES", {k: v for k, v in t.types.items() if v != "leaf"}, "max, min or chance"),
            ("PROBABILITIES", {k: [num(p) for p in v] for k, v in t.probs.items()}, "chance node -> child probabilities"),
            ("USE_ALPHA_BETA", bool(use_alpha_beta), "")]


# ---------------------------------------------------------------------------
# Probability
# ---------------------------------------------------------------------------

def bayes_rule(prior=0.01, likelihood=0.9, false_positive_rate=0.05, **_):
    return [("PRIOR", float(prior), "P(H): belief before the evidence"), ("LIKELIHOOD", float(likelihood), "P(E | H)"),
            ("FALSE_POSITIVE_RATE", float(false_positive_rate), "P(E | not H)")]


def bayes_net(nodes=None, query="", evidence=None, **_):
    bn = BayesNet(nodes or {})
    return [("NODES", bn.order, "parents before children"), ("PARENTS", {n: bn.parents[n] for n in bn.order}, ""),
            ("CPT", {n: {k: num(v) for k, v in bn.cpt[n].items()} for n in bn.order},
             "P(node = true | parent values), keyed by the parents' values in order"),
            ("QUERY", query, ""), ("EVIDENCE", {str(k): _tf(v) for k, v in (evidence or {}).items()}, "")]


def joint(variables=(), table=(), query="", evidence=None, **_):
    rows = [tuple(_tf(v) for v in r[:-1]) + (num(r[-1]),) for r in table]
    return [("VARIABLES", list(variables), ""), ("TABLE", rows, "values of each variable, then the probability"),
            ("QUERY", query, ""), ("EVIDENCE", {str(k): _tf(v) for k, v in (evidence or {}).items()}, "")]


def naive_bayes(attributes=(), data=(), query=None, laplace=0.0, **_):
    return [("ATTRIBUTES", list(attributes), ""), ("DATA", [tuple(str(x) for x in r) for r in data],
                                                   "attribute values, then the class"),
            ("QUERY", {str(k): str(v) for k, v in (query or {}).items()}, ""),
            ("K", float(laplace), "Laplace smoothing (0 = raw counts)")]


# ---------------------------------------------------------------------------
# Machine learning
# ---------------------------------------------------------------------------

def _pts(points):
    return [tuple(num(v) for v in p) for p in points]


def kmeans(points=(), centres=(), metric="euclidean", max_iterations=1, **_):
    return [("POINTS", _pts(points), ""), ("CENTRES", _pts(centres), "starting centres; k = how many"),
            ("METRIC", metric, '"euclidean" or "manhattan"'), ("ITERATIONS", int(max_iterations), "")]


def knn(train=(), query=(), k=1, normalise=False, **_):
    return [("TRAIN", [(tuple(num(v) for v in r[:-1]), str(r[-1])) for r in train], "(attributes, class)"),
            ("QUERY", tuple(num(v) for v in query), ""), ("K", int(k), ""),
            ("NORMALISE", bool(normalise), "min-max scale every attribute to [0, 1]")]


def linear_regression(xs=(), ys=(), **_):
    return [("XS", [num(v) for v in xs], ""), ("YS", [num(v) for v in ys], "")]


def gradient_descent(xs=(), ys=(), weights=(0, 0), alpha=0.01, steps=1, mode="batch", **_):
    return [("XS", [num(v) for v in xs], ""), ("YS", [num(v) for v in ys], ""),
            ("WEIGHTS", [float(w) for w in weights], "starting [w0, w1]"), ("ALPHA", float(alpha), "learning rate"),
            ("STEPS", int(steps), ""), ("MODE", mode, '"batch" or "stochastic"')]


def logistic(weights=(0, 0), x=0.0, y=1.0, alpha=0.1, **_):
    return [("WEIGHTS", [float(w) for w in weights], "[w0, w1]"), ("X", float(x), ""),
            ("Y", float(y), "target for the update step"), ("ALPHA", float(alpha), "")]


def neuron(inputs=(), weights=(), **_):
    return [("INPUTS", [float(v) for v in inputs], ""), ("WEIGHTS", [float(w) for w in weights], "[w0 (bias), w1, ...]")]


def perceptron(examples=(), weights=(), alpha=0.1, epochs=1, **_):
    return [("EXAMPLES", [(tuple(num(v) for v in e[:-1]), num(e[-1])) for e in examples], "(inputs, target)"),
            ("WEIGHTS", [float(w) for w in weights], "[w0 (bias), w1, ...]"), ("ALPHA", float(alpha), ""),
            ("EPOCHS", int(epochs), "")]


def network(inputs=(), layers=(), targets=None, alpha=0.1, **_):
    return [("INPUTS", [float(v) for v in inputs], ""),
            ("LAYERS", [[[float(w) for w in unit] for unit in layer] for layer in layers],
             "one list per layer; one [w0, w1, ...] per unit"),
            ("TARGETS", [float(t) for t in (targets or [])], ""), ("ALPHA", float(alpha), "")]


def cnn(input_shape=(32, 32, 3), filter_size=(5, 5), n_filters=6, stride=1, padding=0, **_):
    return [("INPUT_SHAPE", tuple(int(v) for v in input_shape), "width A, height B, depth C"),
            ("FILTER_SIZE", tuple(int(v) for v in filter_size)[:2], "P x Q"), ("FILTERS", int(n_filters), ""),
            ("STRIDE", int(stride), ""), ("PADDING", int(padding), "")]


SPECS: dict[str, Callable[..., list]] = {
    "search_trace": search_trace, "search_heuristic": search_heuristic,
    "truth_table": truth_table, "cnf": cnf, "entailment": entailment, "chaining": chaining,
    "dpll": dpll, "walksat_step": walksat_step, "walksat_run": walksat_run,
    "unify": unify, "fol_chaining": fol_chaining,
    "csp_backtracking": csp_backtracking, "csp_ac3": csp_ac3,
    "games": games,
    "bayes_rule": bayes_rule, "bayes_net": bayes_net, "joint": joint, "naive_bayes": naive_bayes,
    "kmeans": kmeans, "knn": knn, "linear_regression": linear_regression, "gradient_descent": gradient_descent,
    "logistic": logistic, "neuron": neuron, "perceptron": perceptron, "network": network, "cnn": cnn,
}
