"""The web UI: every page and every built-in example renders without an error, every field has a tooltip,
and every view has its explanations and code."""

import pathlib
import re

import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")

from aiml_calc import app as app_module  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
VIEW_KEYS = list(app_module.VIEWS)
WIDGETS = ["text_input", "text_area", "selectbox", "slider", "number_input", "checkbox", "toggle", "radio"]


def render(key):
    script = f"from aiml_calc import app\napp.setup()\napp.VIEWS[{key!r}]()\n"
    at = st_testing.AppTest.from_string(script, default_timeout=60)
    at.run()
    return at


def problems(at):
    return [e.value for e in at.error] + [str(x.value) for x in at.exception]


@pytest.mark.parametrize("key", VIEW_KEYS)
def test_view_and_its_examples_render(key):
    at = render(key)
    assert problems(at) == []
    for i, sb in enumerate(at.selectbox):
        if sb.label != "Example":
            continue
        for opt in sb.options:
            at.selectbox[i].set_value(opt).run()
            assert problems(at) == [], f"{key} / {opt}"


@pytest.mark.parametrize("key", VIEW_KEYS)
def test_every_field_has_a_tooltip(key):
    at = render(key)
    missing = [f"{kind}: {w.label}" for kind in WIDGETS for w in at.get(kind)
               if not (getattr(w, "help", None) or getattr(w.proto, "help", ""))]
    assert missing == [], f"{key}: fields without a tooltip: {missing}"


@pytest.mark.parametrize("key", VIEW_KEYS)
def test_every_view_has_panels_walkthrough_and_code_button(key):
    at = render(key)
    labels = [e.label for e in at.expander]
    for panel in ("🌱 New to this? Start here", "📖 How it works (technical)", "🌍 When and where to use this"):
        assert panel in labels, f"{key} is missing {panel}"
    assert any("How it got this answer" in m.value for m in at.markdown), f"{key} has no walkthrough"
    assert [b for b in at.button if b.label == "💻 Code"], f"{key} has no code button"


def test_code_button_opens_the_dialog():
    at = render("bayes_rule")
    next(b for b in at.button if b.label == "💻 Code").click().run()
    assert [b for b in at.button if b.label == "▶ Run"], "the dialog should open with a Run button"
    assert any("def " in c.value for c in at.code), "the dialog should show the program"


def test_code_dialog_runs_the_program():
    # In the browser the dialog reruns on its own; here we keep it open by calling it on every run.
    script = ("from aiml_calc import app\nfrom aiml_calc.codegen import generate\napp.setup()\n"
              "app._code_dialog('bayes_rule', generate('bayes_rule', prior=0.01, likelihood=0.9, "
              "false_positive_rate=0.05))\n")
    at = st_testing.AppTest.from_string(script, default_timeout=60)
    at.run()
    next(b for b in at.button if b.label == "▶ Run").click().run()
    outputs = [c.value for c in at.code if "Answer: P(H | E) = 0.1538" in c.value]
    assert outputs, "running the generated program should print the answer"


def test_home_page_and_navigation(monkeypatch):
    monkeypatch.setenv("AIML_CALC_PUBLIC", "0")   # keep the public-mode default from leaking into other tests
    at = st_testing.AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60)
    at.run()
    assert problems(at) == []
    assert any("aiml-calc" in t.value for t in at.title)


def test_every_view_has_explanations():
    from aiml_calc import beginner, explain, usecases
    src = (ROOT / "src" / "aiml_calc" / "app.py").read_text()
    assert set(re.findall(r'learn\("(\w+)"', src)) == set(explain.VIEWS) == set(VIEW_KEYS)
    assert set(beginner.BEGINNER) == set(explain.VIEWS) == set(usecases.USES)
    assert set(re.findall(r'walk\("(\w+)"', src)) == set(VIEW_KEYS)
    for key in explain.VIEWS:
        body = explain.VIEWS[key]["body"]
        assert "Reference" in body, key
        assert body.count("**Cost.**") == 1, f"{key} technical panel needs exactly one Cost section"
        assert body.index("**Cost.**") < body.index("*Reference:"), f"{key} Cost section belongs before the reference"
        for part in ("**The idea.**", "**Tiny example", "**How long it takes.**", "**Words to know**\n- **"):
            assert part in beginner.BEGINNER[key], f"{key} beginner panel is missing {part}"
        for part in ("**Use it when**", "**Real world**", "**In software engineering**"):
            assert part in usecases.USES[key], f"{key} use-case panel is missing {part}"
    from aiml_calc.search import ALGORITHMS
    assert set(explain.SEARCH_ALGOS) == set(ALGORITHMS)


def test_dot_builders():
    from aiml_calc import csp, games, viz
    g = viz.search_graph([["A", "B", 1], ["B", "C", 2]], False, "A", ["C"], ["A", "B", "C"], ["A", "B"], {"A": 2})
    assert g.startswith("graph") and "penwidth=3" in g
    r = games.alphabeta([[3, 12, 8], [2, 4, 6], [14, 5, 2]])
    assert 'style="dashed"' in viz.game_tree(r["tree"], r["values"], r["pruned"], "B")
    c = csp.backtracking(["X", "Y"], {"X": ["red", "green"], "Y": ["red", "green"]}, [["X", "!=", "Y"]])
    assert "fillcolor" in viz.constraint_graph(["X", "Y"], c["edges"], c["solution"])
    assert "->" in viz.bayes_net({"A": [], "B": ["A"]}, "A", {"B": True})
    assert "->" in viz.network([[[0.1, 0.2]], [[0.3, -0.4]]], 1)


def test_quick_search_finds_views():
    found = lambda q: [k for _, k, _, _ in app_module.search_views(q)]  # noqa: E731
    assert found("a*")[0] == "search_trace"
    assert "bayes_net" in found("bayes") and "naive_bayes" in found("bayes")
    assert found("backprop") == ["network"]
    assert found("alpha beta") == ["games"]
    assert found("k-means") == ["kmeans"]
    assert found("zzzz") == [] and found("  ") == []


def test_sidebar_search_and_groups(monkeypatch):
    monkeypatch.setenv("AIML_CALC_PUBLIC", "0")
    at = st_testing.AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60)
    at.run()
    assert [e.label for e in at.sidebar.expander] == list(app_module.SECTIONS)
    at.sidebar.text_input[0].set_value("pruning").run()
    assert problems(at) == []
    assert at.sidebar.expander.len == 0   # search results replace the groups
