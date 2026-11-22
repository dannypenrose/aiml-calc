"""Propositional logic (AIMA chapter 7): parsing, truth tables, model counting, entailment,
CNF conversion, resolution, forward and backward chaining.

Formula syntax (any mix works):
  not:  ¬  ~  !  -  not      and: ∧  &  ^  /\\  and      or: ∨  |  \\/  or
  implies: ⇒  =>  ->         iff: ⇔  <=>  <->           constants: True, False
Precedence (tightest first): ¬, ∧, ∨, ⇒, ⇔.  ⇒ is right-associative.

Clauses may also be given in a compact form, e.g. "-BvSvW".
"""

from __future__ import annotations

import itertools
import re
from typing import Any, Iterable, Optional

from .common import md_table, natural_key

# AST nodes are tuples: ('sym', name) ('const', bool) ('not', a) ('and', a, b) ('or', a, b)
# ('imp', a, b) ('iff', a, b)

_TOKEN_RE = re.compile(
    r"\s*(?:(?P<iff><=>|<->|⇔|\biff\b)|(?P<imp>=>|->|⇒|\bimplies\b)|(?P<and>∧|&&|&|\^|/\\|\band\b)"
    r"|(?P<or>∨|\|\||\||\\/|\bor\b)|(?P<not>¬|~|!|-|\bnot\b)|(?P<lp>\()|(?P<rp>\))"
    r"|(?P<const>\bTrue\b|\bFalse\b|\btrue\b|\bfalse\b)|(?P<sym>[A-Za-z_][A-Za-z0-9_]*))",
)


def tokenize(s: str) -> list[tuple[str, str]]:
    out = []
    pos = 0
    s = s.strip()
    while pos < len(s):
        m = _TOKEN_RE.match(s, pos)
        if not m or m.end() == pos:
            raise ValueError(f"Cannot parse formula near: {s[pos:pos + 15]!r}")
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
        pos = m.end()
        while pos < len(s) and s[pos].isspace():
            pos += 1
    return out


def parse(s: str):
    """Parse a propositional formula into an AST."""
    toks = tokenize(s)
    i = 0

    def peek():
        return toks[i][0] if i < len(toks) else None

    def eat(kind):
        nonlocal i
        if peek() != kind:
            raise ValueError(f"Expected {kind} in {s!r}")
        i += 1
        return toks[i - 1][1]

    def p_iff():
        a = p_imp()
        while peek() == "iff":
            eat("iff")
            a = ("iff", a, p_imp())
        return a

    def p_imp():
        a = p_or()
        if peek() == "imp":
            eat("imp")
            return ("imp", a, p_imp())
        return a

    def p_or():
        a = p_and()
        while peek() == "or":
            eat("or")
            a = ("or", a, p_and())
        return a

    def p_and():
        a = p_not()
        while peek() == "and":
            eat("and")
            a = ("and", a, p_not())
        return a

    def p_not():
        if peek() == "not":
            eat("not")
            return ("not", p_not())
        return p_atom()

    def p_atom():
        k = peek()
        if k == "lp":
            eat("lp")
            a = p_iff()
            eat("rp")
            return a
        if k == "const":
            return ("const", eat("const").lower() == "true")
        if k == "sym":
            return ("sym", eat("sym"))
        raise ValueError(f"Unexpected token in {s!r}")

    tree = p_iff()
    if i != len(toks):
        raise ValueError(f"Trailing input in {s!r}")
    return tree


_PREC = {"iff": 1, "imp": 2, "or": 3, "and": 4, "not": 5, "sym": 6, "const": 6}
_OPS = {"iff": " ⇔ ", "imp": " ⇒ ", "or": " ∨ ", "and": " ∧ "}


def to_str(t, parent: int = 0) -> str:
    k = t[0]
    if k == "sym":
        return t[1]
    if k == "const":
        return "True" if t[1] else "False"
    if k == "not":
        return "¬" + to_str(t[1], _PREC["not"])
    p = _PREC[k]
    left = to_str(t[1], p if k in ("and", "or") else p + 1)
    right = to_str(t[2], p if k in ("and", "or", "imp") else p + 1)
    s = left + _OPS[k] + right
    return f"({s})" if p < parent or (parent == p and k in ("imp", "iff")) else s


