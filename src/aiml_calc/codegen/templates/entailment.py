"""Does a knowledge base entail a query (KB |= query)? Two independent methods
(Russell & Norvig, AIMA §7.4–7.5):
  1. model checking: the query must be true in every model where the whole KB is true;
  2. resolution: KB & ~query must be unsatisfiable, shown by deriving the empty clause.
"""
from itertools import combinations, product


def Sym(name): return ("sym", name)
def Not(a): return ("not", a)
def And(a, b): return ("and", a, b)
def Or(a, b): return ("or", a, b)
def Imp(a, b): return ("imp", a, b)
def Iff(a, b): return ("iff", a, b)
TRUE, FALSE = ("const", True), ("const", False)


# --- inputs ---
KB = [Imp(Sym("A"), Sym("B")), Sym("A")]
QUERY = Sym("B")
# Clauses of KB & ~QUERY in CNF (see the CNF view), as lists of literals; "-X" means not X.
CLAUSES = [["-A", "B"], ["A"], ["-B"]]
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


def model_checking():
    """TT-ENTAILS: look for a model where every KB sentence is true but the query is false."""
    syms = set()
    for f in KB + [QUERY]:
        symbols(f, syms)
    syms = sorted(syms)
    kb_models = 0
    for values in product([False, True], repeat=len(syms)):
        model = dict(zip(syms, values))
        if all(evaluate(f, model) for f in KB):
            kb_models += 1
            if not evaluate(QUERY, model):
                print("  counter-example: " + ", ".join(f"{s}={'T' if model[s] else 'F'}" for s in syms))
                return False
    print(f"  the query is true in all {kb_models} models of the KB")
    return True


def resolution():
    """PL-RESOLUTION: resolve pairs of clauses until the empty clause appears or nothing new can be made."""
    def lit(s):
        return (s.lstrip("-"), not s.startswith("-"))

    clauses = [frozenset(lit(x) for x in c) for c in CLAUSES]
    seen = set(clauses)
    while True:
        new = []
        for ci, cj in combinations(clauses, 2):
            for sym, positive in ci:
                if (sym, not positive) in cj:
                    resolvent = (ci - {(sym, positive)}) | (cj - {(sym, not positive)})
                    if any((s, not v) in resolvent for s, v in resolvent) or resolvent in seen:
                        continue                       # skip always-true and already-known clauses
                    seen.add(resolvent)
                    new.append(resolvent)
                    shown = " | ".join(("" if v else "~") + s for s, v in sorted(resolvent)) or "EMPTY"
                    print(f"  resolve on {sym}: {shown}")
                    if not resolvent:
                        return True
        if not new:
            return False
        clauses.extend(new)


def main():
    print("Method 1: model checking")
    by_models = model_checking()
    print("Method 2: resolution on KB & ~query")
    by_resolution = resolution()
    print(f"Answer: KB entails query: {'yes' if by_models else 'no'} "
          f"(model checking {'yes' if by_models else 'no'}, resolution {'yes' if by_resolution else 'no'})")


if __name__ == "__main__":
    main()
