"""Streamlit web UI: every algorithm on its own page, with explanations, worked steps, graphs and runnable code.

Run with `aiml-calc-ui` (or `streamlit run src/aiml_calc/app.py`).
"""

from __future__ import annotations

import hashlib
import html
import json
import math
import re
from typing import Any, Callable

import altair as alt
import pandas as pd
import streamlit as st

from aiml_calc import beginner, csp, explain, fol, games, logic, ml, probability, sat, search, usecases, viz, walkthrough
from aiml_calc.codegen import generate
from aiml_calc.codegen.runner import run as run_code
from aiml_calc.codegen.runner import running_allowed
from aiml_calc.common import fmt

try:  # syntax-highlighted editor that grows with its content; falls back to a plain text box
    from streamlit_ace import st_ace
except ImportError:  # pragma: no cover - optional dependency
    st_ace = None

ACCENT = "#2563EB"
PALETTE = ["#2563EB", "#F59E0B", "#10B981", "#EF4444", "#8B5CF6", "#EC4899"]

# Tooltips shared by several views
H_EXAMPLE = "Load a ready-made problem. You can edit any field afterwards."
H_FORMULA_SYNTAX = "Use ¬ ~ ! for not, ∧ & for and, ∨ | for or, ⇒ => for implies, ⇔ <=> for iff, and brackets."
H_CLAUSES = "One clause per line, as literals joined by OR: `A | ~B | C`, `A ∨ ¬B ∨ C`, or the compact form `Av-BvC`."
H_EVIDENCE = 'Observed values as JSON, e.g. {"JohnCalls": true}. Use {} for no evidence.'
H_ALPHA = "Learning rate α: how big a step each update takes. Too large overshoots; too small learns slowly."


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------

def lines(text: str) -> list[str]:
    return [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]


def parse_edges(text: str) -> list[list[Any]]:
    out = []
    for l in lines(text):
        parts = [p for p in re.split(r"[\s,]+|--|->|—", l) if p]
        if len(parts) < 2:
            raise ValueError(f"Edge line needs 'from to [cost]': {l!r}")
        out.append([parts[0], parts[1], float(parts[2])] if len(parts) > 2 else [parts[0], parts[1]])
    return out


def parse_kv(text: str) -> dict[str, float]:
    out = {}
    for l in lines(text):
        k, v = [p for p in re.split(r"[\s,:=]+", l) if p][:2]
        out[k] = float(v)
    return out


def parse_rows(text: str, label: bool = False) -> list[list[Any]]:
    out = []
    for l in lines(text):
        parts = [p for p in re.split(r"[\s,;()]+", l) if p]
        out.append([float(p) for p in parts[:-1]] + [parts[-1]] if label else [float(p) for p in parts])
    return out


def numbers(text: str) -> list[float]:
    return [float(v) for v in text.replace(",", " ").split()]


def run(fn, *args, **kwargs):
    """Call an algorithm and show any input error neatly instead of a stack trace."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:  # noqa: BLE001 - shown to the user
        st.error(f"Couldn't run that: {e}")
        return None


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def split_answer(md: str) -> tuple[str, str]:
    """Separate the **Answer:** line from the working, and tidy markdown for display."""
    body = [l for l in md.split("\n") if not l.startswith("## ")]
    text = "\n".join(body).strip()
    answer = ""
    m = re.search(r"\*\*Answer:\*\*\s*(.*?)(?:\n\n|\n(?=[#|\-]|Method|\*\*)|$)", text, re.S)
    if m:
        answer = m.group(1).strip()
        text = (text[:m.start()] + text[m.end():]).strip()
    out = []
    for l in text.split("\n"):
        if l.startswith("### "):
            l = "##### " + l[4:]
        out.append(l if l.startswith("|") or not l.strip() else l + "  ")  # keep single line breaks
    return answer, "\n".join(out)


def walk(key: str, result: Any, **params) -> list[str] | None:
    """The step-by-step account of how this result was reached (see walkthrough.py)."""
    return run(walkthrough.steps, key, result, **params)


def how(steps: list[str] | None) -> None:
    if not steps:
        return
    with st.container(border=True):
        st.markdown("##### 🪜 How it got this answer")
        st.markdown("\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1)))


def show(md: str, answer: bool = True, steps: list[str] | None = None) -> None:
    ans, body = split_answer(md)
    if answer and ans:
        st.success(ans)
    elif ans:
        body = ans + "\n\n" + body
    if steps:
        how(steps)
        st.markdown("##### Full working")
    st.markdown(body)


def _inline_md(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return re.sub(r"(?<![\w*])\*(\w[^*]*?)\*(?![\w*])", r"<em>\1</em>", s)


def page_header(title: str, section_key: str, key: str) -> None:
    left, right = st.columns([5, 1], vertical_alignment="center")
    left.header(title)
    if right.button("💻 Code", key=f"open_code_{key}", width="stretch",
                    help="See this algorithm as a standalone Python program with the values on this page built in. "
                         "Edit it, run it or download it."):
        st.session_state["_code_open"] = key
    st.markdown(f'<div class="lead">{_inline_md(explain.SECTIONS[section_key])}</div>', unsafe_allow_html=True)


def learn(key: str, extra_top: str = "", extra_bottom: str = "") -> None:
    """One-line overview plus three panels: for newcomers, technical, and where it's used."""
    v = explain.VIEWS[key]
    st.markdown(f'<p class="summary">{v["summary"]}</p>', unsafe_allow_html=True)
    with st.expander("🌱 New to this? Start here"):
        st.markdown(beginner.BEGINNER[key])
    with st.expander("📖 How it works (technical)"):
        if extra_top:
            st.markdown(extra_top)
        st.markdown(v["body"])
        if extra_bottom:
            st.markdown(extra_bottom)
    with st.expander("🌍 When and where to use this"):
        st.markdown(usecases.USES[key])


EDIT_TAB, OUTPUT_TAB, READ_TAB = "✏️ Edit", "▶ Output", "📄 Read"


def _run_now(key: str, source: str, digest: str, edit_key: str) -> None:
    """Run button callback: run the code in the editor, then switch to the Output tab."""
    code = st.session_state.get(edit_key) or source
    st.session_state[f"out_{key}"] = (digest, run_code(code))
    st.session_state[f"tabs_{key}"] = OUTPUT_TAB


def _reset(key: str) -> None:
    st.session_state[f"resets_{key}"] = st.session_state.get(f"resets_{key}", 0) + 1  # fresh editor from the generated code
    st.session_state.pop(f"out_{key}", None)
    st.session_state[f"tabs_{key}"] = EDIT_TAB


@st.dialog("💻 Python code", width="large")
def _code_dialog(key: str, source: str) -> None:
    digest = hashlib.sha1(source.encode()).hexdigest()[:10]
    resets = st.session_state.get(f"resets_{key}", 0)
    edit_key, out_key = f"code_{key}_{digest}_{resets}", f"out_{key}"
    st.caption("A standalone program that implements this algorithm, with the values from the page built in. Change a "
               "value on the page and the code updates. Edit it here and press Run to try your own changes.")
    allowed = running_allowed()
    c1, c2, c3, _ = st.columns([1, 1, 1.3, 3])
    c1.button("▶ Run", key=f"run_{key}", type="primary", disabled=not allowed, width="stretch",
              on_click=_run_now, args=(key, source, digest, edit_key),
              help="Run the program in the editor and show what it prints." if allowed else
              "Running code is turned off on public deployments. Download it and run it locally.")
    c2.button("↺ Reset", key=f"reset_{key}", width="stretch", on_click=_reset, args=(key,),
              help="Throw away your edits and go back to the generated code.")
    current = st.session_state.get(edit_key) or source
    c3.download_button("⬇ Download", current, file_name=f"{key}.py", mime="text/x-python", key=f"dl_{key}",
                       on_click="ignore", width="stretch", help=f"Save the program and run it with `python {key}.py`.")
    result = st.session_state.get(out_key)
    result = result[1] if result and result[0] == digest else None
    edit_tab, out_tab, read_tab = st.tabs([EDIT_TAB, OUTPUT_TAB, READ_TAB], key=f"tabs_{key}", on_change="rerun",
                                          default=EDIT_TAB)
    with edit_tab:
        if st_ace is not None:
            st_ace(value=source, language="python", theme="chrome", keybinding="vscode", font_size=13, tab_size=4,
                   min_lines=8, max_lines=None, show_gutter=True, wrap=False, auto_update=True, key=edit_key)
        else:
            st.text_area("Program", source, height=460, key=edit_key, label_visibility="collapsed",
                         help="Edit the program freely. Changing a value on the page regenerates it.")
    with out_tab:
        if result is None:
            st.info("Press **▶ Run** to run the program in the editor. What it prints appears here.")
        else:
            if result.error and not result.ok:
                st.error("The program stopped with an error. Fix it in the ✏️ Edit tab and run it again.")
            elif result.ok:
                st.caption(f"Finished in {result.seconds:.2f} s.")
            if result.output:
                st.code(result.output.rstrip(), language="text")
            if result.error:
                st.code(result.error.rstrip(), language="text")
    with read_tab:
        st.code(source, language="python", line_numbers=True)


