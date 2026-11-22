"""Convert a propositional formula to conjunctive normal form (an AND of ORs), one rewrite rule at a time
(Russell & Norvig, AIMA §7.5.2):
  1. eliminate <=>:  a <=> b  becomes  (a => b) & (b => a)
  2. eliminate =>:   a => b   becomes  ~a | b
  3. move ~ inwards (De Morgan's laws; ~~a becomes a)
  4. distribute | over &:  a | (b & c)  becomes  (a | b) & (a | c)
"""


def Sym(name): return ("sym", name)
def Not(a): return ("not", a)
def And(a, b): return ("and", a, b)
def Or(a, b): return ("or", a, b)
def Imp(a, b): return ("imp", a, b)
def Iff(a, b): return ("iff", a, b)
TRUE, FALSE = ("const", True), ("const", False)


# --- inputs ---
FORMULA = Imp(And(Sym("B"), Not(Sym("S"))), Sym("W"))
# --- end inputs ---


def eliminate_iff(f):
    if f[0] in ("sym", "const"):
        return f
    if f[0] == "not":
        return Not(eliminate_iff(f[1]))
    a, b = eliminate_iff(f[1]), eliminate_iff(f[2])
    return And(Imp(a, b), Imp(b, a)) if f[0] == "iff" else (f[0], a, b)


def eliminate_imp(f):
    if f[0] in ("sym", "const"):
        return f
    if f[0] == "not":
        return Not(eliminate_imp(f[1]))
    a, b = eliminate_imp(f[1]), eliminate_imp(f[2])
    return Or(Not(a), b) if f[0] == "imp" else (f[0], a, b)


def move_not_inwards(f):
    if f[0] in ("sym", "const"):
        return f
    if f[0] == "not":
        a = f[1]
        if a[0] == "not":                      # ~~a  ==  a
            return move_not_inwards(a[1])
        if a[0] == "and":                      # ~(a & b)  ==  ~a | ~b
            return Or(move_not_inwards(Not(a[1])), move_not_inwards(Not(a[2])))
        if a[0] == "or":                       # ~(a | b)  ==  ~a & ~b
            return And(move_not_inwards(Not(a[1])), move_not_inwards(Not(a[2])))
        if a[0] == "const":
            return ("const", not a[1])
        return f
    return (f[0], move_not_inwards(f[1]), move_not_inwards(f[2]))


def distribute(f):
    if f[0] in ("sym", "const", "not"):
        return f
    a, b = distribute(f[1]), distribute(f[2])
    if f[0] == "or":
        if a[0] == "and":                      # (x & y) | b  ==  (x | b) & (y | b)
            return distribute(And(Or(a[1], b), Or(a[2], b)))
        if b[0] == "and":                      # a | (x & y)  ==  (a | x) & (a | y)
            return distribute(And(Or(a, b[1]), Or(a, b[2])))
    return (f[0], a, b)


def flatten(f, op):
    return flatten(f[1], op) + flatten(f[2], op) if f[0] == op else [f]


def clauses_of(cnf):
    """List of clauses, each a list of (symbol, positive?) literals; always-true clauses are dropped."""
    out = []
    for conj in flatten(cnf, "and"):
        lits, tautology = [], False
        for d in flatten(conj, "or"):
            if d[0] == "const":
                tautology |= d[1]
                continue
            lit = (d[1], True) if d[0] == "sym" else (d[1][1], False)
            if lit not in lits:
                lits.append(lit)
        if tautology or any((s, not v) in lits for s, v in lits):
            continue
        if sorted(lits) not in [sorted(c) for c in out]:
            out.append(lits)
    return out


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


def appearance_order(f, order):
    """Symbols in the order they appear, used to print each clause like the input."""
    if f[0] == "sym":
        order.setdefault(f[1], len(order))
    elif f[0] != "const":
        for part in f[1:]:
            appearance_order(part, order)
    return order


def main():
    steps = [("start", FORMULA)]
    for name, rule in [("eliminate <=>", eliminate_iff), ("eliminate =>", eliminate_imp),
                       ("move ~ inwards", move_not_inwards), ("distribute | over &", distribute)]:
        steps.append((name, rule(steps[-1][1])))
    for name, f in steps:
        print(f"{name:>20}: {show(f)}")
    order = appearance_order(FORMULA, {})
    compact = []
    for clause in clauses_of(steps[-1][1]):
        clause.sort(key=lambda lit: (order.get(lit[0], 10**6), lit[0], not lit[1]))
        compact.append("v".join(("" if positive else "-") + s for s, positive in clause))
    print("Answer: " + (", ".join(compact) if compact else "(no clauses: the formula is valid)"))


if __name__ == "__main__":
    main()
