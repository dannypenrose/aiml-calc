"""AC-3: make every arc X -> Y consistent by deleting values of X that have no support in Y
(Russell & Norvig, AIMA §6.2.2, Fig 6.3). When X loses a value, every arc Z -> X (Z != Y) is re-checked.
An empty domain proves there is no solution.
"""
import operator
import re

OPS = {"!=": operator.ne, "==": operator.eq, "<": operator.lt, ">": operator.gt, "<=": operator.le, ">=": operator.ge}
FLIP = {"!=": "!=", "==": "==", "<": ">", ">": "<", "<=": ">=", ">=": "<="}

# --- inputs ---
VARIABLES = ["X", "Y"]
DOMAINS = {"X": [1, 2, 3], "Y": [1, 2, 3]}
CONSTRAINTS = [("X", "<", "Y")]
# --- end inputs ---

arcs = {}
for a, op, b in CONSTRAINTS:
    arcs.setdefault((a, b), []).append(op)
    arcs.setdefault((b, a), []).append(FLIP[op])


def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def neighbours(x):
    return sorted({b for a, b in arcs if a == x}, key=natural_key)


def consistent(x, vx, y, vy):
    return all(OPS[op](vx, vy) for op in arcs.get((x, y), []))


def ac3():
    domains = {v: list(DOMAINS[v]) for v in VARIABLES}
    queue = sorted(arcs, key=lambda arc: (natural_key(arc[0]), natural_key(arc[1])))
    while queue:
        x, y = queue.pop(0)
        removed = [vx for vx in domains[x] if not any(consistent(x, vx, y, vy) for vy in domains[y])]
        if removed:
            domains[x] = [v for v in domains[x] if v not in removed]
            print(f"  {x} -> {y}: remove {removed}, {x} is now {domains[x]}")
            if not domains[x]:
                return None
            queue.extend((z, x) for z in neighbours(x) if z != y and (z, x) not in queue)
        else:
            print(f"  {x} -> {y}: nothing to remove")
    return domains


def main():
    domains = ac3()
    if domains is None:
        print("Answer: inconsistent (a domain became empty, so there is no solution)")
    else:
        print("Answer: arc consistent; " + "; ".join(f"{v}: {{{', '.join(map(str, domains[v]))}}}" for v in VARIABLES))


if __name__ == "__main__":
    main()
