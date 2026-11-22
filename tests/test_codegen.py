"""Every generated Python program must run and print the same answer as the library, for the UI's example
inputs and for variations. If one fails, the code shown in the app doesn't match what the app computes."""

import json
import re

import pytest

from aiml_calc import csp, fol, games, logic, ml, probability, sat, search
from aiml_calc.codegen import SPECS, generate
from aiml_calc.codegen.runner import run


def answer(source: str) -> str:
    r = run(source)
    assert r.ok, r.error
    lines = [l for l in r.output.splitlines() if l.startswith("Answer: ")]
    assert lines, r.output
    return lines[-1][len("Answer: "):]


def numbers(s: str) -> list[float]:
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", s)]


def close(a: str, b: list[float], tol: float = 1e-3):
    got = numbers(a)
    assert len(got) == len(b) and all(abs(x - y) <= tol for x, y in zip(got, b)), (a, b)


ROADS = [["H", "L", 15], ["H", "T", 12], ["T", "M", 5], ["T", "Y", 6], ["L", "W", 9], ["L", "Y", 10], ["Y", "P", 11],
         ["M", "P", 10], ["M", "S", 7], ["M", "Y", 4], ["P", "W", 14]]
H = dict(H=20, L=17, S=19, T=12, M=10, W=12, Y=8, P=0)
CRANE = [["B", "E", 3], ["E", "B", 3], ["E", "F", 10], ["F", "C", 7], ["F", "E", 3], ["C", "A", 3], ["C", "F", 7]]
CRANE_H = dict(A=0, B=20, C=3, D=5, E=16, F=9)


def fmt(x):
    from aiml_calc.common import fmt as f
    return f(x)


@pytest.mark.parametrize("alg", search.ALGORITHMS)
@pytest.mark.parametrize("case", ["roads", "roads-tree-fifo", "crane"])
def test_search(alg, case):
    if case == "crane":
        params = dict(edges=CRANE, start="B", goal="A", heuristic=CRANE_H, directed=True, mode="tree")
    else:
        params = dict(edges=ROADS, start="H", goal="P", heuristic=H)
        if case == "roads-tree-fifo":
            if alg in ("bfs", "dfs"):
                pytest.skip("tree-search BFS/DFS on an undirected graph is tested with graph mode")
            params.update(mode="tree", tie_break="fifo")
    lib = search.run_search(alg, **params)
    got = answer(generate("search_trace", algorithm=alg, **params))
    expected = "no solution" if lib["path"] is None else f"path {' -> '.join(lib['path'])}, cost {fmt(lib['cost'])}"
    assert got == expected


def test_heuristic():
    lib = search.check_heuristic(ROADS, "P", H)
    got = answer(generate("search_heuristic", edges=ROADS, goal="P", heuristic=H))
    assert got == f"admissible {'yes' if lib['admissible'] else 'no'}, consistent {'yes' if lib['consistent'] else 'no'}"


@pytest.mark.parametrize("formulas,extra", [(["(A => B) & A", "A | ~A", "A & ~A"], []),
                                            (["B & ~D", "C | A | ~C"], ["A", "B", "C", "D"]),
                                            (["A <=> (B | C)"], [])])
def test_truth_table(formulas, extra):
    lib = logic.truth_table(formulas, extra or None)
    got = answer(generate("truth_table", formulas=formulas, extra_symbols=extra))
    assert got == ", ".join(f"{c}/{lib['total']}" for c in lib["counts"].values())


@pytest.mark.parametrize("formula", ["(B & ~S) => W", "(~B & S) => ~L", "A <=> (B | C)", "~(A & B) | (C & D)",
                                     "A | ~A", "(P => Q) & (Q => R)"])
def test_cnf(formula):
    lib = set(frozenset(c.split("v")) for c in logic.to_cnf(formula)["clauses"])
    got = answer(generate("cnf", formula=formula))
    got_set = set() if got.startswith("(no clauses") else set(frozenset(c.split("v")) for c in got.split(", "))
    assert got_set == lib


