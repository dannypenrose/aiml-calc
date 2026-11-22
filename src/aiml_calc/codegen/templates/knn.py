"""k-nearest-neighbour classification (Witten et al. §4.7; AIMA §18.8.1).

Measure the distance from the query to every training example, take the K closest, and predict the majority
class among them (ties go to the class of the nearest neighbour). Optional min-max normalisation rescales
every attribute to [0, 1] so no attribute dominates because of its units.
"""
import math
from collections import Counter

# --- inputs ---
TRAIN = [((1, 1), "a"), ((2, 1.5), "a"), ((1.5, 2.5), "a"), ((6, 6), "b"), ((7, 5.5), "b"), ((6.5, 7), "b"), ((4, 4.5), "b")]
QUERY = (3.5, 3.5)
K = 3
NORMALISE = False
# --- end inputs ---


def fmt(x):
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")


def main():
    points = [list(p) for p, _ in TRAIN]
    labels = [label for _, label in TRAIN]
    query = list(QUERY)
    if NORMALISE:
        columns = list(zip(*points, query))
        lo, hi = [min(c) for c in columns], [max(c) for c in columns]
        scale = lambda v: [(x - a) / (b - a) if b > a else 0.0 for x, a, b in zip(v, lo, hi)]
        points, query = [scale(p) for p in points], scale(query)
    ranked = sorted((math.dist(p, query), i) for i, p in enumerate(points))
    for rank, (d, i) in enumerate(ranked[:K], 1):
        print(f"{rank}. {TRAIN[i][0]} class {labels[i]}, distance {fmt(d)}")
    votes = Counter(labels[i] for _, i in ranked[:K])
    best = max(votes.values())
    winners = [c for c, n in votes.items() if n == best]
    prediction = min(winners, key=lambda c: min(d for d, i in ranked[:K] if labels[i] == c))
    print(f"Answer: {prediction} (votes {dict(votes)})")


if __name__ == "__main__":
    main()
