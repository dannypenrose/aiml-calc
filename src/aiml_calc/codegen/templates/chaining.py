"""Forward and backward chaining over definite clauses: rules "p1 & p2 & ... => q" plus known facts
(Russell & Norvig, AIMA §7.5.4).
  forward chaining: start from the facts and fire every rule whose premises are all known;
  backward chaining: start from the query and prove each premise of a rule that concludes it.
"""

# --- inputs ---
RULES = [(["P"], "Q"), (["L", "M"], "P"), (["B", "L"], "M"), (["A", "P"], "L"), (["A", "B"], "L")]
FACTS = ["A", "B"]
QUERY = "Q"
# --- end inputs ---


def forward_chaining():
    """PL-FC-ENTAILS: count[r] is how many premises of rule r are still unknown; at 0 the rule fires."""
    count = [len(set(premises)) for premises, _ in RULES]
    inferred = set()
    agenda = list(dict.fromkeys(FACTS))
    while agenda:
        p = agenda.pop(0)
        if p == QUERY:
            return True
        if p in inferred:
            continue
        inferred.add(p)
        for i, (premises, conclusion) in enumerate(RULES):
            if p in premises:
                count[i] -= 1
                if count[i] == 0:
                    print(f"  {' & '.join(premises)} => {conclusion}: fires, add {conclusion}")
                    agenda.append(conclusion)
    return False


def backward_chaining(goal, stack=(), depth=0, proven=None, failed=None):
    """Prove goal from facts, or from all premises of some rule that concludes it."""
    proven = proven if proven is not None else set(FACTS)
    failed = failed if failed is not None else set()
    pad = "  " * (depth + 1)
    if goal in proven:
        print(f"{pad}{goal}: known")
        return True
    if goal in stack or goal in failed:      # loop, or already shown to fail
        return False
    for premises, conclusion in RULES:
        if conclusion == goal:
            print(f"{pad}{goal}: try {' & '.join(premises)} => {conclusion}")
            if all(backward_chaining(p, stack + (goal,), depth + 1, proven, failed) for p in premises):
                proven.add(goal)
                return True
    failed.add(goal)
    return False


def main():
    print("Forward chaining")
    fc = forward_chaining()
    print("Backward chaining")
    bc = backward_chaining(QUERY)
    print(f"Answer: forward chaining {'yes' if fc else 'no'}, backward chaining {'yes' if bc else 'no'}")


if __name__ == "__main__":
    main()
