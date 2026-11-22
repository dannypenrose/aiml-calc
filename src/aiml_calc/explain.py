"""Explanations shown in the web UI: what each algorithm does, how it works, and what to know to read its trace.

Each entry has a one-line `summary` (always visible) and a markdown `body` (in a "How it works" panel).
Formulas use KaTeX ($...$), which Streamlit renders.
"""

from __future__ import annotations

SECTIONS: dict[str, str] = {
    "search": (
        "A **search problem** is defined by an initial state, the actions available in each state, a transition model, "
        "a goal test and a step cost. Search algorithms build a tree of paths from the start, keeping a **frontier** of "
        "paths not yet explored. They differ only in *which* frontier node they expand next, and that one choice "
        "decides whether they are complete, optimal, and how much time and memory they use."
    ),
    "logic": (
        "**Propositional logic** represents knowledge as sentences built from true/false symbols. A **model** assigns a "
        "truth value to every symbol. A knowledge base **entails** a sentence (KB ⊨ α) when α is true in every model "
        "where the KB is true. The tools here decide entailment in different ways: by checking every model, by "
        "resolution, or by chaining through rules."
    ),
    "sat": (
        "**Satisfiability (SAT)** asks whether some model makes every clause of a CNF formula true. It was the first "
        "problem proved **NP-complete** (Cook, 1971), so no known algorithm is fast in the worst case, yet modern "
        "solvers handle millions of variables. Entailment reduces to SAT: KB ⊨ α exactly when KB ∧ ¬α is unsatisfiable."
    ),
    "fol": (
        "**First-order logic** adds objects, relations, functions and the quantifiers ∀ and ∃, so one rule can cover "
        "every object (\"all missiles are weapons\"). Inference has to match rules to facts that use different variable "
        "names, and **unification** is the operation that does that matching."
    ),
    "csp": (
        "A **constraint satisfaction problem** has variables, each with a domain of values, and constraints saying "
        "which combinations are allowed. Because the state has this structure, the solver can reason about "
        "constraints directly: pruning values that can't work before it tries them, instead of searching blindly."
    ),
    "games": (
        "**Adversarial search** plans in a two-player, zero-sum game: what's good for MAX is bad for MIN. A game tree "
        "alternates the players' moves, leaves hold the final **utility** for MAX, and each player is assumed to play "
        "optimally. Chance nodes model dice or other randomness."
    ),
    "probability": (
        "When an agent can't be certain, it keeps **degrees of belief** as probabilities and updates them with "
        "evidence. Every query here is an application of two rules: the **product rule** P(a ∧ b) = P(a | b) P(b) and "
        "**marginalisation** (summing out variables you don't care about), followed by normalisation."
    ),
    "ml": (
        "**Machine learning** builds a model from examples instead of hand-written rules. Supervised methods learn a "
        "mapping from inputs to known labels (regression for numbers, classification for categories); unsupervised "
        "methods such as clustering find structure in unlabelled data. Each model is defined by its hypothesis space, "
        "the loss it minimises and the algorithm that minimises it."
    ),
}


