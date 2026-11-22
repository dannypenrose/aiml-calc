"""k-means clustering (Lloyd's algorithm; Witten et al. §4.8).

Repeat: assign every point to its nearest centre, then move each centre to the mean of its points.
Stops early when the centres stop moving. Ties go to the first centre.
"""
import math

# --- inputs ---
POINTS = [(1, 1), (1.5, 2), (3, 4), (5, 7), (3.5, 5), (4.5, 5), (3.5, 4.5)]
CENTRES = [(1, 1), (5, 7)]
METRIC = "euclidean"     # "euclidean" or "manhattan"
ITERATIONS = 1
# --- end inputs ---


def distance(a, b):
    if METRIC == "manhattan":
        return sum(abs(x - y) for x, y in zip(a, b))
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def fmt(x):
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")


def main():
    centres = [list(c) for c in CENTRES]
    for iteration in range(1, ITERATIONS + 1):
        # assign each point to its nearest centre
        clusters = [[] for _ in centres]
        for p in POINTS:
            d = [distance(p, c) for c in centres]
            nearest = min(range(len(centres)), key=lambda i: (d[i], i))
            clusters[nearest].append(p)
        # move each centre to the mean of its points
        new = [[sum(col) / len(members) for col in zip(*members)] if members else c
               for c, members in zip(centres, clusters)]
        print(f"Iteration {iteration}: " + "; ".join(
            f"centre {chr(65 + i)} has {len(m)} points -> ({', '.join(fmt(v) for v in new[i])})" for i, m in enumerate(clusters)))
        moved = any(distance(a, b) > 1e-12 for a, b in zip(centres, new))
        centres = new
        if not moved:
            print("Centres did not move: converged")
            break
    print("Answer: " + ", ".join(f"{chr(65 + i)} = ({', '.join(fmt(v) for v in c)})" for i, c in enumerate(centres)))


if __name__ == "__main__":
    main()
