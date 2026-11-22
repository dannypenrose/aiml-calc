"""A feed-forward network with logistic units: one forward pass and one back-propagation step
(Russell & Norvig, AIMA §18.7.4, Fig 18.24).

    forward:  in_j = w0 + sum_i w_ij a_i,   a_j = sigma(in_j)
    output:   delta_j = a_j (1 - a_j) (y_j - a_j)
    hidden:   delta_i = a_i (1 - a_i) sum_j w_ij delta_j
    update:   w_ij <- w_ij + ALPHA a_i delta_j     (a_0 = 1 for the bias)
"""
import math

# --- inputs ---
INPUTS = [1.0, 0.0]
LAYERS = [   # one list per layer; one [w0 (bias), w1, w2, ...] per unit
    [[0.1, 0.2, 0.3], [0.2, -0.1, 0.4]],   # hidden layer: 2 units
    [[0.3, 0.5, -0.2]],                    # output layer: 1 unit
]
TARGETS = [1.0]
ALPHA = 0.5
# --- end inputs ---


def sigmoid(z):
    return 1 / (1 + math.exp(-z))


def fmt(x):
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")


def main():
    # forward pass: activations[l] are the inputs to layer l
    activations = [list(INPUTS)]
    for layer in LAYERS:
        prev = activations[-1]
        activations.append([sigmoid(w[0] + sum(wi * a for wi, a in zip(w[1:], prev))) for w in layer])
    print("activations: " + " | ".join(", ".join(fmt(a) for a in layer) for layer in activations))

    # backward pass: deltas from the output layer back to the first hidden layer
    deltas = [None] * len(LAYERS)
    out = activations[-1]
    deltas[-1] = [a * (1 - a) * (t - a) for a, t in zip(out, TARGETS)]
    for l in range(len(LAYERS) - 2, -1, -1):
        deltas[l] = [a * (1 - a) * sum(LAYERS[l + 1][j][i + 1] * deltas[l + 1][j] for j in range(len(LAYERS[l + 1])))
                     for i, a in enumerate(activations[l + 1])]
    print("deltas: " + " | ".join(", ".join(fmt(d) for d in layer) for layer in deltas))

    # weight update
    new_layers = []
    for l, layer in enumerate(LAYERS):
        inputs = [1.0] + activations[l]
        new_layers.append([[w + ALPHA * a * deltas[l][j] for w, a in zip(unit, inputs)] for j, unit in enumerate(layer)])
    for l, layer in enumerate(new_layers):
        print(f"layer {l + 1} new weights: " + "; ".join("[" + ", ".join(fmt(w) for w in unit) + "]" for unit in layer))
    print("Answer: output " + ", ".join(fmt(a) for a in out) + "; output delta " + ", ".join(fmt(d) for d in deltas[-1]))


if __name__ == "__main__":
    main()
