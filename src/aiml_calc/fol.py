"""First-order logic (AIMA chapter 9): unification, forward chaining and backward chaining over definite clauses.

Syntax: variables start with a lower-case letter (x, y, z1); constants, functions and predicates start with an
upper-case letter (John, Mother(x), Knows(John, x)). Rules are written "P(x) & Q(x, y) => R(y)".
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass
from typing import Any, Iterator, Optional, Union


@dataclass(frozen=True)
class Var:
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Compound:
    op: str
    args: tuple = ()

    def __str__(self) -> str:
        return self.op if not self.args else f"{self.op}({', '.join(str(a) for a in self.args)})"


Term = Union[Var, Compound]

_TOK = re.compile(r"\s*([A-Za-z_][A-Za-z0-9_]*|\(|\)|,)")


def parse_term(s: str) -> Term:
    toks = []
    pos = 0
    s = s.strip()
    while pos < len(s):
        m = _TOK.match(s, pos)
        if not m:
            raise ValueError(f"Cannot parse {s!r} near {s[pos:pos + 10]!r}")
        toks.append(m.group(1))
        pos = m.end()
    i = 0

    def term() -> Term:
        nonlocal i
        name = toks[i]
        i += 1
        if i < len(toks) and toks[i] == "(":
            i += 1
            args = []
            if toks[i] != ")":
                while True:
                    args.append(term())
                    if toks[i] == ",":
                        i += 1
                        continue
                    break
            if toks[i] != ")":
                raise ValueError(f"Missing ')' in {s!r}")
            i += 1
            return Compound(name, tuple(args))
        return Var(name) if name[0].islower() else Compound(name)

    t = term()
    if i != len(toks):
        raise ValueError(f"Trailing input in {s!r}")
    return t


def subst(theta: dict[Var, Term], t: Term) -> Term:
    if isinstance(t, Var):
        return subst(theta, theta[t]) if t in theta else t
    return Compound(t.op, tuple(subst(theta, a) for a in t.args))


def _occurs(v: Var, t: Term, theta) -> bool:
    if v == t:
        return True
    if isinstance(t, Var) and t in theta:
        return _occurs(v, theta[t], theta)
    if isinstance(t, Compound):
        return any(_occurs(v, a, theta) for a in t.args)
    return False


def _unify(x: Term, y: Term, theta: Optional[dict], log: Optional[list], depth: int = 0) -> Optional[dict]:
    ind = "  " * depth
    if theta is None:
        return None
    if x == y:
        return theta
    if isinstance(x, Var):
        return _unify_var(x, y, theta, log, depth)
    if isinstance(y, Var):
        return _unify_var(y, x, theta, log, depth)
    if x.op != y.op or len(x.args) != len(y.args):
        if log is not None:
            log.append(f"{ind}- {x} vs {y}: different {'symbols' if x.op != y.op else 'number of arguments'} → **fail**")
        return None
    if log is not None and x.args:
        log.append(f"{ind}- {x} vs {y}: same symbol {x.op}/{len(x.args)}, unify arguments in turn")
    for a, b in zip(x.args, y.args):
        theta = _unify(a, b, theta, log, depth + 1)
        if theta is None:
            return None
    return theta


def _unify_var(v: Var, x: Term, theta: dict, log, depth) -> Optional[dict]:
    ind = "  " * depth
    if v in theta:
        return _unify(theta[v], x, theta, log, depth)
    if isinstance(x, Var) and x in theta:
        return _unify(v, theta[x], theta, log, depth)
    if _occurs(v, x, theta):
        if log is not None:
            log.append(f"{ind}- {v} occurs inside {subst(theta, x)} → **fail** (occur check)")
        return None
    if log is not None:
        log.append(f"{ind}- bind **{v}/{subst(theta, x)}**")
    return {**theta, v: x}


def _theta_str(theta: dict) -> str:
    if not theta:
        return "{}"
    return "{" + ", ".join(f"{k}/{subst(theta, v)}" for k, v in sorted(theta.items(), key=lambda kv: kv[0].name)) + "}"


def unify(x: str, y: str) -> dict[str, Any]:
    """Most general unifier of two terms or atoms, with each step."""
    tx, ty = parse_term(x), parse_term(y)
    log: list[str] = []
    theta = _unify(tx, ty, {}, log)
    md = ["## Unification", "", f"`{tx}` and `{ty}`", ""]
    if theta is None:
        md.insert(1, "**Answer:** they do not unify.\n")
    else:
        result = subst(theta, tx)
        md.insert(1, f"**Answer:** MGU θ = {_theta_str(theta)}; both become `{result}`.\n")
        check = subst(theta, tx) == subst(theta, ty)
        md += log + ["", f"Check: SUBST(θ, first) = `{subst(theta, tx)}`, SUBST(θ, second) = `{subst(theta, ty)}` "
                     f"→ {'identical ✓' if check else 'different ✗'}"]
        return {"unifier": {str(k): str(subst(theta, v)) for k, v in theta.items()}, "markdown": "\n".join(md)}
    md += log
    return {"unifier": None, "markdown": "\n".join(md)}


# ---------------------------------------------------------------------------
# Definite-clause knowledge bases
# ---------------------------------------------------------------------------

def _split_conj(s: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if depth == 0 and ch in "&∧^":
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def parse_rule(s: str) -> tuple[list[Term], Term]:
    s = s.replace("⇒", "=>").replace("->", "=>")
    if "=>" in s:
        lhs, rhs = s.split("=>", 1)
        return [parse_term(p) for p in _split_conj(lhs)], parse_term(rhs)
    return [], parse_term(s)


def _vars(t: Term) -> set[Var]:
    if isinstance(t, Var):
        return {t}
    out: set[Var] = set()
    for a in t.args:
        out |= _vars(a)
    return out


def _rename(t: Term, mapping: dict[Var, Var]) -> Term:
    if isinstance(t, Var):
        return mapping.get(t, t)
    return Compound(t.op, tuple(_rename(a, mapping) for a in t.args))


def forward_chaining(kb: list[str], query: str) -> dict[str, Any]:
    """FOL-FC-ASK (AIMA Fig 9.3): fire every rule whose premises unify with known facts, round by round."""
    parsed = [parse_rule(r) for r in kb]
    facts: list[Term] = [c for p, c in parsed if not p]
    rules = [(p, c, r) for (p, c), r in zip(parsed, kb) if p]
    q = parse_term(query)
    md = ["## First-order forward chaining", ""]
    rounds = []
    answer: Optional[dict] = None
    for rnd in itertools.count(1):
        new: list[Term] = []
        fired = []
        for prem, concl, txt in rules:
            for theta in _match_all(prem, facts, {}):
                q2 = subst(theta, concl)
                if q2 not in facts and q2 not in new:
                    new.append(q2)
                    fired.append(f"- `{txt}` with θ = {_theta_str(theta)} ⇒ **{q2}**")
                    phi = _unify(q2, q, {}, None)
                    if phi is not None and answer is None:
                        answer = phi
        rounds.append((rnd, fired))
        facts.extend(new)
        if answer is not None or not new:
            break
        if rnd > 50:
            break
    for rnd, fired in rounds:
        md.append(f"### Round {rnd}")
        md += fired or ["- nothing new can be inferred (fixed point)"]
        md.append("")
    if answer is not None:
        md.insert(1, f"**Answer:** proved `{subst(answer, q)}`" + (f" with θ = {_theta_str(answer)}" if answer else "") + ".\n")
    else:
        md.insert(1, f"**Answer:** `{q}` cannot be derived (no new facts after round {len(rounds)}).\n")
    md.append(f"Facts known at the end: {', '.join(str(f) for f in facts)}")
    return {"proved": answer is not None, "facts": [str(f) for f in facts], "rounds": len(rounds),
            "markdown": "\n".join(md)}


def _match_all(premises: list[Term], facts: list[Term], theta: dict) -> Iterator[dict]:
    if not premises:
        yield theta
        return
    first, rest = premises[0], premises[1:]
    for f in facts:
        t2 = _unify(subst(theta, first), f, dict(theta), None)
        if t2 is not None:
            yield from _match_all(rest, facts, t2)


def backward_chaining(kb: list[str], query: str, max_depth: int = 20) -> dict[str, Any]:
    """FOL-BC-ASK (AIMA Fig 9.6): depth-first, rules tried in order, variables renamed apart for each use."""
    parsed = [parse_rule(r) for r in kb]
    q = parse_term(query)
    counter = itertools.count(1)
    lines: list[str] = []

    def standardize(prem, concl):
        n = next(counter)
        mapping = {v: Var(f"{v.name}{n}") for t in prem + [concl] for v in _vars(t)}
        return [_rename(p, mapping) for p in prem], _rename(concl, mapping)

    def or_(goal: Term, theta: dict, depth: int) -> Iterator[dict]:
        g = subst(theta, goal)
        ind = "  " * depth
        if depth > max_depth:
            lines.append(f"{ind}- {g}: depth limit reached ✗")
            return
        lines.append(f"{ind}- goal **{g}**")
        for (prem, concl), txt in zip(parsed, kb):
            prem2, concl2 = standardize(prem, concl)
            t2 = _unify(concl2, g, dict(theta), None)
            if t2 is None:
                continue
            lines.append(f"{ind}  - matches `{txt}`" + (f", subgoals {', '.join(str(subst(t2, p)) for p in prem2)}" if prem2 else " (fact) ✓"))
            yield from and_(prem2, t2, depth + 2)

    def and_(goals: list[Term], theta: dict, depth: int) -> Iterator[dict]:
        if not goals:
            yield theta
            return
        for t1 in or_(goals[0], theta, depth):
            yield from and_(goals[1:], t1, depth)

    result = next(or_(q, {}, 0), None)
    md = ["## First-order backward chaining", ""]
    if result is not None:
        shown = {v: subst(result, v) for v in _vars(q)}
        md.append(f"**Answer:** proved `{subst(result, q)}`" + (f" with {_theta_str(shown)}" if shown else "") + ".")
    else:
        md.append(f"**Answer:** `{q}` cannot be proved.")
    md += ["", *lines, "", "Rules are tried in the order given, subgoals left to right, and each rule's variables are "
           "renamed apart (x → x1, x2, …) every time it is used."]
    return {"proved": result is not None, "markdown": "\n".join(md)}
