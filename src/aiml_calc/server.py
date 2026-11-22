"""MCP server exposing every calculator as a tool. Each tool returns a markdown result + step-by-step working."""

from __future__ import annotations

import functools
from typing import Any, Callable, Optional

from . import csp, fol, games, logic, ml, probability, sat, search

try:  # MCP Python SDK 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # MCP Python SDK 1.x
    from mcp.server.fastmcp import FastMCP as _Server  # type: ignore

INSTRUCTIONS = (
    "Exact, step-by-step implementations of classic AI and ML algorithms from Russell & Norvig's AIMA: search, "
    "propositional and first-order logic, SAT, constraint satisfaction, game search, probability and machine learning. "
    "Use them to compute or verify any trace or numeric result rather than working it out mentally. Every result starts with **Answer:** and ends with the conventions used (tie-breaking, "
    "goal-test timing, etc.); if the problem uses a different convention, pass the matching parameter and rerun."
)

mcp = _Server("aiml-calc", instructions=INSTRUCTIONS)


def _safe(fn: Callable[..., dict[str, Any]]) -> Callable[..., str]:
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        try:
            return fn(*args, **kwargs)["markdown"]
        except Exception as e:  # report input problems to the model instead of crashing the tool
            return f"**Error:** {e}"
    return wrapper


# ---------------------------------------------------------------- search

@mcp.tool()
def search_trace(
    algorithm: str,
    edges: list[list[Any]],
    start: str,
    goal: str,
    heuristic: Optional[dict[str, float]] = None,
    mode: str = "graph",
    directed: bool = False,
    child_order: str = "alphabetical",
    tie_break: str = "alphabetical",
    goal_test: str = "default",
    depth_limit: int = 3,
    max_depth: int = 10,
    max_steps: int = 200,
) -> str:
    """Trace a search algorithm step by step (selected node, children added/skipped, frontier, explored set).

    algorithm: bfs | dfs | ucs | greedy | astar | dls | ids | idastar
    edges: [[from, to, cost], ...]; cost defaults to 1. Undirected unless directed=true.
    heuristic: {"state": h, ...} for greedy / astar / idastar.
    mode: "graph" (explored set; don't re-add states in frontier/explored) or "tree" (no explored set).
    child_order: "alphabetical" or "given" (order edges were listed). tie_break: alphabetical | fifo | lifo.
    goal_test: "default" (BFS on generation, everything else on selection), "generation" or "selection".
    """
    return _safe(search.run_search)(algorithm, edges, start, goal, heuristic, mode, directed, child_order,
                                    tie_break, goal_test, depth_limit, max_depth, max_steps)


@mcp.tool()
def heuristic_check(edges: list[list[Any]], goal: str, heuristic: dict[str, float], directed: bool = False,
                    compare_with: Optional[dict[str, float]] = None) -> str:
    """Is a heuristic admissible (h ≤ true cost) and consistent (h(n) ≤ c(n,n') + h(n'))? Optionally compare two for dominance."""
    return _safe(search.check_heuristic)(edges, goal, heuristic, directed, compare_with)


# ---------------------------------------------------------------- logic

@mcp.tool()
def truth_table(formulas: list[str], extra_symbols: Optional[list[str]] = None) -> str:
    """Truth table and model count for one or more formulas. Syntax: ¬ ~ ! -, ∧ &, ∨ |, ⇒ =>, ⇔ <=>.
    extra_symbols: symbols in the problem that don't appear in the formula (they still double the model count)."""
    return _safe(logic.truth_table)(formulas, extra_symbols)


@mcp.tool()
def cnf_convert(formula: str) -> str:
    """Convert a formula to CNF with each rewrite step, plus the compact form (e.g. -BvSvW) and a truth-table check."""
    return _safe(logic.to_cnf)(formula)


@mcp.tool()
def entailment_check(kb: list[str], query: str) -> str:
    """Does KB ⊨ query? Method 1: model checking (truth table). Method 2: resolution refutation."""
    def both(kb, query):
        a = logic.entails(kb, query)
        b = logic.resolution(kb, query)
        return {"markdown": a["markdown"] + "\n\n---\n\n" + b["markdown"]}
    return _safe(both)(kb, query)


@mcp.tool()
def resolution_proof(kb: list[str], query: Optional[str] = None) -> str:
    """Resolution: convert KB ∧ ¬query to clauses and derive the empty clause, listing each resolvent used."""
    return _safe(logic.resolution)(kb, query)


@mcp.tool()
def forward_chaining(rules: list[str], facts: list[str], query: str) -> str:
    """Forward chaining over definite clauses (e.g. "L & M => P") with the agenda and count table at every step."""
    return _safe(logic.forward_chaining)(rules, facts, query)


@mcp.tool()
def backward_chaining(rules: list[str], facts: list[str], query: str) -> str:
    """Backward chaining over definite clauses, shown as an indented goal tree (checked against forward chaining)."""
    return _safe(logic.backward_chaining)(rules, facts, query)


