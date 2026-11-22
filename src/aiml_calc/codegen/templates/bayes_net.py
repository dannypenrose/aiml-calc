"""Exact inference in a Bayesian network by enumeration (Russell & Norvig, AIMA §14.4, Fig 14.9).

Each node has parents and a table P(node = true | parent values). The probability of a complete assignment is
the product of one table entry per node (the chain rule). To answer P(query | evidence), sum that product over
every value of the hidden variables, for query = true and for query = false, then normalise.
"""
from itertools import product
from math import prod

# --- inputs ---
NODES = ["Burglary", "Earthquake", "Alarm", "JohnCalls", "MaryCalls"]     # parents before children
PARENTS = {"Burglary": [], "Earthquake": [], "Alarm": ["Burglary", "Earthquake"],
           "JohnCalls": ["Alarm"], "MaryCalls": ["Alarm"]}
CPT = {   # P(node = true | parent values), keyed by the parents' values in order
    "Burglary": {(): 0.001},
    "Earthquake": {(): 0.002},
    "Alarm": {(True, True): 0.95, (True, False): 0.94, (False, True): 0.29, (False, False): 0.001},
    "JohnCalls": {(True,): 0.9, (False,): 0.05},
    "MaryCalls": {(True,): 0.7, (False,): 0.01},
}
QUERY = "Burglary"
EVIDENCE = {"JohnCalls": True, "MaryCalls": True}
# --- end inputs ---


def p(node, value, assignment):
    p_true = CPT[node][tuple(assignment[parent] for parent in PARENTS[node])]
    return p_true if value else 1 - p_true


def joint(assignment):
    """Chain rule: P(x1, ..., xn) = product of P(xi | parents(Xi))."""
    return prod(p(node, assignment[node], assignment) for node in NODES)


def fmt(x):
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")


def main():
    hidden = [n for n in NODES if n != QUERY and n not in EVIDENCE]
    totals = {}
    for q in (True, False):
        totals[q] = sum(joint({**EVIDENCE, QUERY: q, **dict(zip(hidden, values))})
                        for values in product([True, False], repeat=len(hidden)))
        print(f"sum over {hidden} with {QUERY} = {q}: {totals[q]:.6g}")
    alpha = 1 / (totals[True] + totals[False])
    print(f"Answer: P({QUERY} | evidence) = <{fmt(alpha * totals[True])}, {fmt(alpha * totals[False])}>")


if __name__ == "__main__":
    main()
