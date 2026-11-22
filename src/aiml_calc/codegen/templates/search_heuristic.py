"""Check a search heuristic: is it admissible (never overestimates) and consistent (a triangle inequality
on every edge)? The true cost h*(n) comes from Dijkstra's algorithm run backwards from the goal.
(Russell & Norvig, AIMA §3.5–3.6.)
"""
import heapq

# --- inputs ---
DIRECTED = False
GOAL = "P"
EDGES = [("H", "L", 15), ("H", "T", 12), ("T", "M", 5), ("T", "Y", 6), ("L", "W", 9), ("L", "Y", 10),
         ("Y", "P", 11), ("M", "P", 10), ("M", "S", 7), ("M", "Y", 4), ("P", "W", 14)]
H = {"H": 20, "L": 17, "S": 19, "T": 12, "M": 10, "W": 12, "Y": 8, "P": 0}
# --- end inputs ---


def edges_both_ways():
    cost = {}
    for a, b, c in EDGES:
        for x, y in ([(a, b)] if DIRECTED else [(a, b), (b, a)]):
            cost[(x, y)] = min(c, cost.get((x, y), c))
    return cost


def true_costs(cost):
    """h*(n): cheapest real cost from n to the goal (Dijkstra on the reversed edges)."""
    reverse = {}
    for (x, y), c in cost.items():
        reverse.setdefault(y, []).append((x, c))
    dist = {GOAL: 0.0}
    queue = [(0.0, GOAL)]
    while queue:
        d, u = heapq.heappop(queue)
        if d > dist.get(u, float("inf")):
            continue
        for v, c in reverse.get(u, []):
            if d + c < dist.get(v, float("inf")):
                dist[v] = d + c
                heapq.heappush(queue, (d + c, v))
    return dist


def fmt(x):
    if x == float("inf"):
        return "inf"
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")


def main():
    cost = edges_both_ways()
    nodes = sorted({s for e in EDGES for s in e[:2]})
    h_star = true_costs(cost)

    print("Admissibility: h(n) <= h*(n)")
    admissible = True
    for n in nodes:
        ok = H.get(n, 0) <= h_star.get(n, float("inf"))
        admissible &= ok
        print(f"  {n}: h = {fmt(H.get(n, 0))}, h* = {fmt(h_star.get(n, float('inf')))}  {'ok' if ok else 'OVERESTIMATES'}")

    print("Consistency: h(n) <= c(n, n') + h(n')")
    consistent = True
    for (x, y), c in sorted(cost.items()):
        ok = H.get(x, 0) <= c + H.get(y, 0)
        consistent &= ok
        if not ok:
            print(f"  {x} -> {y}: {fmt(H.get(x, 0))} > {fmt(c)} + {fmt(H.get(y, 0))}  FAILS")

    print(f"Answer: admissible {'yes' if admissible else 'no'}, consistent {'yes' if consistent else 'no'}")


if __name__ == "__main__":
    main()
