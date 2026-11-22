"""Truth tables and model counting for propositional formulas (Russell & Norvig, AIMA §7.4).

A formula is a small tree built with Sym, Not, And, Or, Imp and Iff. With n symbols there are 2**n models
(rows); a formula is valid if it is true in all of them, satisfiable if true in at least one.
"""
from itertools import product


def Sym(name): return ("sym", name)
def Not(a): return ("not", a)
def And(a, b): return ("and", a, b)
def Or(a, b): return ("or", a, b)
def Imp(a, b): return ("imp", a, b)
def Iff(a, b): return ("iff", a, b)
TRUE, FALSE = ("const", True), ("const", False)


# --- inputs ---
FORMULAS = [And(Imp(Sym("A"), Sym("B")), Sym("A")), Or(Sym("A"), Not(Sym("A"))), And(Sym("A"), Not(Sym("A")))]
EXTRA_SYMBOLS = []   # symbols in the problem that don't appear in the formulas
# --- end inputs ---


def evaluate(f, model):
    kind = f[0]
    if kind == "sym":
        return model[f[1]]
    if kind == "const":
        return f[1]
    if kind == "not":
        return not evaluate(f[1], model)
    a, b = evaluate(f[1], model), evaluate(f[2], model)
    return {"and": a and b, "or": a or b, "imp": (not a) or b, "iff": a == b}[kind]


def symbols(f, found):
    if f[0] == "sym":
        found.add(f[1])
    elif f[0] != "const":
        for part in f[1:]:
            symbols(part, found)
    return found


def show(f):
    kind = f[0]
    if kind == "sym":
        return f[1]
    if kind == "const":
        return str(f[1])
    if kind == "not":
        return "~" + show(f[1])
    op = {"and": " & ", "or": " | ", "imp": " => ", "iff": " <=> "}[kind]
    return "(" + show(f[1]) + op + show(f[2]) + ")"


def main():
    syms = set(EXTRA_SYMBOLS)
    for f in FORMULAS:
        symbols(f, syms)
    syms = sorted(syms)
    counts = [0] * len(FORMULAS)
    print(" ".join(syms) + " | " + " | ".join(show(f) for f in FORMULAS))
    for values in product([False, True], repeat=len(syms)):      # first row all false, last all true
        model = dict(zip(syms, values))
        results = [evaluate(f, model) for f in FORMULAS]
        for i, r in enumerate(results):
            counts[i] += r
        print(" ".join("T" if model[s] else "F" for s in syms) + " | " + " | ".join("T" if r else "F" for r in results))
    total = 2 ** len(syms)
    print("Answer: " + ", ".join(f"{c}/{total}" for c in counts))


if __name__ == "__main__":
    main()
