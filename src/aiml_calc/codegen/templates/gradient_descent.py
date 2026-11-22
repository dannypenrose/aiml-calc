"""Gradient descent on squared error for y = w0 + w1 x (Russell & Norvig, AIMA §18.6.1–18.6.2).

    batch:      w_i <- w_i + ALPHA * sum over examples of (y - h(x)) * x_i
    stochastic: the same update after every single example
(x_0 = 1 for the bias; AIMA folds the factor 2 from the derivative into ALPHA.)
"""

# --- inputs ---
XS = [1, 2, 3, 4]
YS = [3, 5, 7, 10]
WEIGHTS = [0.0, 0.0]     # starting [w0, w1]
ALPHA = 0.02             # learning rate
STEPS = 100
MODE = "batch"           # "batch" or "stochastic"
# --- end inputs ---


def loss(w):
    return sum((y - (w[0] + w[1] * x)) ** 2 for x, y in zip(XS, YS))


def fmt(x):
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")


def main():
    w = list(WEIGHTS)
    for step in range(1, STEPS + 1):
        if MODE == "batch":
            errors = [y - (w[0] + w[1] * x) for x, y in zip(XS, YS)]
            w[0] += ALPHA * sum(errors)
            w[1] += ALPHA * sum(e * x for e, x in zip(errors, XS))
        else:
            for x, y in zip(XS, YS):
                e = y - (w[0] + w[1] * x)
                w[0] += ALPHA * e
                w[1] += ALPHA * e * x
        if step <= 5 or step == STEPS or step % max(1, STEPS // 10) == 0:
            print(f"step {step}: w = [{fmt(w[0])}, {fmt(w[1])}], loss = {fmt(loss(w))}")
    print(f"Answer: w = [{fmt(w[0])}, {fmt(w[1])}]")


if __name__ == "__main__":
    main()
