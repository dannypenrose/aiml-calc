"""Least-squares linear regression y = w0 + w1 x (Russell & Norvig, AIMA §18.6.1, Eq 18.3).

Two closed forms that must agree:
  1. w1 = (N sum(xy) - sum(x) sum(y)) / (N sum(x^2) - sum(x)^2),   w0 = (sum(y) - w1 sum(x)) / N
  2. w1 = covariance(x, y) / variance(x),                            w0 = mean(y) - w1 mean(x)
"""

# --- inputs ---
XS = [1, 2, 3, 4, 5, 6]
YS = [3, 5, 7, 10, 11, 14]
# --- end inputs ---


def fmt(x):
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")


def main():
    n = len(XS)
    sx, sy = sum(XS), sum(YS)
    sxx, sxy = sum(x * x for x in XS), sum(x * y for x, y in zip(XS, YS))
    w1 = (n * sxy - sx * sy) / (n * sxx - sx ** 2)
    w0 = (sy - w1 * sx) / n
    print(f"Method 1: w1 = ({n} x {fmt(sxy)} - {fmt(sx)} x {fmt(sy)}) / ({n} x {fmt(sxx)} - {fmt(sx)}^2) = {fmt(w1)}, w0 = {fmt(w0)}")

    mx, my = sx / n, sy / n
    cov = sum((x - mx) * (y - my) for x, y in zip(XS, YS))
    var = sum((x - mx) ** 2 for x in XS)
    print(f"Method 2: w1 = {fmt(cov)} / {fmt(var)} = {fmt(cov / var)}, w0 = {fmt(my - cov / var * mx)}")

    loss = sum((y - (w0 + w1 * x)) ** 2 for x, y in zip(XS, YS))
    print(f"Squared-error loss = {fmt(loss)}")
    print(f"Answer: y = {fmt(w0)} + {fmt(w1)}x")


if __name__ == "__main__":
    main()