def symbols(t, acc: Optional[set] = None) -> set[str]:
    acc = set() if acc is None else acc
    if t[0] == "sym":
        acc.add(t[1])
    elif t[0] != "const":
        for c in t[1:]:
            symbols(c, acc)
    return acc


def evaluate(t, model: dict[str, bool]) -> bool:
    k = t[0]
    if k == "sym":
        return model[t[1]]
    if k == "const":
        return t[1]
    if k == "not":
        return not evaluate(t[1], model)
    a, b = evaluate(t[1], model), evaluate(t[2], model)
    return {"and": a and b, "or": a or b, "imp": (not a) or b, "iff": a == b}[k]


def _as_tree(f):
    return parse(f) if isinstance(f, str) else f


# ---------------------------------------------------------------------------
# Truth tables, model counting, entailment by model checking
# ---------------------------------------------------------------------------

def all_models(syms: list[str]) -> Iterable[dict[str, bool]]:
    """Models in textbook order: first row all false, last row all true (AIMA Fig 7.9)."""
    for bits in itertools.product([False, True], repeat=len(syms)):
        yield dict(zip(syms, bits))


def truth_table(formulas: list[str], extra_symbols: Optional[list[str]] = None, max_rows: int = 64) -> dict[str, Any]:
    trees = [_as_tree(f) for f in formulas]
    syms = set(extra_symbols or [])
    for t in trees:
        symbols(t, syms)
    syms_l = sorted(syms, key=natural_key)
    rows = []
    counts = [0] * len(trees)
    for m in all_models(syms_l):
        vals = [evaluate(t, m) for t in trees]
        for i, v in enumerate(vals):
            counts[i] += v
        if len(rows) < max_rows:
            rows.append(["T" if m[s] else "F" for s in syms_l] + ["**T**" if v else "F" for v in vals])
    n = 2 ** len(syms_l)
    labels = [to_str(t) for t in trees]
    md = ["## Truth table", ""]
    summary = []
    for lab, c in zip(labels, counts):
        kind = "valid (tautology)" if c == n else "unsatisfiable (contradiction)" if c == 0 else "satisfiable"
        summary.append(f"`{lab}`: **{c} of {n}** models ({kind})")
    md.append("**Answer:** " + "; ".join(summary))
    md.append("")
    md.append(md_table(syms_l + labels, rows))
    if n > max_rows:
        md.append(f"\n_(showing first {max_rows} of {n} rows)_")
    md.append("")
    md.append(f"Method 2 (counting): {len(syms_l)} symbols give 2^{len(syms_l)} = {n} models in total. "
              "Fix the symbols the formula forces, then each free symbol doubles the count.")
    return {"symbols": syms_l, "counts": dict(zip(labels, counts)), "total": n, "markdown": "\n".join(md)}


def count_models(formula: str, all_symbols: Optional[list[str]] = None) -> dict[str, Any]:
    """How many models of `formula` over the given symbol set (the full list of symbols in the problem)."""
    r = truth_table([formula], extra_symbols=all_symbols)
    return {"count": list(r["counts"].values())[0], "total": r["total"], "markdown": r["markdown"]}


# ---------------------------------------------------------------------------
# CNF
# ---------------------------------------------------------------------------

def _elim_iff(t):
    k = t[0]
    if k in ("sym", "const"):
        return t
    if k == "not":
        return ("not", _elim_iff(t[1]))
    a, b = _elim_iff(t[1]), _elim_iff(t[2])
    if k == "iff":
        return ("and", ("imp", a, b), ("imp", b, a))
    return (k, a, b)


def _elim_imp(t):
    k = t[0]
    if k in ("sym", "const"):
        return t
    if k == "not":
        return ("not", _elim_imp(t[1]))
    a, b = _elim_imp(t[1]), _elim_imp(t[2])
    if k == "imp":
        return ("or", ("not", a), b)
    return (k, a, b)