@pytest.mark.parametrize("kb,q", [(["A => B", "A"], "B"), (["A => B", "B"], "A"),
                                  (["~P11", "B11 <=> (P12 | P21)", "B21 <=> (P11 | P22 | P31)", "~B11", "B21"], "~P12")])
def test_entailment(kb, q):
    ent = logic.entails(kb, q)["entails"]
    word = "yes" if ent else "no"
    assert answer(generate("entailment", kb=kb, query=q)) == f"KB entails query: {word} (model checking {word}, resolution {word})"


@pytest.mark.parametrize("q", ["Q", "M", "Z"])
def test_chaining(q):
    rules, facts = ["P => Q", "L & M => P", "B & L => M", "A & P => L", "A & B => L"], ["A", "B"]
    fc = logic.forward_chaining(rules, facts, q)["entails"]
    bc = logic.backward_chaining(rules, facts, q)["entails"]
    got = answer(generate("chaining", rules=rules, facts=facts, query=q))
    assert got == f"forward chaining {'yes' if fc else 'no'}, backward chaining {'yes' if bc else 'no'}"


DPLL_CASES = [(["A | B", "A | ~B | C", "~A | B", "~A | ~B | C", "~B | ~C"], ["A", "B", "C"], True, True),
              (["~A|B", "~B|~C", "A|B", "A|C", "A|D", "B|C", "B|D", "C|D"], ["A", "B", "C", "D"], True, True),
              (["A | B", "~A | B", "~B | C", "~C | A"], [], True, True),
              (["AvB", "-Av-B", "Av-C"], ["C", "B", "A"], False, False)]


@pytest.mark.parametrize("clauses,order,pure,tf", DPLL_CASES)
def test_dpll(clauses, order, pure, tf):
    lib = sat.dpll(clauses, order or None, pure, tf)
    r = run(generate("dpll", clauses=clauses, symbol_order=order, use_pure_symbols=pure, true_first=tf))
    assert r.ok, r.error
    assert [l for l in r.output.splitlines() if l.startswith("Step ")] == lib["step_summary"]


def test_dpll_random_agrees():
    import random
    rng = random.Random(9)
    for _ in range(15):
        clauses = [" | ".join(("~" if rng.random() < .5 else "") + s for s in rng.sample("ABCD", rng.randint(1, 3)))
                   for _ in range(rng.randint(3, 7))]
        lib = sat.dpll(clauses)
        r = run(generate("dpll", clauses=clauses))
        assert [l for l in r.output.splitlines() if l.startswith("Step ")] == lib["step_summary"], clauses


@pytest.mark.parametrize("model,p,idx", [({"A": False, "B": False, "C": True}, 0.0, 3),
                                         ({"A": False, "B": False, "C": True}, 0.5, 0),
                                         ({"A": True, "B": True, "C": True}, 1.0, 0)])
def test_walksat_step(model, p, idx):
    clauses = ["A | B", "A | ~B", "A | B | ~C"]
    lib = sat.walksat_step(clauses, model, p, idx or None)
    got = answer(generate("walksat_step", clauses=clauses, model=model, p=p, clause_index=idx))
    if not lib.get("reachable"):
        assert got == "every clause is already satisfied"
    else:
        assert got == "; ".join(f"flip {s} ({' and '.join(sorted(h))})" for s, h in sorted(lib["reachable"].items()))


@pytest.mark.parametrize("seed", [0, 1, 7])
def test_walksat_run_matches_library_exactly(seed):
    clauses = ["A | B | ~C | D", "~A | B | ~C", "~B | ~C", "E", "E | C"]
    lib = sat.walksat_run(clauses, 0.5, 100, seed)
    got = answer(generate("walksat_run", clauses=clauses, p=0.5, max_flips=100, seed=seed))
    assert got == "solved, " + ", ".join(f"{s}={str(v).lower()}" for s, v in sorted(lib["model"].items()))


@pytest.mark.parametrize("x,y", [("Knows(John, x)", "Knows(y, Mother(y))"), ("Knows(John, x)", "Knows(x, Elizabeth)"),
                                 ("P(x)", "P(F(x))"), ("Knows(John, x)", "Knows(y, Bill)")])