VIEWS: dict[str, dict[str, str]] = {
    # ------------------------------------------------------------------ search
    "search_trace": {
        "summary": "Watch a search algorithm grow its frontier step by step and see which path it returns, and why.",
        "body": r"""
**Reading the trace.** Each step removes one node from the **frontier**, goal-tests it, and (if it isn't the goal)
**expands** it: generates its children and adds them to the frontier. The *Why* column shows the value that made
this node the next choice.

**Graph search vs tree search.** Graph search keeps an **explored set** and never adds a state it has already seen,
so it can't loop. Tree search keeps no memory of visited states, so the same state can be expanded many times and
infinite loops are possible on graphs with cycles.

**The evaluation function.** Best-first algorithms order the frontier by $f(n)$:

| Algorithm | Frontier | Expands the node with the lowest… |
|---|---|---|
| Breadth-first | FIFO queue | depth |
| Depth-first | LIFO stack | (deepest first) |
| Uniform-cost | priority queue | $g(n)$, path cost so far |
| Greedy best-first | priority queue | $h(n)$, estimated cost to goal |
| A* | priority queue | $f(n) = g(n) + h(n)$, estimated total cost |

**When the goal test happens matters.** Testing when a node is *generated* finds a goal one step sooner, which is
safe for BFS. For UCS and A* it would be wrong: a cheaper path to the goal might still be on the frontier, so they
test when a node is *selected*.

**Why A\* is optimal.** If $h$ never overestimates (admissible), the true cost of the best solution $C^*$ is at least
$f(n)$ for every node on its path, so A* can't select a worse goal first. Graph search needs the stronger property of
**consistency**, $h(n) \le c(n, n') + h(n')$, so that the first path found to each state is the cheapest.

**Cost.** Time and space depend on the algorithm; the table below gives both for each one (AIMA Fig 3.21).
The pattern to remember: algorithms that keep the whole frontier (breadth-first, uniform-cost, A\*) need space
exponential in depth, $O(b^d)$, and usually run out of memory before they run out of time. Depth-first variants
(depth-first, iterative deepening, IDA\*) keep only the current path and its siblings, $O(bd)$. On an explicit graph
with $V$ states and $E$ edges, graph search never expands a state twice, so uniform-cost search (and A\* with a
consistent heuristic) runs in $O((V + E) \log V)$ time with a binary-heap priority queue.

*Reference: AIMA §3.3–3.5.*
""",
    },
    "search_heuristic": {
        "summary": "Test whether a heuristic is admissible and consistent, and compare two heuristics for dominance.",
        "body": r"""
A **heuristic** $h(n)$ estimates the cheapest cost from $n$ to a goal. Its quality decides how much work informed
search saves.

- **Admissible:** never overestimates, $h(n) \le h^*(n)$ where $h^*$ is the true cost. This is what makes tree-search
  A* optimal. The tool computes $h^*$ exactly by running Dijkstra's algorithm backwards from the goal.
- **Consistent (monotone):** a triangle inequality on every edge, $h(n) \le c(n, n') + h(n')$. It means $f$ never
  decreases along a path, which makes graph-search A* optimal. Every consistent heuristic (with $h(\text{goal}) = 0$)
  is admissible, but not the other way round.
- **Dominance:** if $h_2(n) \ge h_1(n)$ everywhere and both are admissible, $h_2$ is never worse: A* with $h_2$ expands
  no more nodes. Higher is better, as long as it stays admissible.

**Where heuristics come from.** The exact cost of a **relaxed problem** (one with some rules removed) is always an
admissible heuristic for the original. For the 8-puzzle, letting tiles move anywhere gives "misplaced tiles";
letting them move through each other gives Manhattan distance, which dominates it.

**Cost.** Computing $h^*$ exactly is one run of Dijkstra's algorithm from the goal over the reversed edges:
$O((V + E) \log V)$ time and $O(V)$ space for $V$ states and $E$ edges. Admissibility is then one comparison per
state, $O(V)$, and consistency one per edge, $O(E)$. That only works because the graph is small and explicit; the
8-puzzle has 181,440 reachable states and a Rubik's cube about $4.3 \times 10^{19}$, so for real problems you prove
admissibility by reasoning about the relaxed problem instead.

*Reference: AIMA §3.5.2, §3.6.*
""",
    },
    # ------------------------------------------------------------------ propositional logic
    "truth_table": {
        "summary": "List every model and count how many make each formula true.",
        "body": r"""
With $n$ symbols there are $2^n$ models (each symbol is either true or false). A truth table evaluates the formula
in every one.

- **Valid** (a tautology): true in every model, e.g. $A \lor \lnot A$.
- **Satisfiable:** true in at least one model.
- **Unsatisfiable** (a contradiction): true in none, e.g. $A \land \lnot A$.

**Counting shortcut.** Fix the symbols the formula forces, then each free symbol doubles the count. $B \land \lnot D$
over $\{A, B, C, D\}$ forces $B$ and $D$, leaving $2^2 = 4$ models. Symbols that don't appear in the formula still
double the total, which is why you can add extra symbols.

**Cost.** $O(2^n \cdot s)$ time for $n$ symbols and a formula of size $s$, because each of the $2^n$ rows
evaluates the whole formula. Generating rows one at a time needs only $O(n + s)$ space; this tool keeps the full table
to display it, which takes $O(2^n)$. Fine for a handful of symbols, hopeless for hundreds: 30 symbols is already over
a billion rows. That exponential wall is what DPLL and local search are designed to get around.

*Reference: AIMA §7.4.*
""",
    },
    "cnf": {
        "summary": "Rewrite any formula as a conjunction of clauses (conjunctive normal form), one rule at a time.",
        "body": r"""
**Conjunctive normal form** is an AND of clauses, where each clause is an OR of literals:
$(\lnot A \lor B) \land (A \lor C)$. Resolution and SAT solvers only work on CNF, and every formula has an equivalent
CNF.

**The four steps.**
1. **Eliminate ⇔:** $\alpha \Leftrightarrow \beta \;\equiv\; (\alpha \Rightarrow \beta) \land (\beta \Rightarrow \alpha)$
2. **Eliminate ⇒:** $\alpha \Rightarrow \beta \;\equiv\; \lnot\alpha \lor \beta$
3. **Move ¬ inwards** with De Morgan's laws, $\lnot(\alpha \land \beta) \equiv \lnot\alpha \lor \lnot\beta$ and
   $\lnot(\alpha \lor \beta) \equiv \lnot\alpha \land \lnot\beta$, and remove double negation, $\lnot\lnot\alpha \equiv \alpha$.
4. **Distribute ∨ over ∧:** $\alpha \lor (\beta \land \gamma) \equiv (\alpha \lor \beta) \land (\alpha \lor \gamma)$

**The check.** Each row where the formula is false gives one clause that rules that row out, so the truth table
gives a second CNF. The tool confirms the two are equivalent on every row.

**Cost.** Steps 1–3 visit each part of the formula once, so they take time and space linear in its size $s$
(except that eliminating ⇔ copies both sides, which doubles the size at each level of nested ⇔). Step 4 is the
expensive one: $(A_1 \land B_1) \lor \dots \lor (A_n \land B_n)$ distributes into $2^n$ clauses, so time and space
can be $O(2^s)$. Real solvers use the Tseitin transformation instead, which adds one new variable per subformula to
keep the result $O(s)$ (equisatisfiable rather than equivalent). The truth-table check costs $O(2^n)$ for $n$
symbols, like any truth table.

*Reference: AIMA §7.5.2.*
""",
    },
    "entailment": {
        "summary": "Decide whether the knowledge base entails a query, by checking models and by resolution.",
        "body": r"""
**Entailment** $KB \models \alpha$ means: in every model where all of $KB$ is true, $\alpha$ is true too. It is about
meaning, not proof.

**Method 1: model checking.** List the models of $KB$ and check $\alpha$ in each. A single model where $KB$ is true
and $\alpha$ false is a **counter-example**.

**Method 2: resolution.** Proof by contradiction: $KB \models \alpha$ exactly when $KB \land \lnot\alpha$ is
unsatisfiable. Convert $KB \land \lnot\alpha$ to clauses and repeatedly apply the **resolution rule**: from
$(A \lor B)$ and $(\lnot B \lor C)$ infer $(A \lor C)$. Deriving the **empty clause** (□) proves a contradiction.
If no new clauses can be produced, $\alpha$ is not entailed.

**Why it works.** Resolution is **sound** (it only derives entailed clauses) and **refutation-complete** (if
$KB \land \lnot\alpha$ is unsatisfiable, it will find □). The tool lists only the resolvents used in the final proof.

**Validity and inference.** $\vdash$ means "derivable by an algorithm"; $\models$ means "true in all models". A sound
and complete algorithm makes the two coincide.

**Cost.** Model checking takes $O(2^n)$ time for $n$ symbols but only $O(n)$ space if each model is checked and
then discarded. Resolution can be exponential in both: over $n$ symbols there are $3^n$ possible clauses (each symbol
appears positively, negatively or not at all), and in the worst case it generates and stores most of them.
Propositional entailment is co-NP-complete, so no method is known to be fast in every case; resolution wins when a
short proof exists, model checking when there are few symbols.

*Reference: AIMA §7.5.*
""",
    },
    "chaining": {
        "summary": "Infer new facts from if-then rules: forward from what is known, or backward from the question.",
        "body": r"""
Both algorithms work on **definite clauses**: rules with a conjunction of positive premises and one positive
conclusion, such as $L \land M \Rightarrow P$, plus known facts. Many real knowledge bases fit this form, and it
makes inference **linear time** instead of exponential.

**Forward chaining (data-driven).** Keep an **agenda** of known facts and, for each rule, a **count** of premises not
yet known. Popping a fact decrements the count of every rule that uses it; when a count reaches 0 the rule fires and
its conclusion joins the agenda. It stops when the query appears or nothing new can be added.

**Backward chaining (goal-driven).** Start from the query and find a rule that concludes it; its premises become
subgoals, proved the same way. It only touches facts relevant to the question, which is why it is often much
faster. A **loop check** stops it from chasing a goal that is already being proved.

**The graph.** In the AND-OR graph, arrows meeting at ∧ need *all* their premises; separate arrows into a symbol are
alternatives (any one will do). Green symbols are given facts; blue ones were inferred.

Both are **sound and complete** for definite clauses.

**Cost.** Forward chaining takes $O(s)$ time and space, linear in the size $s$ of the knowledge base (the total
number of symbols across all rules and facts): each fact enters the agenda at most once, and decrements each premise
count that mentions it once. Backward chaining is often much less than linear in practice, because it only touches
rules relevant to the query; its space is the chain of open subgoals plus a record of the goals already proved, at
most $O(n)$ for $n$ symbols.

*Reference: AIMA §7.5.4, Fig 7.15–7.16.*
""",
    },
    # ------------------------------------------------------------------ SAT
    "dpll": {
        "summary": "A complete SAT solver: depth-first search over partial assignments, pruned by three simple rules.",
        "body": r"""
DPLL (Davis, Putnam, Logemann, Loveland) is depth-first search over partial models, with three improvements over
plain truth-table enumeration:

1. **Early termination.** A clause is true as soon as one literal is true; the formula is false as soon as one
   clause is false. No need to wait for a full assignment.
2. **Pure symbol rule.** A symbol that appears with only one sign in the remaining clauses can be set to make those
   literals true. That can never hurt.
3. **Unit clause rule.** A clause with exactly one unassigned literal (all others false) forces that literal.
   One assignment can trigger another, a cascade called **unit propagation**.

Only when no rule applies does DPLL **branch**: pick the next symbol, try true, and **backtrack** to false if that
fails.

**Reading the step summary.** Each step runs from a branching decision to success or fail, listing every assignment
made on the way, including forced ones.

**Properties.** DPLL is **complete**: it proves unsatisfiability as well as finding models. The worst case is still
exponential, but modern solvers add clause learning, smart variable ordering and restarts on top of this core.

**Cost.** Worst case $O(2^n \cdot s)$ time for $n$ symbols and a formula of size $s$: the search tree has up to
$2^n$ leaves, and each node scans the clauses. Space is polynomial, because depth-first search keeps only one branch:
the clauses plus one partial model per level of recursion, at most $n$ levels, so $O(s + n^2)$ for a straightforward
implementation. Unit propagation and early termination are what usually keep the tree far smaller than $2^n$.

*Reference: AIMA §7.6.1, Fig 7.17.*
""",
    },
    "walksat_step": {
        "summary": "One move of a local-search SAT solver: pick a false clause and flip one of its symbols.",
        "body": r"""
**WalkSAT** starts from a complete (random) assignment and repairs it one flip at a time.

Each step:
1. Pick a **clause that is currently false** (at random).
2. With probability $p$, flip a **random** symbol from that clause (a *random walk* step that escapes local minima).
3. Otherwise flip the symbol that **maximises the number of satisfied clauses** (a *greedy* step).

Only symbols in the chosen clause can flip, because flipping any of them makes that clause true.

**Reading $p$.** $p = 0$ means always greedy; $p = 1$ means always random. With $p$ strictly between, both moves are
possible, so this view lists every model one step can reach and how.

**Cost.** One step is cheap. Finding the false clauses takes $O(s)$ for a formula of size $s$, and scoring each
candidate flip means re-counting the satisfied clauses, $O(k \cdot s)$ for a chosen clause of $k$ literals (real
solvers keep incremental counts to make this nearly constant). Space beyond the formula is $O(n)$ for $n$ symbols:
just the current assignment.

*Reference: AIMA §7.6.2, Fig 7.18.*
""",
    },
    "walksat_run": {
        "summary": "A full randomised WalkSAT run, repeatable with a seed.",
        "body": r"""
Repeats the WalkSAT step until every clause is satisfied or the flip limit is reached.

**Strengths.** Local search is often dramatically faster than DPLL on large satisfiable problems, and it uses almost
no memory: it only stores the current assignment.

**Limits.** WalkSAT is **incomplete**. If it fails, the formula might be unsatisfiable or it might just have been
unlucky, so it can never prove unsatisfiability. It also has no memory of past models, so it can revisit them.

**Hard problems.** For random 3-SAT, problems are easy when the clause-to-symbol ratio is low (almost always
satisfiable) or high (almost always unsatisfiable). The hardest instances sit near the **critical ratio of about
4.26**, where the probability of being satisfiable drops sharply.

**Cost.** At most $F$ flips for a flip limit $F$, each $O(k \cdot s)$ as in the single step, so
$O(F \cdot k \cdot s)$ time; space stays $O(n)$ beyond the formula, however long it runs. There is no useful bound on how many
flips a satisfiable formula needs: the time to success is random, which is why real runs combine a flip limit with
restarts from a fresh random assignment.

*Reference: AIMA §7.6.2–7.6.3.*
""",
    },
    # ------------------------------------------------------------------ FOL
    "unify": {
        "summary": "Find the most general substitution that makes two first-order expressions identical.",
        "body": r"""
**Unification** finds a substitution $\theta$ (a set of variable bindings like $\{x/John\}$) such that
$\text{SUBST}(\theta, p) = \text{SUBST}(\theta, q)$. It is the matching step behind every first-order inference rule.

**How it works.** Compare the two expressions symbol by symbol:
- identical → nothing to do;
- a variable against anything → bind it (after applying the bindings so far);
- two compound terms → same function or predicate and same number of arguments, then unify each pair of arguments;
- anything else → fail.

**Most general unifier (MGU).** Of all the unifiers, the MGU commits to as little as possible: unifying
$Knows(John, x)$ with $Knows(y, z)$ gives $\{y/John, x/z\}$, not $\{y/John, x/John, z/John\}$. Every other unifier is
a special case of the MGU.

**Occur check.** A variable can't be bound to a term containing itself: $P(x)$ and $P(F(x))$ would need
$x = F(F(F(\dots)))$, so they fail.

**Standardising apart.** $Knows(John, x)$ and $Knows(x, Elizabeth)$ fail only because both use the name $x$.
Renaming one sentence's variables first (to $x_1$) makes them unify. Backward chaining does this automatically.

**Cost.** For expressions of total size $s$, the AIMA algorithm keeps its bindings without substituting them
everywhere, which makes it $O(s)$ without the occur check and $O(s^2)$ with it, because the check scans a term each
time a variable is bound; that is why Prolog leaves it out by default. Written out in full, the substitution can be
exponentially large: unifying $P(x_1, \dots, x_n)$ with $P(F(x_0, x_0), \dots, F(x_{n-1}, x_{n-1}))$ binds $x_n$ to
a term containing $2^n$ copies of $x_0$. Linear-time algorithms (Paterson and Wegman, 1978) share subterms instead of
copying them. Space is $O(s)$ for the bindings and the recursion.

*Reference: AIMA §9.2.2.*
""",
    },
    "fol_chaining": {
        "summary": "Prove first-order queries from rules and facts, forward round by round or backward goal by goal.",
        "body": r"""
These are the first-order versions of propositional chaining, over **definite clauses** such as
$Missile(x) \Rightarrow Weapon(x)$. Variables are implicitly universally quantified ("for all $x$").

**Forward chaining (FOL-FC-ASK).** In each **round**, find every substitution that makes all of a rule's premises
match known facts, and add the resulting conclusion if it is new. Stop when the query unifies with a new fact or a
round adds nothing (a **fixed point**). The crime example needs two rounds: first it infers $Weapon(M1)$,
$Sells(West, M1, Nono)$ and $Hostile(Nono)$, then $Criminal(West)$.

**Backward chaining (FOL-BC-ASK).** Unify the goal with a rule's conclusion, then prove the rule's premises as
subgoals, left to right, carrying the bindings along. It is depth-first, the strategy behind **Prolog**, and can
return the binding that answers a query with variables (e.g. $Criminal(w)$ gives $w = West$).

**Properties.** Forward chaining is sound and complete for definite clauses; without function symbols (Datalog) it
always terminates. Backward chaining is sound but can loop forever on recursive rules, so it is not complete.

**Cost.** With $p$ predicates of arity at most $k$ and $n$ constants, a Datalog knowledge base can hold at most
$p\,n^k$ distinct facts, so forward chaining reaches its fixed point within that many rounds and stores at most that
many facts: polynomial in $n$ for a fixed $k$. Each round is the expensive part: matching a rule's premises against
the facts is a constraint-satisfaction problem, NP-hard in general, so a rule with $r$ premises can try up to $f^r$
combinations of $f$ facts. Backward chaining needs space only linear in the depth of the proof, but without
memoisation it can re-prove the same subgoal many times, and on recursive rules it may never stop.

*Reference: AIMA §9.3–9.4.*
""",
    },
    # ------------------------------------------------------------------ CSP
    "csp_backtracking": {
        "summary": "Solve a constraint problem by assigning one variable at a time and backtracking on dead ends.",
        "body": r"""
**Backtracking search** is depth-first search that assigns one variable per level and backs up as soon as a
constraint is violated. Three choices make it fast:

**Which variable next?**
- **MRV (minimum remaining values):** pick the variable with the fewest legal values left. This is the "fail-first"
  idea: if a dead end is coming, find it early.
- **Degree heuristic:** break MRV ties by picking the variable involved in the most constraints with unassigned
  variables. On the Australia map it picks SA (5 neighbours) first.

**Which value first?**
- **LCV (least constraining value):** try the value that rules out the fewest options for neighbours. This is
  "fail-last": we only need one solution, so keep options open.

**What to infer after each assignment?**
- **Forward checking:** remove now-impossible values from neighbours' domains; an empty domain means backtrack
  immediately.
- **MAC (maintaining arc consistency):** run AC-3 from the assigned variable, which also propagates the knock-on
  effects that forward checking misses.

Try switching the settings on the "Ordering puzzle" example and compare the assignment counts.

**Cost.** In the worst case backtracking tries every assignment: $O(d^n)$ time for $n$ variables with domains of
size $d$, since CSPs are NP-complete in general. Space is polynomial: the current assignment plus the pruned domains,
at most $O(n^2 d)$ if each of the $n$ levels keeps its own copy. The heuristics leave the worst case unchanged but
often cut the search by orders of magnitude, and MAC spends one AC-3 run, $O(cd^3)$, per assignment to save far
more in backtracking. Tree-structured constraint graphs are the exception: they can be solved in $O(nd^2)$ time.

*Reference: AIMA §6.3.*
""",
    },
    "csp_ac3": {
        "summary": "Shrink every domain until each remaining value has support in every neighbouring variable.",
        "body": r"""
An arc $X \to Y$ is **consistent** if every value left in $X$'s domain has at least one compatible value in $Y$'s.
**AC-3** makes every arc consistent:

1. Put every arc in a queue.
2. Take an arc $X \to Y$ and **revise** it: delete each value of $X$ with no support in $Y$.
3. If $X$ lost any values, re-queue every arc $Z \to X$ (except from $Y$), because values of $Z$ may have just lost
   their only support.
4. Stop when the queue is empty, or a domain becomes empty, which proves there is **no solution**.

**What it does and doesn't guarantee.** Arc consistency is a necessary condition for a solution, not a sufficient
one: three variables in a triangle with domains $\{red, green\}$ and $\neq$ constraints are arc consistent but have
no solution. It is usually used to shrink the problem before or during backtracking.

**Cost.** With $n$ variables, $c$ binary constraints (so $2c$ arcs) and domains of size at most $d$, AC-3 runs in
$O(cd^3)$ time: each arc is re-queued at most $d$ times (once per value its neighbour loses), and each revision
compares $d^2$ pairs of values. Space is $O(c + nd)$ for the queue and the domains. AC-4 brings the time down to
$O(cd^2)$, which is optimal, at the cost of extra bookkeeping.

*Reference: AIMA §6.2.2, Fig 6.3.*
""",
    },
    # ------------------------------------------------------------------ games
    "games": {
        "summary": "Back up values from the leaves to choose MAX's best move, and see how alpha-beta skips branches.",
        "body": r"""
**Minimax.** Assuming both players play perfectly, the value of a node is

$$
\text{MINIMAX}(n) = \begin{cases}
\text{utility}(n) & \text{leaf} \\
\max_{c}\ \text{MINIMAX}(c) & \text{MAX to move} \\
\min_{c}\ \text{MINIMAX}(c) & \text{MIN to move}
\end{cases}
$$

MAX picks the child with the highest backed-up value. Minimax is complete (on finite trees) and optimal against an
optimal opponent, but visits every node: $O(b^m)$ for branching factor $b$ and depth $m$.

**Alpha-beta pruning** returns the same value while skipping branches that can't affect the decision. It carries two
bounds down the tree:
- $\alpha$: the best value MAX can already guarantee on this path;
- $\beta$: the best (lowest) value MIN can already guarantee.

When a MIN node's value drops to $\le \alpha$, MAX above will never let play reach it, so its remaining children are
**pruned** (and symmetrically at MAX nodes when the value reaches $\ge \beta$).

**Move ordering matters.** With the best moves examined first, alpha-beta needs about $O(b^{m/2})$ nodes, letting it
search roughly twice as deep in the same time. Compare the "Good move ordering" example with Fig 5.2.

**Chance nodes (expectiminimax)** take the probability-weighted average of their children. Unlike minimax, the
result then depends on the actual scale of the utilities, not just their order.

**Cost.** Minimax is depth-first, so it takes $O(b^m)$ time but only $O(bm)$ space ($O(m)$ if moves are
generated one at a time). Alpha-beta needs the same space; its time ranges from $O(b^{m/2})$ with perfect move
ordering through about $O(b^{3m/4})$ with random ordering to $O(b^m)$ with the worst. Expectiminimax also branches at
every chance node: with $n$ distinct outcomes per chance node it takes $O(b^m n^m)$. For chess, $b \approx 35$ and a
game often lasts 50 moves by each player, so the full tree has about $35^{100} \approx 10^{154}$ nodes; real programs
stop at a fixed depth and score the position with an evaluation function.

*Reference: AIMA §5.2–5.3, §5.5.*
""",
    },
    # ------------------------------------------------------------------ probability
    "bayes_rule": {
        "summary": "Update a prior belief with evidence: how likely is the hypothesis now that we've seen E?",
        "body": r"""
$$
P(H \mid E) = \frac{P(E \mid H)\, P(H)}{P(E)}, \qquad
P(E) = P(E \mid H) P(H) + P(E \mid \lnot H) P(\lnot H)
$$

- **Prior** $P(H)$: belief before the evidence (e.g. how common a disease is).
- **Likelihood** $P(E \mid H)$: how often the evidence appears when $H$ is true (a test's sensitivity).
- **False-positive rate** $P(E \mid \lnot H)$: how often it appears anyway.
- **Posterior** $P(H \mid E)$: the updated belief.

**The base-rate effect.** With a 1% prior, a test that is 90% sensitive and 5% false-positive still gives only a
**15%** posterior, because most positives come from the much larger healthy group. The natural-frequency view makes
this concrete. Ignoring the prior is the **base-rate fallacy**.

**Odds form.** Posterior odds = prior odds × the **likelihood ratio** $P(E \mid H) / P(E \mid \lnot H)$, which is a
handy way to combine several independent pieces of evidence.

**Cost.** Constant time and space: two multiplications, one addition and one division. Combining $k$ pieces of
evidence that are conditionally independent given $H$ is $O(k)$, one likelihood ratio each in the odds form. The cost
only grows when the pieces of evidence are not independent, which is what Bayesian networks are for.

*Reference: AIMA §13.5.*
""",
    },
    "bayes_net": {
        "summary": "Answer a probability query in a Bayesian network by summing over every unobserved variable.",
        "body": r"""
A **Bayesian network** is a directed acyclic graph where each node has a **conditional probability table** (CPT)
giving $P(X \mid \text{Parents}(X))$. The graph encodes **conditional independence**: each node is independent of
its non-descendants given its parents. That lets the full joint distribution factorise:

$$
P(x_1, \dots, x_n) = \prod_i P(x_i \mid \text{parents}(X_i))
$$

The burglary network needs 10 numbers instead of the $2^5 - 1 = 31$ a full joint table would need.

**Inference by enumeration.** To compute $P(X \mid e)$, sum the joint over every **hidden** variable $y$, then
normalise:

$$
P(X \mid e) = \alpha \sum_{y} P(X, e, y)
$$

Each term is a product of one CPT entry per node, which is exactly what the working lists. $\alpha$ just rescales
the two totals to sum to 1.

**Explaining away.** Burglary and earthquake are independent causes of the alarm, but once there is evidence the
alarm went off they compete to explain it. Add `"Earthquake": true` to the example's evidence: P(burglary) falls from
0.284 to about 0.003, because the earthquake already accounts for the calls.

**Cost.** Enumeration takes $O(2^n)$ time for $n$ Boolean variables but only $O(n)$ space, because it walks the
terms depth-first, one at a time. The network itself is the space saving: with at most $k$ parents per node it needs
$O(n \cdot 2^k)$ numbers instead of the full joint's $2^n$. Variable elimination avoids recomputing shared terms and
is linear in the size of the network for polytrees (networks with at most one path between any two nodes), but exact
inference is NP-hard in general, which is why sampling methods exist.

*Reference: AIMA §14.1–14.4.*
""",
    },
    "joint": {
        "summary": "Answer any query by summing the matching rows of the full joint distribution and normalising.",
        "body": r"""
The **full joint distribution** gives a probability for every combination of values, so it can answer any query:

1. **Select** the rows consistent with the evidence.
2. **Sum** them separately for each value of the query variable (this is **marginalisation**, summing out the rest).
3. **Normalise** so the results add to 1: multiply by $\alpha = 1 / P(e)$.

$$
P(\text{Cavity} \mid \text{toothache}) = \alpha \langle 0.108 + 0.012,\ 0.016 + 0.064 \rangle
= \alpha \langle 0.12, 0.08 \rangle = \langle 0.6, 0.4 \rangle
$$

**Why we need anything else.** The table has $2^n$ rows for $n$ Boolean variables, so it is impossible to store or
estimate for realistic problems. Independence and conditional independence let Bayesian networks represent the same
information compactly.

**Cost.** A query takes $O(2^n)$ time, one pass over the table, and the table itself takes $O(2^n)$ space for $n$
Boolean variables ($O(d^n)$ for variables with $d$ values each). Both costs come from the size of the table, not the
method: 30 Boolean variables already need over a billion entries, each of which would have to be estimated from
data.

*Reference: AIMA §13.3.*
""",
    },
    "naive_bayes": {
        "summary": "Classify by combining each attribute's evidence as if the attributes were independent given the class.",
        "body": r"""
**Naive Bayes** assumes every attribute is conditionally independent of the others given the class:

$$
P(c \mid x_1, \dots, x_n) \;\propto\; P(c) \prod_i P(x_i \mid c)
$$

Each probability is just a count from the training data, so training is a single pass. Predict the class with the
highest score; normalising the scores gives probabilities.

**Why "naive" works.** The independence assumption is almost always false (temperature and humidity are related),
but the classifier only needs the *ranking* of classes to be right, and it often is. It is a strong baseline for text
classification such as spam filtering.

**The zero-count problem.** If a value never appears with a class in training, its probability is 0 and wipes out
the whole product. **Laplace smoothing** adds $k$ (usually 1) to every count:

$$
P(x_i = v \mid c) = \frac{\text{count}(v, c) + k}{\text{count}(c) + k \cdot |\text{values}|}
$$

**Cost.** Training is one counting pass over the data: $O(N \cdot a)$ time for $N$ examples with $a$ attributes.
The model stores one probability per class per attribute value, $O(c \cdot a \cdot v)$ space for $c$ classes and at
most $v$ values per attribute, and a prediction takes $O(c \cdot a)$. A full joint distribution over the same
attributes would need $O(c \cdot v^a)$ numbers; that drop from exponential to linear is the whole point of the
independence assumption.

*Reference: AIMA §20.2.2; Witten et al. §4.2.*
""",
    },
    # ------------------------------------------------------------------ ML
    "kmeans": {
        "summary": "Group points into k clusters by alternately assigning points to centres and moving centres to means.",
        "body": r"""
**k-means** (Lloyd's algorithm) is **unsupervised**: there are no labels, only points.

1. Choose $k$ starting centres.
2. **Assign** each point to its nearest centre (Euclidean distance by default).
3. **Update** each centre to the **mean** (centroid) of the points assigned to it.
4. Repeat 2–3 until the centres stop moving.

**What it optimises.** Each step reduces (never increases) the total squared distance from points to their centres,
$\sum_i \lVert x_i - \mu_{c(i)} \rVert^2$. The mean is exactly the point that minimises squared distance within a
cluster. So k-means always **converges**, but only to a **local** minimum.

**In practice.**
- Results depend on the starting centres: run it several times and keep the best, or use **k-means++** seeding.
- Choosing $k$: total distance always falls as $k$ grows, so look for the **elbow** where it stops falling fast.
- It assumes compact, round, similar-sized clusters, and features on similar scales (normalise first).

**Cost.** Each iteration measures the distance from all $N$ points to all $k$ centres in $d$ dimensions, $O(Nkd)$
time, then recomputes the means in $O(Nd)$, so $I$ iterations take $O(INkd)$. Space is $O((N + k)d)$ for the points
and centres, plus $O(N)$ for the assignments. $I$ is usually small in practice, but there are inputs on which Lloyd's
algorithm needs exponentially many iterations, and finding the best clustering (the global minimum) is NP-hard.

*Reference: Witten et al. §4.8 (Lloyd, 1982).*
""",
    },
    "knn": {
        "summary": "Classify a new point by a majority vote of its k closest training examples.",
        "body": r"""
**k-nearest neighbour** is **instance-based** (or "lazy") learning: training just stores the examples, and all the
work happens at prediction time.

1. Compute the distance from the query to every training example.
2. Take the $k$ nearest.
3. Predict the majority class among them (or the average, for regression).

**Choosing k.** $k = 1$ follows the training data exactly and is sensitive to noise (**overfitting**); large $k$
smooths the boundary and can blur real structure (**underfitting**). An odd $k$ avoids ties between two classes.

**Normalise your features.** Distance is dominated by whichever attribute has the largest range. Min-max scaling,
$a = (v - \min) / (\max - \min)$, puts every attribute on $[0, 1]$. Try turning it on and off.

**The curse of dimensionality.** In many dimensions, all points become roughly equally far apart, so "nearest" stops
meaning much, and prediction cost grows with the size of the training set.

**Cost.** Training is free: $O(1)$ time beyond storing the data, which takes $O(Nd)$ space for $N$ examples in $d$
dimensions. Each prediction pays instead: $O(Nd)$ to compute every distance, plus $O(N \log k)$ to keep the $k$
nearest (or $O(N \log N)$ by sorting). That is the reverse of most models, which are slow to train and fast to use.
Spatial indexes such as k-d trees cut a query to about $O(\log N)$ in low dimensions, but lose their advantage as $d$
grows: the curse of dimensionality again.

*Reference: Witten et al. §4.7; AIMA §18.8.1.*
""",
    },
    "linear_regression": {
        "summary": "Fit the straight line that minimises the sum of squared errors, in closed form.",
        "body": r"""
**Linear regression** fits $h_w(x) = w_0 + w_1 x$ by minimising the **squared-error loss**
$\text{Loss} = \sum_j (y_j - h_w(x_j))^2$.

Setting the partial derivatives to zero gives a unique solution:

$$
w_1 = \frac{N \sum x y - \sum x \sum y}{N \sum x^2 - (\sum x)^2}, \qquad
w_0 = \frac{\sum y - w_1 \sum x}{N}
$$

Equivalently, $w_1 = \text{cov}(x, y) / \text{var}(x)$ and the line always passes through $(\bar{x}, \bar{y})$. With
several inputs the same idea gives the **normal equations** $w^* = (X^\top X)^{-1} X^\top y$.

**Why squared error?** It is smooth and convex (one global minimum), and if the noise is Gaussian it gives the
**maximum-likelihood** weights (Gauss).

**Reading the chart.** Dashed lines are the **residuals** $y - h(x)$; the fitted line makes the sum of their squares
as small as possible. Squaring means outliers pull hard on the line.

**Cost.** The one-input closed form needs four sums, $\sum x$, $\sum y$, $\sum xy$ and $\sum x^2$: one pass, $O(N)$
time and $O(1)$ extra space for $N$ points. With $d$ inputs the normal equations cost $O(Nd^2)$ to form $X^\top X$
and $O(d^3)$ to solve (by Gaussian elimination), with $O(d^2)$ space for the matrix. That $d^3$ is why problems with
very many inputs use gradient descent instead.

*Reference: AIMA §18.6.1–18.6.2; Witten et al. §4.6.*
""",
    },
    "gradient_descent": {
        "summary": "Minimise the loss by repeatedly stepping the weights downhill, against the gradient.",
        "body": r"""
**Gradient descent** minimises a loss by moving each weight a small step in the direction that reduces it fastest:

$$
w_i \leftarrow w_i - \alpha \frac{\partial \text{Loss}}{\partial w_i}
$$

For linear regression the gradient gives the update (AIMA folds the factor 2 into $\alpha$):

$$
w_i \leftarrow w_i + \alpha \sum_j (y_j - h_w(x_j))\, x_{j,i}
$$

**Learning rate $\alpha$.** Too small and it crawls; too large and every step overshoots the minimum, so the loss
grows instead of shrinking. Try raising $\alpha$ until the warning appears.

**Batch vs stochastic.**
- **Batch** sums over every example per step: smooth, and guaranteed to converge for a small enough $\alpha$ because
  the loss is convex.
- **Stochastic** updates after each example: noisier, but much cheaper per step and works on data that arrives one
  example at a time.

Gradient descent matters because most models (logistic regression, neural networks) have **no closed-form
solution**; it is how they are all trained.

**Cost.** One batch step computes the gradient over all $N$ examples for $d$ weights: $O(Nd)$ time. A stochastic
step uses one example: $O(d)$. Over $T$ steps the totals are $O(TNd)$ and $O(Td)$, and space is $O(d)$ for the
weights beyond the data itself. How large $T$ must be depends on the learning rate and the shape of the loss, not on
$N$, which is why stochastic and mini-batch methods win on large datasets: a single batch step means reading all of
the data.

*Reference: AIMA §18.6.1–18.6.2.*
""",
    },
    "logistic": {
        "summary": "Turn a linear score into a probability with the logistic (sigmoid) function.",
        "body": r"""
**Logistic regression** is a classifier. It passes a linear score through the **logistic function**:

$$
P(y = 1 \mid x) = \sigma(w \cdot x) = \frac{1}{1 + e^{-w \cdot x}}
$$

The output lies between 0 and 1, so it reads as a probability. The **decision boundary** is where $w \cdot x = 0$
(probability 0.5); it is a straight line (or hyperplane), so logistic regression is a **linear classifier**.

**Log-odds.** Taking $\ln \frac{p}{1 - p}$ gives back $w \cdot x$: the model is linear in the **log-odds**, so each
weight says how much one unit of that input multiplies the odds (by $e^{w_i}$).

**Training.** There is no closed form, so the weights are found iteratively:
- maximising the **log-likelihood** gives the update $w_i \leftarrow w_i + \alpha (y - h)\, x_i$;
- AIMA minimises squared error instead, which adds the sigmoid's derivative: $w_i \leftarrow w_i + \alpha (y - h)\, h(1 - h)\, x_i$.

Both appear in the working.

**Cost.** A prediction is a dot product and one exponential: $O(d)$ time for $d$ weights. Each training pass over
$N$ examples costs $O(Nd)$, the same as gradient descent for linear regression, and space is $O(d)$ for the weights.
With no closed form, the total depends on how many passes it takes to converge.

*Reference: AIMA §18.6.4; Witten et al. §4.6.*
""",
    },
    "neuron": {
        "summary": "One artificial neuron: a weighted sum of inputs passed through an activation function.",
        "body": r"""
A **unit** computes a weighted sum of its inputs plus a bias, then applies an **activation function** $g$:

$$
in = w_0 + \sum_i w_i x_i, \qquad a = g(in)
$$

The bias $w_0$ is treated as the weight on a dummy input $x_0 = 1$, so a unit with $n$ inputs has $n + 1$ weights.

| Activation | Formula | Notes |
|---|---|---|
| Hard threshold | $1$ if $in \ge 0$, else $0$ | the **perceptron**; not differentiable |
| Logistic (sigmoid) | $1 / (1 + e^{-in})$ | smooth, output in $(0, 1)$, reads as a probability |
| ReLU | $\max(0, in)$ | the default in modern deep networks |
| tanh | $\tanh(in)$ | output in $(-1, 1)$, a rescaled sigmoid |

**Why the nonlinearity matters.** Without it, a network of any depth collapses into one linear function. The
activation is what lets layered networks represent curved decision boundaries.

**Geometry.** A threshold unit splits its input space with the hyperplane $in = 0$. With weights $[-1.5, 1, 1]$ it
computes AND; with $[-0.5, 1, 1]$ it computes OR.

**Cost.** $O(n)$ time for $n$ inputs: $n$ multiplications, $n$ additions and one activation, and $O(n)$ space for
the weights. Everything larger is built from this: a fully connected layer of $m$ units on $n$ inputs costs $O(nm)$,
one multiply-add per connection.

*Reference: AIMA §18.7.1.*
""",
    },
    "perceptron": {
        "summary": "Learn a linear classifier by nudging the weights after every misclassified example.",
        "body": r"""
The **perceptron learning rule** updates the weights after each example:

$$
w_i \leftarrow w_i + \alpha\, (y - h_w(x))\, x_i
$$

- If the prediction is right, $y - h = 0$ and nothing changes.
- If it says 0 but the answer is 1, each weight increases in proportion to its input, raising the score next time;
  the reverse when it says 1 and the answer is 0.

**Perceptron convergence theorem.** If the data are **linearly separable**, the rule finds a separating line in a
finite number of updates. The chart shows the line it found (where $w_0 + w_1 x_1 + w_2 x_2 = 0$).

**The limit: XOR.** No single line separates XOR's positive and negative examples, so a single perceptron can never
learn it (Minsky & Papert, 1969). Change the labels to `0 1 1 0` and run several epochs: every epoch still contains mistakes, and the weights keep returning to the same values instead of converging. Adding
a hidden layer fixes this.

**Cost.** Each example costs $O(d)$ for $d$ weights (one prediction and, if it is wrong, one update), so an epoch
over $N$ examples takes $O(Nd)$ and space is $O(d)$. The convergence theorem bounds the number of mistakes by
$(R / \gamma)^2$, where $R$ is the length of the longest input and $\gamma$ the margin by which the data can be
separated: classes far apart are learned quickly, nearly touching ones slowly. On data that is not separable there is
no bound, so training stops at an epoch limit.

*Reference: AIMA §18.6.3, §18.7.2.*
""",
    },
    "network": {
        "summary": "A feed-forward pass through a small network, and one step of back-propagation.",
        "body": r"""
**Forward pass.** Each layer computes its units' activations from the previous layer's outputs, $a_j = g(in_j)$,
until the output layer gives the prediction.

**Back-propagation** trains every weight by gradient descent, using the chain rule to pass the error backwards:

1. **Output units:** $\Delta_j = g'(in_j)\, (y_j - a_j)$, the error scaled by how sensitive the unit is.
2. **Hidden units:** $\Delta_i = g'(in_i) \sum_j w_{i,j} \Delta_j$, each hidden unit takes a share of the errors of
   the units it feeds, weighted by its connections.
3. **Update every weight:** $w_{i,j} \leftarrow w_{i,j} + \alpha\, a_i\, \Delta_j$.

For the logistic function, $g'(in) = a(1 - a)$, so everything comes from values already computed in the forward pass.

**Why hidden layers?** A network with one sufficiently large hidden layer can approximate any continuous function
(the **universal approximation** result), which is what single perceptrons can't do.

**Practical issues.** The loss is not convex, so training can stop in a local minimum; and with sigmoid units,
gradients shrink as they pass back through many layers (the **vanishing gradient** problem), one reason ReLU replaced
them.

**Cost.** A forward pass does one multiply-add per weight, so it takes $O(W)$ time for a network with $W$ weights.
Back-propagation costs the same again, one pass backwards, and gives the gradient for every weight at once;
estimating each gradient separately would need a forward pass per weight, $O(W^2)$ in all. That is why it made
training practical. $E$ epochs over $N$ examples take $O(ENW)$. Space is $O(W)$ for the weights plus the activation of
every unit, which back-propagation must keep from the forward pass; in deep networks those stored activations are
often the larger part of the memory.

*Reference: AIMA §18.7.3–18.7.4, Fig 18.24.*
""",
    },
    "cnn": {
        "summary": "Work out a convolutional layer's output size, neurons and weights.",
        "body": r"""
A **convolutional layer** slides small **filters** across the input. Each filter looks at a $P \times Q$ patch
through the full input depth $C$ and produces one output value per position.

**Output size.** Along each side:

$$
\text{out} = \frac{\text{in} - \text{filter} + 2 \times \text{padding}}{\text{stride}} + 1
$$

With stride 1 and no padding this is $(A - P + 1) \times (B - Q + 1)$, and the output depth is the number of filters.

**Weight sharing.** Every position uses the *same* filter weights, so the layer has only
$n \times (P \cdot Q \cdot C + 1)$ weights (the $+1$ is each filter's bias), however large the input. A fully
connected layer on the same input would need weights for every input–output pair. Sharing is what makes CNNs
practical for images, and it makes them **translation equivariant**: a feature is detected wherever it appears.

**Neurons.** Each output value counts as one neuron (one copy of a filter at one position), so there are
$\text{out}_A \times \text{out}_B \times n$ of them. A common mistake is to multiply neurons by weights per filter,
which counts the shared weights many times over.

**Fully connected layers** after a convolutional volume have $(\text{inputs} + 1)$ weights per neuron.

**Cost.** Each output value is one filter applied at one position, $P \cdot Q \cdot C$ multiply-adds, so a layer
with an $\text{out}_A \times \text{out}_B \times n$ output takes $O(\text{out}_A \cdot \text{out}_B \cdot n \cdot PQC)$
time. Space is $n(PQC + 1)$ weights, which weight sharing keeps small, plus the output volume itself. Sharing saves
storage, not work: the time still grows with the size of the image. (This tool only works out the sizes, which takes
constant time.)

*Reference: AIMA 4th ed. §21.3.*
""",
    },
}