def _push_not(t):
    k = t[0]
    if k in ("sym", "const"):
        return t
    if k == "not":
        a = t[1]
        ka = a[0]
        if ka == "not":
            return _push_not(a[1])  # double negation
        if ka == "and":
            return ("or", _push_not(("not", a[1])), _push_not(("not", a[2])))  # De Morgan
        if ka == "or":
            return ("and", _push_not(("not", a[1])), _push_not(("not", a[2])))  # De Morgan
        if ka == "const":
            return ("const", not a[1])
        return t
    return (k, _push_not(t[1]), _push_not(t[2]))


def _distribute(t):
    k = t[0]
    if k in ("sym", "const", "not"):
        return t
    a, b = _distribute(t[1]), _distribute(t[2])
    if k == "or":
        if a[0] == "and":
            return _distribute(("and", ("or", a[1], b), ("or", a[2], b)))
        if b[0] == "and":
            return _distribute(("and", ("or", a, b[1]), ("or", a, b[2])))
    return (k, a, b)


Literal = tuple[str, bool]  # (symbol, positive?)
Clause = frozenset


def _collect(t, op):
    if t[0] == op:
        return _collect(t[1], op) + _collect(t[2], op)
    return [t]


def tree_to_clauses(t) -> list[frozenset]:
    """CNF tree → list of clauses (frozensets of literals). Tautological clauses are dropped."""
    clauses: list[frozenset] = []
    for conj in _collect(t, "and"):
        lits = set()
        taut = False
        for d in _collect(conj, "or"):
            if d[0] == "sym":
                lits.add((d[1], True))
            elif d[0] == "not" and d[1][0] == "sym":
                lits.add((d[1][1], False))
            elif d[0] == "const":
                if d[1]:
                    taut = True
            else:
                raise ValueError("Formula is not in CNF")
        if any((s, not v) in lits for s, v in lits):
            taut = True
        if taut:
            continue
        c = frozenset(lits)
        if c not in clauses:
            clauses.append(c)
    return clauses


def lit_str(l: Literal) -> str:
    return l[0] if l[1] else "¬" + l[0]


def _sorted_lits(c, order: Optional[dict[str, int]] = None) -> list[Literal]:
    if order:
        return sorted(c, key=lambda l: (order.get(l[0], 10**6), natural_key(l[0]), not l[1]))
    return sorted(c, key=lambda l: (natural_key(l[0]), not l[1]))


def appearance_order(formula: str) -> dict[str, int]:
    """Symbols in the order they first appear in the formula text (used to print clauses in the order the input uses)."""
    order: dict[str, int] = {}
    for kind, val in tokenize(formula):
        if kind == "sym" and val not in order:
            order[val] = len(order)
    return order


def clause_str(c, order: Optional[dict[str, int]] = None) -> str:
    if not c:
        return "□ (empty clause)"
    return " ∨ ".join(lit_str(l) for l in _sorted_lits(c, order))


def clause_compact(c, order: Optional[dict[str, int]] = None) -> str:
    """Compact clause notation, e.g. -BvSvW."""
    return "v".join(("" if v else "-") + s for s, v in _sorted_lits(c, order))


def parse_clause(c: Any) -> frozenset:
    """Accept 'A ∨ ¬B', 'A | ~B', '-BvSvW', or a list like ['A', '-B']."""
    if isinstance(c, (list, tuple)):
        lits = set()
        for x in c:
            x = str(x).strip()
            neg = x[:1] in ("-", "~", "¬", "!")
            lits.add((x.lstrip("-~¬! "), not neg))
        return frozenset(lits)
    s = str(c).strip()
    if re.fullmatch(r"-?[A-Z][A-Z0-9_]*(v-?[A-Z][A-Z0-9_]*)*", s):
        return parse_clause(s.split("v"))
    cl = tree_to_clauses(_push_not(_elim_imp(_elim_iff(parse(s)))))
    if len(cl) != 1:
        raise ValueError(f"{s!r} is not a single clause")
    return cl[0]


