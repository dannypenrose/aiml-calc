"""Backtracking search for constraint satisfaction problems (Russell & Norvig, AIMA §6.3, Fig 6.5).

Assign one variable at a time and back up as soon as a constraint can't be met. Three choices make it fast:
  which variable next: MRV (fewest values left), ties broken by degree (most constraints on open variables);
  which value first:   LCV (the value that rules out fewest options for the neighbours);
  what to infer:       forward checking (prune neighbours' domains) or MAC (full arc consistency with AC-3).
"""
import operator
import re

OPS = {"!=": operator.ne, "==": operator.eq, "<": operator.lt, ">": operator.gt, "<=": operator.le, ">=": operator.ge}
FLIP = {"!=": "!=", "==": "==", "<": ">", ">": "<", "<=": ">=", ">=": "<="}

# --- inputs ---
VARIABLES = ["WA", "NT", "Q", "NSW", "V", "SA", "T"]
DOMAINS = {v: ["red", "green", "blue"] for v in VARIABLES}
CONSTRAINTS = [("WA", "!=", "NT"), ("WA", "!=", "SA"), ("NT", "!=", "SA"), ("NT", "!=", "Q"), ("SA", "!=", "Q"),
               ("SA", "!=", "NSW"), ("SA", "!=", "V"), ("Q", "!=", "NSW"), ("NSW", "!=", "V")]
VARIABLE_ORDER = "mrv"            # "mrv" or "static" (as listed)
VALUE_ORDER = "lcv"               # "lcv" or "static"
INFERENCE = "forward_checking"    # "none", "forward_checking" or "mac"
# --- end inputs ---

arcs = {}                         # (X, Y) -> list of operators that must hold between X's and Y's values
for a, op, b in CONSTRAINTS:
    arcs.setdefault((a, b), []).append(op)
    arcs.setdefault((b, a), []).append(FLIP[op])
stats = {"assignments": 0, "backtracks": 0}


def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def neighbours(x):
    return sorted({b for a, b in arcs if a == x}, key=natural_key)


def consistent(x, vx, y, vy):
    return all(OPS[op](vx, vy) for op in arcs.get((x, y), []))


def select_variable(assignment, domains):
    unassigned = [v for v in VARIABLES if v not in assignment]
    if VARIABLE_ORDER == "static":
        return unassigned[0]
    def degree(v):
        return sum(1 for n in neighbours(v) if n not in assignment)
    return min(unassigned, key=lambda v: (len(domains[v]), -degree(v), VARIABLES.index(v)))


def order_values(var, assignment, domains):
    values = list(domains[var])
    if VALUE_ORDER != "lcv":
        return values
    def ruled_out(val):
        return sum(1 for n in neighbours(var) if n not in assignment for vn in domains[n] if not consistent(var, val, n, vn))
    return sorted(values, key=lambda v: (ruled_out(v), values.index(v)))


def infer(var, val, assignment, domains):
    """New domains after assigning var = val, or None if some domain is wiped out."""
    d = {k: list(v) for k, v in domains.items()}
    d[var] = [val]
    if INFERENCE == "forward_checking":
        for n in neighbours(var):
            if n not in assignment:
                d[n] = [vn for vn in d[n] if consistent(var, val, n, vn)]
                if not d[n]:
                    return None
    elif INFERENCE == "mac":
        queue = [(n, var) for n in neighbours(var) if n not in assignment]
        while queue:
            x, y = queue.pop(0)
            removed = [vx for vx in d[x] if not any(consistent(x, vx, y, vy) for vy in d[y])]
            if removed:
                d[x] = [v for v in d[x] if v not in removed]
                if not d[x]:
                    return None
                queue.extend((z, x) for z in neighbours(x) if z != y)
    return d


def backtrack(assignment, domains, depth=0):
    if len(assignment) == len(VARIABLES):
        return assignment
    var = select_variable(assignment, domains)
    for val in order_values(var, assignment, domains):
        if not all(consistent(var, val, other, assignment[other]) for other in assignment if (var, other) in arcs):
            continue
        stats["assignments"] += 1
        print("  " * depth + f"{var} = {val}")
        new_domains = infer(var, val, assignment, domains)
        if new_domains is None:
            print("  " * depth + "  a domain was wiped out")
            continue
        result = backtrack({**assignment, var: val}, new_domains, depth + 1)
        if result is not None:
            return result
        stats["backtracks"] += 1
    return None


def main():
    solution = backtrack({}, {v: list(DOMAINS[v]) for v in VARIABLES})
    counts = f"({stats['assignments']} assignments, {stats['backtracks']} backtracks)"
    if solution is None:
        print(f"Answer: no solution {counts}")
    else:
        print("Answer: " + ", ".join(f"{v}={solution[v]}" for v in VARIABLES) + " " + counts)


if __name__ == "__main__":
    main()