def code_panel(key: str, **params) -> None:
    """Open the code dialog if this page's Code button was just pressed, with the current inputs built in."""
    if st.session_state.get("_code_open") != key:
        return
    st.session_state.pop("_code_open")
    try:
        source = generate(key, **params)
    except Exception as e:  # noqa: BLE001
        st.toast(f"Fix the inputs to see the code ({e}).")
        return
    _code_dialog(key, source)


def example_picker(name: str, examples: dict[str, Any]) -> tuple[str, Any]:
    choice = st.selectbox("Example", list(examples), key=f"ex_{name}", help=H_EXAMPLE)
    return choice, examples[choice]


def _bar(dist: dict[str, float], title: str) -> alt.Chart:
    df = pd.DataFrame({"value": list(dist), "probability": list(dist.values())})
    base = alt.Chart(df, title=title).encode(
        y=alt.Y("value:N", title=None, sort=None),
        x=alt.X("probability:Q", scale=alt.Scale(domain=[0, 1]), title="probability"),
        tooltip=["value", alt.Tooltip("probability:Q", format=".4f")])
    bars = base.mark_bar(color=ACCENT)
    labels = base.mark_text(align="left", dx=4, color="#1F2937").encode(text=alt.Text("probability:Q", format=".4f"))
    return (bars + labels).properties(height=48 * len(df) + 30)


def _scatter(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = "") -> alt.Chart:
    enc = dict(x=alt.X(f"{x}:Q", scale=alt.Scale(zero=False), title=x),
               y=alt.Y(f"{y}:Q", scale=alt.Scale(zero=False), title=y), tooltip=list(df.columns))
    if color:
        enc["color"] = alt.Color(f"{color}:N", scale=alt.Scale(range=PALETTE))
    return alt.Chart(df, title=title).mark_circle(size=110, opacity=0.9).encode(**enc)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

SEARCH_EXAMPLES = {
    "Road map (undirected, weighted)": dict(
        edges="H L 15\nH T 12\nT M 5\nT Y 6\nL W 9\nL Y 10\nY P 11\nM P 10\nM S 7\nM Y 4\nP W 14",
        h="H 20\nL 17\nS 19\nT 12\nM 10\nW 12\nY 8\nP 0", start="H", goal="P", directed=False),
    "Romania (AIMA Fig 3.2, part)": dict(
        edges="Arad Zerind 75\nArad Sibiu 140\nArad Timisoara 118\nZerind Oradea 71\nOradea Sibiu 151\n"
              "Sibiu Fagaras 99\nSibiu RimnicuVilcea 80\nRimnicuVilcea Pitesti 97\nRimnicuVilcea Craiova 146\n"
              "Pitesti Craiova 138\nPitesti Bucharest 101\nFagaras Bucharest 211\nTimisoara Lugoj 111\n"
              "Lugoj Mehadia 70\nMehadia Drobeta 75\nDrobeta Craiova 120",
        h="Arad 366\nBucharest 0\nCraiova 160\nDrobeta 242\nFagaras 176\nLugoj 244\nMehadia 241\nOradea 380\n"
          "Pitesti 100\nRimnicuVilcea 193\nSibiu 253\nTimisoara 329\nZerind 374",
        start="Arad", goal="Bucharest", directed=False),
    "Crane and container (directed)": dict(
        edges="B E 3\nE B 3\nE F 10\nF C 7\nF E 3\nC A 3\nC F 7", h="A 0\nB 20\nC 3\nD 5\nE 16\nF 9",
        start="B", goal="A", directed=True),
}
ALG_NAMES = {"astar": "A*", "greedy": "Greedy best-first", "ucs": "Uniform-cost", "bfs": "Breadth-first",
             "dfs": "Depth-first", "ids": "Iterative deepening", "dls": "Depth-limited", "idastar": "IDA*"}


def view_search_trace() -> None:
    page_header("Trace a search", "search", "search_trace")
    name, ex = example_picker("search", SEARCH_EXAMPLES)
    overview = st.container()
    c1, c2, c3 = st.columns(3)
    alg = c1.selectbox("Algorithm", list(ALG_NAMES), format_func=ALG_NAMES.get,
                       help="Which node to expand next: by depth (BFS, DFS, IDS), path cost (UCS), "
                            "heuristic estimate (greedy) or both (A*, IDA*).")
    mode = c2.selectbox("Mode", ["graph", "tree"],
                        help="Graph search remembers explored states and never re-adds them. Tree search doesn't, "
                             "so states can repeat (and it can loop). IDS, DLS and IDA* always use tree search.")
    tie = c3.selectbox("Tie-break", ["alphabetical", "fifo", "lifo"],
                       help="How to choose between frontier nodes with equal priority: alphabetically by state, "
                            "the one added first (FIFO), or the one added last (LIFO).")
    c4, c5, c6 = st.columns(3)
    start = c4.text_input("Start", ex["start"], key=f"s_{name}", help="The initial state: a node name from the edge list.")
    goal = c5.text_input("Goal", ex["goal"], key=f"g_{name}", help="The state the goal test looks for.")
    directed = c6.checkbox("Directed edges", ex["directed"], key=f"d_{name}",
                           help="Ticked: each edge can only be travelled from the first node to the second. "
                                "Unticked: every edge works both ways.")
    depth = 3
    if alg == "dls":
        depth = st.slider("Depth limit", 0, 10, 3, help="Nodes at this depth are not expanded. A goal deeper than the "
                                                        "limit can't be found.")
    e1, e2 = st.columns(2)
    edges_t = e1.text_area("Edges: from to cost", ex["edges"], height=220, key=f"e_{name}",
                           help="One edge per line: two node names and a step cost (cost defaults to 1).")
    h_t = e2.text_area("Heuristic h(n)", ex["h"], height=220, key=f"h_{name}",
                       help="Estimated cost from each node to the goal, one `node value` per line. Used by greedy, A* "
                            "and IDA*; missing nodes count as 0.")
    alg_label = ALG_NAMES[alg].replace("*", "\\*")
    with overview:
        learn("search_trace", extra_top=f"**{alg_label}.** {explain.SEARCH_ALGOS[alg]}",
              extra_bottom="**How the algorithms compare** (AIMA Fig 3.21)\n" + explain.SEARCH_PROPERTIES)
    edges, h = run(parse_edges, edges_t), run(parse_kv, h_t)
    if edges is None or h is None:
        return
    r = run(search.run_search, alg, edges, start, goal, h, mode=mode, directed=directed, tie_break=tie,
            depth_limit=depth)
    if r is None:
        return
    g1, g2 = st.columns([1.6, 1])
    ans, body = split_answer(r["markdown"])
    with g1:
        st.graphviz_chart(viz.search_graph(edges, directed, start, [goal], r["path"],
                                           r["expanded"] if alg in ("bfs", "dfs", "ucs", "greedy", "astar") else None,
                                           h if alg in ("greedy", "astar", "idastar") else None))
    with g2:
        st.success(ans)
        if r.get("expanded"):
            st.metric("Nodes expanded", len(r["expanded"]))
        if r.get("path"):
            st.metric("Path cost", fmt(r["cost"]))
        st.caption("Blue: path found. Grey fill: expanded. #n: expansion order. Double ring: goal.")
    params = dict(algorithm=alg, edges=edges, start=start, goal=goal, heuristic=h, mode=mode, directed=directed,
                  tie_break=tie, depth_limit=depth)
    how(walk("search_trace", r, **params))
    st.markdown("##### Full working")
    st.markdown(body)
    code_panel("search_trace", **params)


def view_search_heuristic() -> None:
    page_header("Check a heuristic", "search", "search_heuristic")
    name, ex = example_picker("heur", SEARCH_EXAMPLES)
    learn("search_heuristic")
    c1, c2 = st.columns(2)
    edges = run(parse_edges, c1.text_area("Edges", ex["edges"], height=180, key=f"he_{name}",
                                          help="One edge per line: `from to cost`."))
    h = run(parse_kv, c2.text_area("Heuristic h(n)", ex["h"], height=180, key=f"hh_{name}",
                                   help="The heuristic to test, one `node value` per line."))
    c3, c4 = st.columns(2)
    goal = c3.text_input("Goal", ex["goal"], key=f"hg_{name}", help="True costs h*(n) are measured to this node.")
    h2_t = c4.text_input("Second heuristic to compare (optional)", "", key=f"h2_{name}",
                         help="Another heuristic as `node value` pairs, e.g. `H 25 L 20 …`, to check which one dominates.")
    if edges and h:
        h2 = None
        if h2_t.strip():
            parts = h2_t.replace(",", " ").split()
            h2 = {parts[i]: float(parts[i + 1]) for i in range(0, len(parts) - 1, 2)}
        r = run(search.check_heuristic, edges, goal, h, directed=ex["directed"], compare_with=h2)
        if r:
            show(r["markdown"], steps=walk("search_heuristic", r, edges=edges, goal=goal, heuristic=h,
                                           directed=ex["directed"]))
        code_panel("search_heuristic", edges=edges, goal=goal, heuristic=h, directed=ex["directed"])


