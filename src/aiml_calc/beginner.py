"""Plain-language explanations for newcomers, shown in the "New to this? Start here" panel of each view.

Each entry walks through: the idea as an everyday picture, the steps in plain words, the maths one symbol at a time,
a tiny example with real numbers, and the words worth knowing. No prior AI or maths background is assumed beyond
school arithmetic.
"""

from __future__ import annotations

BEGINNER: dict[str, str] = {
    # ------------------------------------------------------------------ search
    "search_trace": r"""
**The idea.** Imagine planning a car journey with a paper map. You can't see the whole route at once, so you keep a
list of places you *could* drive to next (the **frontier**). Each turn you pick one place from the list, check whether
it's your destination, and if not, write down the places you can reach from there. Search algorithms are different
rules for *which place to pick next*.

**Step by step.**
1. Put the starting town on the list.
2. Pick one town from the list (each algorithm has its own rule for this).
3. Is it the destination? Then stop: you've found a route.
4. If not, add the towns you can drive to from there, and go back to step 2.

**The maths, symbol by symbol.** The clever algorithms give every town a score and always pick the lowest:
- $g(n)$: how far you've **already driven** to reach town $n$ (real distance, known exactly).
- $h(n)$: a **guess** of how far is left from $n$ to the destination, like the straight-line distance on the map.
- $f(n) = g(n) + h(n)$: the estimated **total** length of a trip that goes through $n$.

Uniform-cost search uses only $g$ (closest to home first). Greedy search uses only $h$ (whatever looks closest to the
destination). A\* uses both, $f = g + h$, which is why it finds the shortest route without wasting time.

**Tiny example.** You've driven 12 km to reach town T, and T is about 12 km from the destination as the crow flies.
Then $g = 12$, $h = 12$, so $f = 12 + 12 = 24$: the trip through T is probably about 24 km. If town L scores
$f = 32$, A\* looks at T first.

**How long it takes.** It depends on the rule. Algorithms that keep every place they've found on the list
(breadth-first, uniform-cost, A\*) can need a huge list: if every town has 10 roads out, 6 roads deep is already a
million towns. Depth-first search only remembers the current route and the turnings off it, so it needs very little
memory, but it can wander a long way. A good guess $h(n)$ is what stops A\* looking at most of those towns.

**Words to know**
- **Node / state**: A place you can be.
- **Expand**: Look at where you can go from a place.
- **Frontier**: Places found but not yet explored.
- **Path cost**: Total distance of a route.
- **Optimal**: Guaranteed to find the shortest route.
""",
    "search_heuristic": r"""
**The idea.** A **heuristic** is an educated guess of how far you still have to go, like looking at a map and saying
"about 10 km left". A good guess helps search head in the right direction. This view checks whether a guess can be
trusted.

**Two ways a guess can be trustworthy.**
1. **Admissible: it never overestimates.** Straight-line distance is admissible, because no road can be shorter than
   a straight line. An optimistic guess is safe: the search will never skip the best route thinking it's too long.
2. **Consistent: it doesn't jump around.** As you drive one road, your guess shouldn't drop by more than the length
   of that road. If it does, the guess was wrong somewhere.

**The maths, symbol by symbol.**
- $h(n)$: your guess from place $n$.
- $h^*(n)$: the **true** shortest distance from $n$ (the tool works this out exactly).
- Admissible means $h(n) \le h^*(n)$ for every place: guess ≤ truth.
- Consistent means $h(n) \le c(n, n') + h(n')$ for every road, where $c(n, n')$ is the length of the road from $n$ to
  its neighbour $n'$: "my guess here is no more than the road ahead plus my guess from the next place".

**Tiny example.** At town Y the guess is $h = 8$ and the true remaining distance is 11. Since $8 \le 11$, the guess is
fine there. If town S had $h = 19$ but the true distance was 17, the guess overestimates ($19 > 17$), so it isn't
admissible.

**How long it takes.** The checks are one quick pass over the map: one comparison per place for admissible, one
per road for consistent. The slow part is finding the true distances, which this tool can only do because the map is
small. For a real puzzle with billions of positions, you prove a guess is admissible by reasoning about it instead.

**Words to know**
- **Heuristic**: Rule-of-thumb estimate.
- **Dominates**: One admissible guess is always at least as high as another, which makes it more informative (closer to the truth) and so more useful.
""",
    # ------------------------------------------------------------------ propositional logic
    "truth_table": r"""
**The idea.** In logic, each basic statement (called a **symbol**, like $A$ = "it is raining") is either true or
false. A **truth table** tries every possible combination, like checking every position of a row of light switches,
and works out whether a bigger statement is true in each.

**Step by step.**
1. List every combination of true/false for the symbols.
2. For each row, work out the value of the whole formula.
3. Count the rows where it comes out true.

**The maths, symbol by symbol.**

| Symbol | Read it as | True when… |
|---|---|---|
| $\lnot A$ | not A | A is false |
| $A \land B$ | A and B | both are true |
| $A \lor B$ | A or B | at least one is true |
| $A \Rightarrow B$ | if A then B | every case except A true and B false |
| $A \Leftrightarrow B$ | A if and only if B | A and B have the same value |

Each symbol doubles the number of combinations, so $n$ symbols give $2^n$ rows: 3 symbols give $2 \times 2 \times 2 = 8$.

**Tiny example.** "If it rains, the grass is wet": $R \Rightarrow W$. The only row where this is false is
$R$ = true, $W$ = false (it rained but the grass is dry). The other 3 of the 4 rows make it true.

**How long it takes.** Every extra symbol doubles the work. 10 symbols give about a thousand rows, 20 about a
million, and 30 over a billion. That's why truth tables are only practical for small problems.

**Words to know**
- **Model**: One row (one complete set of true/false values).
- **Valid / tautology**: True in every row.
- **Satisfiable**: True in at least one row.
- **Unsatisfiable / contradiction**: True in none.
""",
    "cnf": r"""
**The idea.** Computers reason most easily about rules written in one standard shape: a list of conditions that must
**all** hold, where each condition says "at least **one** of these is true". It's like a checklist where every line is
a set of acceptable options. That shape is called **conjunctive normal form (CNF)**.

**Step by step.** Rewrite the formula using four tidy-up rules, in order:
1. Replace "if and only if" with two "if… then…" rules.
2. Replace "if A then B" with "not A, or B" (the two mean the same thing).
3. Push every "not" inwards until it sits directly on a symbol.
4. Rearrange so the result is an AND of ORs.

**The maths, symbol by symbol.**
- $A \Rightarrow B$ becomes $\lnot A \lor B$: "if A then B" is false only when A is true and B is false, and
  "not A, or B" is false in exactly the same case.
- **De Morgan's laws** move a "not" inside brackets and swap AND with OR: $\lnot(A \land B)$ becomes
  $\lnot A \lor \lnot B$ ("not both" = "at least one isn't").
- $\lnot\lnot A$ becomes $A$ (two nots cancel).

**Tiny example.** "If it's raining and I have no umbrella, I get wet": $(R \land \lnot U) \Rightarrow W$.
- Step 2: $\lnot(R \land \lnot U) \lor W$
- Step 3: $\lnot R \lor U \lor W$, which reads "it's not raining, **or** I have an umbrella, **or** I get wet". One
  clause, and it means exactly the same as the original rule.

**How long it takes.** Steps 1 to 3 are quick: they go through the formula once. Step 4 can explode:
"(A and B) or (C and D) or (E and F)" becomes 8 clauses, and every extra pair doubles that. Real solvers use a trick
that adds new symbols instead, which keeps the result small.

**Words to know**
- **Literal**: A symbol or its negation ($A$ or $\lnot A$).
- **Clause**: Literals joined by OR.
- **CNF**: Clauses joined by AND.
""",
    "entailment": r"""
**The idea.** You're a detective with a set of facts you know are true (the **knowledge base**, KB). A question is
**entailed** if it *must* be true whenever all your facts are true, with no way around it. This view checks that in
two ways.

**Method 1: check every possible world.** List every combination of true/false. Keep only the rows where all your
facts hold. If the question is true in every one of those rows, it's entailed. A single row where the facts hold but
the question doesn't is a **counter-example**: proof it doesn't follow.

**Method 2: proof by contradiction (resolution).** Assume the question is *false*, add that to your facts, and combine
clues until you reach a contradiction. If you do, the question must have been true.

**The maths, symbol by symbol.**
- $KB \models \alpha$: "the knowledge base entails $\alpha$" ($\alpha$, the Greek letter alpha, is the question).
- The **resolution rule** combines two clues that disagree about one symbol:
  from "A or B" and "not B or C", conclude "A or C". Either B is false (so A must be true), or B is true (so C must
  be).
- **□**, the empty clause, means "a contradiction": nothing can make it true.

**Tiny example.** Facts: "it's Tuesday or Wednesday" and "it isn't Wednesday, or I have gym". Resolving on Wednesday
gives "it's Tuesday or I have gym". Add "it isn't Tuesday" and "I don't have gym" and you reach □: so the facts
entail "Tuesday or gym".

**How long it takes.** Checking every model doubles with each extra symbol, like a truth table, but needs very
little memory: look at one row, then throw it away. Resolution can be much faster when a short proof exists, but in
the worst case it piles up a huge number of clauses.

**Words to know**
- **Entails**: Must follow.
- **Sound**: Only proves true things.
- **Complete**: Can prove everything that is true.
""",
    "chaining": r"""
**The idea.** Think of a recipe book of "if you have these, you can make that" rules: "flour and eggs ⇒ batter",
"batter and a pan ⇒ pancakes". Chaining uses rules like these to work out what's possible.

**Two directions.**
- **Forward chaining** starts from what's in your cupboard and keeps making whatever you can, until the thing you want
  appears (or nothing new can be made). Like dominoes falling.
- **Backward chaining** starts from what you want ("can I make pancakes?") and asks what you'd need, then what *that*
  needs, until it reaches things you already have.

**The maths, symbol by symbol.**
- A rule like $L \land M \Rightarrow P$ reads "if L and M are both true, then P is true".
- **Count**: for each rule, how many of its ingredients you're still missing. When it reaches 0, the rule "fires" and
  its result is added.
- **Agenda**: the queue of facts waiting to be used.

**Tiny example.** Rules: $A \land B \Rightarrow L$, $B \land L \Rightarrow M$, $L \land M \Rightarrow P$,
$P \Rightarrow Q$. You have $A$ and $B$. Forward: $A$ and $B$ give $L$; $B$ and $L$ give $M$; $L$ and $M$ give $P$;
$P$ gives $Q$. Backward: to get $Q$ I need $P$; for $P$ I need $L$ and $M$; $L$ comes from $A$ and $B$, which I have.

**How long it takes.** Forward chaining looks at each rule and fact only a fixed number of times, so twice as
many rules means about twice the work, never more. Backward chaining is often quicker still, because it ignores rules
that have nothing to do with the question.

**Words to know**
- **Fact**: Something known to be true.
- **Rule / definite clause**: "these together ⇒ that".
- **Fires**: A rule whose ingredients are all known adds its result.
""",
    # ------------------------------------------------------------------ SAT
    "dpll": r"""
**The idea.** You have a list of rules (clauses) and need to find true/false values that satisfy every one, or prove
that's impossible. It's like a Sudoku: you make a guess, fill in everything that guess forces, and rub it out if you
hit a contradiction. DPLL is that strategy done carefully.

**Step by step.**
1. **Any rule already broken?** Then this line of guesses is wrong: go back.
2. **All rules satisfied?** Done.
3. **Forced moves first.** If a rule has only one unfilled option left and everything else in it is false, that
   option must be true (a **unit clause**). If a symbol only ever appears in one form, set it that way (a
   **pure symbol**): it can only help.
4. **Otherwise guess.** Pick the next symbol, try *true*; if that fails, come back and try *false*.

**The maths, symbol by symbol.**
- A clause like $\lnot A \lor B$ ("not A, or B") is satisfied if *any one* of its parts is true.
- If $A$ = true, then $\lnot A$ is false, so the clause can only be saved by $B$: **B is forced to be true**.
- **Backtracking**: undo the most recent guess and try its other value.

**Tiny example.** Clauses: $(A \lor B)$, $(\lnot A \lor B)$, $(\lnot B \lor C)$, $(\lnot C \lor A)$. No rule is
forced at the start, so DPLL guesses $A$ = true. That satisfies the first and last clauses. In what's left, $C$ only
appears without a "not", so it's a pure symbol: $C$ = true. Then $(\lnot A \lor B)$ has one open option, so $B$ is
forced to be true. Every clause is satisfied after a single guess. (Paste these clauses into the DPLL view to see the
same steps.)

**How long it takes.** In the worst case it still tries every combination, doubling with each symbol. In
practice the shortcuts (stopping early, pure symbols and forced unit clauses) cut off most branches, and because it
only remembers one branch at a time it needs little memory.

**Words to know**
- **Satisfiable**: Some assignment makes every clause true.
- **Unit clause**: A clause with one open option left.
- **Pure symbol**: Appears only as $A$, never as $\lnot A$ (or the reverse).
""",
    "walksat_step": r"""
**The idea.** Instead of building an answer one piece at a time, WalkSAT starts with a complete (probably wrong)
answer and repairs it, like fixing a timetable by changing one thing at a time until there are no clashes.

**One step.**
1. Find a rule that's currently broken.
2. Flip a coin that lands "random" with probability $p$.
3. **Random:** change any one symbol in that rule. **Otherwise:** change the symbol that fixes the most rules overall.

Changing any symbol in a broken rule fixes that rule, but it might break others. That's why the greedy choice counts.

**The maths, symbol by symbol.**
- $p$: the probability of a random move, between 0 and 1. $p = 0$ means always greedy; $p = 1$ always random;
  $p = 0.5$ means a 50–50 chance.
- *Flip*: change a symbol from true to false or false to true.

**Tiny example.** Clauses: $(A \lor B)$, $(A \lor \lnot B)$, $(A \lor B \lor \lnot C)$, with $A$ = false, $B$ = false,
$C$ = true. Clauses 1 and 3 are broken. Pick clause 3 with $p = 0$ (greedy). Flipping $A$ satisfies all 3 clauses;
flipping $B$ or $C$ satisfies only 2. So WalkSAT flips $A$.

**How long it takes.** One step is quick: find the false clauses, then try flipping each symbol in the chosen
clause and count how many clauses become true. It only has to remember the current true/false values.

**Words to know**
- **Local search**: Improving a complete answer by small changes.
- **Greedy**: Always take the move that looks best right now.
""",
    "walksat_run": r"""
**The idea.** This repeats the WalkSAT step (find a broken rule, flip one symbol) over and over until every rule is
satisfied or it gives up after a set number of flips.

**Why the randomness?** A purely greedy fixer can get stuck going round in circles, where every single change makes
things look worse even though a better answer exists a few changes away. An occasional random move shakes it loose,
like stepping sideways to get round an obstacle.

**The maths, symbol by symbol.**
- $p$: chance of a random move on each step.
- *Max flips*: how many changes to try before giving up.
- *Seed*: a number that fixes the "random" choices, so the same seed always gives the same run.

**What it can and can't tell you.** If WalkSAT finds an answer, the answer is definitely right (you can check it). If
it gives up, that proves nothing: maybe there's no answer, or maybe it was unlucky. That's why it's called
**incomplete**, unlike DPLL, which can prove there's no answer.

**Tiny example.** Try the default puzzle with seed 0, then 1, then 2: the runs take different paths but all end with
every clause satisfied.

**How long it takes.** Each flip is quick, but nobody can say in advance how many flips a run will need: it's
partly luck. That's why there's a flip limit. Memory stays tiny however long it runs.

**Words to know**
- **Incomplete**: May fail to find an answer that exists.
- **Seed**: The starting point for the random choices.
""",
    # ------------------------------------------------------------------ FOL
    "unify": r"""
**The idea.** First-order logic talks about things and relationships, with **variables** as blanks to fill in, like
a form: "Knows(John, ___)". **Unification** asks: can two such expressions be made identical by filling in the blanks,
and with what?

**Step by step.** Compare the two expressions piece by piece:
1. Same word in the same place (e.g. both say *Knows*)? Good, carry on.
2. A blank (variable) facing something? Fill the blank with it.
3. Two different fixed words (e.g. *John* vs *Mary*)? They can never match: fail.

**The maths, symbol by symbol.**
- Lower-case words ($x$, $y$) are **variables**: blanks.
- Capitalised words are fixed: *John* (a thing), *Mother(y)* (a function: "the mother of y"), *Knows(x, y)*
  (a relationship).
- $\theta$ (theta) is the list of fillings, written $\{x / John\}$, meaning "put John wherever x appears".

**Tiny example.** Unify $Knows(John, x)$ with $Knows(y, Mother(y))$.
- First slot: $John$ vs $y$, so $y = John$.
- Second slot: $x$ vs $Mother(y)$, and $y$ is John, so $x = Mother(John)$.
- Both become $Knows(John, Mother(John))$: "John knows his mother".

**How long it takes.** Usually one pass through the two expressions, so longer expressions take proportionally
longer. The occur check adds a look inside a term each time a variable is bound, which is why fast systems such as
Prolog skip it.

**Words to know**
- **Substitution**: The list of fillings.
- **Most general unifier**: The filling that commits to as little as possible.
- **Occur check**: A blank can't be filled with something containing itself, like $x = Mother(x)$.
""",
    "fol_chaining": r"""
**The idea.** First-order rules apply to *everything* at once: "every missile is a weapon" covers every missile there
is. Chaining matches those general rules against specific facts to reach new conclusions.

**Step by step (forward).**
1. Look at each rule, such as "if x is a missile, then x is a weapon".
2. Find facts that fit its "if" part, filling in the blanks: "M1 is a missile" fits with x = M1.
3. Add the conclusion with the same filling: "M1 is a weapon".
4. Repeat, round after round, until the question is answered or nothing new appears.

Backward chaining works from the question instead: "is West a criminal? A rule says criminals are Americans who sell
weapons to hostile nations… so is West American? Is there a weapon he sold?…"

**The maths, symbol by symbol.**
- $Missile(x) \Rightarrow Weapon(x)$: for any $x$, if $x$ is a missile then $x$ is a weapon.
- $\land$ joins conditions that must all hold.
- Variables in a rule can be filled with anything, but the same variable gets the **same** filling everywhere in that
  rule.

**Tiny example.** Rules: $Missile(x) \Rightarrow Weapon(x)$ and the fact $Missile(M1)$. Filling $x = M1$ gives
$Weapon(M1)$ in round 1.

**How long it takes.** Forward chaining can only invent so many facts from a fixed set of names, so without
function symbols it always finishes. Each round, though, tries every way of matching a rule's premises to the facts,
which grows fast as rules get longer. Backward chaining needs little memory, but it can prove the same subgoal again
and again.

**Words to know**
- **Ground fact**: A fact with no blanks.
- **Round**: One pass applying every rule.
- **Fixed point**: A round that adds nothing new, so stop.
""",
    # ------------------------------------------------------------------ CSP
    "csp_backtracking": r"""
**The idea.** A **constraint problem** is a puzzle: some things to decide (**variables**), the options for each
(**domains**) and rules about which combinations are allowed (**constraints**). Colouring a map so no neighbours share
a colour is the classic example; so is a seating plan where certain people can't sit together.

**Step by step.**
1. Pick a variable to decide next.
2. Try one of its options.
3. Cross off options that now break a rule for its neighbours.
4. If some variable has no options left, undo the last choice and try another (**backtrack**).
5. Repeat until everything is decided.

**Three simple tricks make it fast.**
- **Do the hardest one first (MRV):** decide the variable with the fewest options left; if you're going to get stuck,
  find out early.
- **Break ties by the busiest (degree):** pick the one that affects the most others.
- **Be kind to neighbours (LCV):** try the option that rules out the fewest choices for others.

**Tiny example.** Colour Australia's map with red, green and blue. SA (South Australia) borders five regions, so it's
decided first: SA = red. That crosses red off all five neighbours, and from then on each choice is forced or easy, so
the whole map is coloured with no going back.

**How long it takes.** In the worst case it tries every combination: 3 colours for 7 regions is $3^7 = 2187$
assignments, and each extra region triples that. The ordering rules and inference don't change the worst case, but
they usually find dead ends so early that only a tiny fraction gets tried. Memory stays small, since it only
remembers the current partial answer.

**Words to know**
- **Variable**: Something to decide.
- **Domain**: Its possible values.
- **Constraint**: A rule between variables.
- **Backtrack**: Undo a choice that led to a dead end.
""",
    "csp_ac3": r"""
**The idea.** Before you start guessing, cross off any option that can **never** work. If my option has no possible
partner in a neighbouring variable, it's useless. AC-3 keeps crossing such options off until none are left.

**Step by step.**
1. For each pair of connected variables, X and Y, look at each option of X.
2. If no option of Y is compatible with it, cross it off X's list.
3. If X lost an option, recheck X's other neighbours, because they may have been relying on it.
4. Stop when nothing changes. If any list becomes empty, the puzzle has no solution.

**The maths, symbol by symbol.**
- $X \to Y$ (an **arc**): "check X's options against Y".
- An option is **supported** if at least one option of Y works with it.

**Tiny example.** X and Y can each be 1, 2 or 3, with the rule $X < Y$.
- X = 3 needs a bigger Y, but Y can't be 4, so cross off 3: X is now {1, 2}.
- Y = 1 needs a smaller X, but X can't be 0, so cross off 1: Y is now {2, 3}.
- Every remaining option has a partner, so AC-3 stops.

**How long it takes.** Each arc check compares every value of one variable with every value of the other, so
bigger domains slow it down quickly: twice as many values means up to eight times the work. It never tries whole
combinations, though, so it finishes quickly compared with a full search.

**Words to know**
- **Arc consistent**: Every option has a compatible partner.
- **Domain wipe-out**: A variable has no options left, so there is no solution.
""",
    # ------------------------------------------------------------------ games
    "games": r"""
**The idea.** In a two-player game like noughts and crosses, a good player thinks: "if I move here, what's my
opponent's best reply, and what's my best answer to that?" **Minimax** does exactly this, assuming the opponent always
plays their best.

**The game tree.** Start at the current position. Each branch is a move; the next level is the opponent's moves, and
so on. The bottom of the tree (the **leaves**) shows how good the final outcome is for you (MAX): higher is better.
Your opponent (MIN) wants it low.

**Step by step.** Work up from the bottom:
1. At your opponent's turn, they'll pick the **smallest** value below them.
2. At your turn, you pick the **largest**.
3. The value that reaches the top tells you how well you'll do, and which move gets you there.

**The maths, symbol by symbol.**
- $\max(3, 2, 2) = 3$: the biggest of the options.
- $\min(3, 12, 8) = 3$: the smallest.
- $\alpha$ (alpha): the best score *you* can already guarantee. $\beta$ (beta): the best score your *opponent* can
  already hold you to. When they cross, the rest of a branch can't matter.

**Tiny example.** You have 3 moves. After each, your opponent picks the lowest of their replies:
min(3, 12, 8) = 3, min(2, 4, 6) = 2, min(14, 5, 2) = 2. You pick the highest of those: max(3, 2, 2) = 3, so play the
first move. **Alpha-beta** notices that once your opponent can reach 2 in the second branch, which is already worse than
your 3, the 4 and 6 don't need checking.

**How long it takes.** Minimax looks at every possible game. With 35 moves per turn (about right for chess),
looking 4 turns ahead is $35^4 \approx 1.5$ million positions; 8 turns ahead is over 2 trillion. With good move
ordering, alpha-beta looks at roughly the square root of that, so it can see about twice as far ahead in the same
time. Both only remember the current line of play, so they need very little memory.

**Words to know**
- **Utility**: How good an ending is for MAX.
- **Ply**: One player's move.
- **Pruning**: Skipping branches that can't change the decision.
""",
    # ------------------------------------------------------------------ probability
    "bayes_rule": r"""
**The idea.** Bayes' rule updates a belief when new evidence arrives. The classic example: a medical test comes back
positive. How likely is it that you really have the condition? The surprising answer depends heavily on how **common**
the condition is.

**Tiny example (1,000 people).**
1. Start with how common it is: 1% of 1,000 people is **10** people who have it.
2. The test catches 90% of them: **9** true positives.
3. Of the **990** healthy people, 5% wrongly test positive: about **49.5** false positives.
4. So of about 58.5 positive tests, only 9 are real: $9 / 58.5 \approx$ **15%**.

**The maths, symbol by symbol.**

$$P(H \mid E) = \dfrac{P(E \mid H) \times P(H)}{P(E)}$$

- $P(H)$: the probability the hypothesis is true before any evidence (the **prior**): 0.01.
- $P(E \mid H)$: read "probability of E **given** H": how likely the evidence is if the hypothesis is true: 0.9.
- $P(E)$: how likely the evidence is overall, counting both true and false positives:
  $0.9 \times 0.01 + 0.05 \times 0.99 = 0.0585$.
- $P(H \mid E)$: the updated belief (the **posterior**): $0.009 / 0.0585 \approx 0.154$.

**Why it matters.** People tend to ignore how rare something is (the **base-rate fallacy**). A positive result from
a good test can still mean you're probably fine when the condition is rare.

**How long it takes.** Instantly: a few multiplications and one division, whatever the numbers are.

**Words to know**
- **Prior**: Belief before evidence.
- **Posterior**: Belief after.
- **Conditional probability** $P(A \mid B)$: Probability of A when we know B happened.
""",
    "bayes_net": r"""
**The idea.** A **Bayesian network** is a cause-and-effect diagram with probabilities. Arrows point from causes to
effects: a burglary or an earthquake can set off the alarm; the alarm can make your neighbours John and Mary call
you. Each circle has a small table saying how likely it is, given its causes.

**Step by step (answering a question).**
1. You observe something, e.g. "John and Mary both called".
2. To ask "was there a burglary?", consider every way the unknown parts could have gone (earthquake or not, alarm
   or not).
3. For each possibility, multiply the probabilities along the diagram to see how likely that whole story is.
4. Add up the stories with a burglary, add up those without, and compare.

**The maths, symbol by symbol.**
- $P(\text{Alarm} \mid \text{Burglary}, \lnot\text{Earthquake}) = 0.94$: "if there's a burglary and no earthquake,
  the alarm goes off 94% of the time". Each circle's table is a list of these.
- The probability of a whole story is the **product** of one table entry per circle:
  $P(b, \lnot e, a, j, m) = P(b) \times P(\lnot e) \times P(a \mid b, \lnot e) \times P(j \mid a) \times P(m \mid a)$.
- $\alpha$ (alpha) just rescales the two totals so they add up to 1.

**Tiny example.** The story "burglary, no earthquake, alarm, both call" has probability
$0.001 \times 0.998 \times 0.94 \times 0.9 \times 0.7 \approx 0.00059$. Summing all the stories gives a 28% chance of a
burglary once both neighbours have called: much higher than the 0.1% you started with.

**How long it takes.** Summing over the unknowns doubles the work for each hidden yes/no variable: 5 hidden
variables mean 32 terms, 30 mean over a billion. The network saves a lot of storage, though: the burglary example
needs 10 numbers instead of 31.

**Words to know**
- **Node**: One variable (circle).
- **Parent**: A direct cause.
- **CPT (conditional probability table)**: A node's probabilities given its parents.
- **Evidence**: What you've observed.
""",
    "joint": r"""
**The idea.** The **full joint distribution** is one big table listing every possible combination of facts and how
likely each is. Every question can be answered from it just by adding up the right rows.

**Step by step.**
1. Keep only the rows that match what you know (the **evidence**).
2. Add up the ones where your question is true, and separately the ones where it's false.
3. Divide each by the total of the kept rows so they add up to 1.

**The maths, symbol by symbol.**
- Each row's number is the probability of that exact combination; all rows together add up to 1.
- **Marginalising** (or "summing out"): adding rows together to ignore a variable you don't care about.
- **Normalising**: dividing by the total so the answers form proper probabilities. $\alpha$ (alpha) is shorthand for
  "1 divided by the total".

**Tiny example.** You have a toothache. Rows with a toothache *and* a cavity: $0.108 + 0.012 = 0.12$. Rows with a
toothache and *no* cavity: $0.016 + 0.064 = 0.08$. So the chance of a cavity is $0.12 / (0.12 + 0.08) = 0.6$, or 60%.

**The catch.** With 30 yes/no facts the table would need over a billion rows. That's why Bayesian networks exist:
they store the same information far more compactly.

**How long it takes.** Answering a question means reading the table, and the table doubles with every yes/no
variable: 10 variables need 1,024 rows, 30 need over a billion. Both the time and the storage blow up, which is why
real systems use Bayesian networks instead.

**Words to know**
- **Joint distribution**: Probabilities of every combination.
- **Evidence**: The facts you condition on.
- **Normalise**: Rescale so things add up to 1.
""",
    "naive_bayes": r"""
**The idea.** A spam filter sees words like "free", "winner" and "click". Each word is a clue: "free" turns up much
more in spam than in normal email. **Naive Bayes** combines all the clues by multiplying how strongly each one points
to each class, and picks the class with the highest score.

**Step by step.**
1. Count how often each class appears in the training data (e.g. 9 of 14 days were good for playing outside).
2. For each class, count how often each clue value appears with it (e.g. "sunny" on 2 of those 9 days).
3. For a new example, multiply the class's frequency by the frequency of each of its clue values.
4. The class with the biggest product wins.

**The maths, symbol by symbol.**

$$\text{score}(c) = P(c) \times P(x_1 \mid c) \times P(x_2 \mid c) \times \dots$$

- $P(c)$: how common class $c$ is overall.
- $P(x_1 \mid c)$: how often clue value $x_1$ appears when the class is $c$.
- "Naive" because it pretends the clues don't influence each other, which is rarely true but works surprisingly well.

**Tiny example.** On the weather data, "play = yes" on 9 of 14 days, and "outlook = sunny" on 2 of those 9. So its
score starts $\frac{9}{14} \times \frac{2}{9} \approx 0.14$, and each further clue multiplies in.

**A pitfall.** If a clue value never appeared with a class, its frequency is 0 and wipes out the whole product.
**Laplace smoothing** adds 1 to every count so nothing is ever exactly 0.

**How long it takes.** Training is one pass through the data, counting. Predicting is one multiplication per
attribute per class. Twice the data means twice the training time and no change at all to the prediction time, which
is why naive Bayes copes with millions of emails.

**Words to know**
- **Class**: The label to predict.
- **Attribute / feature**: A clue.
- **Smoothing**: Adjusting counts to avoid zeros.
""",
    # ------------------------------------------------------------------ ML
    "kmeans": r"""
**The idea.** You have a pile of unlabelled points and want to sort them into $k$ groups of similar ones, like sorting
a bag of mixed sweets into piles without being told the flavours. **k-means** does it by repeatedly moving each pile's
centre to the middle of its sweets.

**Step by step.**
1. Pick $k$ starting centres (for example, $k = 2$).
2. **Assign:** each point joins its **nearest** centre.
3. **Update:** move each centre to the **average** position of its points.
4. Repeat steps 2 and 3 until the centres stop moving.

**The maths, symbol by symbol.**
- **Distance** between points $(x_1, y_1)$ and $(x_2, y_2)$ is Pythagoras: $\sqrt{(x_1 - x_2)^2 + (y_1 - y_2)^2}$.
- The **average** (mean) of points: average the x values, and separately average the y values.
- $k$: how many groups you ask for. You choose it; the algorithm doesn't.

**Tiny example.** The distance from $(0, 0)$ to $(3, 4)$ is $\sqrt{3^2 + 4^2} = \sqrt{25} = 5$. If a group contains
$(1, 1)$ and $(1.5, 2)$, its new centre is $\left(\frac{1 + 1.5}{2}, \frac{1 + 2}{2}\right) = (1.25, 1.5)$.

**Good to know.** Different starting centres can give different groupings, so it's common to run it a few times and
keep the best. It also works best when groups are roughly round blobs of similar size.

**How long it takes.** Each round measures the distance from every point to every centre: 1,000 points and 5
centres is 5,000 distances per round. Twice the points, or twice the centres, means twice the work. It usually
settles within a few rounds.

**Words to know**
- **Cluster**: A group.
- **Centroid**: The average point of a group.
- **Unsupervised**: No correct answers are given; the algorithm finds structure on its own.
""",
    "knn": r"""
**The idea.** To guess something about a new house, look at the most similar houses you already know about. **k-nearest
neighbour** classifies a new point by asking its $k$ closest neighbours to vote.

**Step by step.**
1. Measure the distance from the new point to every known example.
2. Take the $k$ closest.
3. The most common label among them wins.

**The maths, symbol by symbol.**
- **Distance**: straight-line (Pythagoras), $\sqrt{(x_1 - x_2)^2 + (y_1 - y_2)^2}$.
- $k$: how many neighbours vote. An odd number avoids ties between two classes.
- **Normalising**: rescale each measurement to between 0 and 1 using
  $\frac{\text{value} - \text{smallest}}{\text{largest} - \text{smallest}}$, so a measurement in big units (like
  salary) doesn't drown out one in small units (like age).

**Tiny example.** With $k = 3$, the new point's three nearest neighbours are labelled *a*, *a* and *b*. Two votes beat
one, so it's classified as *a*.

**Choosing $k$.** $k = 1$ copies the single nearest example, so one odd example can mislead it. A very large $k$
ignores local detail. Something in between usually works best.

**How long it takes.** "Training" takes no time at all: it just keeps the examples. Every question is slow
instead, because it measures the distance to every example: twice as much data means twice as long per prediction,
and all of it has to stay in memory.

**Words to know**
- **Training example**: A point with a known label.
- **Lazy learning**: No training step; all the work happens when you ask a question.
""",
    "linear_regression": r"""
**The idea.** You have some points on a graph (say, house size against price) and want the **straight line that fits
them best**, so you can predict new values. Linear regression finds that line.

**Step by step.**
1. A straight line has two numbers: where it crosses the y-axis, and how steep it is.
2. For any line, measure how far each point is above or below it (the **error** or **residual**).
3. Square each error (so negatives don't cancel positives, and big misses count extra) and add them up.
4. The best line is the one that makes that total as small as possible. There's a formula for it, so no guessing
   is needed.

**The maths, symbol by symbol.**
- $y = w_0 + w_1 x$: the line.
  - $w_0$: the **intercept**, the value of $y$ when $x = 0$.
  - $w_1$: the **slope**, how much $y$ goes up when $x$ goes up by 1.
- Residual: $y - (w_0 + w_1 x)$, the actual value minus the predicted one.
- $\sum$ (sigma) means "add up over all points". The loss is $\sum (\text{residual})^2$.

**Tiny example.** For the points (1, 3), (2, 5), (3, 7), (4, 10), the best line is $y = 0.5 + 2.3x$. At $x = 2$ it
predicts $0.5 + 2.3 \times 2 = 5.1$; the real value is 5, so the residual is $-0.1$.

**How long it takes.** One pass through the data to add up four totals, so twice the points take twice as long,
and it needs almost no memory beyond the data. With many inputs the formula means solving a set of equations, which
gets slow when there are thousands of inputs.

**Words to know**
- **Regression**: Predicting a number.
- **Fit**: Choosing the line.
- **Least squares**: Making the sum of squared errors as small as possible.
""",
    "gradient_descent": r"""
**The idea.** Imagine standing on a foggy hillside, trying to reach the bottom of the valley. You can't see far, but
you can feel which way the ground slopes. So you take a step downhill, feel again, and repeat. **Gradient descent**
finds the best settings for a model the same way: the "height" is how wrong the model is, and each step makes it a
little less wrong.

**Step by step.**
1. Start with any settings (weights), for example all zero.
2. Work out which direction makes the error go down, and how steep it is.
3. Take a small step that way.
4. Repeat until the error stops shrinking.

**The maths, symbol by symbol.**

$$w \leftarrow w - \alpha \times \text{slope}$$

- $w$: a setting of the model (a **weight**).
- $\leftarrow$: "replace with".
- slope (the **gradient**): how much the error changes if $w$ increases a little. Positive slope: go down by
  decreasing $w$; negative slope: increase $w$.
- $\alpha$ (alpha): the **learning rate**, the size of each step.

**Tiny example.** $w = 0$, the slope there is $-10$ (error falls as $w$ rises), and $\alpha = 0.1$. Then
$w \leftarrow 0 - 0.1 \times (-10) = 1$: the weight moves up to 1.

**The learning rate matters.** Too small and you shuffle forever. Too big and you leap right over the valley and
land higher up the other side, getting worse each step. Try it on the chart.

**How long it takes.** Each batch step looks at every example once, so twice the data means each step takes
twice as long. A stochastic step looks at only one example, which is why it's used on huge datasets. How many steps
you need depends mostly on the learning rate, not on the amount of data.

**Words to know**
- **Loss / error**: How wrong the model is.
- **Gradient**: The slope of the loss.
- **Epoch**: One pass through all the data.
""",
    "logistic": r"""
**The idea.** Sometimes you want a **probability**, not just a number: "how likely is this email to be spam?" Logistic
regression computes a score, then squashes it into the range 0 to 1 with an S-shaped curve, so it can be read as a
probability.

**Step by step.**
1. Compute a score as a weighted sum: $w_0 + w_1 x$.
2. Push it through the S-curve (the **logistic** or **sigmoid** function).
3. Read the result as a probability. Above 0.5, predict "yes"; below, "no".

**The maths, symbol by symbol.**

$$\sigma(z) = \dfrac{1}{1 + e^{-z}}$$

- $z$: the score.
- $e$: a mathematical constant (about 2.718); $e^{-z}$ is tiny when $z$ is large and huge when $z$ is very negative.
- $\sigma$ (sigma): the S-curve. A big positive score gives nearly 1, a big negative score gives nearly 0, and a
  score of 0 gives exactly 0.5.

**Tiny example.** $\sigma(0) = \frac{1}{1 + 1} = 0.5$. $\sigma(2) \approx 0.88$, so 88% likely. $\sigma(-2) \approx
0.12$. With weights $w_0 = -4$ and $w_1 = 1.5$, the score at $x = 3$ is $-4 + 1.5 \times 3 = 0.5$, giving
$\sigma(0.5) \approx 0.62$.

**Where the line is drawn.** The prediction flips from "no" to "yes" exactly where the score is 0, here at
$x = 4 / 1.5 \approx 2.67$.

**How long it takes.** A prediction is one multiply-and-add per input, then one sigmoid. Training repeats that
for every example, many times over, so its cost depends on how many passes it takes to settle.

**Words to know**
- **Sigmoid / logistic function**: The S-curve.
- **Classifier**: A model that predicts a category.
- **Decision boundary**: Where the prediction switches.
""",
    "neuron": r"""
**The idea.** An artificial **neuron** makes a simple decision from several inputs, like deciding whether to go out:
each factor (sunny? free time? friends going?) gets a weight for how much it matters, you add them up, and if the
total is high enough you go.

**Step by step.**
1. Multiply each input by its weight.
2. Add them up, plus a **bias** (a starting nudge up or down).
3. Pass the total through an **activation function**, which decides the output.

**The maths, symbol by symbol.**
- $x_1, x_2$: the inputs.
- $w_1, w_2$: their **weights** (how much each counts; negative weights count against).
- $w_0$: the **bias**.
- $in = w_0 + w_1 x_1 + w_2 x_2$: the total.
- Activation functions:
  - **Threshold**: output 1 if $in \ge 0$, otherwise 0. A yes/no decision.
  - **Logistic**: a smooth S-curve from 0 to 1.
  - **ReLU**: $\max(0, in)$, which keeps positive totals and turns negatives into 0.

**Tiny example (an AND gate).** Weights $w_0 = -1.5$, $w_1 = 1$, $w_2 = 1$ with a threshold.
- Inputs 1 and 1: $-1.5 + 1 + 1 = 0.5 \ge 0$, so output **1**.
- Inputs 1 and 0: $-1.5 + 1 + 0 = -0.5 < 0$, so output **0**.

It only says "yes" when both inputs are 1, which is exactly AND.

**How long it takes.** One multiplication and one addition per input, then the activation. A neuron with 100
inputs does about 100 of each; big networks are billions of these simple steps.

**Words to know**
- **Weight**: Importance of an input.
- **Bias**: A built-in offset.
- **Activation**: The rule that turns the total into an output.
""",
    "perceptron": r"""
**The idea.** A **perceptron** is a single neuron that learns from its mistakes. Show it an example; if it gets it
right, do nothing. If it gets it wrong, nudge the weights so it would be closer to right next time. Repeat.

**Step by step.**
1. Start with some weights (often all zero).
2. For each example, compute the neuron's answer.
3. If it said 0 but should have said 1, increase the weights of the inputs that were on. If it said 1 but should have
   said 0, decrease them.
4. Go through all the examples again (another **epoch**) until it makes no mistakes.

**The maths, symbol by symbol.**

$$w_i \leftarrow w_i + \alpha \times (y - h) \times x_i$$

- $y$: the correct answer. $h$: what the neuron said.
- $y - h$: $+1$ if it should have said more, $-1$ if less, $0$ if right (so no change).
- $x_i$: the input. Only inputs that were switched on get adjusted.
- $\alpha$: the learning rate (how big the nudge is).

**Tiny example.** Weights $[0, 0, 0]$, $\alpha = 0.5$. Example: inputs $(1, 1)$, correct answer 0. The total is
$0 + 0 \times 1 + 0 \times 1 = 0$, and the threshold says 1 when the total is $\ge 0$, so the neuron answers 1: wrong.
Then $y - h = 0 - 1 = -1$, so each weight changes by $0.5 \times (-1) \times x_i = -0.5$ (the bias counts as an input
that is always 1). The new weights are $[-0.5, -0.5, -0.5]$, and the same example now gives a total of $-1.5$, so the
answer becomes 0: fixed.

**Its limit.** A perceptron draws one straight line to separate "yes" from "no". If no straight line can do it, as with
XOR ("one or the other but not both"), it never learns. Try XOR's labels `0 1 1 0` to see.

**How long it takes.** Each example costs one prediction and, if it was wrong, one update: a few operations per
weight. When the classes are far apart it learns in a few epochs; when they nearly touch it needs many more, and on
XOR it never finishes, which is why you set an epoch limit.

**Words to know**
- **Epoch**: One pass through all the examples.
- **Linearly separable**: A straight line can split the classes.
""",
    "network": r"""
**The idea.** A single neuron can only draw a straight line. Connect many in **layers**, where the outputs of one
layer become the inputs of the next, and the network can learn curved, complicated patterns. Training it means
working out how much each connection was to blame for a mistake.

**Step by step.**
1. **Forward pass:** feed in the inputs; each layer computes its neurons' outputs and passes them on; the last layer
   gives the prediction.
2. **Compare** the prediction with the right answer.
3. **Backward pass (back-propagation):** work backwards through the layers, sharing out the blame for the error.
   Neurons with strong connections to a wrong output get more of the blame.
4. **Adjust** every weight a little to reduce its share of the error.

**The maths, symbol by symbol.**
- $a$: a neuron's output (**activation**).
- $\Delta$ (delta): a neuron's share of the blame.
  - For the output: $\Delta = a(1 - a) \times (\text{target} - a)$. The $a(1 - a)$ part is how sensitive the
    S-curve is at that point.
  - For a hidden neuron: its $\Delta$ is the blame of the neurons it feeds, weighted by its connections to them.
- Each weight changes by $\alpha \times (\text{input along that connection}) \times \Delta$.

**Tiny example.** With the default network, inputs $(1, 0)$ produce an output of about 0.62, but the target is 1. The
output's blame is $0.62 \times 0.38 \times 0.38 \approx 0.09$, so the weights feeding it are increased slightly to push
the output up next time.

**How long it takes.** The forward pass does one multiplication per weight, and back-propagation costs about the
same again going backwards. So one training step costs only a small multiple of a prediction, however many weights
there are, and that is what makes training networks with billions of weights possible.

**Words to know**
- **Hidden layer**: A layer between input and output.
- **Forward pass**: Computing the prediction.
- **Back-propagation**: Passing the error backwards to update weights.
""",
    "cnn": r"""
**The idea.** To spot a cat in a photo, you don't need to look at every pixel separately. A **convolutional network**
slides a small window (a **filter**) across the image, checking each patch for a pattern such as an edge or a corner,
like running a magnifying glass over a picture.

**Step by step.**
1. Take a small filter, e.g. 3 × 3 pixels.
2. Place it on the top-left corner of the image and compute one number from the patch underneath.
3. Slide it along one step and repeat, row by row, until it has covered the image.
4. The grid of results is a map of where that pattern appears. Using several filters gives several maps.

**The maths, symbol by symbol.**
- **Output size** (sliding one pixel at a time, no padding): $\text{image size} - \text{filter size} + 1$ along each
  side.
- **Stride**: how many pixels the filter jumps each step. **Padding**: a border of zeros added round the image.
- **Weights per filter**: one per value it looks at, plus one bias:
  $\text{width} \times \text{height} \times \text{depth} + 1$.
- **Weight sharing**: the same filter is reused at every position, so those weights are counted once, not once per
  position.

**Tiny example.** A 5 × 5 image with a 3 × 3 filter: $5 - 3 + 1 = 3$, so the output is 3 × 3 (9 positions). For a
colour image (depth 3), each filter has $3 \times 3 \times 3 + 1 = 28$ weights, and those same 28 are used at all 9
positions.

**How long it takes.** Every output value is one filter applied to one patch: a $3 \times 3$ filter over 3
colour channels is 27 multiplications. A $32 \times 32$ output with 16 filters has $32 \times 32 \times 16 = 16{,}384$
values, so about 440,000 multiplications. Sharing weights keeps the *storage* small, but the *work* still grows with
the size of the image.

**Words to know**
- **Filter / kernel**: The small sliding window of weights.
- **Feature map**: The grid of results from one filter.
- **Channel / depth**: Layers of the input, e.g. red, green and blue.
""",
}
