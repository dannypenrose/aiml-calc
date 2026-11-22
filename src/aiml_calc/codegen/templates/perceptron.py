"""The perceptron learning rule (Russell & Norvig, AIMA §18.6.3, Eq 18.7).

For each example, compute the threshold output h = 1 if w0 + w1 x1 + ... >= 0 else 0, then
    w_i <- w_i + ALPHA (y - h) x_i         (x0 = 1 for the bias)
Right answers change nothing. It converges if the data are linearly separable (XOR isn't).
"""

# --- inputs ---
EXAMPLES = [((0, 0), 0), ((0, 1), 0), ((1, 0), 0), ((1, 1), 1)]   # inputs, target: the AND function
WEIGHTS = [0.0, 0.0, 0.0]                                          # [w0 (bias), w1, w2]
ALPHA = 0.5
EPOCHS = 6
# --- end inputs ---


def fmt(x):
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")


def main():
    w = list(WEIGHTS)
    for epoch in range(1, EPOCHS + 1):
        mistakes = 0
        for x, y in EXAMPLES:
            inputs = [1.0, *x]
            h = 1.0 if sum(wi * xi for wi, xi in zip(w, inputs)) >= 0 else 0.0
            if h != y:
                mistakes += 1
                w = [wi + ALPHA * (y - h) * xi for wi, xi in zip(w, inputs)]
        print(f"epoch {epoch}: {mistakes} mistake(s), w = [{', '.join(fmt(v) for v in w)}]")
    print(f"Answer: w = [{', '.join(fmt(v) for v in w)}]")


if __name__ == "__main__":
    main()
