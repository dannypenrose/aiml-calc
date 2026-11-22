"""One artificial neuron (Russell & Norvig, AIMA §18.7.1).

    in = w0 + w1 x1 + ... + wn xn        (w0 is the bias, on a dummy input x0 = 1)
    a  = g(in)                           for an activation function g
"""
import math

# --- inputs ---
INPUTS = [1.0, 1.0]
WEIGHTS = [-1.5, 1.0, 1.0]     # [w0 (bias), w1, ...]: these compute AND
# --- end inputs ---

ACTIVATIONS = {
    "threshold": lambda z: 1.0 if z >= 0 else 0.0,
    "logistic": lambda z: 1 / (1 + math.exp(-z)),
    "relu": lambda z: max(0.0, z),
    "tanh": math.tanh,
}


def fmt(x):
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")


def main():
    z = WEIGHTS[0] + sum(w * x for w, x in zip(WEIGHTS[1:], INPUTS))
    print(f"in = {fmt(WEIGHTS[0])} + " + " + ".join(f"{fmt(w)} x {fmt(x)}" for w, x in zip(WEIGHTS[1:], INPUTS)) + f" = {fmt(z)}")
    outputs = {name: g(z) for name, g in ACTIVATIONS.items()}
    for name, value in outputs.items():
        print(f"  {name}: {fmt(value)}")
    print(f"Answer: in = {fmt(z)}; " + ", ".join(f"{name} {fmt(v)}" for name, v in outputs.items()))


if __name__ == "__main__":
    main()
