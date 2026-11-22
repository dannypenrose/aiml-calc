"""Cross-checks: each algorithm is compared with an independent method on random inputs."""

import itertools
import math
import random

from aiml_calc import logic, ml, sat, search


def _random_cnf(rng, n_syms=4, n_clauses=6):
    syms = "ABCD"[:n_syms]
    out = []
    for _ in range(n_clauses):
        k = rng.randint(1, 3)
        lits = rng.sample(syms, k)
        out.append(" | ".join(("~" if rng.random() < 0.5 else "") + s for s in lits))
    return out


def _brute_sat(clauses):
    cls = [logic.parse_clause(c) for c in clauses]
    syms = sorted({s for c in cls for s, _ in c})
    for bits in itertools.product([False, True], repeat=len(syms)):
        m = dict(zip(syms, bits))
        if all(any(m[s] == v for s, v in c) for c in cls):
            return True
    return False


def test_dpll_agrees_with_brute_force():
    rng = random.Random(1)
    for _ in range(300):
        cnf = _random_cnf(rng)
        r = sat.dpll(cnf)
        assert r["satisfiable"] == _brute_sat(cnf)
        if r["satisfiable"]:
            m = r["model"]
            for c in map(logic.parse_clause, cnf):
                assert any(m.get(s, False) == v for s, v in c) or any(s not in m for s, _ in c)


def test_cnf_is_always_equivalent():
    rng = random.Random(2)
    ops = ["&", "|", "=>", "<=>"]

    def rand(d):
        if d == 0 or rng.random() < 0.3:
            return rng.choice("ABC")
        if rng.random() < 0.2:
            return "~" + rand(d - 1)
        return f"({rand(d - 1)} {rng.choice(ops)} {rand(d - 1)})"

    for _ in range(200):
        assert logic.to_cnf(rand(3))["equivalent"]


def test_resolution_agrees_with_model_checking():
    rng = random.Random(3)
    for _ in range(80):
        kb = _random_cnf(rng, 3, 3)
        q = rng.choice(["A", "~B", "A | C", "B & C"])
        assert logic.resolution(kb, q)["proved"] == logic.entails(kb, q)["entails"]


def test_astar_with_consistent_heuristic_matches_ucs():
    rng = random.Random(4)
    for _ in range(100):
        nodes = [f"N{i}" for i in range(7)]
        edges = [[a, b, rng.randint(1, 9)] for a, b in itertools.combinations(nodes, 2) if rng.random() < 0.4]
        if not edges:
            continue
        hstar = search.true_costs(search.build_graph(edges), {"N6"})
        h = {n: (v * 0.8 if v < math.inf else 0) for n, v in hstar.items()}  # scaled h* is consistent
        u = search.run_search("ucs", edges, "N0", "N6")
        a = search.run_search("astar", edges, "N0", "N6", h)
        assert (u["cost"] is None) == (a["cost"] is None)
        if u["cost"] is not None:
            assert abs(u["cost"] - a["cost"]) < 1e-9
            assert abs(search.run_search("idastar", edges, "N0", "N6", h)["cost"] - u["cost"]) < 1e-9


def test_backprop_matches_numerical_gradient():
    x, t, alpha = [0.7, -0.2], [1.0], 1.0
    layers = [[[0.1, 0.4, -0.3], [-0.2, 0.2, 0.5]], [[0.05, -0.6, 0.9]]]

    def loss(ls):
        return (t[0] - ml.mlp_step(x, ls)["outputs"][0]) ** 2

    upd = ml.mlp_step(x, layers, t, alpha)["new_layers"]
    eps = 1e-6
    for l, layer in enumerate(layers):
        for j, w in enumerate(layer):
            for i in range(len(w)):
                plus = [[r[:] for r in L] for L in layers]
                plus[l][j][i] += eps
                minus = [[r[:] for r in L] for L in layers]
                minus[l][j][i] -= eps
                grad = (loss(plus) - loss(minus)) / (2 * eps)
                # AIMA folds the factor 2 into alpha: Δw = −α/2 · ∂Loss/∂w
                assert abs((upd[l][j][i] - w[i]) - (-alpha / 2 * grad)) < 1e-6


def test_linear_regression_methods_agree():
    r = ml.linear_regression([1, 2, 3, 4], [3, 5, 7, 10])
    assert [round(v, 6) for v in r["weights"]] == [0.5, 2.3]
    gd = ml.gradient_descent([1, 2, 3, 4], [3, 5, 7, 10], [0, 0], alpha=0.02, steps=5000)
    assert [round(v, 3) for v in gd["weights"]] == [0.5, 2.3]


def test_forward_and_backward_chaining_agree():
    rules = ["P => Q", "L & M => P", "B & L => M", "A & P => L", "A & B => L"]
    for q in ["Q", "P", "M", "Z"]:
        assert logic.forward_chaining(rules, ["A", "B"], q)["entails"] == logic.backward_chaining(rules, ["A", "B"], q)["entails"]


def test_server_tools_return_markdown():
    from aiml_calc import server
    out = server.search_trace("astar", [["S", "G", 1]], "S", "G", {"S": 1, "G": 0})
    assert out.startswith("## ASTAR") and "**Answer:**" in out
    assert server.cnf_convert("A =>").startswith("**Error:**")