def to_cnf(formula: str) -> dict[str, Any]:
    t0 = parse(formula)
    stages = [("Start", t0)]
    t1 = _elim_iff(t0)
    if t1 != t0:
        stages.append(("Eliminate ⇔: α ⇔ β ≡ (α ⇒ β) ∧ (β ⇒ α)", t1))
    t2 = _elim_imp(t1)
    if t2 != t1:
        stages.append(("Eliminate ⇒: α ⇒ β ≡ ¬α ∨ β", t2))
    t3 = _push_not(t2)
    if t3 != t2:
        stages.append(("Move ¬ inwards: De Morgan, ¬¬α ≡ α", t3))
    t4 = _distribute(t3)
    if t4 != t3:
        stages.append(("Distribute ∨ over ∧", t4))
    clauses = tree_to_clauses(t4)
    order = appearance_order(formula)

    # Method 2: read the CNF off the truth table (one clause per false row) and confirm equivalence.
    syms = sorted(symbols(t0), key=natural_key)
    equivalent = all(evaluate(t0, m) == all(any(m[s] == v for s, v in c) for c in clauses) for m in all_models(syms))
    false_rows = [m for m in all_models(syms) if not evaluate(t0, m)]

    md = ["## CNF conversion", "",
          f"**Answer:** {' ∧ '.join('(' + clause_str(c, order) + ')' for c in clauses) or 'True (valid: no clauses)'}",
          f"Compact form: **{', '.join(clause_compact(c, order) for c in clauses) or '(none)'}** "
          "(literal order within a clause doesn't matter logically; printed in the order symbols appear in the input)", "",
          "### Method 1: rewrite rules (AIMA §7.5.2)"]
    for i, (rule, t) in enumerate(stages):
        md.append(f"{i}. {rule}: `{to_str(t)}`")
    md.append("")
    md.append("### Method 2: truth-table check")
    md.append(f"The formula is false in {len(false_rows)} of {2 ** len(syms)} rows. Each false row gives one clause that "
              "rules it out (negate every symbol's value in that row). "
              f"The CNF above is {'**equivalent**' if equivalent else '**NOT equivalent** (bug!)'} to the original on all rows.")
    if 0 < len(false_rows) <= 8:
        md.append("Clauses from false rows: " + ", ".join(
            "(" + " ∨ ".join(("¬" if m[s] else "") + s for s in syms) + ")" for m in false_rows))
    return {"clauses": [clause_compact(c, order) for c in clauses], "equivalent": equivalent, "markdown": "\n".join(md)}


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

def _resolve(ci, cj):
    out = []
    for s, v in ci:
        if (s, not v) in cj:
            r = (ci - {(s, v)}) | (cj - {(s, not v)})
            out.append((s, frozenset(r)))
    return out


def _is_taut(c) -> bool:
    return any((s, not v) in c for s, v in c)


