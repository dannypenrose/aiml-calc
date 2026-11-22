"""Reference cases worked by hand, with results confirmed independently.
Each one pins down a convention (goal-test timing, tie-breaking, weight sharing, ...) that is easy to get wrong."""

from aiml_calc import logic, ml, sat, search

ROADS = [["H", "L", 15], ["H", "T", 12], ["T", "M", 5], ["T", "Y", 6], ["L", "W", 9], ["L", "Y", 10],
        ["Y", "P", 11], ["M", "P", 10], ["M", "S", 7], ["M", "Y", 4], ["P", "W", 14]]
ROADS_H = dict(H=20, L=17, S=19, T=12, M=10, W=12, Y=8, P=0)


def test_greedy_graph_search_trace():
    r = search.run_search("greedy", ROADS, "H", "P", ROADS_H)
    assert r["path"] == ["H", "T", "Y", "P"]
    assert r["cost"] == 29
    frontiers = ["".join(sorted(s for s, _ in st["frontier"])) for st in r["steps"]]
    assert frontiers == ["LT", "LMY", "LMP", "LM"]
    assert [st["selected"] for st in r["steps"]] == ["H", "T", "Y", "P"]


def test_astar_finds_the_cheaper_path():
    assert search.run_search("astar", ROADS, "H", "P", ROADS_H)["cost"] == 27


CRANE = [["B", "E", 3], ["E", "B", 3], ["E", "F", 10], ["F", "C", 7], ["F", "E", 3], ["C", "A", 3], ["C", "F", 7]]
CRANE_H = dict(A=0, B=20, C=3, D=5, E=16, F=9)


def test_astar_tree_search_revisits_states():
    r = search.run_search("astar", CRANE, "B", "A", CRANE_H, mode="tree", directed=True)
    frontiers = ["".join(sorted(s for s, _ in st["frontier"])) for st in r["steps"][:3]]
    assert frontiers == ["E", "BF", "BCE"]
    assert r["cost"] == 23
    assert r["path"] == ["B", "E", "F", "C", "A"]


def test_cnf_compact_form():
    assert logic.to_cnf("(B & ~S) => W")["clauses"] == ["-BvSvW"]
    assert logic.to_cnf("(~B & S) => ~L")["clauses"] == ["Bv-Sv-L"]


def test_model_counting():
    assert logic.truth_table(["A | ~A"], list("ABCDE"))["total"] == 32
    assert logic.count_models("B & ~D", list("ABCD"))["count"] == 4
    assert logic.count_models("C | A | ~C", list("ABCD"))["count"] == 16
    assert logic.count_models("A & B & ~A", list("ABCD"))["count"] == 0


def test_walksat_greedy_step():
    r = sat.walksat_step(["A | B", "A | ~B", "A | B | ~C"], {"A": False, "B": False, "C": True}, p=0, clause_index=3)
    assert "A=T, B=F, C=T | T | T | T | **3**" in r["markdown"]
    assert r["reachable"] == {"A": ["greedy"]}


def test_walksat_reachable_models():
    r = sat.walksat_step(["A | B", "A | ~B | C", "~A | B", "~A | ~B | C"], {"A": False, "B": False, "C": False}, p=0.5)
    assert r["false_clauses"] == [1]
    assert set(r["reachable"]) == {"A", "B"}


def test_dpll_step_summary():
    r = sat.dpll(["A | B", "A | ~B | C", "~A | B", "~A | ~B | C", "~B | ~C"], ["A", "B", "C"])
    assert r["step_summary"] == ["Step 1: A=true, B=true, C=true, fail", "Step 2: A=false, B=true, C=true, fail"]
    assert not r["satisfiable"]


def test_kmeans_update():
    r = ml.kmeans([[3, 1], [4, 3], [4, 4], [5, 3], [5, 4]], [[2, 1], [3, 3]])
    assert r["centres"] == [[3.0, 1.0], [4.5, 3.5]]


def test_cnn_layer_sizes():
    a = ml.cnn_layer([8, 8, 3], [3, 3], 10)
    assert (a["output"], a["neurons"], a["weights"]) == ([6, 6, 10], 360, 280)
    b = ml.cnn_layer([9, 9, 3], [4, 4, 3], 10)
    assert (b["output"], b["neurons"], b["weights"]) == ([6, 6, 10], 360, 490)


def test_fully_connected_weights():
    assert ml.fc_layer([8, 8, 8], 5)["weights"] == 2565


def test_activations():
    out = ml.neuron([], [6])["outputs"]
    assert out["threshold"] == 1 and round(out["logistic"]) == 1 and out["relu"] == 6


def test_linear_hypotheses():
    r = ml.check_hypotheses([[1, 1, 0], [1, 2, 0], [2, 1, 0], [2, 2, 1]],
                           [[-4.5, 1, 1], [-3.5, 1, 1], [3.5, -1, -1], [-2.5, 1, 1]])
    assert r["verdict"] == {"A": False, "B": True, "C": False, "D": False}