# Per-algorithm notes for the search view, plus the standard properties table (AIMA Fig 3.21).
SEARCH_ALGOS: dict[str, str] = {
    "bfs": "Expands the shallowest node first using a FIFO queue. It finds the path with the fewest steps, which is "
           "the cheapest only when every step costs the same. Memory is its weakness: it stores every node at the "
           "frontier's depth.",
    "dfs": "Expands the deepest node first using a LIFO stack. It needs very little memory (just the current path and "
           "the siblings along it) but can return a long, expensive path, and tree-search DFS can loop forever.",
    "ucs": "Expands the node with the lowest path cost g(n). It is Dijkstra's algorithm with a goal test, and is "
           "optimal for any non-negative step costs, at the price of exploring in every direction equally.",
    "greedy": "Expands the node that looks closest to the goal, by h(n) alone, ignoring the cost so far. Often fast, but "
              "not optimal: compare its path on the road map with A*'s.",
    "astar": "Expands the node with the lowest f(n) = g(n) + h(n), the estimated cost of the cheapest solution through "
             "it. Optimal with an admissible (tree search) or consistent (graph search) heuristic, and no other optimal "
             "algorithm using the same heuristic expands fewer nodes.",
    "dls": "Depth-first search that refuses to go below a depth limit, so it can't run forever, but misses any goal "
           "deeper than the limit.",
    "ids": "Runs depth-limited search with limits 0, 1, 2, … until it finds a goal. It combines BFS's completeness and "
           "shallowest-goal guarantee with DFS's small memory. Re-visiting the shallow levels costs surprisingly "
           "little, because most nodes are at the deepest level.",
    "idastar": "Iterative deepening with an f-cost limit instead of a depth limit: each iteration searches depth-first "
               "inside one f-contour, then raises the limit to the smallest f that exceeded it. Optimal like A*, with "
               "memory linear in depth.",
}