def resolution(kb: list[str], query: Optional[str] = None, max_clauses: int = 400) -> dict[str, Any]:
    """PL-RESOLUTION: show KB ⊨ query by deriving the empty clause from CNF(KB ∧ ¬query).
    With no query, checks whether the KB itself is unsatisfiable."""
    sentences = [parse(f) for f in kb]
    if query:
        sentences.append(("not", parse(query)))
    clauses: list[frozenset] = []
    origin: dict[frozenset, str] = {}
    for idx, t in enumerate(sentences):
        src = "¬query" if (query and idx == len(sentences) - 1) else f"KB {idx + 1}"
        for c in tree_to_clauses(_distribute(_push_not(_elim_imp(_elim_iff(t))))):
            if c not in origin:
                clauses.append(c)
                origin[c] = src
    initial = list(clauses)
    parents: dict[frozenset, tuple[frozenset, frozenset, str]] = {}
    seen = set(clauses)
    empty_found = False
    rounds = 0
    while not empty_found:
        rounds += 1
        new = []
        for ci, cj in itertools.combinations(list(clauses), 2):
            for sym, r in _resolve(ci, cj):
                if _is_taut(r) or r in seen:
                    continue
                parents[r] = (ci, cj, sym)
                seen.add(r)
                new.append(r)
                if not r:
                    empty_found = True
                    break
            if empty_found:
                break
        if not new or len(seen) > max_clauses:
            break
        clauses.extend(new)

    md = ["## Resolution", ""]
    numbered = {c: i + 1 for i, c in enumerate(initial)}
    md.append("Clauses from CNF(KB" + (" ∧ ¬query" if query else "") + "):")
    for c in initial:
        md.append(f"- C{numbered[c]}: {clause_str(c)}  _(from {origin[c]})_")
    md.append("")
    if empty_found:
        # walk back from the empty clause to list only the clauses used in the proof
        used: list[frozenset] = []

        def walk(c):
            if c in numbered or c in used:
                return
            p1, p2, _ = parents[c]
            walk(p1)
            walk(p2)
            used.append(c)

        walk(frozenset())
        n = len(initial)
        for c in used:
            n += 1
            numbered[c] = n
            p1, p2, sym = parents[c]
            md.append(f"- C{n} = resolve C{numbered[p1]}, C{numbered[p2]} on {sym}: **{clause_str(c)}**")
        ans = ("**KB ⊨ query** (the empty clause was derived, so KB ∧ ¬query is unsatisfiable)" if query
               else "**the clause set is unsatisfiable**")
    else:
        ans = ("**KB ⊭ query** (no new clauses can be derived and the empty clause never appears)" if query
               else "**the clause set is satisfiable** (resolution reached a fixed point without the empty clause)")
        if len(seen) > max_clauses:
            ans = f"stopped after {max_clauses} clauses without a result"
    md.insert(1, f"**Answer:** {ans}\n")
    if query:
        try:
            ent = entails(kb, query)["entails"]
            md.append("")
            md.append(f"Method 2 (truth table / model checking) agrees: KB {'⊨' if ent else '⊭'} query.")
        except Exception:  # pragma: no cover - too many symbols
            pass
    return {"proved": empty_found, "markdown": "\n".join(md)}


def entails(kb: list[str], query: str, show_rows: int = 32) -> dict[str, Any]:
    """TT-ENTAILS: KB ⊨ α iff α is true in every model where every KB sentence is true."""
    kb_t = [parse(f) for f in kb]
    q = parse(query)
    syms = set()
    for t in kb_t + [q]:
        symbols(t, syms)
    syms_l = sorted(syms, key=natural_key)
    kb_models = 0
    counter = None
    rows = []
    for m in all_models(syms_l):
        kbv = all(evaluate(t, m) for t in kb_t)
        qv = evaluate(q, m)
        if kbv:
            kb_models += 1
            if not qv and counter is None:
                counter = m
            if len(rows) < show_rows:
                rows.append(["T" if m[s] else "F" for s in syms_l] + ["T", "**T**" if qv else "**F** ✗"])
    ok = counter is None
    md = ["## Entailment by model checking", "",
          f"**Answer:** KB {'⊨' if ok else '⊭'} `{to_str(q)}`. "
          + (f"The query is true in all {kb_models} models of the KB." if ok else
             "Counter-example (KB true, query false): " + ", ".join(f"{s}={'T' if counter[s] else 'F'}" for s in syms_l)),
          "", "Rows where every KB sentence is true:", "",
          md_table(syms_l + ["KB", "query"], rows) if rows else "_(none: the KB is unsatisfiable, so it entails everything)_"]
    return {"entails": ok, "kb_models": kb_models, "markdown": "\n".join(md)}


# ---------------------------------------------------------------------------
# Forward and backward chaining over definite clauses
# ---------------------------------------------------------------------------

def _parse_definite(rules: list[str], facts: list[str]):
    parsed = []
    for r in rules:
        t = parse(r)
        if t[0] == "imp":
            prem = [p[1] for p in _collect(t[1], "and")]
            if not all(p[0] == "sym" for p in _collect(t[1], "and")) or t[2][0] != "sym":
                raise ValueError(f"{r!r} is not a definite clause (conjunction of symbols ⇒ symbol)")
            parsed.append((prem, t[2][1], r))
        elif t[0] == "sym":
            facts = list(facts) + [t[1]]
        else:
            raise ValueError(f"{r!r} is not a definite clause")
    return parsed, [str(f) for f in facts]


