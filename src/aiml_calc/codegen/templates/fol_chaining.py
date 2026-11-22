"""First-order forward and backward chaining over definite clauses (Russell & Norvig, AIMA §9.3–9.4).

A rule is (premises, conclusion), e.g. ([Missile(x)], Weapon(x)): "for every x, if x is a missile then x is
a weapon". A fact is a rule with no premises.
  forward chaining (FOL-FC-ASK): each round, fire every rule whose premises all unify with known facts;
  backward chaining (FOL-BC-ASK): prove the query by proving the premises of a rule that concludes it,
  renaming the rule's variables apart each time it is used.
"""
import itertools


class Var:
    def __init__(self, name): self.name = name
    def __eq__(self, other): return isinstance(other, Var) and other.name == self.name
    def __hash__(self): return hash(("var", self.name))
    def __repr__(self): return self.name


class Fn:
    def __init__(self, op, *args): self.op, self.args = op, args
    def __eq__(self, other): return isinstance(other, Fn) and (other.op, other.args) == (self.op, self.args)
    def __hash__(self): return hash((self.op, self.args))
    def __repr__(self): return self.op + (f"({', '.join(map(repr, self.args))})" if self.args else "")


# --- inputs ---
KB = [
    ([Fn("American", Var("x")), Fn("Weapon", Var("y")), Fn("Sells", Var("x"), Var("y"), Var("z")), Fn("Hostile", Var("z"))], Fn("Criminal", Var("x"))),
    ([], Fn("Owns", Fn("Nono"), Fn("M1"))),
    ([], Fn("Missile", Fn("M1"))),
    ([Fn("Missile", Var("x")), Fn("Owns", Fn("Nono"), Var("x"))], Fn("Sells", Fn("West"), Var("x"), Fn("Nono"))),
    ([Fn("Missile", Var("x"))], Fn("Weapon", Var("x"))),
    ([Fn("Enemy", Var("x"), Fn("America"))], Fn("Hostile", Var("x"))),
    ([], Fn("American", Fn("West"))),
    ([], Fn("Enemy", Fn("Nono"), Fn("America"))),
]
QUERY = Fn("Criminal", Fn("West"))
# --- end inputs ---


def substitute(theta, t):
    if isinstance(t, Var):
        return substitute(theta, theta[t]) if t in theta else t
    return Fn(t.op, *(substitute(theta, a) for a in t.args))


def occurs(v, t, theta):
    if v == t:
        return True
    if isinstance(t, Var) and t in theta:
        return occurs(v, theta[t], theta)
    return isinstance(t, Fn) and any(occurs(v, a, theta) for a in t.args)


def unify(a, b, theta):
    if theta is None:
        return None
    if a == b:
        return theta
    if isinstance(a, Var):
        return unify_var(a, b, theta)
    if isinstance(b, Var):
        return unify_var(b, a, theta)
    if a.op != b.op or len(a.args) != len(b.args):
        return None
    for p, q in zip(a.args, b.args):
        theta = unify(p, q, theta)
    return theta


def unify_var(v, t, theta):
    if v in theta:
        return unify(theta[v], t, theta)
    if isinstance(t, Var) and t in theta:
        return unify(v, theta[t], theta)
    return None if occurs(v, t, theta) else {**theta, v: t}


def variables(t):
    return {t} if isinstance(t, Var) else set().union(*(variables(a) for a in t.args)) if t.args else set()


def rename(t, mapping):
    return mapping.get(t, t) if isinstance(t, Var) else Fn(t.op, *(rename(a, mapping) for a in t.args))


# ---------------------------------------------------------------- forward chaining

def match_all(premises, facts, theta):
    """Every substitution that makes all premises equal to known facts."""
    if not premises:
        yield theta
        return
    for fact in facts:
        t = unify(substitute(theta, premises[0]), fact, dict(theta))
        if t is not None:
            yield from match_all(premises[1:], facts, t)


def forward_chaining():
    facts = [c for p, c in KB if not p]
    rules = [(p, c) for p, c in KB if p]
    for round_number in itertools.count(1):
        new = []
        for premises, conclusion in rules:
            for theta in match_all(premises, facts, {}):
                fact = substitute(theta, conclusion)
                if fact not in facts and fact not in new:
                    print(f"  round {round_number}: {fact}")
                    new.append(fact)
                    if unify(fact, QUERY, {}) is not None:
                        return True, round_number
        facts.extend(new)
        if not new:
            return False, round_number


# ---------------------------------------------------------------- backward chaining

counter = itertools.count(1)


def prove(goal, theta, depth=0):
    """Yield every substitution that proves goal (depth-first, rules in order)."""
    if depth > 20:
        return
    goal = substitute(theta, goal)
    print("  " * (depth + 1) + f"goal {goal}")
    for premises, conclusion in KB:
        n = next(counter)                    # standardise apart: x becomes x1, x2, ...
        mapping = {v: Var(f"{v.name}{n}") for t in premises + [conclusion] for v in variables(t)}
        premises = [rename(p, mapping) for p in premises]
        t = unify(rename(conclusion, mapping), goal, dict(theta))
        if t is not None:
            yield from prove_all(premises, t, depth + 1)


def prove_all(goals, theta, depth):
    if not goals:
        yield theta
        return
    for t in prove(goals[0], theta, depth):
        yield from prove_all(goals[1:], t, depth)


def main():
    print("Forward chaining")
    fc, rounds = forward_chaining()
    print("Backward chaining")
    bc = next(prove(QUERY, {}), None)
    if bc is not None:
        print(f"  proved {substitute(bc, QUERY)}")
    print(f"Answer: forward chaining {'yes' if fc else 'no'} ({rounds} round{'s' if rounds != 1 else ''}), "
          f"backward chaining {'yes' if bc is not None else 'no'}")


if __name__ == "__main__":
    main()