SEARCH_PROPERTIES = r"""
| Algorithm | Complete? | Optimal? | Time | Space |
|---|---|---|---|---|
| Breadth-first | yes¹ | if step costs are equal | $O(b^d)$ | $O(b^d)$ |
| Uniform-cost | yes² | yes | $O(b^{1+\lfloor C^*/\epsilon \rfloor})$ | $O(b^{1+\lfloor C^*/\epsilon \rfloor})$ |
| Depth-first | graph search in finite spaces | no | $O(b^m)$ | $O(bm)$ |
| Depth-limited | if $\ell \ge d$ | no | $O(b^\ell)$ | $O(b\ell)$ |
| Iterative deepening | yes¹ | if step costs are equal | $O(b^d)$ | $O(bd)$ |
| Greedy best-first | graph search in finite spaces | no | $O(b^m)$ | $O(b^m)$ |
| A* | yes² | yes³ | exponential in the heuristic's error | keeps every node |
| IDA* | yes² | yes³ | exponential | $O(bd)$ |

$b$ branching factor, $d$ depth of the shallowest goal, $m$ maximum depth, $C^*$ optimal cost, $\epsilon$ smallest
step cost. ¹ if $b$ is finite. ² if step costs are at least $\epsilon > 0$. ³ admissible $h$ for tree search,
consistent $h$ for graph search.
"""
