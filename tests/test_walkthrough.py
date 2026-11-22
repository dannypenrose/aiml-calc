"""The step-by-step walkthroughs: every view has one, and the numbers they work out agree with the algorithms."""

import random

import pytest

from aiml_calc import explain, ml, probability, search, walkthrough
from aiml_calc.common import fmt


def test_every_view_has_a_walkthrough():
    assert set(walkthrough.STEPS) == set(explain.VIEWS)


@pytest.mark.parametrize("seed", range(20))
def test_perceptron_replay_matches_the_library(seed):
    rng = random.Random(seed)
    exs = [[rng.randint(0, 1), rng.randint(0, 1), rng.randint(0, 1)] for _ in range(4)]
    w = [rng.choice([-1, 0, 0.5]) for _ in range(3)]
    r = ml.perceptron_learning(exs, w, 0.5, 5)
    steps = walkthrough.steps("perceptron", r, examples=exs, weights=w, alpha=0.5, epochs=5)
    updates = [s for s in steps if "w →" in s]
    final = "[" + ", ".join(fmt(v) for v in r["weights"]) + "]"
    # The walkthrough replays the training itself; when it lists every update, the last one is the library's answer.
    if updates and not any("more update" in s for s in steps):
        assert updates[-1].split("w → ")[1].rstrip(".") == final


def test_naive_bayes_scores_normalise_to_the_posterior():
    rows = [["S", "H", "no"], ["S", "C", "yes"], ["R", "C", "yes"], ["R", "H", "no"], ["S", "C", "yes"]]
    for k in (0, 1):
        r = probability.naive_bayes(["Outlook", "Temp"], rows, {"Outlook": "S", "Temp": "C"}, k)
        steps = walkthrough.steps("naive_bayes", r, attributes=["Outlook", "Temp"], data=rows,
                                  query={"Outlook": "S", "Temp": "C"}, laplace=k)
        scores = {s.split("Score for ")[1].split(":")[0]: float(s.rsplit("= ", 1)[1].rstrip("."))
                  for s in steps if s.startswith("**Score for")}
        z = sum(scores.values())
        for c, p in r["posterior"].items():
            assert abs(scores[c] / z - p) < 2e-3


def test_linear_regression_steps_match():
    xs, ys = [1, 2, 3, 4, 5], [2, 4, 5, 4, 5]
    r = ml.linear_regression(xs, ys)
    text = " ".join(walkthrough.steps("linear_regression", r, xs=xs, ys=ys))
    assert f"**{fmt(r['weights'][1])}**" in text and f"**{fmt(r['weights'][0])}**" in text


def test_search_walkthrough_ends_with_the_path():
    edges = [["S", "A", 1], ["A", "G", 5], ["S", "B", 2], ["B", "G", 1]]
    for alg in search.ALGORITHMS:
        r = search.run_search(alg, edges, "S", "G", {"S": 2, "A": 4, "B": 1, "G": 0}, depth_limit=3)
        text = " ".join(walkthrough.steps("search_trace", r, algorithm=alg, start="S", goal="G", depth_limit=3))
        assert " → ".join(r["path"]) in text, alg