def test_unify(x, y):
    lib = fol.unify(x, y)["unifier"]
    got = answer(generate("unify", x=x, y=y))
    assert got == ("no unifier" if lib is None else ", ".join(f"{k}/{v}" for k, v in sorted(lib.items())))


CRIME = ["American(x) & Weapon(y) & Sells(x, y, z) & Hostile(z) => Criminal(x)", "Owns(Nono, M1)", "Missile(M1)",
         "Missile(x) & Owns(Nono, x) => Sells(West, x, Nono)", "Missile(x) => Weapon(x)",
         "Enemy(x, America) => Hostile(x)", "American(West)", "Enemy(Nono, America)"]


@pytest.mark.parametrize("q", ["Criminal(West)", "Criminal(Nono)", "Criminal(w)", "Weapon(M1)"])
def test_fol_chaining(q):
    fc = fol.forward_chaining(CRIME, q)
    bc = fol.backward_chaining(CRIME, q)
    got = answer(generate("fol_chaining", kb=CRIME, query=q))
    r = fc["rounds"]
    assert got == (f"forward chaining {'yes' if fc['proved'] else 'no'} ({r} round{'s' if r != 1 else ''}), "
                   f"backward chaining {'yes' if bc['proved'] else 'no'}")


AUS = ["WA", "NT", "Q", "NSW", "V", "SA", "T"]
AUS_C = [["WA", "!=", "NT"], ["WA", "!=", "SA"], ["NT", "!=", "SA"], ["NT", "!=", "Q"], ["SA", "!=", "Q"],
         ["SA", "!=", "NSW"], ["SA", "!=", "V"], ["Q", "!=", "NSW"], ["NSW", "!=", "V"]]
ORDER_D = {v: [1, 2, 3, 4] for v in "ABCD"}
ORDER_C = [["A", "<", "B"], ["B", "<", "C"], ["C", "!=", "D"], ["A", "!=", "D"], ["D", ">", "B"]]


@pytest.mark.parametrize("settings", [("mrv", "lcv", "forward_checking"), ("static", "static", "none"),
                                      ("mrv", "static", "mac")])
@pytest.mark.parametrize("problem", ["australia", "ordering", "two-colours"])
def test_csp_backtracking(settings, problem):
    if problem == "australia":
        vs, d, c = AUS, {v: ["red", "green", "blue"] for v in AUS}, AUS_C
    elif problem == "ordering":
        vs, d, c = list("ABCD"), ORDER_D, ORDER_C
    else:
        vs, d, c = ["X", "Y", "Z"], {v: ["red", "green"] for v in "XYZ"}, [["X", "!=", "Y"], ["Y", "!=", "Z"], ["X", "!=", "Z"]]
    lib = csp.backtracking(vs, d, c, None, *settings)
    got = answer(generate("csp_backtracking", variables=vs, domains=d, constraints=c, variable_order=settings[0],
                          value_order=settings[1], inference=settings[2]))
    counts = f"({lib['assignments']} assignments, {lib['backtracks']} backtracks)"
    sol = lib["solution"]
    assert got == (f"no solution {counts}" if sol is None else ", ".join(f"{v}={sol[v]}" for v in vs) + " " + counts)


@pytest.mark.parametrize("problem", ["xy", "ordering", "two-colours"])
def test_ac3(problem):
    if problem == "xy":
        vs, d, c = ["X", "Y"], {"X": [1, 2, 3], "Y": [1, 2, 3]}, [["X", "<", "Y"]]
    elif problem == "ordering":
        vs, d, c = list("ABCD"), ORDER_D, ORDER_C
    else:
        vs, d, c = ["X", "Y", "Z"], {v: ["red", "green"] for v in "XYZ"}, [["X", "!=", "Y"], ["Y", "!=", "Z"], ["X", "!=", "Z"]]
    lib = csp.ac3(vs, d, c)
    got = answer(generate("csp_ac3", variables=vs, domains=d, constraints=c))
    if not lib["consistent"]:
        assert got.startswith("inconsistent")
    else:
        assert got == "arc consistent; " + "; ".join(f"{v}: {{{', '.join(map(str, lib['domains'][v]))}}}" for v in vs)


