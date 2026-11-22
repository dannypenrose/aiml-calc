"""Bayes' rule: update a prior belief with evidence (Russell & Norvig, AIMA §13.5).

    P(H | E) = P(E | H) P(H) / P(E),   where   P(E) = P(E | H) P(H) + P(E | not H) P(not H)

Checked a second way with natural frequencies: imagine 10,000 cases and count.
"""

# --- inputs ---
PRIOR = 0.01                 # P(H): belief before the evidence
LIKELIHOOD = 0.9             # P(E | H): how often the evidence appears when H is true
FALSE_POSITIVE_RATE = 0.05   # P(E | not H): how often it appears anyway
# --- end inputs ---


def fmt(x):
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")


def main():
    p_evidence = LIKELIHOOD * PRIOR + FALSE_POSITIVE_RATE * (1 - PRIOR)
    posterior = LIKELIHOOD * PRIOR / p_evidence
    print(f"Method 1: P(E) = {fmt(LIKELIHOOD)} x {fmt(PRIOR)} + {fmt(FALSE_POSITIVE_RATE)} x {fmt(1 - PRIOR)} = {fmt(p_evidence)}")
    print(f"          P(H | E) = {fmt(LIKELIHOOD * PRIOR)} / {fmt(p_evidence)} = {fmt(posterior)}")

    n = 10_000
    true_positives = LIKELIHOOD * PRIOR * n
    false_positives = FALSE_POSITIVE_RATE * (1 - PRIOR) * n
    by_counting = true_positives / (true_positives + false_positives)
    print(f"Method 2: of {n} cases, {fmt(true_positives)} true positives and {fmt(false_positives)} false positives,")
    print(f"          so {fmt(true_positives)} / {fmt(true_positives + false_positives)} = {fmt(by_counting)}")
    print(f"Answer: P(H | E) = {fmt(posterior)}")


if __name__ == "__main__":
    main()