# ---------------------------------------------------------------------------
# Propositional logic
# ---------------------------------------------------------------------------

LOGIC_EXAMPLES = {
    "Wumpus world (AIMA §7.4.3)": dict(kb="~P11\nB11 <=> (P12 | P21)\nB21 <=> (P11 | P22 | P31)\n~B11\nB21",
                                       query="~P12"),
    "Modus ponens": dict(kb="A => B\nA", query="B"),
    "Affirming the consequent (invalid)": dict(kb="A => B\nB", query="A"),
}
HORN = {"AIMA Fig 7.16": dict(rules="P => Q\nL & M => P\nB & L => M\nA & P => L\nA & B => L", facts="A\nB", query="Q")}


def view_truth_table() -> None:
    page_header("Truth tables", "logic", "truth_table")
    learn("truth_table")
    f = st.text_area("Formulas (one per line)", "(A => B) & A\nA | ~A\nA & ~A", height=110,
                     help="Each line becomes a column of the truth table. " + H_FORMULA_SYNTAX)
    extra = st.text_input("Extra symbols (optional, space-separated)", "",
                          help="Symbols in the problem that don't appear in these formulas. Each one doubles the "
                               "number of models.")
    r = run(logic.truth_table, lines(f), extra.split() or None)
    if r:
        show(r["markdown"], steps=walk("truth_table", r, formulas=lines(f)))
        code_panel("truth_table", formulas=lines(f), extra_symbols=extra.split())


def view_cnf() -> None:
    page_header("CNF conversion", "logic", "cnf")
    learn("cnf")
    f = st.text_input("Formula", "(B & ~S) => W", help="Any propositional formula. " + H_FORMULA_SYNTAX)
    r = run(logic.to_cnf, f)
    if r:
        show(r["markdown"], steps=walk("cnf", r, formula=f))
        code_panel("cnf", formula=f)


def view_entailment() -> None:
    page_header("Entailment and resolution", "logic", "entailment")
    name, ex = example_picker("logic", LOGIC_EXAMPLES)
    learn("entailment")
    kb = st.text_area("Knowledge base (one sentence per line)", ex["kb"], height=140, key=f"kb_{name}",
                      help="Everything the agent knows; the sentences are ANDed together. " + H_FORMULA_SYNTAX)
    q = st.text_input("Query α", ex["query"], key=f"q_{name}",
                      help="The sentence to test: is it true in every model of the knowledge base?")
    r, r2 = run(logic.entails, lines(kb), q), run(logic.resolution, lines(kb), q)
    if r and r2:
        st.success(split_answer(r["markdown"])[0])
        how(walk("entailment", (r, r2), kb=lines(kb), query=q))
        st.markdown("##### Full working")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Model checking")
            show(r["markdown"], answer=False)
        with c2:
            st.subheader("Resolution")
            show(r2["markdown"], answer=False)
        code_panel("entailment", kb=lines(kb), query=q)


def view_chaining() -> None:
    page_header("Forward and backward chaining", "logic", "chaining")
    name, ex = example_picker("horn", HORN)
    learn("chaining")
    c1, c2, c3 = st.columns([2, 1, 1])
    rules = c1.text_area("Definite clauses", ex["rules"], height=140, key=f"r_{name}",
                         help="One rule per line: positive symbols joined by & on the left, one symbol on the right, "
                              "e.g. `L & M => P`.")
    facts = c2.text_area("Facts", ex["facts"], height=140, key=f"f_{name}", help="Symbols known to be true, one per line.")
    q = c3.text_input("Query", ex["query"], key=f"hq_{name}", help="The symbol to prove.")
    fc = run(logic.forward_chaining, lines(rules), lines(facts), q)
    bc = run(logic.backward_chaining, lines(rules), lines(facts), q)
    if fc and bc:
        parsed = []
        for r_ in lines(rules):
            lhs, rhs = r_.replace("⇒", "=>").split("=>")
            parsed.append(([p.strip() for p in re.split(r"&|∧", lhs)], rhs.strip()))
        st.graphviz_chart(viz.implication_graph(parsed, lines(facts), fc["inferred"], q))
        st.caption("Green: given facts. Blue: inferred by forward chaining. ∧: all premises needed.")
        st.success(split_answer(fc["markdown"])[0])
        how(walk("chaining", (fc, bc), rules=lines(rules), facts=lines(facts), query=q))
        st.markdown("##### Full working")
        c1, c2 = st.columns(2)
        with c1:
            show(fc["markdown"], answer=False)
        with c2:
            show(bc["markdown"], answer=False)
        code_panel("chaining", rules=lines(rules), facts=lines(facts), query=q)


# ---------------------------------------------------------------------------
# SAT
# ---------------------------------------------------------------------------

DPLL_EXAMPLES = {
    "Unsatisfiable (needs backtracking)": dict(clauses="A | B\nA | ~B | C\n~A | B\n~A | ~B | C\n~B | ~C", order="A B C"),
    "Pure symbol then unit propagation": dict(clauses="~A | B\n~B | ~C\nA | B\nA | C\nA | D\nB | C\nB | D\nC | D",
                                              order="A B C D"),
}


def view_dpll() -> None:
    page_header("DPLL", "sat", "dpll")
    name, ex = example_picker("dpll", DPLL_EXAMPLES)
    learn("dpll")
    cl = st.text_area("Clauses", ex["clauses"], height=160, key=f"c_{name}", help=H_CLAUSES)
    c1, c2, c3 = st.columns(3)
    order = c1.text_input("Symbol order", ex["order"], key=f"o_{name}",
                          help="The order DPLL branches on symbols when no pure symbol or unit clause applies.")
    pure = c2.checkbox("Pure symbol rule", True,
                       help="Assign a symbol that appears with only one sign in the remaining clauses. Turn off to "
                            "see DPLL with unit propagation alone.")
    tf = c3.checkbox("Try true first", True, help="When branching, try true before false (or the reverse).")
    r = run(sat.dpll, lines(cl), order.split() or None, pure, tf)
    if r:
        show(r["markdown"], steps=walk("dpll", r, clauses=lines(cl), symbol_order=order.split(), use_pure_symbols=pure,
                                       true_first=tf))
        code_panel("dpll", clauses=lines(cl), symbol_order=order.split(), use_pure_symbols=pure, true_first=tf)


def view_walksat_step() -> None:
    page_header("WalkSAT: one step", "sat", "walksat_step")
    learn("walksat_step")
    cl = st.text_area("Clauses", "A | B\nA | ~B\nA | B | ~C", height=110, key="ws_c", help=H_CLAUSES)
    c1, c2, c3 = st.columns(3)
    model = c1.text_input("Current model", "A=F B=F C=T",
                          help="The complete assignment WalkSAT is currently at, as `Symbol=T` or `Symbol=F` pairs.")
    p = c2.slider("p (random-walk probability)", 0.0, 1.0, 0.0, 0.05,
                  help="Chance of flipping a random symbol from the chosen clause instead of the greedy best. "
                       "0 = always greedy, 1 = always random.")
    idx = c3.number_input("Clause picked (0 = consider every false clause)", 0, 50, 0,
                          help="WalkSAT picks a false clause at random. Fix one here (numbered from 1), or leave 0 to "
                               "analyse every possibility.")
    m = dict(kv.split("=") for kv in model.split()) if model else {}
    r = run(sat.walksat_step, lines(cl), m, p, idx or None)
    if r:
        show(r["markdown"], steps=walk("walksat_step", r, clauses=lines(cl), model=m, p=p, clause_index=idx))
        code_panel("walksat_step", clauses=lines(cl), model=m, p=p, clause_index=idx)


def view_walksat_run() -> None:
    page_header("WalkSAT: a full run", "sat", "walksat_run")
    learn("walksat_run")
    cl = st.text_area("Clauses", "A | B | ~C | D\n~A | B | ~C\n~B | ~C\nE\nE | C", height=130, key="wr_c", help=H_CLAUSES)
    c1, c2 = st.columns(2)
    p = c1.slider("p", 0.0, 1.0, 0.5, 0.05, key="wr_p",
                  help="Random-walk probability. Some randomness (p > 0) lets WalkSAT escape local minima.")
    seed = c2.number_input("Random seed", 0, 10_000, 0,
                           help="Fixes the random choices so a run can be repeated exactly. Change it to see a "
                                "different run.")
    r = run(sat.walksat_run, lines(cl), p, 100, int(seed))
    if r:
        show(r["markdown"], steps=walk("walksat_run", r, clauses=lines(cl), p=p, max_flips=100, seed=int(seed)))
        code_panel("walksat_run", clauses=lines(cl), p=p, max_flips=100, seed=int(seed))


# ---------------------------------------------------------------------------
# First-order logic
# ---------------------------------------------------------------------------