GAME_TREES = [[[3, 12, 8], [2, 4, 6], [14, 5, 2]], [[[3, 17], [2, 12]], [[15, 25], [2, 5]], [[3, 2], [14, 10]]],
              [[14, 5, 2], [3, 12, 8], [2, 4, 6]],
              {"children": {"A": ["B", "C"], "B": ["D", "E"], "C": ["F", "G"]}, "values": {"D": 2, "E": 4, "F": 0, "G": 10},
               "types": {"B": "chance", "C": "chance"}, "probabilities": {"B": [0.5, 0.5], "C": [0.9, 0.1]}}]


@pytest.mark.parametrize("tree", GAME_TREES)
def test_games(tree):
    has_chance = isinstance(tree, dict)
    mm = games.minimax(tree)
    expected = f"value {fmt(mm['value'])}" + (f", best move {mm['best_move']}" if mm["best_move"] else "")
    if not has_chance:
        expected += ", pruned " + (" ".join(games.alphabeta(tree)["pruned"]) or "nothing")
    assert answer(generate("games", tree=tree, use_alpha_beta=True)) == expected


def test_bayes_rule():
    lib = probability.bayes_rule(0.01, 0.9, 0.05)
    close(answer(generate("bayes_rule", prior=0.01, likelihood=0.9, false_positive_rate=0.05)), [lib["posterior"]])


BURGLARY = {"Burglary": {"cpt": {"": 0.001}}, "Earthquake": {"cpt": {"": 0.002}},
            "Alarm": {"parents": ["Burglary", "Earthquake"], "cpt": {"T,T": 0.95, "T,F": 0.94, "F,T": 0.29, "F,F": 0.001}},
            "JohnCalls": {"parents": ["Alarm"], "cpt": {"T": 0.9, "F": 0.05}},
            "MaryCalls": {"parents": ["Alarm"], "cpt": {"T": 0.7, "F": 0.01}}}


@pytest.mark.parametrize("query,evidence", [("Burglary", {"JohnCalls": True, "MaryCalls": True}),
                                            ("Burglary", {"JohnCalls": True, "MaryCalls": True, "Earthquake": True}),
                                            ("Alarm", {}), ("JohnCalls", {"Burglary": False})])
def test_bayes_net(query, evidence):
    lib = probability.bayes_net_query(BURGLARY, query, evidence)["distribution"]
    close(answer(generate("bayes_net", nodes=BURGLARY, query=query, evidence=evidence)), [lib["true"], lib["false"]])


def test_joint():
    vals = [(True, True, True, .108), (True, False, True, .012), (False, True, True, .072), (False, False, True, .008),
            (True, True, False, .016), (True, False, False, .064), (False, True, False, .144), (False, False, False, .576)]
    for q, ev in [("Cavity", {"Toothache": True}), ("Toothache", {}), ("Cavity", {"Toothache": True, "Catch": False})]:
        lib = probability.joint_query(["Toothache", "Catch", "Cavity"], [list(v) for v in vals], q, ev)["distribution"]
        close(answer(generate("joint", variables=["Toothache", "Catch", "Cavity"], table=vals, query=q, evidence=ev)),
              [lib["true"], lib["false"]])


WEATHER = [r.split() for r in """Sunny Hot High F no;Sunny Hot High T no;Overcast Hot High F yes;Rainy Mild High F yes;
Rainy Cool Normal F yes;Rainy Cool Normal T no;Overcast Cool Normal T yes;Sunny Mild High F no;Sunny Cool Normal F yes;
Rainy Mild Normal F yes;Sunny Mild Normal T yes;Overcast Mild High T yes;Overcast Hot Normal F yes;Rainy Mild High T no""".split(";")]


@pytest.mark.parametrize("query,k", [({"Outlook": "Sunny", "Temp": "Cool", "Humidity": "High", "Windy": "T"}, 0),
                                     ({"Outlook": "Overcast", "Windy": "T"}, 0), ({"Outlook": "Overcast", "Windy": "T"}, 1)])
