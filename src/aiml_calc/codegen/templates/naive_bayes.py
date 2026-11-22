"""Naive Bayes classification (Russell & Norvig, AIMA §20.2.2; Witten et al. §4.2).

Assume the attributes are independent given the class, so
    score(c) = P(c) x P(x1 | c) x P(x2 | c) x ...
Every probability is a count from the training data. Laplace smoothing adds K to every count so an unseen
value doesn't make a score exactly zero.
"""
from collections import Counter

# --- inputs ---
ATTRIBUTES = ["Outlook", "Temp", "Humidity", "Windy"]
DATA = [   # attribute values, then the class
    ("Sunny", "Hot", "High", "F", "no"), ("Sunny", "Hot", "High", "T", "no"), ("Overcast", "Hot", "High", "F", "yes"),
    ("Rainy", "Mild", "High", "F", "yes"), ("Rainy", "Cool", "Normal", "F", "yes"), ("Rainy", "Cool", "Normal", "T", "no"),
    ("Overcast", "Cool", "Normal", "T", "yes"), ("Sunny", "Mild", "High", "F", "no"), ("Sunny", "Cool", "Normal", "F", "yes"),
    ("Rainy", "Mild", "Normal", "F", "yes"), ("Sunny", "Mild", "Normal", "T", "yes"), ("Overcast", "Mild", "High", "T", "yes"),
    ("Overcast", "Hot", "Normal", "F", "yes"), ("Rainy", "Mild", "High", "T", "no"),
]
QUERY = {"Outlook": "Sunny", "Temp": "Cool", "Humidity": "High", "Windy": "T"}
K = 0.0     # Laplace smoothing (0 = raw counts)
# --- end inputs ---


def fmt(x):
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")


def main():
    classes = Counter(row[-1] for row in DATA)
    distinct = {a: {row[i] for row in DATA} | ({QUERY[a]} if a in QUERY else set()) for i, a in enumerate(ATTRIBUTES)}
    scores = {}
    for c in sorted(classes):
        score = classes[c] / len(DATA)
        parts = [f"P({c}) = {classes[c]}/{len(DATA)}"]
        for attr, value in QUERY.items():
            i = ATTRIBUTES.index(attr)
            count = sum(1 for row in DATA if row[-1] == c and row[i] == value)
            num, den = count + K, classes[c] + K * len(distinct[attr])
            score *= num / den
            parts.append(f"P({attr}={value} | {c}) = {fmt(num)}/{fmt(den)}")
        scores[c] = score
        print(f"{c}: " + " x ".join(parts) + f" = {score:.6f}")
    total = sum(scores.values())
    best = max(scores, key=scores.get)
    print(f"Answer: {best} (P = {fmt(scores[best] / total) if total else '0'})")


if __name__ == "__main__":
    main()
