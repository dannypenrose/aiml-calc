"""Logistic regression: turn a linear score into a probability (Russell & Norvig, AIMA §18.6.4).

    P(y = 1 | x) = sigma(w0 + w1 x),   sigma(z) = 1 / (1 + e^-z)

Then one update step towards the target Y, under the two common rules:
    AIMA (squared error):   w_i <- w_i + ALPHA (y - h) h (1 - h) x_i
    log-likelihood:         w_i <- w_i + ALPHA (y - h) x_i
"""
import math

# --- inputs ---
WEIGHTS = [-4.0, 1.5]   # [w0, w1]
X = 3.0
Y = 1.0                 # target for the update step
ALPHA = 0.1
# --- end inputs ---


def sigmoid(z):
    return 1 / (1 + math.exp(-z))


def fmt(x):
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")


def main():
    z = WEIGHTS[0] + WEIGHTS[1] * X
    h = sigmoid(z)
    print(f"score z = {fmt(WEIGHTS[0])} + {fmt(WEIGHTS[1])} x {fmt(X)} = {fmt(z)}")
    print(f"P(y = 1 | x) = 1 / (1 + e^-{fmt(z)}) = {fmt(h)}  ->  class {1 if h >= 0.5 else 0}")
    inputs = [1.0, X]
    aima = [w + ALPHA * (Y - h) * h * (1 - h) * xi for w, xi in zip(WEIGHTS, inputs)]
    loglik = [w + ALPHA * (Y - h) * xi for w, xi in zip(WEIGHTS, inputs)]
    print(f"update (AIMA):           [{', '.join(fmt(w) for w in aima)}]")
    print(f"update (log-likelihood): [{', '.join(fmt(w) for w in loglik)}]")
    print(f"Answer: P(y = 1 | x) = {fmt(h)}")


if __name__ == "__main__":
    main()