CRIME = ("American(x) & Weapon(y) & Sells(x, y, z) & Hostile(z) => Criminal(x)\nOwns(Nono, M1)\nMissile(M1)\n"
         "Missile(x) & Owns(Nono, x) => Sells(West, x, Nono)\nMissile(x) => Weapon(x)\nEnemy(x, America) => Hostile(x)\n"
         "American(West)\nEnemy(Nono, America)")
H_FOL = "Variables start lower-case (x, y); constants, functions and predicates start upper-case (John, Mother(x))."


def view_unify() -> None:
    page_header("Unification", "fol", "unify")
    learn("unify")
    c1, c2 = st.columns(2)
    a = c1.text_input("First", "Knows(John, x)", help="A term or atom. " + H_FOL)
    b = c2.text_input("Second", "Knows(y, Mother(y))", help="The term or atom to unify with the first. " + H_FOL)
    r = run(fol.unify, a, b)
    if r:
        show(r["markdown"], steps=walk("unify", r, x=a, y=b))
        code_panel("unify", x=a, y=b)


def view_fol_chaining() -> None:
    page_header("First-order chaining", "fol", "fol_chaining")
    learn("fol_chaining")
    kb = st.text_area("Knowledge base (definite clauses and ground facts)", CRIME, height=200,
                      help="One per line: rules like `Missile(x) => Weapon(x)` (premises joined by &), and facts with "
                           "no variables like `Missile(M1)`. " + H_FOL)
    q = st.text_input("Query", "Criminal(West)",
                      help="The atom to prove. Backward chaining also accepts variables, e.g. `Criminal(w)`, and "
                           "reports the binding that answers it.")
    r, r2 = run(fol.forward_chaining, lines(kb), q), run(fol.backward_chaining, lines(kb), q)
    if r and r2:
        st.success(split_answer(r["markdown"])[0])
        how(walk("fol_chaining", (r, r2), kb=lines(kb), query=q))
        st.markdown("##### Full working")
        c1, c2 = st.columns(2)
        with c1:
            show(r["markdown"], answer=False)
        with c2:
            show(r2["markdown"], answer=False)
        code_panel("fol_chaining", kb=lines(kb), query=q)


# ---------------------------------------------------------------------------
# Constraint satisfaction
# ---------------------------------------------------------------------------

CSP_EXAMPLES = {
    "Map of Australia (AIMA Fig 6.1)": dict(
        domains="WA: red green blue\nNT: red green blue\nQ: red green blue\nNSW: red green blue\nV: red green blue\n"
                "SA: red green blue\nT: red green blue",
        constraints="WA != NT\nWA != SA\nNT != SA\nNT != Q\nSA != Q\nSA != NSW\nSA != V\nQ != NSW\nNSW != V"),
    "Ordering puzzle": dict(domains="A: 1 2 3 4\nB: 1 2 3 4\nC: 1 2 3 4\nD: 1 2 3 4",
                            constraints="A < B\nB < C\nC != D\nA != D\nD > B"),
    "Two colours (no solution)": dict(domains="X: red green\nY: red green\nZ: red green",
                                      constraints="X != Y\nY != Z\nX != Z"),
}


def _parse_csp(dom_t: str, con_t: str):
    variables, domains = [], {}
    for l in lines(dom_t):
        v, vals = l.split(":", 1)
        v = v.strip()
        variables.append(v)
        domains[v] = [int(x) if re.fullmatch(r"-?\d+", x) else x for x in vals.replace(",", " ").split()]
    cons = []
    for l in lines(con_t):
        m = re.match(r"\s*(\S+)\s*(!=|≠|==|=|<=|>=|<|>)\s*(\S+)\s*$", l)
        if not m:
            raise ValueError(f"Constraint must look like 'X != Y': {l!r}")
        cons.append([m.group(1), m.group(2), m.group(3)])
    return variables, domains, cons


def _csp_inputs(name_prefix: str):
    name, ex = example_picker(name_prefix, CSP_EXAMPLES)
    return name, ex


def _csp_fields(name, ex):
    c1, c2 = st.columns(2)
    dom_t = c1.text_area("Domains (Variable: values)", ex["domains"], height=200, key=f"cd_{name}",
                         help="One variable per line followed by its possible values, e.g. `WA: red green blue`. The "
                              "order of lines is the 'as listed' variable order.")
    con_t = c2.text_area("Constraints (X op Y)", ex["constraints"], height=200, key=f"cc_{name}",
                         help="Binary constraints, one per line: `X op Y` with op one of != == < > <= >=.")
    return run(_parse_csp, dom_t, con_t)


def view_csp_backtracking() -> None:
    page_header("Backtracking search", "csp", "csp_backtracking")
    name, ex = _csp_inputs("csp_bt")
    learn("csp_backtracking")
    parsed = _csp_fields(name, ex)
    if not parsed:
        return
    variables, domains, cons = parsed
    c1, c2, c3 = st.columns(3)
    vo = c1.selectbox("Variable order", ["mrv", "static"],
                      format_func=lambda x: {"mrv": "MRV + degree", "static": "As listed"}[x],
                      help="MRV picks the variable with the fewest values left (ties broken by most constraints). "
                           "'As listed' uses the order of the domain lines.")
    vv = c2.selectbox("Value order", ["lcv", "static"],
                      format_func=lambda x: {"lcv": "Least constraining", "static": "As listed"}[x],
                      help="Least constraining tries first the value that removes the fewest options from neighbours.")
    inf = c3.selectbox("Inference", ["forward_checking", "mac", "none"],
                       format_func=lambda x: {"forward_checking": "Forward checking", "mac": "MAC (AC-3)",
                                              "none": "None"}[x],
                       help="What to prune after each assignment: forward checking trims neighbours' domains; MAC "
                            "runs full arc consistency; None only checks constraints when values are tried.")
    r = run(csp.backtracking, variables, domains, cons, None, vo, vv, inf)
    if r:
        g, t = st.columns([1, 1.2])
        with g:
            st.graphviz_chart(viz.constraint_graph(variables, r["edges"], r["solution"]))
            st.caption("The constraint graph: one node per variable, one edge per constraint.")
            st.metric("Assignments tried", r["assignments"], delta=f"{r['backtracks']} backtracks", delta_color="off")
        with t:
            show(r["markdown"], steps=walk("csp_backtracking", r, variables=variables, domains=domains,
                                           constraints=cons, variable_order=vo, value_order=vv, inference=inf))
        code_panel("csp_backtracking", variables=variables, domains=domains, constraints=cons, variable_order=vo,
                   value_order=vv, inference=inf)


def view_csp_ac3() -> None:
    page_header("AC-3 arc consistency", "csp", "csp_ac3")
    name, ex = _csp_inputs("csp_ac3")
    learn("csp_ac3")
    parsed = _csp_fields(name, ex)
    if not parsed:
        return
    variables, domains, cons = parsed
    r = run(csp.ac3, variables, domains, cons)
    if r:
        show(r["markdown"], steps=walk("csp_ac3", r, variables=variables, domains=domains, constraints=cons))
        code_panel("csp_ac3", variables=variables, domains=domains, constraints=cons)


# ---------------------------------------------------------------------------
# Games
# ---------------------------------------------------------------------------

GAME_EXAMPLES = {
    "AIMA Fig 5.2 (two-ply)": "[[3, 12, 8], [2, 4, 6], [14, 5, 2]]",
    "Three-ply": "[[[3, 17], [2, 12]], [[15, 25], [2, 5]], [[3, 2], [14, 10]]]",
    "Good move ordering (more pruning)": "[[14, 5, 2], [3, 12, 8], [2, 4, 6]]",
    "Chance nodes (expectiminimax)": json.dumps({
        "children": {"A": ["B", "C"], "B": ["D", "E"], "C": ["F", "G"]},
        "values": {"D": 2, "E": 4, "F": 0, "G": 10}, "types": {"B": "chance", "C": "chance"},
        "probabilities": {"B": [0.5, 0.5], "C": [0.9, 0.1]}}, indent=1),
}


def view_games() -> None:
    page_header("Minimax and alpha-beta", "games", "games")
    name, ex = example_picker("game", GAME_EXAMPLES)
    learn("games")
    txt = st.text_area("Tree (nested lists of leaf values, or JSON with children/values/types)", ex, height=120,
                       key=f"gt_{name}",
                       help="Nested lists: each list is a node and each number a leaf utility for MAX; levels alternate "
                            "MAX, MIN, MAX… from the root. For chance nodes, use the JSON form with `children`, "
                            "`values`, `types` and `probabilities`.")
    tree = run(json.loads, txt)
    if tree is None:
        return
    has_chance = isinstance(tree, dict) and "chance" in json.dumps(tree.get("types", {}))
    use_ab = st.toggle("Alpha-beta pruning", not has_chance, disabled=has_chance,
                       help="On: alpha-beta, showing which branches are skipped. Off: plain minimax (or expectiminimax "
                            "when the tree has chance nodes), which evaluates every node.")
    r = run(games.alphabeta if use_ab else games.minimax, tree)
    if r:
        best = r.get("best_move")
        if best is None:
            kids = r["tree"].children[r["tree"].root]
            best = next((k for k in kids if abs(r["values"].get(k, math.nan) - r["value"]) < 1e-12), None)
        st.graphviz_chart(viz.game_tree(r["tree"], r["values"], r.get("pruned", []), best))
        st.caption("▲ MAX node, ▼ MIN node, ○ chance node, boxes are leaves. Each node shows its backed-up value. "
                   "Dashed: pruned. Thick blue edge: MAX's best move.")
        show(r["markdown"], steps=walk("games", r, tree=tree, use_alpha_beta=use_ab))
        code_panel("games", tree=tree, use_alpha_beta=use_ab)


