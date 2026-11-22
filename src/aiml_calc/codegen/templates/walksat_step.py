"""One step of WalkSAT, a local-search SAT solver (Russell & Norvig, AIMA §7.6.2, Fig 7.18).

Pick a clause that is false in the current model. With probability P flip a random symbol from it;
otherwise flip the symbol that makes the most clauses true (the greedy move). This program shows what
every possible flip would do, and which models one step can reach.
"""

# --- inputs ---
CLAUSES = [["A", "B"], ["A", "-B"], ["A", "B", "-C"]]     # "-X" means not X
MODEL = {"A": False, "B": False, "C": True}
P = 0.0              # probability of a random-walk move
CLAUSE_INDEX = 3     # the false clause WalkSAT picks (numbered from 1); 0 = consider every false clause
# --- end inputs ---

clauses = [[(s.lstrip("-"), not s.startswith("-")) for s in c] for c in CLAUSES]


def satisfied(clause, model):
    return any(model[sym] == positive for sym, positive in clause)


def count_satisfied(model):
    return sum(satisfied(c, model) for c in clauses)


def main():
    false_clauses = [i for i, c in enumerate(clauses) if not satisfied(c, MODEL)]
    if not false_clauses:
        print("Answer: every clause is already satisfied")
        return
    print("False clauses: " + ", ".join(str(i + 1) for i in false_clauses))
    candidates = [CLAUSE_INDEX - 1] if CLAUSE_INDEX else false_clauses
    reachable = {}
    for ci in candidates:
        print(f"If WalkSAT picks clause {ci + 1}:")
        scores = {}
        for sym in sorted({s for s, _ in clauses[ci]}):
            flipped = {**MODEL, sym: not MODEL[sym]}
            scores[sym] = count_satisfied(flipped)
            print(f"  flip {sym}: {scores[sym]} of {len(clauses)} clauses satisfied")
        best = max(scores.values())
        greedy = [s for s, v in scores.items() if v == best]
        print(f"  greedy choice: {', '.join(greedy)}")
        if P < 1:
            for s in greedy:
                reachable.setdefault(s, set()).add("greedy")
        if P > 0:
            for s in scores:
                reachable.setdefault(s, set()).add("random walk")
    parts = [f"flip {s} ({' and '.join(sorted(how))})" for s, how in sorted(reachable.items())]
    print("Answer: " + "; ".join(parts))


if __name__ == "__main__":
    main()
