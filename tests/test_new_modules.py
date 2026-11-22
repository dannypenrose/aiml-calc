"""First-order logic, CSPs, game search and probability: textbook examples plus independent cross-checks."""

import itertools
import random

from aiml_calc import csp, fol, games, probability

CRIME = [
    "American(x) & Weapon(y) & Sells(x, y, z) & Hostile(z) => Criminal(x)",
    "Owns(Nono, M1)", "Missile(M1)",
    "Missile(x) & Owns(Nono, x) => Sells(West, x, Nono)",
    "Missile(x) => Weapon(x)", "Enemy(x, America) => Hostile(x)",
    "American(West)", "Enemy(Nono, America)",
]


def test_unification_textbook_cases():
    # AIMA §9.2.2
    assert fol.unify("Knows(John, x)", "Knows(John, Jane)")["unifier"] == {"x": "Jane"}
    assert fol.unify("Knows(John, x)", "Knows(y, Bill)")["unifier"] == {"x": "Bill", "y": "John"}
    assert fol.unify("Knows(John, x)", "Knows(y, Mother(y))")["unifier"] == {"x": "Mother(John)", "y": "John"}
    assert fol.unify("Knows(John, x)", "Knows(x, Elizabeth)")["unifier"] is None  # needs standardising apart
    assert fol.unify("P(x)", "P(F(x))")["unifier"] is None  # occur check


def test_fol_forward_chaining_crime_example():
    r = fol.forward_chaining(CRIME, "Criminal(West)")
    assert r["proved"] and r["rounds"] == 2  # AIMA Fig 9.4: two iterations
    assert not fol.forward_chaining(CRIME, "Criminal(Nono)")["proved"]


def test_fol_backward_chaining_crime_example():
    assert fol.backward_chaining(CRIME, "Criminal(w)")["proved"]
    assert not fol.backward_chaining(CRIME, "Criminal(Nono)")["proved"]


AUSTRALIA = {"WA": ["NT", "SA"], "NT": ["WA", "SA", "Q"], "SA": ["WA", "NT", "Q", "NSW", "V"],
             "Q": ["NT", "SA", "NSW"], "NSW": ["Q", "SA", "V"], "V": ["SA", "NSW"], "T": []}


def _brute_csp(vs, d, cons):
    c = csp.CSP(vs, d, cons)
    for vals in itertools.product(*(d[v] for v in vs)):
        a = dict(zip(vs, vals))
        if all(c.consistent(x, a[x], y, a[y]) for x, y in c.arcs):
            return True
    return False


def test_map_colouring_and_mrv_degree():
    vs = list(AUSTRALIA)
    d = {v: ["red", "green", "blue"] for v in vs}
    r = csp.backtracking(vs, d, neighbours=AUSTRALIA)
    sol = r["solution"]
    assert all(sol[a] != sol[b] for a, ns in AUSTRALIA.items() for b in ns)
    assert next(l for l in r["markdown"].split("\n") if "choose" in l).startswith("- choose **SA**")  # degree heuristic picks SA first
    assert csp.backtracking(vs, {v: ["red", "green"] for v in vs}, neighbours=AUSTRALIA)["solution"] is None


def test_csp_settings_agree_with_brute_force():
    rng = random.Random(5)
    ops = ["!=", "<", "<=", "=="]
    for _ in range(150):
        vs = ["A", "B", "C", "D"]
        d = {v: rng.sample(range(1, 5), rng.randint(1, 3)) for v in vs}
        cons = [[a, rng.choice(ops), b] for a, b in itertools.combinations(vs, 2) if rng.random() < 0.5]
        truth = _brute_csp(vs, d, cons)
        for vo, val, inf in [("static", "static", "none"), ("mrv", "lcv", "forward_checking"), ("mrv", "static", "mac")]:
            assert (csp.backtracking(vs, d, cons, None, vo, val, inf)["solution"] is not None) == truth
        if not csp.ac3(vs, d, cons)["consistent"]:
            assert not truth  # AC-3 finding a wipe-out proves there is no solution


