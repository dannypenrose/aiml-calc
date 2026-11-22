"""'When and where to use this': when each algorithm is the right tool, where it shows up in the real world,
and where software engineers meet it. Shown in each view's third panel."""

from __future__ import annotations

USES: dict[str, str] = {
    "search_trace": """
**Use it when** you can describe the problem as states connected by actions with costs, and you need a path from a
start to a goal. Pick **A\\*** when you have a good estimate of the remaining cost, **uniform-cost** when you don't,
**BFS** when every step costs the same, and **iterative deepening** or **IDA\\*** when memory is tight.
**Don't use it** when the state space is too large to explore and you'd accept a good-enough answer: local search
or sampling is usually better there.

**Real world**
- Sat-nav and map apps finding driving routes (shortest-path search with heuristics such as straight-line distance).
- Robots and games planning movement around obstacles: A\\* is the standard pathfinding algorithm in game engines.
- Solving puzzles such as the 8-puzzle or Rubik's cube, where each move is an action.

**In software engineering**
- Network routing: link-state protocols such as OSPF compute shortest paths with Dijkstra's algorithm (uniform-cost search).
- Garbage collectors mark live objects by traversing the object graph from its roots.
- Version control: tools like git walk the commit graph to find ancestors and merge bases.
- Web crawlers and "degrees of separation" features explore graphs breadth-first.
""",
    "search_heuristic": """
**Use it when** you're designing a heuristic for A\\* or IDA\\* and need to know whether it keeps the search optimal,
or which of two heuristics will search less. **Admissible** is enough for tree search; graph search needs
**consistent**.
**Don't bother** if you only need *a* path, not the cheapest: greedy search with any heuristic may be enough.

**Real world**
- Map routing uses straight-line distance, which can never overestimate road distance.
- Grid pathfinding in games uses Manhattan or diagonal distance to match how units can move.
- Puzzle solvers derive heuristics from relaxed versions of the rules (for example "tiles can slide through each other").

**In software engineering**
- Planning and scheduling engines use admissible estimates to prune options without losing the best plan.
- The same "never overestimate" idea appears in lower bounds for branch-and-bound optimisation.
- Comparing heuristics is a form of performance tuning: a dominating heuristic means fewer nodes and less memory.
""",
    "truth_table": """
**Use it when** a problem has a handful of true/false inputs and you need a definite answer: is this condition always
true, ever true, or equivalent to another one?
**Don't use it** with more than about 20 symbols: the table doubles with each one, so DPLL or a SAT solver takes over.

**Real world**
- Digital circuit design: every logic gate and small circuit is specified by its truth table.
- Rule checking in contracts or regulations: listing every combination of conditions to spot gaps.

**In software engineering**
- Refactoring a tangled `if` condition: prove the new version is equivalent by checking every combination.
- Decision tables in requirements and test design, so every combination of flags gets a test case.
- Checking feature-flag combinations for states that should be impossible.
""",
    "cnf": """
**Use it when** you're feeding a logical problem to a SAT solver or a resolution prover: they all take CNF as input.
**Watch out** for the size: distributing ∨ over ∧ can blow up exponentially, so real tools use the Tseitin encoding,
which adds helper variables to stay small.

**Real world**
- Hardware verification encodes circuits as CNF to check them with SAT solvers.
- Planning and scheduling problems are often compiled into CNF and handed to a solver.

**In software engineering**
- DIMACS CNF is the standard file format every SAT solver reads.
- Package managers such as conda and openSUSE's zypper (via libsolv) turn dependency rules into SAT problems.
- Configuration tools turn "if feature A then not feature B" rules into clauses to check a configuration is valid.
""",
    "entailment": """
**Use it when** you need certainty that a conclusion follows from what you know, not just that it's likely.
Model checking is simplest for small problems; resolution scales to larger ones and underpins automated theorem
proving.
**Don't use it** for uncertain knowledge: if your facts are only probably true, use probability instead.

**Real world**
- Automated theorem provers check mathematical proofs and the correctness of designs.
- Legal and policy reasoning: does this set of rules allow that action?

**In software engineering**
- Access-policy analysis: tools reason over cloud access policies (AWS's Zelkova uses SMT solvers) to prove whether
  a resource can ever become public.
- Static analysers and verifiers prove assertions hold on every execution path.
- Query optimisers check whether one condition implies another so a filter can be dropped.
""",
    "chaining": """
**Use it when** your knowledge is a set of "if these, then that" rules. Use **forward chaining** to react to new facts
and derive everything that follows; use **backward chaining** to answer one specific question efficiently.
**Don't use it** when rules need negation or "or" in their conclusions: definite clauses can't express them.

**Real world**
- Expert systems: MYCIN diagnosed infections by backward chaining from possible diagnoses.
- Business rules engines (such as Drools) forward-chain to react as new data arrives.

**In software engineering**
- Prolog runs programs by backward chaining.
- Build tools like `make` work backwards from a target to the prerequisites it needs.
- Datalog-based code analysis (CodeQL's language compiles to a Datalog-style engine) derives facts about code from rules.
""",
    "dpll": """
**Use it when** you need to find a satisfying assignment or prove none exists, and you need the guarantee: DPLL is
complete. Modern solvers are its descendants (CDCL adds clause learning) and handle millions of variables.
**Don't use it** for huge satisfiable problems where any decent answer will do: local search such as WalkSAT can
be faster.

**Real world**
- Chip makers verify hardware designs with SAT-based model checking.
- Timetabling and scheduling problems are solved by encoding them as SAT.

**In software engineering**
- SAT solvers such as MiniSat, Glucose and CaDiCaL are DPLL with clause learning.
- Dependency resolution in package managers, and test-input generation for hard-to-reach code paths.
- Bounded model checking: unrolling a program a few steps and asking a SAT solver for a bug.
""",
    "walksat_step": """
**Use it when** you want to understand local search: start from a complete guess and repair it one change at a time,
mixing greedy moves with random ones to escape dead ends.
**Don't use it** when you must prove there's no solution: local search can't.

**Real world**
- Rostering and timetabling tools repair a draft schedule one swap at a time.
- Delivery and logistics planners improve routes by small local changes.

**In software engineering**
- The "greedy plus occasional random move" idea appears in many optimisers, from simulated annealing to
  random-restart hill climbing.
- Tuning configurations (compiler flags, database parameters) by local search when trying everything is impossible.
""",
    "walksat_run": """
**Use it when** the problem is large, probably satisfiable, and you want a solution fast. Local search often finds one
far sooner than complete methods.
**Don't use it** to show a problem has no solution: if WalkSAT gives up, you've learned nothing.

**Real world**
- Large scheduling and planning problems where a quick valid answer matters more than a guarantee.
- Approximate solving of MAX-SAT (satisfy as many constraints as possible) in configuration problems.

**In software engineering**
- Seeded randomness makes a randomised algorithm reproducible: the same seed gives the same run, which matters for
  debugging and tests.
- Random restarts are a standard trick for avoiding bad starting points in optimisation.
""",
    "unify": """
**Use it when** you need to match patterns that contain variables, and work out what the variables must be.
It's the core operation of logic programming, first-order theorem proving and type inference.
**Remember** to rename variables apart first when the two expressions come from different rules.

**Real world**
- Theorem provers and proof assistants match rules against goals by unification.
- Knowledge-base query engines match questions like "who does John know?" against stored facts.

**In software engineering**
- Type inference in ML-family languages such as Haskell and OCaml (Hindley–Milner) solves type equations by unification.
- Prolog's execution is unification plus backtracking.
- Pattern matching in rewrite systems and some query languages works the same way.
""",
    "fol_chaining": """
**Use it when** your rules are general ("every missile is a weapon") and your facts are about specific things, and
you want to derive conclusions automatically. Forward chaining suits deriving everything from a database;
backward chaining suits answering one query.
**Don't use it** for knowledge with exceptions or uncertainty without extending it, and watch backward chaining
on recursive rules, which can loop forever.

**Real world**
- Knowledge graphs and ontology reasoners derive new relationships from stated ones.
- Eligibility and compliance systems apply general rules to individual cases.

**In software engineering**
- Datalog engines (such as Soufflé, used by the Doop analyser for Java points-to analysis) forward-chain over code facts.
- Policy languages: Open Policy Agent's Rego is inspired by Datalog.
- Prolog-style backward chaining powers some configuration and expert tools.
""",
    "csp_backtracking": """
**Use it when** you're choosing values for variables that must satisfy rules between them: schedules, timetables,
assignments, layouts, puzzles. MRV, LCV and forward checking turn hopeless searches into fast ones.
**Don't use it** for problems that are mostly about optimising a number (cost, profit): add optimisation or use
integer programming.

**Real world**
- University and school timetabling, staff rostering and sports fixture scheduling.
- Sudoku and similar puzzles are textbook constraint problems.

**In software engineering**
- Compilers allocate CPU registers by colouring an interference graph, the same problem as map colouring.
- Constraint solvers such as Google OR-Tools (CP-SAT) are used for scheduling and planning in production.
- Product configurators check that chosen options are compatible.
""",
    "csp_ac3": """
**Use it when** you want to shrink a constraint problem before (or during) search by removing values that can never
work. It's cheap, and sometimes solves the problem outright.
**Remember** it can't always tell whether a solution exists: arc consistency doesn't guarantee a solution.

**Real world**
- Sudoku solvers do this when they cross off candidates a cell can't take.
- Scheduling tools prune impossible time slots before assigning anything.

**In software engineering**
- Constraint propagation is the engine inside constraint solvers.
- Dependent form fields work the same way: choosing a country narrows the valid regions, and an empty list signals
  an impossible combination.
""",
    "games": """
**Use it when** two players take turns, each wants the opposite outcome, and you can evaluate positions.
Alpha-beta gets the same answer as minimax while searching far fewer positions, especially with good move ordering.
Use expectiminimax when dice or other chance events are involved.
**Don't use it** for games with huge branching and no good evaluation (Go was the classic case), where Monte Carlo
tree search and learned evaluations work better.

**Real world**
- Classic chess engines are built on alpha-beta search with heavy refinements.
- AI opponents for turn-based games such as draughts, Connect Four and noughts and crosses.

**In software engineering**
- Turn-based game features in apps and websites use minimax for their computer player.
- The adversarial mindset ("assume the other side plays its best") underpins security threat modelling.
""",
    "bayes_rule": """
**Use it when** you need to update a belief with evidence, especially when the thing you're testing for is rare:
the base rate matters as much as the test.
**Watch out** when evidence isn't independent: combining several pieces naively can overstate your confidence.

**Real world**
- Medical tests: what a positive result actually means depends on how common the condition is.
- Fraud and security alerts: with a rare event, even an accurate detector produces mostly false alarms.

**In software engineering**
- Monitoring and alerting: a low base rate of real incidents is why noisy alerts get ignored, and Bayes' rule shows
  how precision depends on it.
- Interpreting A/B tests and anomaly detectors in terms of how likely a flagged result is to be real.
- Spam filters combine word evidence with Bayes' rule.
""",
    "bayes_net": """
**Use it when** several uncertain factors influence each other through causes and effects, and you want to reason in
any direction: from causes to effects or from symptoms back to causes.
**Don't use** exact enumeration on large networks: it's exponential. Real tools use variable elimination or sampling.

**Real world**
- Medical diagnosis systems relate diseases, risk factors and symptoms.
- Fault diagnosis in machinery, networks and vehicles, and risk models in insurance and finance.

**In software engineering**
- Root-cause analysis: given which alerts fired, which component most likely failed?
- Troubleshooting assistants that choose the next question to ask based on what's most informative.
- The chain-rule factorisation is the same idea behind probabilistic programming libraries.
""",
    "joint": """
**Use it when** there are only a few variables and you have, or can estimate, the probability of every combination.
It's the reference answer for any probability question.
**Don't use it** beyond a handful of variables: the table doubles with each one.

**Real world**
- Contingency tables in medicine and social science (for example symptom versus disease counts).
- Market research cross-tabulations: purchase rates by age group and region.

**In software engineering**
- Analytics: computing P(error | browser) or conversion rate by segment from event counts is exactly this, with
  counts in place of probabilities.
- Building small lookup tables of conditional rates for feature flags or routing decisions.
""",
    "naive_bayes": """
**Use it when** you need a fast, simple classifier, especially for text: it trains in one pass, needs little data and
gives a strong baseline.
**Don't trust** its probabilities too much: the independence assumption makes them overconfident even when the
predicted class is right.

**Real world**
- Spam filtering: Paul Graham's influential "A Plan for Spam" used this approach.
- Sorting documents by topic, sentiment analysis and simple medical screening.

**In software engineering**
- A quick baseline for triaging support tickets or bug reports into categories before trying heavier models.
- Classifying log lines or commit messages.
- Laplace smoothing is a general fix whenever counts can be zero.
""",
    "kmeans": """
**Use it when** you want to group unlabelled data into a chosen number of compact, roughly round clusters.
It's fast and simple and scales to large data.
**Don't use it** for clusters of very different sizes, odd shapes or with many outliers: try DBSCAN or Gaussian
mixtures instead. Always scale your features first.

**Real world**
- Customer segmentation for marketing.
- Image colour quantisation: reducing a photo to k representative colours.
- Grouping similar documents or news stories.

**In software engineering**
- Vector quantisation, used to compress embeddings in large-scale similarity search.
- Grouping similar error reports or log patterns to spot recurring issues.
- Choosing representative test cases or data samples.
""",
    "knn": """
**Use it when** "similar things behave similarly" holds and you can measure similarity. There's no training step,
it handles many classes, and its predictions are easy to explain ("these 5 examples were closest").
**Don't use it** with many irrelevant features or very large datasets without an index: prediction gets slow, and
in high dimensions everything is roughly equally far apart.

**Real world**
- Recommendations: "customers like you also bought".
- Handwriting and image recognition baselines; detecting unusual transactions that have no close neighbours.

**In software engineering**
- Vector databases and semantic search (including retrieval for RAG systems) are nearest-neighbour search,
  made fast with approximate indexes such as HNSW.
- Deduplication: finding near-duplicate records or documents.
""",
    "linear_regression": """
**Use it when** you want to predict a number from inputs and the relationship is roughly a straight line, or you
want an interpretable model where each weight means something.
**Don't use it** for clearly curved relationships without adding features, or when outliers dominate, since squared
error lets them pull the line.

**Real world**
- Forecasting sales, demand or house prices from a few drivers.
- Measuring trends: how much does output change per unit of input?

**In software engineering**
- Capacity planning: projecting storage, traffic or cost growth.
- Performance modelling: how latency grows with load, to set limits before it breaks.
- Estimating build or test time from the size of a change.
""",
    "gradient_descent": """
**Use it when** you have a model with adjustable weights and a loss you can differentiate, and there's no formula
for the best weights, which is the case for almost every modern model.
**Watch** the learning rate: too high diverges, too low crawls. Stochastic and mini-batch versions scale to huge
datasets.

**Real world**
- Every neural network, from image recognisers to large language models, is trained by a variant of it.
- Fitting models in statistics and economics when no closed form exists.

**In software engineering**
- Deep-learning frameworks (PyTorch, TensorFlow, JAX) provide optimisers such as SGD and Adam, all gradient-descent
  variants.
- Tuning the learning rate is one of the first steps when a training run misbehaves.
""",
    "logistic": """
**Use it when** you need a yes/no prediction with a probability attached, and want a model that's fast, stable and
easy to explain: each weight shows how a feature changes the odds.
**Don't use it** when the boundary between classes is clearly curved, unless you add features; then consider trees
or neural networks.

**Real world**
- Credit scoring and loan approval models.
- Predicting customer churn, click-through rates for ads and medical risk scores.

**In software engineering**
- A dependable production baseline for any binary classification feature.
- Calibrated probabilities let you set thresholds by business cost (how bad is a false alarm versus a miss?).
- The sigmoid output layer is the same unit used at the end of many neural networks.
""",
    "neuron": """
**Use it when** you're learning or explaining neural networks: every network, however large, is built from this unit.
**Remember** that a single neuron can only draw a straight-line boundary.

**Real world**
- Logic gates (AND, OR, NOT) can each be built from one threshold neuron.
- Simple scoring rules ("add up weighted factors and compare to a threshold") are single neurons in disguise.

**In software engineering**
- Choosing activation functions (ReLU, sigmoid, tanh) is an everyday decision when building models in a deep-learning
  framework.
- Debugging dead or saturated neurons starts with understanding how the activation behaves.
""",
    "perceptron": """
**Use it when** you want the simplest learning algorithm for a linear classifier, or need to learn online, updating
from one example at a time as data streams in.
**Don't use it** on data that isn't linearly separable (it never settles), or when you need probabilities;
logistic regression does both better.

**Real world**
- The perceptron (Rosenblatt, 1958) was one of the first learning machines, and its limits on XOR shaped the history
  of AI.
- Online linear classifiers still filter streams of items such as messages and events.

**In software engineering**
- Online learning: updating a model incrementally without retraining from scratch.
- The "nudge weights after each mistake" pattern underlies many simple adaptive systems.
""",
    "network": """
**Use it when** the relationship between inputs and outputs is too complex for linear models and you have enough data:
images, audio, text and other rich signals.
**Don't use it** on small tabular datasets, where gradient-boosted trees or linear models are often as good, faster
and easier to explain.

**Real world**
- Image and speech recognition, translation, recommendation and large language models are all trained with
  back-propagation.

**In software engineering**
- Frameworks such as PyTorch and TensorFlow implement back-propagation automatically (automatic differentiation), so
  engineers define the forward pass and get gradients for free.
- Understanding deltas helps debug training: vanishing or exploding gradients show up exactly here.
""",
    "cnn": """
**Use it when** your data has a grid structure (images, spectrograms, some sensor data) and the same pattern can
appear anywhere. Weight sharing keeps the model small and lets it spot a feature wherever it occurs.
**Don't use it** for data without spatial structure, such as plain tables.

**Real world**
- Photo tagging, medical image analysis, document scanning and text recognition (OCR).
- Quality inspection on production lines and perception systems in vehicles.

**In software engineering**
- Sizing a model for phones or edge devices: parameter counts like these decide memory use and speed.
- Choosing stride and padding to control output size and compute cost when designing a network.
""",
}


