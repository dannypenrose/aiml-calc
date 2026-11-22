"""Inference from a full joint distribution (Russell & Norvig, AIMA §13.3).

Keep the rows that match the evidence, add them up separately for each value of the query variable
(marginalisation), then normalise so the two totals sum to 1.
"""

# --- inputs ---
VARIABLES = ["Toothache", "Catch", "Cavity"]
TABLE = [   # one row per combination of values, then its probability
    (True, True, True, 0.108), (True, False, True, 0.012), (False, True, True, 0.072), (False, False, True, 0.008),
    (True, True, False, 0.016), (True, False, False, 0.064), (False, True, False, 0.144), (False, False, False, 0.576),
]
QUERY = "Cavity"
EVIDENCE = {"Toothache": True}
# --- end inputs ---


def fmt(x):
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")


def main():
    index = {v: i for i, v in enumerate(VARIABLES)}
    totals = {True: 0.0, False: 0.0}
    for *values, prob in TABLE:
        if all(values[index[e]] == ev for e, ev in EVIDENCE.items()):
            totals[values[index[QUERY]]] += prob
            print(f"  matches evidence: {dict(zip(VARIABLES, values))} -> {prob}")
    z = totals[True] + totals[False]
    print(f"P({QUERY}=true, evidence) = {fmt(totals[True])}, P({QUERY}=false, evidence) = {fmt(totals[False])}")
    print(f"Answer: P({QUERY} | evidence) = <{fmt(totals[True] / z)}, {fmt(totals[False] / z)}>")


if __name__ == "__main__":
    main()
