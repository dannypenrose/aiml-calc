"""Machine learning calculations (AIMA §18.6–18.7, Witten et al. §4.6–4.8).

Weight vectors always put the bias weight first: [w0, w1, ..., wn], with a dummy input x0 = 1.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any, Optional

from .common import fmt, md_table, natural_key


# ---------------------------------------------------------------------------
# Single neurons and activations
# ---------------------------------------------------------------------------

def _sig(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


ACTIVATIONS = {
    "threshold": lambda z: 1.0 if z >= 0 else 0.0,
    "logistic": _sig,
    "relu": lambda z: max(0.0, z),
    "tanh": math.tanh,
    "linear": lambda z: z,
}


def _linear(weights: list[float], x: list[float]) -> float:
    if len(weights) != len(x) + 1:
        raise ValueError(f"Need {len(x) + 1} weights (bias w0 first) for {len(x)} inputs, got {len(weights)}")
    return weights[0] + sum(w * xi for w, xi in zip(weights[1:], x))


def _lin_expr(weights, x) -> str:
    parts = [fmt(weights[0])] + [f"{fmt(w)}×{fmt(xi)}" for w, xi in zip(weights[1:], x)]
    return " + ".join(parts)


def neuron(inputs: list[float], weights: list[float], activation: str = "all") -> dict[str, Any]:
    """Output of one unit: linear part in = w0 + Σ wi·xi, then g(in) for each activation."""
    z = _linear(weights, inputs)
    acts = list(ACTIVATIONS) if activation == "all" else [activation]
    rows = []
    out = {}
    for a in acts:
        v = ACTIVATIONS[a](z)
        out[a] = v
        formula = {"threshold": f"{fmt(z)} ≥ 0 ? 1 : 0", "logistic": f"1 / (1 + e^−({fmt(z)}))",
                   "relu": f"max(0, {fmt(z)})", "tanh": f"tanh({fmt(z)})", "linear": fmt(z)}[a]
        rows.append([a, formula, fmt(v)])
    md = ["## Neuron output", "",
          f"**Answer:** linear part in = {_lin_expr(weights, inputs)} = **{fmt(z)}**; "
          + ", ".join(f"{a}: **{fmt(v)}**" for a, v in out.items()), "",
          md_table(["Activation", "Calculation", "Output"], rows), "",
          f"A neuron with {len(inputs)} inputs has {len(inputs) + 1} weights (the extra one is the bias w0)."]
    return {"linear": z, "outputs": out, "markdown": "\n".join(md)}


def check_hypotheses(examples: list[list[float]], hypotheses: list[list[float]], activation: str = "threshold",
                    names: Optional[list[str]] = None) -> dict[str, Any]:
    """Which hypotheses (weight vectors, bias first) classify every example [x1, ..., xn, y] correctly?"""
    names = names or [chr(ord("A") + i) for i in range(len(hypotheses))]
    g = ACTIVATIONS[activation]
    rows = []
    verdict = {}
    for name, w in zip(names, hypotheses):
        cells = []
        ok = True
        for ex in examples:
            x, y = ex[:-1], ex[-1]
            z = _linear(w, x)
            out = g(z)
            right = abs(out - y) < 1e-9 if activation == "threshold" else round(out) == y
            ok &= right
            cells.append(f"{fmt(z)} → {fmt(out)}{'' if right else ' ✗'}")
        verdict[name] = ok
        rows.append([f"{name}: {w}"] + cells + ["**y**" if ok else "**n**"])
    headers = ["Hypothesis [w0, w1, …]"] + [f"{tuple(ex[:-1])} y={fmt(ex[-1])}" for ex in examples] + ["Correct on all?"]
    md = ["## Hypothesis check", "",
          "**Answer:** " + ", ".join(f"{n}: {'y' if v else 'n'}" for n, v in verdict.items()), "",
          md_table(headers, rows)]
    return {"verdict": verdict, "markdown": "\n".join(md)}


# ---------------------------------------------------------------------------
# Perceptron / logistic learning
# ---------------------------------------------------------------------------

def perceptron_learning(examples: list[list[float]], weights: list[float], alpha: float = 0.1,
                        epochs: int = 1, activation: str = "threshold") -> dict[str, Any]:
    """AIMA single-example updates.
    threshold: wi ← wi + α (y − h(x)) xi   (perceptron learning rule, Eq 18.7)
    logistic:  wi ← wi + α (y − h(x)) h(x)(1 − h(x)) xi   (Eq 18.8)"""
    w = [float(v) for v in weights]
    g = ACTIVATIONS[activation]
    rows = []
    for ep in range(1, epochs + 1):
        for i, ex in enumerate(examples):
            x, y = [float(v) for v in ex[:-1]], float(ex[-1])
            z = _linear(w, x)
            hx = g(z)
            err = y - hx
            factor = err * (hx * (1 - hx) if activation == "logistic" else 1.0)
            xs = [1.0] + x
            new = [wi + alpha * factor * xi for wi, xi in zip(w, xs)]
            rows.append([f"{ep}.{i + 1}", "(" + ", ".join(fmt(v) for v in x) + ")", fmt(y), fmt(z), fmt(hx), fmt(err),
                         "[" + ", ".join(fmt(v) for v in new) + "]" + ("" if abs(err) > 1e-12 else " (no change)")])
            w = new
    rule = ("wᵢ ← wᵢ + α (y − h(x)) xᵢ" if activation != "logistic"
            else "wᵢ ← wᵢ + α (y − h(x)) h(x)(1 − h(x)) xᵢ")
    md = ["## Weight updates", "", f"**Answer:** final weights [{', '.join(fmt(v) for v in w)}]", "",
          f"Rule: {rule}, α = {fmt(alpha)}, x₀ = 1 (bias input)", "",
          md_table(["Epoch.example", "x", "y", "in", "h(x)", "y − h(x)", "Weights after"], rows)]
    return {"weights": w, "markdown": "\n".join(md)}


# ---------------------------------------------------------------------------
# Linear regression
# ---------------------------------------------------------------------------

def _solve(A: list[list[float]], b: list[float]) -> list[float]:
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[piv][c]) < 1e-12:
            raise ValueError("XᵀX is singular: need more (independent) examples than weights")
        M[c], M[piv] = M[piv], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [a - f * bb for a, bb in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def linear_regression(X: list[Any], y: list[float]) -> dict[str, Any]:
    """Least-squares fit. X is a list of numbers (univariate) or of lists (multivariate)."""
    rows_x = [[float(v)] if not isinstance(v, (list, tuple)) else [float(t) for t in v] for v in X]
    y = [float(v) for v in y]
    N, k = len(rows_x), len(rows_x[0])
    md = ["## Linear regression (least squares)", ""]
    # Normal equations: w = (XᵀX)⁻¹ Xᵀy
    Xa = [[1.0] + r for r in rows_x]
    XtX = [[sum(Xa[n][i] * Xa[n][j] for n in range(N)) for j in range(k + 1)] for i in range(k + 1)]
    Xty = [sum(Xa[n][i] * y[n] for n in range(N)) for i in range(k + 1)]
    w = _solve(XtX, Xty)
    preds = [sum(wi * xi for wi, xi in zip(w, r)) for r in Xa]
    loss = sum((yy - p) ** 2 for yy, p in zip(y, preds))
    md.append(f"**Answer:** h(x) = {fmt(w[0])}" + "".join(f" + {fmt(wi)}·x{i + 1}" for i, wi in enumerate(w[1:]))
              + f"; squared-error loss = {fmt(loss)}")
    md.append("")
    if k == 1:
        xs = [r[0] for r in rows_x]
        sx, sy = sum(xs), sum(y)
        sxx, sxy = sum(v * v for v in xs), sum(a * b for a, b in zip(xs, y))
        w1 = (N * sxy - sx * sy) / (N * sxx - sx ** 2)
        w0 = (sy - w1 * sx) / N
        mx, my = sx / N, sy / N
        cov = sum((a - mx) * (b - my) for a, b in zip(xs, y))
        var = sum((a - mx) ** 2 for a in xs)
        md += ["### Method 1: AIMA closed form (Eq 18.3)",
               f"N = {N}, Σx = {fmt(sx)}, Σy = {fmt(sy)}, Σx² = {fmt(sxx)}, Σxy = {fmt(sxy)}",
               f"w₁ = (NΣxy − ΣxΣy) / (NΣx² − (Σx)²) = ({N}×{fmt(sxy)} − {fmt(sx)}×{fmt(sy)}) / ({N}×{fmt(sxx)} − {fmt(sx)}²) = **{fmt(w1)}**",
               f"w₀ = (Σy − w₁Σx) / N = ({fmt(sy)} − {fmt(w1)}×{fmt(sx)}) / {N} = **{fmt(w0)}**", "",
               "### Method 2: deviations from the mean",
               f"x̄ = {fmt(mx)}, ȳ = {fmt(my)}; w₁ = Σ(x − x̄)(y − ȳ) / Σ(x − x̄)² = {fmt(cov)} / {fmt(var)} = **{fmt(cov / var)}**; "
               f"w₀ = ȳ − w₁x̄ = **{fmt(my - (cov / var) * mx)}**", ""]
    else:
        md += ["### Method: normal equations w = (XᵀX)⁻¹Xᵀy (AIMA §18.6.2)",
               "Each example row gets a leading 1 for the bias. Gradient descent reaches the same weights.", ""]
    md.append(md_table(["x", "y", "prediction", "residual"],
                       [[fmt(r[0]) if len(r) == 1 else "(" + ", ".join(fmt(v) for v in r) + ")", fmt(yy), fmt(p), fmt(yy - p)] for r, yy, p in zip(rows_x, y, preds)]))
    if N <= k:
        md.append("\n⚠ Need more examples than attributes for a unique fit.")
    return {"weights": w, "loss": loss, "markdown": "\n".join(md)}


def gradient_descent(X: list[Any], y: list[float], weights: list[float], alpha: float = 0.01,
                     steps: int = 1, mode: str = "batch", fold_two: bool = True) -> dict[str, Any]:
    """Gradient descent on squared-error loss for a linear model (AIMA Eq 18.5/18.6).
    batch: wᵢ ← wᵢ + α Σⱼ (yⱼ − h(xⱼ)) xⱼ,ᵢ ; stochastic: one example per update.
    fold_two=True folds the 2 from the derivative into α, as AIMA does."""
    rows_x = [[1.0] + ([float(v)] if not isinstance(v, (list, tuple)) else [float(t) for t in v]) for v in X]
    y = [float(v) for v in y]
    w = [float(v) for v in weights]
    c = 1.0 if fold_two else 2.0
    rows = []
    losses = [sum((yy - sum(wi * xi for wi, xi in zip(w, r))) ** 2 for r, yy in zip(rows_x, y))]
    for s in range(1, steps + 1):
        if mode == "batch":
            errs = [yy - sum(wi * xi for wi, xi in zip(w, r)) for r, yy in zip(rows_x, y)]
            grads = [sum(e * r[i] for e, r in zip(errs, rows_x)) for i in range(len(w))]
            w = [wi + alpha * c * g for wi, g in zip(w, grads)]
            loss = sum((yy - sum(wi * xi for wi, xi in zip(w, r))) ** 2 for r, yy in zip(rows_x, y))
            losses.append(loss)
            rows.append([str(s), "all", ", ".join(fmt(e) for e in errs), ", ".join(fmt(g) for g in grads),
                         "[" + ", ".join(fmt(v) for v in w) + "]", fmt(loss)])
        else:
            for j, (r, yy) in enumerate(zip(rows_x, y)):
                e = yy - sum(wi * xi for wi, xi in zip(w, r))
                w = [wi + alpha * c * e * xi for wi, xi in zip(w, r)]
                loss = sum((yv - sum(wi * xi for wi, xi in zip(w, rr))) ** 2 for rr, yv in zip(rows_x, y))
                losses.append(loss)
                rows.append([f"{s}.{j + 1}", str(j + 1), fmt(e), ", ".join(fmt(c * e * xi) for xi in r),
                             "[" + ", ".join(fmt(v) for v in w) + "]", fmt(loss)])
    rule = "wᵢ ← wᵢ + α Σⱼ (yⱼ − h(xⱼ)) xⱼ,ᵢ" if mode == "batch" else "wᵢ ← wᵢ + α (y − h(x)) xᵢ, one example at a time"
    md = ["## Gradient descent (squared error)", "", f"**Answer:** weights after {steps} step(s): [{', '.join(fmt(v) for v in w)}]", "",
          f"Rule ({mode}): {rule}{'' if fold_two else ' (with the factor 2 kept: α·2·…)'}; α = {fmt(alpha)}", "",
          md_table(["Step", "Example", "Errors y − h(x)", "Σ error × x (per weight)", "Weights after", "Loss after"], rows)]
    if len(rows) > 40:
        md[-1] = md_table(["Step", "Example", "Errors y − h(x)", "Σ error × x (per weight)", "Weights after", "Loss after"],
                          rows[:20] + [["…", "", "", "", "", ""]] + rows[-5:])
    return {"weights": w, "losses": losses, "markdown": "\n".join(md)}


def logistic_regression(x: list[float], weights: list[float], y: Optional[float] = None,
                        alpha: Optional[float] = None) -> dict[str, Any]:
    """Probability h(x) = σ(w·x); optionally one update step, shown with both common rules."""
    z = _linear(weights, x)
    p = _sig(z)
    md = ["## Logistic regression", "",
          f"**Answer:** in = {_lin_expr(weights, x)} = {fmt(z)}; P(y = 1 | x) = 1 / (1 + e^−{fmt(z)}) = **{fmt(p)}** "
          f"→ class {1 if p >= 0.5 else 0}", "",
          f"Log-odds check: ln(p / (1 − p)) = {fmt(math.log(p / (1 - p)) if 0 < p < 1 else float('inf'))} = in ✓"]
    out: dict[str, Any] = {"linear": z, "probability": p}
    if y is not None and alpha is not None:
        xs = [1.0] + [float(v) for v in x]
        aima = [w + alpha * (y - p) * p * (1 - p) * xi for w, xi in zip(weights, xs)]
        ll = [w + alpha * (y - p) * xi for w, xi in zip(weights, xs)]
        md += ["", "### One update step",
               f"Method 1, AIMA squared-error rule (Eq 18.8): wᵢ ← wᵢ + α (y − h) h(1 − h) xᵢ → [{', '.join(fmt(v) for v in aima)}]",
               f"Method 2, log-likelihood gradient ascent (Witten): wᵢ ← wᵢ + α (y − h) xᵢ → [{', '.join(fmt(v) for v in ll)}]",
               "_The two differ only by the h(1 − h) factor. Both are in common use._"]
        out.update({"aima_update": aima, "log_likelihood_update": ll})
    out["markdown"] = "\n".join(md)
    return out


# ---------------------------------------------------------------------------
# k-means and nearest neighbour
# ---------------------------------------------------------------------------

def _dist(a, b, metric):
    if metric == "manhattan":
        return sum(abs(x - y) for x, y in zip(a, b))
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _dist_expr(a, b, metric):
    if metric == "manhattan":
        return " + ".join(f"|{fmt(x - y)}|" for x, y in zip(a, b))
    return "√(" + " + ".join(fmt((x - y) ** 2) for x, y in zip(a, b)) + ")"


def kmeans(points: list[list[float]], centres: list[list[float]], names: Optional[list[str]] = None,
           metric: str = "euclidean", max_iterations: int = 1) -> dict[str, Any]:
    """k-means: assign each point to the nearest centre, then move each centre to the mean of its points."""
    pts = [[float(v) for v in p] for p in points]
    cs = [[float(v) for v in c] for c in centres]
    names = names or [chr(ord("A") + i) for i in range(len(cs))]
    md = ["## k-means", ""]
    history = []
    for it in range(1, max_iterations + 1):
        rows = []
        assign = []
        for p in pts:
            ds = [_dist(p, c, metric) for c in cs]
            best = min(range(len(cs)), key=lambda i: (ds[i], i))
            tie = sum(1 for d in ds if abs(d - ds[best]) < 1e-12) > 1
            assign.append(best)
            rows.append([str(tuple(fmt(v) for v in p)).replace("'", "")]
                        + [f"{_dist_expr(p, c, metric)} = {fmt(d)}" if metric == "euclidean" else fmt(d) for c, d in zip(cs, ds)]
                        + [f"**{names[best]}**" + (" (tie → first centre)" if tie else "")])
        total = sum(_dist(p, cs[a], metric) for p, a in zip(pts, assign))
        total_sq = sum(_dist(p, cs[a], "euclidean") ** 2 for p, a in zip(pts, assign))
        new = []
        lines = []
        for i, c in enumerate(cs):
            members = [p for p, a in zip(pts, assign) if a == i]
            if not members:
                new.append(c)
                lines.append(f"- **{names[i]}**: no points, stays at {tuple(fmt(v) for v in c)}")
                continue
            m = [sum(col) / len(members) for col in zip(*members)]
            new.append(m)
            comps = []
            for d in range(len(m)):
                comps.append(f"{'xyzw'[d] if d < 4 else 'x' + str(d)} = ({' + '.join(fmt(p[d]) for p in members)})/{len(members)} = {fmt(m[d])}")
            lines.append(f"- **{names[i]}**: " + ", ".join(comps))
        md += [f"### Iteration {it}", "Assign each point to its nearest centre:", "",
               md_table(["Point"] + [f"to {n} {tuple(fmt(v) for v in c)}".replace("'", "") for n, c in zip(names, cs)] + ["Nearest"], rows),
               "", f"Total distance = {fmt(total)}; total squared distance (Witten) = {fmt(total_sq)}", "",
               "Move each centre to the mean of its points:", *lines, ""]
        history.append({"assignment": [names[a] for a in assign], "centres": new})
        converged = all(_dist(a, b, "euclidean") < 1e-12 for a, b in zip(cs, new))
        cs = new
        if converged:
            md.append("Centres did not move, so k-means has **converged**.")
            break
    md.insert(1, "**Answer:** new centres " + ", ".join(f"{n} = ({', '.join(fmt(v) for v in c)})" for n, c in zip(names, cs)) + "\n")
    return {"centres": cs, "history": history, "markdown": "\n".join(md)}


def knn(train: list[list[Any]], query: list[float], k: int = 1, metric: str = "euclidean",
        normalise: bool = False) -> dict[str, Any]:
    """k-nearest-neighbour classification. Each training row is [a1, ..., an, label]."""
    X = [[float(v) for v in r[:-1]] for r in train]
    labels = [r[-1] for r in train]
    q = [float(v) for v in query]
    note = ""
    if normalise:
        cols = list(zip(*X, q))
        mins = [min(c) for c in cols]
        maxs = [max(c) for c in cols]
        def nz(v):
            return [(x - lo) / (hi - lo) if hi > lo else 0.0 for x, lo, hi in zip(v, mins, maxs)]
        X = [nz(r) for r in X]
        q = nz(q)
        note = "Attributes min-max normalised to [0, 1]: aᵢ = (vᵢ − min vᵢ) / (max vᵢ − min vᵢ) (Witten §4.7)."
    ds = [(_dist(r, q, metric), i) for i, r in enumerate(X)]
    ranked = sorted(ds)
    top = ranked[:k]
    votes = Counter(labels[i] for _, i in top)
    best = max(votes.values())
    winners = [l for l, c in votes.items() if c == best]
    pred = winners[0] if len(winners) == 1 else min(winners, key=lambda l: min(d for d, i in top if labels[i] == l))
    rows = [[str(rank + 1), str(tuple(fmt(v) for v in train[i][:-1])).replace("'", ""), str(labels[i]), fmt(d),
             "✓" if rank < k else ""] for rank, (d, i) in enumerate(ranked)]
    md = ["## k-nearest neighbour", "",
          f"**Answer:** predicted class **{pred}** (k = {k}; votes {dict(votes)}"
          + (", tie broken by nearest neighbour" if len(winners) > 1 else "") + ")", "",
          *( [note, ""] if note else [] ), md_table(["Rank", "Example", "Class", f"{metric.title()} distance", "In top k"], rows)]
    return {"prediction": pred, "markdown": "\n".join(m for m in md)}


# ---------------------------------------------------------------------------
# Network sizes
# ---------------------------------------------------------------------------

def cnn_layer(input_shape: list[int], filter_size: list[int], n_filters: int, stride: int = 1,
              padding: int = 0) -> dict[str, Any]:
    """Convolutional layer: output volume, neurons and weights (weights are shared by every copy of a filter)."""
    A, B, C = input_shape
    P, Q = filter_size[0], filter_size[1]
    if len(filter_size) > 2 and filter_size[2] != C:
        raise ValueError("Filter depth must equal the input depth")
    oa = (A - P + 2 * padding) // stride + 1
    ob = (B - Q + 2 * padding) // stride + 1
    neurons = oa * ob * n_filters
    per = P * Q * C + 1
    shared = per * n_filters
    md = ["## CNN layer", "",
          f"**Answer:** output volume **{oa} × {ob} × {n_filters}**; neurons **{neurons}**; weights **{shared}**", ""]
    if stride == 1 and padding == 0:
        md += ["### Method 1: simple formula (stride 1, no padding)",
               f"Output = (A − P + 1) × (B − Q + 1) × n = ({A} − {P} + 1) × ({B} − {Q} + 1) × {n_filters} = {oa} × {ob} × {n_filters}", ""]
    md += ["### Method 2: general formula",
           f"Each side = (size − filter + 2 × padding) / stride + 1 = ({A} − {P} + 2×{padding}) / {stride} + 1 = {oa}"
           + ("" if A == B and P == Q else f" and ({B} − {Q} + 2×{padding}) / {stride} + 1 = {ob}"), "",
           "### Neurons and weights",
           f"- Neurons: one per output value = {oa} × {ob} × {n_filters} = **{neurons}**",
           f"- Weights per filter: (P × Q × C) + 1 = ({P} × {Q} × {C}) + 1 = {per} (the +1 is the bias)",
           f"- Total weights: every copy of a filter shares its weights, so {n_filters} × {per} = **{shared}**",
           f"- ⚠ Common mistake: counting a separate set per neuron gives {neurons} × {per} = {neurons * per}. Weight sharing is what makes CNNs efficient."]
    if (A - P + 2 * padding) % stride or (B - Q + 2 * padding) % stride:
        md.append("\n⚠ The filter doesn't tile the input exactly with this stride; the result is rounded down.")
    return {"output": [oa, ob, n_filters], "neurons": neurons, "weights": shared, "markdown": "\n".join(md)}


def fc_layer(input_shape: list[int], n_neurons: int) -> dict[str, Any]:
    """Fully connected layer after a volume: every neuron sees every input value, plus a bias."""
    n_in = 1
    for d in input_shape:
        n_in *= int(d)
    w = (n_in + 1) * n_neurons
    md = ["## Fully connected layer", "",
          f"**Answer:** **{w}** weights", "",
          f"Each neuron sees {' × '.join(str(d) for d in input_shape)} = {n_in} inputs, so it has {n_in} + 1 = {n_in + 1} weights. "
          f"{n_neurons} neurons × {n_in + 1} = **{w}**."]
    return {"weights": w, "markdown": "\n".join(md)}


# ---------------------------------------------------------------------------
# Multilayer network: forward pass and one back-propagation step
# ---------------------------------------------------------------------------

def mlp_step(inputs: list[float], layers: list[list[list[float]]], targets: Optional[list[float]] = None,
             alpha: float = 0.1, activation: str = "logistic") -> dict[str, Any]:
    """Forward pass through a feed-forward network and, if targets are given, one back-propagation update (AIMA Fig 18.24).

    layers[l][j] is the weight vector [w0, w1, ...] of unit j in layer l (bias first)."""
    g = ACTIVATIONS[activation]

    def gprime(z, a):
        if activation == "logistic":
            return a * (1 - a)
        if activation == "tanh":
            return 1 - a * a
        if activation == "relu":
            return 1.0 if z > 0 else 0.0
        if activation == "linear":
            return 1.0
        raise ValueError("Back-propagation needs a differentiable activation")

    acts = [[float(v) for v in inputs]]
    ins = []
    md = ["## Feed-forward network", ""]
    rows = []
    for l, layer in enumerate(layers):
        prev = acts[-1]
        zs = [_linear(w, prev) for w in layer]
        a = [g(z) for z in zs]
        ins.append(zs)
        acts.append(a)
        for j, (w, z, av) in enumerate(zip(layer, zs, a)):
            rows.append([f"layer {l + 1}, unit {j + 1}", f"{_lin_expr(w, prev)} = {fmt(z)}", fmt(av)])
    md.append("**Answer:** outputs [" + ", ".join(fmt(v) for v in acts[-1]) + "]")
    out: dict[str, Any] = {"outputs": acts[-1]}
    if targets is not None:
        deltas: list[list[float]] = [[] for _ in layers]
        L = len(layers) - 1
        deltas[L] = [gprime(z, a) * (float(t) - a) for z, a, t in zip(ins[L], acts[L + 1], targets)]
        for l in range(L - 1, -1, -1):
            deltas[l] = [gprime(ins[l][i], acts[l + 1][i]) * sum(layers[l + 1][j][i + 1] * deltas[l + 1][j]
                                                                  for j in range(len(layers[l + 1])))
                         for i in range(len(layers[l]))]
        new_layers = []
        upd_rows = []
        for l, layer in enumerate(layers):
            prev = [1.0] + acts[l]
            nl = []
            for j, w in enumerate(layer):
                nw = [wi + alpha * ai * deltas[l][j] for wi, ai in zip(w, prev)]
                nl.append(nw)
                upd_rows.append([f"layer {l + 1}, unit {j + 1}", fmt(deltas[l][j]),
                                 "[" + ", ".join(fmt(v) for v in nw) + "]"])
            new_layers.append(nl)
        md[-1] += "; updated weights below"
        md += ["", md_table(["Unit", "in = Σ wᵢaᵢ", "a = g(in)"], rows), "",
               "### Back-propagation (one step)",
               "Output units: Δⱼ = g′(inⱼ)(yⱼ − aⱼ). Hidden units: Δᵢ = g′(inᵢ) Σⱼ wᵢ,ⱼ Δⱼ. Update: wᵢ,ⱼ ← wᵢ,ⱼ + α aᵢ Δⱼ "
               f"(α = {fmt(alpha)}; for the logistic function g′(in) = a(1 − a)).", "",
               md_table(["Unit", "Δ", "New weights [w0, …]"], upd_rows)]
        out.update({"deltas": deltas, "new_layers": new_layers})
    else:
        md += ["", md_table(["Unit", "in = Σ wᵢaᵢ", "a = g(in)"], rows)]
    total = sum(len(l) * len(l[0]) for l in layers)
    md.append(f"\nTotal weights in the network (including biases): {total}.")
    out["markdown"] = "\n".join(md)
    return out