def forward_chaining(rules: list[str], facts: list[str], query: str) -> dict[str, Any]:
    """PL-FC-ENTAILS? (AIMA Fig 7.15) with the agenda, count and inferred tables at every step."""
    parsed, facts = _parse_definite(rules, facts)
    count = [len(set(p)) for p, _, _ in parsed]
    inferred: dict[str, bool] = {}
    agenda = list(dict.fromkeys(facts))
    rows = []
    found = False
    step = 0
    while agenda:
        p = agenda.pop(0)
        step += 1
        if p == query:
            rows.append([str(step), p, "**query reached**", "–", " ".join(agenda) or "∅"])
            found = True
            break
        if inferred.get(p):
            rows.append([str(step), p, "already inferred, skip", "–", " ".join(agenda) or "∅"])
            continue
        inferred[p] = True
        fired = []
        for i, (prem, concl, txt) in enumerate(parsed):
            if p in prem:
                count[i] -= 1
                if count[i] == 0:
                    agenda.append(concl)
                    fired.append(f"{concl} (from {txt})")
        counts = ", ".join(f"r{i + 1}:{c}" for i, c in enumerate(count))
        rows.append([str(step), p, ", ".join(fired) or "–", counts, " ".join(agenda) or "∅"])
    md = ["## Forward chaining", "",
          f"**Answer:** KB {'⊨' if found else '⊭'} {query}.", "",
          "Rules: " + "; ".join(f"r{i + 1}: {txt}" for i, (_, _, txt) in enumerate(parsed)), "",
          md_table(["Step", "Pop from agenda", "Rules fired → added to agenda", "Counts after", "Agenda after"], rows), "",
          "**Conventions used:** agenda is a FIFO queue starting with the known facts in the order given; "
          "count[r] = number of premises of rule r not yet known; a rule fires when its count reaches 0."]
    return {"entails": found, "inferred": [k for k, v in inferred.items() if v], "markdown": "\n".join(md)}


def backward_chaining(rules: list[str], facts: list[str], query: str) -> dict[str, Any]:
    """Goal-directed proof: try to prove the query by proving all premises of some rule that concludes it."""
    parsed, facts = _parse_definite(rules, facts)
    lines: list[str] = []
    proven: set[str] = set(facts)
    failed: set[str] = set()

    def prove(goal: str, stack: list[str], depth: int) -> bool:
        ind = "  " * depth
        if goal in proven:
            lines.append(f"{ind}- {goal}: {'known fact' if goal in facts else 'already proved'} ✓")
            return True
        if goal in stack:
            lines.append(f"{ind}- {goal}: already on the goal stack (loop), fail on this branch ✗")
            return False
        if goal in failed:
            lines.append(f"{ind}- {goal}: already shown to fail ✗")
            return False
        rules_for = [(prem, txt) for prem, concl, txt in parsed if concl == goal]
        if not rules_for:
            lines.append(f"{ind}- {goal}: not a fact and no rule concludes it ✗")
            failed.add(goal)
            return False
        for prem, txt in rules_for:
            lines.append(f"{ind}- goal {goal}: try `{txt}`, need {', '.join(prem)}")
            if all(prove(p, stack + [goal], depth + 1) for p in prem):
                lines.append(f"{ind}- {goal} proved ✓")
                proven.add(goal)
                return True
        lines.append(f"{ind}- {goal}: no rule succeeded ✗")
        failed.add(goal)
        return False

    ok = prove(query, [], 0)
    md = ["## Backward chaining", "", f"**Answer:** KB {'⊨' if ok else '⊭'} {query}.", "", *lines, "",
          "**Conventions used:** rules tried in the order given, premises left to right; a goal already on the stack fails "
          "(loop check); proved goals are remembered."]
    fc = forward_chaining(rules, facts, query)["entails"]
    md.append(f"\nMethod 2 (forward chaining) agrees: {'yes' if fc == ok else 'NO (check the rules)'}.")
    return {"entails": ok, "markdown": "\n".join(md)}