# ---------------------------------------------------------------------------
# Probability
# ---------------------------------------------------------------------------

BURGLARY = {
    "Burglary": {"cpt": {"": 0.001}}, "Earthquake": {"cpt": {"": 0.002}},
    "Alarm": {"parents": ["Burglary", "Earthquake"], "cpt": {"T,T": 0.95, "T,F": 0.94, "F,T": 0.29, "F,F": 0.001}},
    "JohnCalls": {"parents": ["Alarm"], "cpt": {"T": 0.90, "F": 0.05}},
    "MaryCalls": {"parents": ["Alarm"], "cpt": {"T": 0.70, "F": 0.01}},
}
SPRINKLER = {
    "Cloudy": {"cpt": {"": 0.5}},
    "Sprinkler": {"parents": ["Cloudy"], "cpt": {"T": 0.1, "F": 0.5}},
    "Rain": {"parents": ["Cloudy"], "cpt": {"T": 0.8, "F": 0.2}},
    "WetGrass": {"parents": ["Sprinkler", "Rain"], "cpt": {"T,T": 0.99, "T,F": 0.90, "F,T": 0.90, "F,F": 0.0}},
}


def view_bayes_rule() -> None:
    page_header("Bayes' rule", "probability", "bayes_rule")
    learn("bayes_rule")
    c1, c2, c3 = st.columns(3)
    prior = c1.number_input("Prior P(H)", 0.0, 1.0, 0.01, 0.001, format="%.4f",
                            help="How likely the hypothesis is before seeing the evidence (e.g. how common a condition is).")
    lik = c2.number_input("P(E | H)", 0.0, 1.0, 0.9, 0.01, format="%.4f",
                          help="Likelihood: how often the evidence appears when the hypothesis is true (a test's "
                               "sensitivity).")
    fpr = c3.number_input("P(E | ¬H)", 0.0, 1.0, 0.05, 0.01, format="%.4f",
                          help="False-positive rate: how often the evidence appears when the hypothesis is false.")
    r = run(probability.bayes_rule, prior, lik, fpr)
    if r:
        g, t = st.columns([1, 1.6])
        g.altair_chart(_bar({"prior P(H)": prior, "posterior P(H|E)": r["posterior"]}, "Belief before and after"),
                       width="stretch")
        with t:
            show(r["markdown"], steps=walk("bayes_rule", r, prior=prior, likelihood=lik, false_positive_rate=fpr))
        code_panel("bayes_rule", prior=prior, likelihood=lik, false_positive_rate=fpr)


def view_bayes_net() -> None:
    page_header("Bayesian networks", "probability", "bayes_net")
    nets = {"Burglary alarm (AIMA Fig 14.2)": (BURGLARY, "Burglary", '{"JohnCalls": true, "MaryCalls": true}'),
            "Sprinkler (AIMA Fig 14.12)": (SPRINKLER, "Rain", '{"WetGrass": true}')}
    name = st.selectbox("Example", list(nets), key="bn_ex", help=H_EXAMPLE)
    learn("bayes_net")
    net0, q0, e0 = nets[name]
    net_t = st.text_area("Network (JSON: parents and P(node = true | parents))", json.dumps(net0, indent=1),
                         height=200, key=f"bn_{name}",
                         help='Each node lists its `parents` and a `cpt` giving P(node = true) for every combination '
                              'of parent values, keyed like "T,F" in parent order ("" for no parents).')
    c1, c2 = st.columns(2)
    q = c1.text_input("Query variable", q0, key=f"bq_{name}", help="The variable whose distribution you want.")
    ev_t = c2.text_input("Evidence (JSON)", e0, key=f"be_{name}", help=H_EVIDENCE)
    net, ev = run(json.loads, net_t), run(json.loads, ev_t)
    if net is None or ev is None:
        return
    r = run(probability.bayes_net_query, net, q, ev)
    if r:
        g, t = st.columns([1, 1.4])
        with g:
            st.graphviz_chart(viz.bayes_net(r["parents"], q, ev))
            st.caption("Blue: query. Bold grey: observed evidence. Arrows point from parent to child.")
            st.altair_chart(_bar(r["distribution"], f"P({q} | evidence)"), width="stretch")
        with t:
            show(r["markdown"], steps=walk("bayes_net", r, nodes=net, query=q, evidence=ev))
        code_panel("bayes_net", nodes=net, query=q, evidence=ev)


def view_joint() -> None:
    page_header("Full joint distribution", "probability", "joint")
    learn("joint")
    default = ("Toothache Catch Cavity P\nT T T 0.108\nT F T 0.012\nF T T 0.072\nF F T 0.008\n"
               "T T F 0.016\nT F F 0.064\nF T F 0.144\nF F F 0.576")
    tbl = st.text_area("Table: header row of variable names, then T/F values and a probability", default, height=220,
                       help="First line: variable names followed by P. Then one row per combination of T/F values with "
                            "its probability. The probabilities should sum to 1.")
    rows = lines(tbl)
    header = rows[0].split()[:-1]
    data = [r_.split() for r_ in rows[1:]]
    c1, c2 = st.columns(2)
    q = c1.text_input("Query", "Cavity", help="The variable whose distribution you want.")
    ev = c2.text_input("Evidence (JSON)", '{"Toothache": true}', key="jt_e", help=H_EVIDENCE)
    evd = run(json.loads, ev)
    if evd is not None:
        table = [d[:-1] + [float(d[-1])] for d in data]
        r = run(probability.joint_query, header, table, q, evd)
        if r:
            show(r["markdown"], steps=walk("joint", r, variables=header, table=table, query=q, evidence=evd))
            code_panel("joint", variables=header, table=table, query=q, evidence=evd)


def view_naive_bayes() -> None:
    page_header("Naive Bayes", "probability", "naive_bayes")
    learn("naive_bayes")
    default = ("Outlook Temp Humidity Windy Play\nSunny Hot High F no\nSunny Hot High T no\nOvercast Hot High F yes\n"
               "Rainy Mild High F yes\nRainy Cool Normal F yes\nRainy Cool Normal T no\nOvercast Cool Normal T yes\n"
               "Sunny Mild High F no\nSunny Cool Normal F yes\nRainy Mild Normal F yes\nSunny Mild Normal T yes\n"
               "Overcast Mild High T yes\nOvercast Hot Normal F yes\nRainy Mild High T no")
    tbl = st.text_area("Training data (header row; class in the last column)", default, height=260,
                       help="Space-separated categorical data: a header row of attribute names, then one example per "
                            "row with its class label last. Default: the classic weather data (Witten et al.).")
    rows = [r_.split() for r_ in lines(tbl)]
    attrs = rows[0][:-1]
    c1, c2 = st.columns([3, 1])
    query = c1.text_input("Classify (JSON)", '{"Outlook": "Sunny", "Temp": "Cool", "Humidity": "High", "Windy": "T"}',
                          help="The attribute values of the new example to classify. You can leave attributes out.")
    lap = c2.number_input("Laplace k", 0.0, 5.0, 0.0, 1.0,
                          help="Added to every count so unseen values don't give probability 0. 0 = raw counts; "
                               "1 = standard Laplace smoothing.")
    qd = run(json.loads, query)
    if qd is not None:
        r = run(probability.naive_bayes, attrs, rows[1:], qd, lap)
        if r:
            g, t = st.columns([1, 1.5])
            g.altair_chart(_bar(r["posterior"], "P(class | x)"), width="stretch")
            with t:
                show(r["markdown"], steps=walk("naive_bayes", r, attributes=attrs, data=rows[1:], query=qd, laplace=lap))
            code_panel("naive_bayes", attributes=attrs, data=rows[1:], query=qd, laplace=lap)


# ---------------------------------------------------------------------------
# Machine learning
# ---------------------------------------------------------------------------