def test_minimax_and_alphabeta_textbook_tree():
    tree = [[3, 12, 8], [2, 4, 6], [14, 5, 2]]  # AIMA Fig 5.2
    assert games.minimax(tree)["value"] == 3
    r = games.alphabeta(tree)
    assert r["value"] == 3 and r["pruned"] == ["I", "J"]  # AIMA Fig 5.5: two leaves pruned under C


def test_alphabeta_always_matches_minimax():
    rng = random.Random(6)
    for _ in range(200):
        def build(depth):
            if depth == 0:
                return rng.randint(-9, 9)
            return [build(depth - 1) for _ in range(rng.randint(1, 3))]
        t = build(rng.randint(1, 4))
        if not isinstance(t, list):
            continue
        assert games.alphabeta(t)["value"] == games.minimax(t)["value"]


def test_expectiminimax():
    spec = {"children": {"A": ["B", "C"], "B": ["D", "E"], "C": ["F", "G"]},
            "values": {"D": 2, "E": 4, "F": 0, "G": 10}, "types": {"B": "chance", "C": "chance"},
            "probabilities": {"B": [0.5, 0.5], "C": [0.9, 0.1]}}
    r = games.minimax(spec)
    assert abs(r["value"] - 3) < 1e-12 and r["best_move"] == "B"


BURGLARY = {
    "Burglary": {"cpt": {"": 0.001}}, "Earthquake": {"cpt": {"": 0.002}},
    "Alarm": {"parents": ["Burglary", "Earthquake"], "cpt": {"T,T": 0.95, "T,F": 0.94, "F,T": 0.29, "F,F": 0.001}},
    "JohnCalls": {"parents": ["Alarm"], "cpt": {"T": 0.90, "F": 0.05}},
    "MaryCalls": {"parents": ["Alarm"], "cpt": {"T": 0.70, "F": 0.01}},
}


def test_bayes_net_burglary():
    r = probability.bayes_net_query(BURGLARY, "Burglary", {"JohnCalls": True, "MaryCalls": True})
    assert abs(r["distribution"]["true"] - 0.284) < 0.001  # AIMA §14.4.1
    assert "✓ agrees" in r["markdown"]


def test_joint_distribution_dentist():
    # AIMA Fig 13.3: Toothache, Catch, Cavity
    table = []
    for tooth, catch, cav in itertools.product([True, False], repeat=3):
        p = {(True, True, True): 0.108, (True, False, True): 0.012, (False, True, True): 0.072, (False, False, True): 0.008,
             (True, True, False): 0.016, (True, False, False): 0.064, (False, True, False): 0.144,
             (False, False, False): 0.576}[(tooth, catch, cav)]
        table.append([tooth, catch, cav, p])
    r = probability.joint_query(["Toothache", "Catch", "Cavity"], table, "Cavity", {"Toothache": True})
    assert abs(r["distribution"]["true"] - 0.6) < 1e-9


def test_bayes_rule_both_methods():
    r = probability.bayes_rule(0.01, 0.9, 0.05)
    assert abs(r["posterior"] - 0.009 / 0.0585) < 1e-12


def test_naive_bayes_weather():
    attrs = ["Outlook", "Windy"]
    data = [["Sunny", "F", "no"], ["Sunny", "T", "no"], ["Overcast", "F", "yes"], ["Rainy", "F", "yes"],
            ["Rainy", "T", "no"], ["Overcast", "T", "yes"], ["Sunny", "F", "yes"]]
    r = probability.naive_bayes(attrs, data, {"Outlook": "Overcast", "Windy": "T"})
    assert r["prediction"] == "yes"
    r2 = probability.naive_bayes(attrs, data, {"Outlook": "Overcast", "Windy": "T"}, laplace=1)
    assert 0 < r2["posterior"]["no"] < 1