def test_naive_bayes(query, k):
    attrs = ["Outlook", "Temp", "Humidity", "Windy"]
    lib = probability.naive_bayes(attrs, WEATHER, query, k)
    got = answer(generate("naive_bayes", attributes=attrs, data=WEATHER, query=query, laplace=k))
    assert got.split(" ")[0] == lib["prediction"]
    close(got, [lib["posterior"][lib["prediction"]]])


def test_kmeans():
    pts, cen = [[1, 1], [1.5, 2], [3, 4], [5, 7], [3.5, 5], [4.5, 5], [3.5, 4.5]], [[1, 1], [5, 7]]
    for metric in ("euclidean", "manhattan"):
        for it in (1, 3):
            lib = ml.kmeans(pts, cen, None, metric, it)["centres"]
            close(answer(generate("kmeans", points=pts, centres=cen, metric=metric, max_iterations=it)),
                  [v for c in lib for v in c])


@pytest.mark.parametrize("k,norm", [(1, False), (3, False), (5, True)])
def test_knn(k, norm):
    train = [[1, 1, "a"], [2, 1.5, "a"], [1.5, 2.5, "a"], [6, 6, "b"], [7, 5.5, "b"], [6.5, 7, "b"], [4, 4.5, "b"]]
    lib = ml.knn(train, [3.5, 3.5], k, "euclidean", norm)["prediction"]
    assert answer(generate("knn", train=train, query=[3.5, 3.5], k=k, normalise=norm)).split(" ")[0] == lib


def test_linear_regression_and_gradient_descent():
    xs, ys = [1, 2, 3, 4, 5, 6], [3, 5, 7, 10, 11, 14]
    close(answer(generate("linear_regression", xs=xs, ys=ys)), ml.linear_regression(xs, ys)["weights"])
    for mode in ("batch", "stochastic"):
        lib = ml.gradient_descent(xs[:4], ys[:4], [0, 0], 0.02, 50, mode)["weights"]
        close(answer(generate("gradient_descent", xs=xs[:4], ys=ys[:4], weights=[0, 0], alpha=0.02, steps=50, mode=mode)), lib)


def test_logistic_neuron_perceptron_network_cnn():
    close(answer(generate("logistic", weights=[-4, 1.5], x=3.0)), [1, ml.logistic_regression([3.0], [-4, 1.5])["probability"]])
    n = ml.neuron([1, 0], [-1.5, 1, 1])
    close(answer(generate("neuron", inputs=[1, 0], weights=[-1.5, 1, 1])),
          [n["linear"], n["outputs"]["threshold"], n["outputs"]["logistic"], n["outputs"]["relu"], n["outputs"]["tanh"]])
    for labels in ([0, 0, 0, 1], [0, 1, 1, 0]):
        ex = [[0, 0, labels[0]], [0, 1, labels[1]], [1, 0, labels[2]], [1, 1, labels[3]]]
        close(answer(generate("perceptron", examples=ex, weights=[0, 0, 0], alpha=0.5, epochs=6)),
              ml.perceptron_learning(ex, [0, 0, 0], 0.5, 6)["weights"])
    layers = [[[0.1, 0.2, 0.3], [0.2, -0.1, 0.4]], [[0.3, 0.5, -0.2]]]
    r = ml.mlp_step([1, 0], layers, [1], 0.5)
    close(answer(generate("network", inputs=[1, 0], layers=layers, targets=[1], alpha=0.5)), r["outputs"] + r["deltas"][-1])
    for shape, filt, n_f, s, p in [([32, 32, 3], [5, 5], 6, 1, 0), ([8, 8, 3], [3, 3], 10, 1, 0), ([28, 28, 1], [3, 3], 4, 2, 1)]:
        lib = ml.cnn_layer(shape, filt, n_f, s, p)
        close(answer(generate("cnn", input_shape=shape, filter_size=filt, n_filters=n_f, stride=s, padding=p)),
              lib["output"] + [lib["neurons"], lib["weights"]])


def test_every_view_has_a_program():
    from aiml_calc import explain
    assert set(SPECS) == set(explain.VIEWS)


def test_public_mode_blocks_running(monkeypatch):
    monkeypatch.setenv("AIML_CALC_PUBLIC", "1")
    r = run("print('hi')")
    assert not r.ok and "turned off" in r.error
