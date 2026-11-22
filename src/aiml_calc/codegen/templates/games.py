"""Minimax, alpha-beta pruning and expectiminimax on an explicit game tree
(Russell & Norvig, AIMA §5.2–5.3, §5.5).

MAX picks the child with the highest value, MIN the lowest, and a chance node the probability-weighted
average. Alpha-beta returns the same value as minimax while skipping branches that can't change the decision:
alpha is the best value MAX can already guarantee, beta the best (lowest) MIN can.
"""
import math
import re

# --- inputs ---
ROOT = "A"
CHILDREN = {"A": ["B", "C", "D"], "B": ["E", "F", "G"], "C": ["H", "I", "J"], "D": ["K", "L", "M"]}
VALUES = {"E": 3, "F": 12, "G": 8, "H": 2, "I": 4, "J": 6, "K": 14, "L": 5, "M": 2}   # leaf utilities for MAX
TYPES = {"A": "max", "B": "min", "C": "min", "D": "min"}                              # max, min or chance
PROBABILITIES = {}                                                                    # chance node -> child probabilities
USE_ALPHA_BETA = True
# --- end inputs ---


def minimax(node):
    kind = TYPES.get(node, "leaf")
    if kind == "leaf":
        return VALUES[node]
    values = [minimax(c) for c in CHILDREN[node]]
    if kind == "max":
        return max(values)
    if kind == "min":
        return min(values)
    probs = PROBABILITIES.get(node) or [1 / len(values)] * len(values)
    return sum(p * v for p, v in zip(probs, values))


def subtree(node):
    return [node] + [n for c in CHILDREN.get(node, []) for n in subtree(c)]


def alphabeta(node, alpha, beta, pruned, depth=0):
    kind = TYPES.get(node, "leaf")
    pad = "  " * depth
    if kind == "leaf":
        return VALUES[node]
    v = -math.inf if kind == "max" else math.inf
    kids = CHILDREN[node]
    for i, child in enumerate(kids):
        cv = alphabeta(child, alpha, beta, pruned, depth + 1)
        if kind == "max":
            v = max(v, cv)
            if v >= beta:                       # MIN above will never let play reach here
                skipped = kids[i + 1:]
                if skipped:
                    print(f"{pad}{node}: v = {fmt(v)} >= beta = {fmt(beta)}, prune {' '.join(skipped)}")
                pruned.extend(n for s in skipped for n in subtree(s))
                return v
            alpha = max(alpha, v)
        else:
            v = min(v, cv)
            if v <= alpha:                      # MAX above already has something better
                skipped = kids[i + 1:]
                if skipped:
                    print(f"{pad}{node}: v = {fmt(v)} <= alpha = {fmt(alpha)}, prune {' '.join(skipped)}")
                pruned.extend(n for s in skipped for n in subtree(s))
                return v
            beta = min(beta, v)
    return v


def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def fmt(x):
    if math.isinf(x):
        return "inf" if x > 0 else "-inf"
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")


def main():
    value = minimax(ROOT)
    for child in CHILDREN[ROOT]:
        print(f"{child}: {fmt(minimax(child))}")
    best = next((c for c in CHILDREN[ROOT] if abs(minimax(c) - value) < 1e-12), None) \
        if TYPES.get(ROOT) != "chance" else None
    answer = f"value {fmt(value)}" + (f", best move {best}" if best else "")
    if USE_ALPHA_BETA and "chance" not in TYPES.values():
        pruned = []
        ab = alphabeta(ROOT, -math.inf, math.inf, pruned)
        assert abs(ab - value) < 1e-12, "alpha-beta must agree with minimax"
        answer += ", pruned " + (" ".join(sorted(set(pruned), key=natural_key)) or "nothing")
    print("Answer: " + answer)


if __name__ == "__main__":
    main()