def view_kmeans() -> None:
    page_header("k-means clustering", "ml", "kmeans")
    learn("kmeans")
    c1, c2 = st.columns([1, 1])
    pts_t = c1.text_area("Points (x, y)", "1 1\n1.5 2\n3 4\n5 7\n3.5 5\n4.5 5\n3.5 4.5", height=180,
                         help="The data to cluster, one `x y` point per line.")
    cen_t = c2.text_area("Starting centres", "1 1\n5 7", height=80,
                         help="One starting centre per line; the number of lines is k. Different starting centres can "
                              "lead to different final clusters.")
    iters = c2.slider("Iterations", 1, 10, 1,
                      help="How many assign-then-update rounds to run. It stops early if the centres stop moving.")
    metric = c2.selectbox("Distance", ["euclidean", "manhattan"],
                          help="Euclidean: straight-line distance. Manhattan: sum of absolute differences (city-block).")
    pts, cen = run(parse_rows, pts_t), run(parse_rows, cen_t)
    if pts and cen:
        r = run(ml.kmeans, pts, cen, None, metric, iters)
        if r:
            names = [chr(65 + i) for i in range(len(cen))]
            last = r["history"][-1]
            prev = cen if len(r["history"]) == 1 else r["history"][-2]["centres"]
            df = pd.DataFrame([{"x": p[0], "y": p[1], "cluster": a} for p, a in zip(pts, last["assignment"])])
            old = pd.DataFrame([{"x": c[0], "y": c[1], "cluster": n} for n, c in zip(names, prev)])
            new = pd.DataFrame([{"x": c[0], "y": c[1], "cluster": n} for n, c in zip(names, r["centres"])])
            move = pd.DataFrame([{"x": a[0], "y": a[1], "x2": b[0], "y2": b[1], "cluster": n}
                                 for n, a, b in zip(names, prev, r["centres"])])
            col = alt.Color("cluster:N", scale=alt.Scale(range=PALETTE))
            chart = (_scatter(df, "x", "y", "cluster", "Clusters after the last iteration")
                     + alt.Chart(old).mark_point(shape="cross", size=200, filled=True, opacity=0.4)
                     .encode(x="x", y="y", color=col)
                     + alt.Chart(move).mark_rule(strokeDash=[4, 3]).encode(x="x", y="y", x2="x2", y2="y2", color=col)
                     + alt.Chart(new).mark_point(shape="diamond", size=260, filled=True, stroke="black")
                     .encode(x="x", y="y", color=col))
            st.altair_chart(chart.properties(height=380), width="stretch")
            st.caption("Faded crosses: centres before the last update. Diamonds: centres after it. Dashed lines show "
                       "how far each centre moved.")
            show(r["markdown"], steps=walk("kmeans", r, points=pts, centres=cen, metric=metric, max_iterations=iters))
            code_panel("kmeans", points=pts, centres=cen, metric=metric, max_iterations=iters)


def view_knn() -> None:
    page_header("k-nearest neighbour", "ml", "knn")
    learn("knn")
    c1, c2 = st.columns([1, 1])
    tr_t = c1.text_area("Training data (x, y, class)", "1 1 a\n2 1.5 a\n1.5 2.5 a\n6 6 b\n7 5.5 b\n6.5 7 b\n4 4.5 b",
                        height=180, help="Labelled examples, one per line: two attribute values then a class label.")
    q_t = c2.text_input("Query point", "3.5 3.5", help="The new point to classify, as `x y`.")
    k = c2.slider("k", 1, 7, 3, help="How many nearest neighbours vote. Small k follows noise; large k smooths over "
                                     "real structure.")
    norm = c2.checkbox("Min-max normalise", help="Rescale each attribute to [0, 1] before measuring distance, so no "
                                                 "attribute dominates just because of its units.")
    tr = run(parse_rows, tr_t, True)
    if tr:
        q = numbers(q_t)
        r = run(ml.knn, tr, q, k, "euclidean", norm)
        if r:
            df = pd.DataFrame([{"x": t[0], "y": t[1], "class": t[2]} for t in tr])
            dists = sorted(((math.dist(t[:2], q), i) for i, t in enumerate(tr)))[:k]
            links = pd.DataFrame([{"x": q[0], "y": q[1], "x2": tr[i][0], "y2": tr[i][1]} for _, i in dists])
            qdf = pd.DataFrame([{"x": q[0], "y": q[1]}])
            chart = (alt.Chart(links).mark_rule(color="#9CA3AF", strokeDash=[3, 3]).encode(x="x", y="y", x2="x2", y2="y2")
                     + _scatter(df, "x", "y", "class", f"{k} nearest neighbours (unnormalised view)")
                     + alt.Chart(qdf).mark_point(shape="star", size=400, filled=True, color="black").encode(x="x", y="y"))
            st.altair_chart(chart.properties(height=360), width="stretch")
            st.caption(f"Star: the query, predicted as **{r['prediction']}**. Dashed lines join it to its {k} nearest "
                       "neighbours.")
            show(r["markdown"], steps=walk("knn", r, train=tr, query=q, k=k, normalise=norm))
            code_panel("knn", train=tr, query=q, k=k, normalise=norm)


def view_linear_regression() -> None:
    page_header("Linear regression", "ml", "linear_regression")
    learn("linear_regression")
    xy_t = st.text_area("Data (x, y)", "1 3\n2 5\n3 7\n4 10\n5 11\n6 14", height=150, key="lr",
                        help="Training examples, one `x y` pair per line.")
    xy = run(parse_rows, xy_t)
    if xy:
        r = run(ml.linear_regression, [p[0] for p in xy], [p[1] for p in xy])
        if r:
            w0, w1 = r["weights"]
            df = pd.DataFrame([{"x": p[0], "y": p[1], "fit": w0 + w1 * p[0]} for p in xy])
            chart = (alt.Chart(df).mark_rule(color="#F59E0B", strokeDash=[2, 2]).encode(x="x", y="y", y2="fit")
                     + _scatter(df, "x", "y", title=f"y = {fmt(w0)} + {fmt(w1)}x (residuals dashed)")
                     + alt.Chart(df).mark_line(color=ACCENT, strokeWidth=3).encode(x="x", y="fit"))
            st.altair_chart(chart.properties(height=340), width="stretch")
            show(r["markdown"], steps=walk("linear_regression", r, xs=[p[0] for p in xy], ys=[p[1] for p in xy]))
            code_panel("linear_regression", xs=[p[0] for p in xy], ys=[p[1] for p in xy])


def view_gradient_descent() -> None:
    page_header("Gradient descent", "ml", "gradient_descent")
    learn("gradient_descent")
    xy_t = st.text_area("Data (x, y)", "1 3\n2 5\n3 7\n4 10", height=120, key="gd",
                        help="Training examples, one `x y` pair per line. Weights start at [0, 0].")
    c1, c2, c3 = st.columns(3)
    alpha = c1.number_input("Learning rate α", 0.0001, 1.0, 0.02, 0.005, format="%.4f", help=H_ALPHA)
    steps = c2.slider("Steps", 1, 500, 100, help="Number of updates (passes over the data in batch mode).")
    mode = c3.selectbox("Mode", ["batch", "stochastic"],
                        help="Batch: one update per pass using every example. Stochastic: one update per example.")
    xy = run(parse_rows, xy_t)
    if xy:
        r = run(ml.gradient_descent, [p[0] for p in xy], [p[1] for p in xy], [0, 0], alpha, steps, mode)
        if r:
            df = pd.DataFrame({"update": range(len(r["losses"])), "loss": r["losses"]})
            if not all(math.isfinite(v) for v in r["losses"]) or r["losses"][-1] > r["losses"][0]:
                st.warning("The loss is growing: the learning rate is too large, so each step overshoots the minimum.")
            st.altair_chart(alt.Chart(df.replace([math.inf], None), title="Squared-error loss (log scale)")
                            .mark_line(color=ACCENT).encode(x="update:Q", y=alt.Y("loss:Q", scale=alt.Scale(type="symlog")))
                            .properties(height=260), width="stretch")
            show(r["markdown"], steps=walk("gradient_descent", r, xs=[p[0] for p in xy], ys=[p[1] for p in xy],
                                           weights=[0, 0], alpha=alpha, steps=steps, mode=mode))
            code_panel("gradient_descent", xs=[p[0] for p in xy], ys=[p[1] for p in xy], weights=[0, 0], alpha=alpha,
                       steps=steps, mode=mode)


def view_logistic() -> None:
    page_header("Logistic regression", "ml", "logistic")
    learn("logistic")
    c1, c2 = st.columns(2)
    w_t = c1.text_input("Weights [w0, w1]", "-4, 1.5",
                        help="Bias w0 then the input's weight w1. The decision boundary is at x = −w0 / w1.")
    x_t = c2.number_input("x", value=3.0, help="The input value to score. One update step uses target y = 1 and α = 0.1.")
    w = numbers(w_t)
    r = run(ml.logistic_regression, [x_t], w, 1.0, 0.1)
    if r and len(w) == 2:
        lo, hi = x_t - 8, x_t + 8
        xs = [lo + (hi - lo) * i / 200 for i in range(201)]
        df = pd.DataFrame({"x": xs, "P(y=1|x)": [1 / (1 + math.exp(-(w[0] + w[1] * v))) for v in xs]})
        pt = pd.DataFrame({"x": [x_t], "P(y=1|x)": [r["probability"]]})
        chart = (alt.Chart(df, title="Logistic curve").mark_line(color=ACCENT, strokeWidth=3).encode(x="x", y="P(y=1|x)")
                 + alt.Chart(pt).mark_point(size=200, filled=True, color="#F59E0B").encode(x="x", y="P(y=1|x)")
                 + alt.Chart(pd.DataFrame({"y": [0.5]})).mark_rule(strokeDash=[4, 4], color="#9CA3AF").encode(y="y"))
        st.altair_chart(chart.properties(height=300), width="stretch")
        st.caption("Orange point: this input. Dashed line: the 0.5 decision threshold.")
        show(r["markdown"], steps=walk("logistic", r, weights=w, x=x_t, y=1.0, alpha=0.1))
        code_panel("logistic", weights=w, x=x_t, y=1.0, alpha=0.1)


