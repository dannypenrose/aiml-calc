"""WalkSAT, a local-search SAT solver (Russell & Norvig, AIMA §7.6.2, Fig 7.18).

Start from a random model and repeatedly pick a false clause and flip one of its symbols: with probability
P a random one, otherwise the one that makes the most clauses true. WalkSAT is incomplete: if it gives up,
the formula might still be satisfiable.
"""
import random

# --- inputs ---
CLAUSES = [["A", "B", "-C", "D"], ["-A", "B", "-C"], ["-B", "-C"], ["E"], ["E", "C"]]   # "-X" means not X
P = 0.5             # probability of a random-walk move
MAX_FLIPS = 100
SEED = 0            # the same seed gives the same run
# --- end inputs ---

clauses = [[(s.lstrip("-"), not s.startswith("-")) for s in c] for c in CLAUSES]
symbols = sorted({s for c in clauses for s, _ in c})


def satisfied(clause, model):
    return any(model[sym] == positive for sym, positive in clause)


def walksat():
    rng = random.Random(SEED)
    model = {s: rng.random() < 0.5 for s in symbols}            # random starting model
    for flip in range(1, MAX_FLIPS + 1):
        false_clauses = [i for i, c in enumerate(clauses) if not satisfied(c, model)]
        if not false_clauses:
            return model
        ci = rng.choice(false_clauses)
        if rng.random() < P:
            sym = rng.choice(sorted(s for s, _ in clauses[ci]))
            how = "random"
        else:
            best, sym = -1, None
            for s, _ in sorted(clauses[ci]):
                flipped = {**model, s: not model[s]}
                score = sum(satisfied(c, flipped) for c in clauses)
                if score > best:
                    best, sym = score, s
            how = "greedy"
        model[sym] = not model[sym]
        print(f"flip {flip}: clause {ci + 1}, {how}, flip {sym} -> "
              + " ".join(f"{s}={'T' if model[s] else 'F'}" for s in symbols))
    return model if all(satisfied(c, model) for c in clauses) else None


def main():
    model = walksat()
    if model is None:
        print("Answer: no model found within MAX_FLIPS (WalkSAT can't prove there is none)")
    else:
        print("Answer: solved, " + ", ".join(f"{s}={'true' if model[s] else 'false'}" for s in symbols))


if __name__ == "__main__":
    main()
