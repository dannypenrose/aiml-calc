"""Unification: the most general substitution that makes two first-order expressions identical
(Russell & Norvig, AIMA §9.2.2, Fig 9.1).

Var("x") is a variable; Fn("Knows", Fn("John"), Var("x")) is a predicate, function or constant applied to
arguments (a constant is Fn with no arguments).
"""


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
X = Fn("Knows", Fn("John"), Var("x"))
Y = Fn("Knows", Var("y"), Fn("Mother", Var("y")))
# --- end inputs ---


def substitute(theta, t):
    if isinstance(t, Var):
        return substitute(theta, theta[t]) if t in theta else t
    return Fn(t.op, *(substitute(theta, a) for a in t.args))


def occurs(v, t, theta):
    """Occur check: does variable v appear inside t (after applying theta)?"""
    if v == t:
        return True
    if isinstance(t, Var) and t in theta:
        return occurs(v, theta[t], theta)
    return isinstance(t, Fn) and any(occurs(v, a, theta) for a in t.args)


def unify(x, y, theta, depth=0):
    pad = "  " * depth
    if theta is None:
        return None
    if x == y:
        return theta
    if isinstance(x, Var):
        return unify_var(x, y, theta, depth)
    if isinstance(y, Var):
        return unify_var(y, x, theta, depth)
    if x.op != y.op or len(x.args) != len(y.args):
        print(f"{pad}{x} vs {y}: different symbols or arity, fail")
        return None
    print(f"{pad}{x} vs {y}: unify the arguments in turn")
    for a, b in zip(x.args, y.args):
        theta = unify(a, b, theta, depth + 1)
        if theta is None:
            return None
    return theta


def unify_var(v, x, theta, depth):
    pad = "  " * depth
    if v in theta:
        return unify(theta[v], x, theta, depth)
    if isinstance(x, Var) and x in theta:
        return unify(v, theta[x], theta, depth)
    if occurs(v, x, theta):
        print(f"{pad}{v} occurs inside {substitute(theta, x)}: fail (occur check)")
        return None
    print(f"{pad}bind {v}/{substitute(theta, x)}")
    return {**theta, v: x}


def main():
    theta = unify(X, Y, {})
    if theta is None:
        print("Answer: no unifier")
    else:
        print(f"Both become {substitute(theta, X)}")
        print("Answer: " + ", ".join(f"{v}/{substitute(theta, t)}" for v, t in sorted(theta.items(), key=lambda kv: kv[0].name)))


if __name__ == "__main__":
    main()