# ---------------------------------------------------------------- SAT

@mcp.tool()
def dpll_trace(clauses: list[str], symbol_order: Optional[list[str]] = None, use_pure_symbols: bool = True,
               true_first: bool = True) -> str:
    """DPLL as a step summary ("Step 1: A=true, B=true, C=true, fail") plus a detailed trace.
    clauses: ["A | ~B | C", ...] or compact ["Av-BvC", ...]. Unit clauses are taken in the order given."""
    return _safe(sat.dpll)(clauses, symbol_order, use_pure_symbols, true_first)


@mcp.tool()
def walksat_step(clauses: list[str], model: dict[str, bool], p: float = 0.5, clause_index: Optional[int] = None) -> str:
    """One WalkSAT step: which clauses are false, the satisfied-clause count after each possible flip, the greedy choice,
    and every assignment reachable in one step. clause_index (1-based) fixes which false clause is picked."""
    return _safe(sat.walksat_step)(clauses, model, p, clause_index)


@mcp.tool()
def walksat_run(clauses: list[str], p: float = 0.5, max_flips: int = 100, seed: int = 0,
                model: Optional[dict[str, bool]] = None) -> str:
    """A full randomised WalkSAT run for practice (repeatable with a seed)."""
    return _safe(sat.walksat_run)(clauses, p, max_flips, seed, model)


# ---------------------------------------------------------------- ML

@mcp.tool()
def neuron_output(inputs: list[float], weights: list[float], activation: str = "all") -> str:
    """Output of one neuron. weights = [w0 (bias), w1, ...]. activation: all | threshold | logistic | relu | tanh | linear."""
    return _safe(ml.neuron)(inputs, weights, activation)


@mcp.tool()
def hypothesis_check(examples: list[list[float]], hypotheses: list[list[float]], activation: str = "threshold",
                     names: Optional[list[str]] = None) -> str:
    """Which linear classifiers get every example right? examples: [[x1, ..., y]]; hypotheses: [[w0, w1, ...]]."""
    return _safe(ml.check_hypotheses)(examples, hypotheses, activation, names)


@mcp.tool()
def weight_update(examples: list[list[float]], weights: list[float], alpha: float = 0.1, epochs: int = 1,
                  activation: str = "threshold") -> str:
    """Perceptron (threshold) or logistic single-example weight updates, one row per example. examples: [[x1, ..., y]]."""
    return _safe(ml.perceptron_learning)(examples, weights, alpha, epochs, activation)


@mcp.tool()
def linear_regression_fit(X: list[Any], y: list[float]) -> str:
    """Least-squares linear regression. Univariate: two closed-form methods. Multivariate: normal equations."""
    return _safe(ml.linear_regression)(X, y)


@mcp.tool()
def gradient_descent_steps(X: list[Any], y: list[float], weights: list[float], alpha: float = 0.01, steps: int = 1,
                           mode: str = "batch", fold_two: bool = True) -> str:
    """Gradient descent on squared error for a linear model. mode: batch | stochastic. weights = [w0, w1, ...]."""
    return _safe(ml.gradient_descent)(X, y, weights, alpha, steps, mode, fold_two)


@mcp.tool()
def logistic_regression_calc(x: list[float], weights: list[float], y: Optional[float] = None,
                             alpha: Optional[float] = None) -> str:
    """Logistic regression probability, and (with y and alpha) one update step under both common rules."""
    return _safe(ml.logistic_regression)(x, weights, y, alpha)


@mcp.tool()
def kmeans_step(points: list[list[float]], centres: list[list[float]], names: Optional[list[str]] = None,
                metric: str = "euclidean", max_iterations: int = 1) -> str:
    """k-means: distance table, assignments, new centres (and quality measures). Ties go to the first centre."""
    return _safe(ml.kmeans)(points, centres, names, metric, max_iterations)


@mcp.tool()
def knn_classify(train: list[list[Any]], query: list[float], k: int = 1, metric: str = "euclidean",
                 normalise: bool = False) -> str:
    """k-nearest-neighbour classification. train rows: [a1, ..., an, label]. Optional min-max normalisation."""
    return _safe(ml.knn)(train, query, k, metric, normalise)


@mcp.tool()
def cnn_layer_size(input_shape: list[int], filter_size: list[int], n_filters: int, stride: int = 1,
                   padding: int = 0) -> str:
    """Convolutional layer output volume, number of neurons and number of (shared) weights.
    input_shape: [A, B, C]; filter_size: [P, Q] or [P, Q, C]."""
    return _safe(ml.cnn_layer)(input_shape, filter_size, n_filters, stride, padding)


@mcp.tool()
def fc_layer_weights(input_shape: list[int], n_neurons: int) -> str:
    """Weights in a fully connected layer: (inputs + 1) × neurons."""
    return _safe(ml.fc_layer)(input_shape, n_neurons)