def view_neuron() -> None:
    page_header("A single neuron", "ml", "neuron")
    learn("neuron")
    c1, c2 = st.columns(2)
    x_t = c1.text_input("Inputs x1, x2, …", "1, 1", key="n_x", help="The values arriving at the neuron.")
    w_t = c2.text_input("Weights w0 (bias), w1, …", "-1.5, 1, 1", key="n_w",
                        help="Bias first, then one weight per input, so one more weight than inputs. [-1.5, 1, 1] "
                             "computes AND; [-0.5, 1, 1] computes OR.")
    r = run(ml.neuron, numbers(x_t), numbers(w_t))
    if r:
        z = r["linear"]
        zs = [i / 10 for i in range(-60, 61)]
        df = pd.DataFrame([{"in": v, "output": f(v), "activation": n} for n, f in ml.ACTIVATIONS.items()
                           if n != "linear" for v in zs])
        chart = (alt.Chart(df, title="Activation functions")
                 .mark_line(strokeWidth=2.5).encode(x="in:Q", y=alt.Y("output:Q", scale=alt.Scale(domain=[-1.2, 6])),
                                                    color=alt.Color("activation:N", scale=alt.Scale(range=PALETTE)))
                 + alt.Chart(pd.DataFrame({"in": [z]})).mark_rule(color="black", strokeDash=[4, 3]).encode(x="in:Q"))
        st.altair_chart(chart.properties(height=300), width="stretch")
        st.caption("The dashed line marks this neuron's linear input; where it crosses each curve is that activation's "
                   "output.")
        show(r["markdown"], steps=walk("neuron", r, inputs=numbers(x_t), weights=numbers(w_t)))
        code_panel("neuron", inputs=numbers(x_t), weights=numbers(w_t))


def view_perceptron() -> None:
    page_header("Perceptron learning", "ml", "perceptron")
    learn("perceptron")
    ex_t = st.text_area("Examples (x1, x2, y): AND function by default", "0 0 0\n0 1 0\n1 0 0\n1 1 1", height=120,
                        help="One training example per line: inputs then the target label (0 or 1). Try `0 1 1 0` as "
                             "the labels (XOR) to see a problem it can't learn.")
    c1, c2, c3 = st.columns(3)
    w_t = c1.text_input("Starting weights", "0, 0, 0", help="Initial [w0 (bias), w1, w2].")
    alpha = c2.number_input("α", 0.01, 2.0, 0.5, 0.1, help=H_ALPHA)
    epochs = c3.slider("Epochs", 1, 20, 6, help="Passes through the training examples.")
    exs = run(parse_rows, ex_t)
    if exs:
        r = run(ml.perceptron_learning, exs, numbers(w_t), alpha, epochs)
        if r:
            w = r["weights"]
            df = pd.DataFrame([{"x1": e[0], "x2": e[1], "class": str(int(e[-1]))} for e in exs])
            chart = _scatter(df, "x1", "x2", "class", "Data and the learned decision boundary")
            if len(w) == 3 and abs(w[2]) > 1e-12:
                xs = [-0.5, 1.5]
                line = pd.DataFrame({"x1": xs, "x2": [-(w[0] + w[1] * v) / w[2] for v in xs]})
                chart = chart + alt.Chart(line).mark_line(color="black", strokeDash=[5, 3]).encode(x="x1", y="x2")
            st.altair_chart(chart.properties(height=320), width="stretch")
            st.caption("Dashed line: where w0 + w1·x1 + w2·x2 = 0. Points on one side are classified 1, the other 0.")
            show(r["markdown"], steps=walk("perceptron", r, examples=exs, weights=numbers(w_t), alpha=alpha,
                                           epochs=epochs))
            code_panel("perceptron", examples=exs, weights=numbers(w_t), alpha=alpha, epochs=epochs)


def view_network() -> None:
    page_header("Neural network and back-propagation", "ml", "network")
    learn("network")
    c1, c2 = st.columns(2)
    x_t = c1.text_input("Inputs", "1, 0", key="mlp_x", help="Values for the input units x1, x2, …")
    t_t = c2.text_input("Targets (blank = forward pass only)", "1",
                        help="The desired output(s). With targets, one back-propagation step is shown.")
    layers_t = st.text_area("Layers (JSON: one list per layer, one [w0, w1, …] per unit)",
                            "[[[0.1, 0.2, 0.3], [0.2, -0.1, 0.4]], [[0.3, 0.5, -0.2]]]", height=90,
                            help="Each layer is a list of units; each unit is [bias, weight from previous unit 1, "
                                 "weight from unit 2, …]. The default is 2 inputs → 2 hidden units → 1 output.")
    alpha = st.number_input("α", 0.01, 5.0, 0.5, 0.1, key="mlp_a", help=H_ALPHA)
    layers = run(json.loads, layers_t)
    if layers:
        x = numbers(x_t)
        tg = numbers(t_t) or None
        r = run(ml.mlp_step, x, layers, tg, alpha)
        if r:
            acts = [x]
            for layer in layers:
                prev = acts[-1]
                acts.append([1 / (1 + math.exp(-(w[0] + sum(a * b for a, b in zip(w[1:], prev))))) for w in layer])
            st.graphviz_chart(viz.network(layers, len(x), acts))
            st.caption("Blue edges: positive weights; red: negative; thickness shows size. b = bias, a = activation "
                       "(logistic).")
            show(r["markdown"], steps=walk("network", r, inputs=x, layers=layers, targets=tg, alpha=alpha) if tg else None)
            if tg:
                code_panel("network", inputs=x, layers=layers, targets=tg, alpha=alpha)


def view_cnn() -> None:
    page_header("Convolutional layer sizes", "ml", "cnn")
    learn("cnn")
    c1, c2, c3, c4, c5 = st.columns(5)
    shape = c1.text_input("Input A×B×C", "32 32 3", help="Width, height and depth (channels) of the input, e.g. "
                                                        "32 32 3 for a small RGB image.")
    filt = c2.text_input("Filter P×Q", "5 5", help="Width and height of each filter. Its depth always equals the "
                                                  "input depth.")
    n = c3.number_input("Filters", 1, 512, 6, help="Number of filters, which is also the output depth.")
    stride = c4.number_input("Stride", 1, 8, 1, help="How many positions the filter moves at each step.")
    pad = c5.number_input("Padding", 0, 8, 0, help="Rows/columns of zeros added around each edge of the input.")
    shape_v, filt_v = [int(v) for v in shape.split()], [int(v) for v in filt.split()]
    r = run(ml.cnn_layer, shape_v, filt_v, int(n), int(stride), int(pad))
    if r:
        m1, m2, m3 = st.columns(3)
        m1.metric("Output volume", " × ".join(str(v) for v in r["output"]))
        m2.metric("Neurons", f"{r['neurons']:,}")
        m3.metric("Weights (shared)", f"{r['weights']:,}")
        show(r["markdown"], answer=False, steps=walk("cnn", r, input_shape=shape_v, filter_size=filt_v,
                                                     n_filters=int(n), stride=int(stride), padding=int(pad)))
        code_panel("cnn", input_shape=shape_v, filter_size=filt_v, n_filters=int(n), stride=int(stride), padding=int(pad))


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

# section title -> [(view key, page title, icon, function)]
SECTIONS: dict[str, list[tuple[str, str, str, Callable[[], None]]]] = {
    "Search": [("search_trace", "Trace a search", "🧭", view_search_trace),
               ("search_heuristic", "Check a heuristic", "📏", view_search_heuristic)],
    "Propositional logic": [("truth_table", "Truth tables", "🔢", view_truth_table),
                            ("cnf", "CNF conversion", "🔁", view_cnf),
                            ("entailment", "Entailment and resolution", "✅", view_entailment),
                            ("chaining", "Forward and backward chaining", "⛓️", view_chaining)],
    "Satisfiability": [("dpll", "DPLL", "🌳", view_dpll),
                       ("walksat_step", "WalkSAT: one step", "👣", view_walksat_step),
                       ("walksat_run", "WalkSAT: a full run", "🎲", view_walksat_run)],
    "First-order logic": [("unify", "Unification", "🧩", view_unify),
                          ("fol_chaining", "First-order chaining", "🔗", view_fol_chaining)],
    "Constraint satisfaction": [("csp_backtracking", "Backtracking search", "🗺️", view_csp_backtracking),
                                ("csp_ac3", "AC-3 arc consistency", "✂️", view_csp_ac3)],
    "Game search": [("games", "Minimax and alpha-beta", "♟️", view_games)],
    "Probability": [("bayes_rule", "Bayes' rule", "🧪", view_bayes_rule),
                    ("bayes_net", "Bayesian networks", "🕸️", view_bayes_net),
                    ("joint", "Full joint distribution", "🧮", view_joint),
                    ("naive_bayes", "Naive Bayes", "📨", view_naive_bayes)],
    "Machine learning": [("kmeans", "k-means clustering", "🎯", view_kmeans),
                         ("knn", "k-nearest neighbour", "📍", view_knn),
                         ("linear_regression", "Linear regression", "📈", view_linear_regression),
                         ("gradient_descent", "Gradient descent", "⛰️", view_gradient_descent),
                         ("logistic", "Logistic regression", "〰️", view_logistic),
                         ("neuron", "A single neuron", "⚪", view_neuron),
                         ("perceptron", "Perceptron learning", "➗", view_perceptron),
                         ("network", "Neural network", "🧠", view_network),
                         ("cnn", "Convolutional layer sizes", "🖼️", view_cnn)],
}
VIEWS: dict[str, Callable[[], None]] = {key: fn for items in SECTIONS.values() for key, _, _, fn in items}
_PAGES: dict[str, Any] = {}