# One line each for the overview table on the home page: (use it when, real world, in software engineering).
# Each is a short form of the fuller panel above.
SUMMARY: dict[str, tuple[str, str, str]] = {
    "search_trace": ("You need a path from a start to a goal through states with costs",
                     "Sat-nav route finding", "Network routing (Dijkstra in OSPF)"),
    "search_heuristic": ("You're designing a heuristic and need A\\* to stay optimal",
                         "Straight-line distance for road maps", "Pruning in planning and scheduling engines"),
    "truth_table": ("A few true/false inputs and you need a definite answer",
                    "Specifying logic gates and circuits", "Proving a refactored `if` condition is equivalent"),
    "cnf": ("Feeding a problem to a SAT solver or resolution prover",
            "Encoding circuits for hardware verification", "DIMACS, the standard SAT solver input format"),
    "entailment": ("You need certainty that a conclusion follows, not just likelihood",
                   "Automated theorem proving", "Checking cloud access policies (AWS Zelkova)"),
    "chaining": ("Your knowledge is a set of if-then rules",
                 "Expert systems such as MYCIN", "Prolog, rule engines and build systems"),
    "dpll": ("You need a satisfying assignment, or proof that none exists",
             "Hardware model checking", "Modern SAT solvers (MiniSat, CaDiCaL)"),
    "walksat_step": ("Repairing a complete guess one change at a time",
                     "Swapping shifts in a draft roster", "Greedy-plus-random moves in optimisers"),
    "walksat_run": ("A large, probably satisfiable problem where speed matters",
                    "Large scheduling and planning problems", "Reproducible randomised runs with a seed"),
    "unify": ("Matching patterns with variables and working out their values",
              "Proof assistants matching rules to goals", "Type inference in Haskell and OCaml"),
    "fol_chaining": ("General rules plus facts about specific things",
                     "Knowledge graphs and ontology reasoners", "Datalog engines for program analysis"),
    "csp_backtracking": ("Choosing values that must satisfy rules between them",
                         "Timetabling, rostering and fixture scheduling", "Register allocation by graph colouring"),
    "csp_ac3": ("Shrinking a constraint problem before or during search",
                "Crossing off Sudoku candidates", "Constraint propagation inside solvers"),
    "games": ("Two players take turns with opposite goals",
              "Classic chess engines", "Computer players in turn-based games"),
    "bayes_rule": ("Updating a belief with evidence, especially for rare events",
                   "Interpreting medical test results", "Why noisy alerts on rare incidents get ignored"),
    "bayes_net": ("Several uncertain causes and effects influence each other",
                  "Medical diagnosis systems", "Root-cause analysis from fired alerts"),
    "joint": ("A few variables with a known probability for every combination",
              "Contingency tables in medicine", "Conditional rates by segment in analytics"),
    "naive_bayes": ("A fast, simple classifier, especially for text",
                    "Spam filtering", "A quick baseline for triaging tickets"),
    "kmeans": ("Grouping unlabelled data into k compact clusters",
               "Customer segmentation", "Vector quantisation of embeddings"),
    "knn": ("Similar things behave similarly and you can measure similarity",
            "\"Customers like you also bought\"", "Vector databases and semantic search"),
    "linear_regression": ("Predicting a number from a roughly straight-line relationship",
                          "Forecasting sales or house prices", "Capacity planning for storage and traffic"),
    "gradient_descent": ("Fitting weights to a differentiable loss with no closed form",
                         "Training every neural network", "Optimisers in PyTorch, TensorFlow and JAX"),
    "logistic": ("A yes/no prediction with a probability attached",
                 "Credit scoring", "A dependable baseline for binary classification"),
    "neuron": ("Learning or explaining how neural networks are built",
               "Logic gates as threshold units", "Choosing activation functions"),
    "perceptron": ("The simplest linear classifier, or learning online",
                   "One of the first learning machines (1958)", "Incremental updates without retraining"),
    "network": ("Relationships too complex for linear models, with enough data",
                "Image and speech recognition, LLMs", "Automatic back-propagation in frameworks"),
    "cnn": ("Grid-shaped data where the same pattern can appear anywhere",
            "Photo tagging, medical imaging, OCR", "Sizing models for phones and edge devices"),
}