@mcp.tool()
def mlp_forward_backprop(inputs: list[float], layers: list[list[list[float]]], targets: Optional[list[float]] = None,
                         alpha: float = 0.1, activation: str = "logistic") -> str:
    """Forward pass through a feed-forward network and, with targets, one back-propagation step (AIMA Fig 18.24).
    layers[l][j] = weights [w0, w1, ...] of unit j in layer l."""
    return _safe(ml.mlp_step)(inputs, layers, targets, alpha, activation)


# ---------------------------------------------------------------- first-order logic

@mcp.tool()
def fol_unify(x: str, y: str) -> str:
    """Most general unifier of two first-order terms or atoms, e.g. "Knows(John, x)" and "Knows(y, Mother(y))".
    Variables start lower-case; constants, functions and predicates start upper-case."""
    return _safe(fol.unify)(x, y)


@mcp.tool()
def fol_forward_chaining(kb: list[str], query: str) -> str:
    """First-order forward chaining over definite clauses ("A(x) & B(x, y) => C(y)" or ground facts), round by round."""
    return _safe(fol.forward_chaining)(kb, query)


@mcp.tool()
def fol_backward_chaining(kb: list[str], query: str) -> str:
    """First-order backward chaining: depth-first proof tree with variables renamed apart for each rule use."""
    return _safe(fol.backward_chaining)(kb, query)


# ---------------------------------------------------------------- constraint satisfaction

@mcp.tool()
def csp_backtracking(variables: list[str], domains: dict[str, list[Any]], constraints: Optional[list[list[Any]]] = None,
                     neighbours: Optional[dict[str, list[str]]] = None, variable_order: str = "mrv",
                     value_order: str = "lcv", inference: str = "forward_checking") -> str:
    """Backtracking search for a CSP. constraints: [[X, op, Y]] with op in != == < > <= >=; or neighbours
    {X: [Y, ...]} meaning X != Y (map colouring). variable_order: static | mrv. value_order: static | lcv.
    inference: none | forward_checking | mac."""
    return _safe(csp.backtracking)(variables, domains, constraints, neighbours, variable_order, value_order, inference)


@mcp.tool()
def csp_ac3(variables: list[str], domains: dict[str, list[Any]], constraints: Optional[list[list[Any]]] = None,
            neighbours: Optional[dict[str, list[str]]] = None) -> str:
    """AC-3 arc consistency: every arc revision, the values removed and the arcs re-queued."""
    return _safe(csp.ac3)(variables, domains, constraints, neighbours)


# ---------------------------------------------------------------- game search

@mcp.tool()
def game_minimax(tree: Any, root_type: str = "max") -> str:
    """Minimax / expectiminimax values for a game tree. tree: nested lists of leaf utilities (levels alternate MAX, MIN)
    or {"children": {...}, "values": {...}, "types": {"B": "chance"}, "probabilities": {"B": [0.5, 0.5]}}."""
    return _safe(games.minimax)(tree, root_type)


@mcp.tool()
def game_alphabeta(tree: Any, root_type: str = "max") -> str:
    """Alpha-beta pruning, left to right: α and β at every node, which subtrees are pruned, checked against minimax."""
    return _safe(games.alphabeta)(tree, root_type)


# ---------------------------------------------------------------- probability

@mcp.tool()
def bayes_rule(prior: float, likelihood: float, false_positive_rate: float, hypothesis: str = "H",
               evidence: str = "E") -> str:
    """P(H | E) from P(H), P(E | H) and P(E | ¬H), by formula and by natural frequencies."""
    return _safe(probability.bayes_rule)(prior, likelihood, false_positive_rate, hypothesis, evidence)


@mcp.tool()
def joint_distribution_query(variables: list[str], table: list[list[Any]], query: str,
                             evidence: Optional[dict[str, Any]] = None) -> str:
    """P(query | evidence) from a full joint table of Boolean variables. Rows: [v1, v2, ..., probability]."""
    return _safe(probability.joint_query)(variables, table, query, evidence)


@mcp.tool()
def bayes_net_query(nodes: dict[str, dict[str, Any]], query: str, evidence: Optional[dict[str, Any]] = None) -> str:
    """Exact inference in a Bayesian network by enumeration, checked against the full joint distribution.
    nodes: {"Alarm": {"parents": ["Burglary", "Earthquake"], "cpt": {"T,T": 0.95, "T,F": 0.94, "F,T": 0.29, "F,F": 0.001}},
    "Burglary": {"cpt": {"": 0.001}}, ...}; CPT values are P(node = true | parents)."""
    return _safe(probability.bayes_net_query)(nodes, query, evidence)


@mcp.tool()
def naive_bayes_classify(attributes: list[str], data: list[list[Any]], query: dict[str, Any], laplace: float = 0.0) -> str:
    """Naive Bayes classification from categorical data rows [attr values..., class], with optional Laplace smoothing."""
    return _safe(probability.naive_bayes)(attributes, data, query, laplace)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
