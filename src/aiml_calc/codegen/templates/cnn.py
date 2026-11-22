"""Size of a convolutional layer: output volume, neurons and (shared) weights (AIMA 4th ed. §21.3).

Each side of the output is  (input - filter + 2 x padding) / stride + 1, and the output depth is the number of
filters. Every position reuses the same filter weights, so the layer has  filters x (P x Q x C + 1)  weights.
"""

# --- inputs ---
INPUT_SHAPE = (32, 32, 3)    # width A, height B, depth C
FILTER_SIZE = (5, 5)         # P x Q (the depth is always C)
FILTERS = 6
STRIDE = 1
PADDING = 0
# --- end inputs ---


def main():
    a, b, c = INPUT_SHAPE
    p, q = FILTER_SIZE
    out_a = (a - p + 2 * PADDING) // STRIDE + 1
    out_b = (b - q + 2 * PADDING) // STRIDE + 1
    neurons = out_a * out_b * FILTERS
    per_filter = p * q * c + 1
    weights = FILTERS * per_filter
    print(f"output side: ({a} - {p} + 2 x {PADDING}) / {STRIDE} + 1 = {out_a}")
    print(f"weights per filter: {p} x {q} x {c} + 1 = {per_filter} (the +1 is the bias)")
    print(f"without weight sharing it would be {neurons} x {per_filter} = {neurons * per_filter}")
    print(f"Answer: output {out_a} x {out_b} x {FILTERS}, {neurons} neurons, {weights} weights")


if __name__ == "__main__":
    main()