# Extra words people search for, beyond each view's title, summary and section
ALIASES = {
    "search_trace": "bfs dfs ucs breadth depth uniform cost greedy a* astar ids iterative deepening ida* dijkstra path "
                    "frontier graph",
    "search_heuristic": "admissible consistent dominance h* heuristic a*",
    "truth_table": "models valid satisfiable propositional",
    "cnf": "conjunctive normal form clauses de morgan",
    "entailment": "resolution model checking proof kb",
    "chaining": "horn definite clauses forward backward inference",
    "dpll": "sat davis putnam unit clause pure symbol backtracking",
    "walksat_step": "sat local search flip random walk",
    "walksat_run": "sat local search flip random walk",
    "unify": "unifier mgu substitution occur check first-order",
    "fol_chaining": "first-order predicate datalog forward backward crime west",
    "csp_backtracking": "constraint csp mrv degree lcv forward checking mac map colouring coloring sudoku",
    "csp_ac3": "arc consistency constraint csp",
    "games": "minimax alpha beta pruning expectiminimax adversarial game tree chess",
    "bayes_rule": "bayes theorem posterior prior conditional probability test",
    "bayes_net": "bayesian network belief graphical model inference enumeration burglary alarm",
    "joint": "joint distribution marginal conditional probability",
    "naive_bayes": "classifier spam laplace smoothing",
    "kmeans": "k-means clustering unsupervised centroids",
    "knn": "k-nn nearest neighbour neighbor classifier distance",
    "linear_regression": "least squares line fit ols",
    "gradient_descent": "learning rate sgd stochastic batch loss optimisation optimization",
    "logistic": "sigmoid logistic regression classifier probability",
    "neuron": "activation relu sigmoid tanh threshold perceptron unit",
    "perceptron": "linear classifier learning rule and or xor",
    "network": "neural network mlp backpropagation backprop deep learning hidden layer",
    "cnn": "convolutional neural network filter stride padding convolution image",
}


def search_views(query: str) -> list[tuple[str, str, str, str]]:
    """Views matching every word of the query, as (section, key, title, icon), best matches first."""
    words = query.lower().split()
    if not words:
        return []
    hits = []
    for section, items in SECTIONS.items():
        for key, title, icon, _ in items:
            name = title.lower()
            text = " ".join([name, section.lower(), explain.VIEWS[key]["summary"].lower(), ALIASES.get(key, "")])
            if all(w in text for w in words):
                score = sum(2 if w in name else 1 for w in words)
                hits.append((score, section, key, title, icon))
    hits.sort(key=lambda h: -h[0])
    return [h[1:] for h in hits]


def sidebar_nav(home, current) -> None:
    """Home, a quick search, then one collapsible group per area. The group holding the current page starts open."""
    st.page_link(home, label="Home", icon="🏠")
    q = st.text_input("Search", key="nav_search", placeholder="🔍 Search, e.g. A*, Bayes, k-means",
                      label_visibility="collapsed",
                      help="Type an algorithm's name or a keyword (BFS, pruning, backprop, smoothing…) to jump to it.")
    if q.strip():
        hits = search_views(q)
        for section, key, title, icon in hits:
            st.page_link(_PAGES[key], label=title, icon=icon, help=section)
        if not hits:
            st.caption("No matching algorithm. Try a shorter word.")
        return
    for section, items in SECTIONS.items():
        open_ = any(_PAGES[key] is current or getattr(current, "url_path", None) == url_path(key) for key, *_ in items)
        with st.expander(section, expanded=open_):
            for key, title, icon, _ in items:
                st.page_link(_PAGES[key], label=title, icon=icon)


def url_path(key: str) -> str:
    return key.replace("_", "-")


def view_home() -> None:
    st.title("aiml-calc")
    st.markdown(
        '<div class="lead">Classic AI and machine-learning algorithms, implemented from scratch and worked step by '
        "step. Every page explains its algorithm three ways (for newcomers, technically, and where it's used), walks "
        "through how it reached its answer, draws the graphs, and gives you the Python code with your values built in, "
        "ready to edit and run.</div>", unsafe_allow_html=True)
    st.markdown(
        "The algorithms follow Russell & Norvig's *Artificial Intelligence: A Modern Approach* and are written in pure "
        "Python with no numerical libraries. Every result comes with a second method or an independent check where one "
        "exists, and states the conventions it used (tie-breaking, goal-test timing and so on), because those small "
        "choices are where implementations quietly differ. The same algorithms are available to AI assistants as an "
        "MCP server, and a test suite checks each one against textbook examples, against independent methods on "
        "hundreds of random inputs, and against the programs the app generates.")
    st.subheader("Which algorithm, when")
    st.caption("Pick an algorithm from the sidebar, or click a name below.")
    md = lambda t: _inline_md(html.escape(t)).replace("\\*", "*")  # noqa: E731
    md_code = lambda t: re.sub(r"`(.+?)`", r"<code>\1</code>", md(t))  # noqa: E731
    rows = []
    for section, items in SECTIONS.items():
        for i, (key, title, icon, _) in enumerate(items):
            when, world, soft = usecases.SUMMARY[key]
            area = f'<td class="area" rowspan="{len(items)}">{section}</td>' if i == 0 else ""
            rows.append(f'<tr>{area}<td class="algo"><a href="{url_path(key)}" target="_self">{icon} {title}</a></td>'
                        f"<td>{md_code(when)}</td><td>{md_code(world)}</td><td>{md_code(soft)}</td></tr>")
    st.markdown('<table class="matrix"><thead><tr><th>Area</th><th>Algorithm</th><th>Use it when</th>'
                "<th>Real world</th><th>In software</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>",
                unsafe_allow_html=True)


CSS = """
<style>
div.block-container {padding-top: 2rem; max-width: 1400px;}
[data-testid=stMarkdownContainer] table {font-size: 0.86rem;}
.lead {font-size: 1.02rem; line-height: 1.6; color: #374151; max-width: 900px; margin: -0.4rem 0 1.2rem;}
[data-testid=stTextArea] textarea {font-family: "Source Code Pro", ui-monospace, monospace; font-size: 0.88rem;}
section[data-testid=stSidebar] [data-testid=stExpander] details {border: none;}
section[data-testid=stSidebar] [data-testid=stExpander] summary {font-weight: 600; padding-left: 0.4rem;}
table.matrix {width: 100%; border-collapse: collapse; font-size: 0.9rem;}
table.matrix th {text-align: left; background: #F3F4F6; padding: 0.5rem 0.6rem;}
table.matrix td {padding: 0.45rem 0.6rem; border-top: 1px solid #E5E7EB; vertical-align: top;}
table.matrix td.area {font-weight: 600; color: #1E3A8A; background: #F9FAFB; white-space: nowrap;}
table.matrix td.algo a {white-space: nowrap; font-weight: 600; text-decoration: none;}
p.summary {font-size: 1.05rem; font-weight: 600; color: #1E3A8A; margin: 0.4rem 0 0.2rem;}
</style>
"""


def setup() -> None:
    st.set_page_config(page_title="aiml-calc", page_icon="🧭", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


def main() -> None:
    setup()
    home = st.Page(view_home, title="Home", icon="🏠", default=True)
    nav: dict[str, list] = {"": [home]}
    for section, items in SECTIONS.items():
        pages = []
        for key, title, icon, fn in items:
            page = st.Page(fn, title=title, icon=icon, url_path=url_path(key))
            _PAGES[key] = page
            pages.append(page)
        nav[section] = pages
    current = st.navigation(nav, position="hidden")
    with st.sidebar:
        sidebar_nav(home, current)
    current.run()
    if st.session_state.pop("_code_open", None):   # the page stopped early, e.g. on an input error
        st.toast("Fix the inputs on this page to see its code.")


if __name__ == "__main__":
    main()
