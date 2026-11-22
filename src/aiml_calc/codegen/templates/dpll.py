"""DPLL: a complete SAT solver (Russell & Norvig, AIMA §7.6.1, Fig 7.17).

Depth-first search over partial models with three improvements over trying every model:
  early termination - stop as soon as every clause is true, or any clause is false;
  pure symbols      - a symbol with only one sign in the clauses still open can be set to make it true;
  unit clauses      - a clause with one open literal (the rest false) forces that literal (unit propagation).
Only when none applies does it branch on the next symbol, trying true first.
"""

# --- inputs ---
CLAUSES = [["A", "B"], ["A", "-B", "C"], ["-A", "B"], ["-A", "-B", "C"], ["-B", "-C"]]   # "-X" means not X
SYMBOL_ORDER = ["A", "B", "C"]
USE_PURE_SYMBOLS = True
TRUE_FIRST = True
# --- end inputs ---

clauses = [frozenset((s.lstrip("-"), not s.startswith("-")) for s in c) for c in CLAUSES]
order = list(SYMBOL_ORDER) + sorted({s for c in clauses for s, _ in c} - set(SYMBOL_ORDER))
steps = [[]]      # each summary step runs from a branching decision to success or fail


def value(clause, model):
    """True if a literal is true, False if every literal is false, None if still undecided."""
    undecided = False
    for sym, positive in clause:
        if sym in model:
            if model[sym] == positive:
                return True
        else:
            undecided = True
    return None if undecided else False


def find_pure_symbol(model):
    signs = {}
    for c in clauses:
        if value(c, model) is True:
            continue
        for sym, positive in c:
            if sym not in model:
                signs.setdefault(sym, set()).add(positive)
    for sym in order:
        if sym in signs and len(signs[sym]) == 1:
            return sym, next(iter(signs[sym]))
    return None


def find_unit_clause(model):
    for i, c in enumerate(clauses):            # in clause order
        if value(c, model) is not None:
            continue
        open_literals = [(s, v) for s, v in c if s not in model]
        if len(open_literals) == 1:
            return i, open_literals[0]
    return None


def assign(sym, val, why, depth):
    steps[-1].append(f"{sym}={'true' if val else 'false'}")
    print("  " * depth + f"{why}: {sym} = {'true' if val else 'false'}")


def dpll(model, depth=0):
    values = [value(c, model) for c in clauses]
    if all(v is True for v in values):
        steps[-1].append("success")
        return model
    if any(v is False for v in values):
        steps[-1].append("fail")
        print("  " * depth + f"clause {values.index(False) + 1} is false: fail")
        return None
    if USE_PURE_SYMBOLS and (pure := find_pure_symbol(model)):
        assign(*pure, "pure symbol", depth)
        return dpll({**model, pure[0]: pure[1]}, depth)
    if unit := find_unit_clause(model):
        i, (sym, val) = unit
        assign(sym, val, f"unit clause {i + 1}", depth)
        return dpll({**model, sym: val}, depth)
    sym = next(s for s in order if s not in model)
    first = TRUE_FIRST
    assign(sym, first, "branch", depth)
    result = dpll({**model, sym: first}, depth + 1)
    if result is not None:
        return result
    steps.append([])                           # backtrack: a new summary step starts here
    assign(sym, not first, "backtrack", depth)
    return dpll({**model, sym: not first}, depth + 1)


def main():
    model = dpll({})
    for i, step in enumerate(s for s in steps if s):
        print(f"Step {i + 1}: {', '.join(step)}")
    if model is None:
        print("Answer: unsatisfiable")
    else:
        print("Answer: satisfiable, " + ", ".join(f"{s}={'true' if model[s] else 'false'}" for s in order if s in model))


if __name__ == "__main__":
    main()
