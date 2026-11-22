"""Graph search: breadth-first, depth-first, uniform-cost, greedy best-first, A*, depth-limited,
iterative deepening and IDA* (Russell & Norvig, AIMA chapter 3).

Conventions: children are generated in alphabetical order; BFS goal-tests a node when it is generated,
every other algorithm when it is selected; graph search never adds a state already in the frontier or
explored set (uniform-cost and A* replace a frontier entry when they find a cheaper path to it).
"""
import heapq
import itertools
import re

# --- inputs ---
ALGORITHM = "astar"          # bfs, dfs, ucs, greedy, astar, dls, ids or idastar
MODE = "graph"               # "graph" keeps an explored set; "tree" does not
TIE_BREAK = "alphabetical"   # alphabetical, fifo or lifo
DIRECTED = False
START, GOAL = "H", "P"
DEPTH_LIMIT = 3              # used by depth-limited search
MAX_STEPS = 200              # tree search can loop forever on a graph with cycles, so stop here
EDGES = [("H", "L", 15), ("H", "T", 12), ("T", "M", 5), ("T", "Y", 6), ("L", "W", 9), ("L", "Y", 10),
         ("Y", "P", 11), ("M", "P", 10), ("M", "S", 7), ("M", "Y", 4), ("P", "W", 14)]
H = {"H": 20, "L": 17, "S": 19, "T": 12, "M": 10, "W": 12, "Y": 8, "P": 0}
# --- end inputs ---


def natural_key(s):
    """Sort 'A2' before 'A10'."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def build_graph():
    """Adjacency lists {state: [(child, step_cost), ...]}, children in alphabetical order."""
    cost = {}
    for a, b, c in EDGES:
        for x, y in ([(a, b)] if DIRECTED else [(a, b), (b, a)]):
            cost[(x, y)] = min(c, cost.get((x, y), c))
    adj = {s: [] for e in EDGES for s in e[:2]}
    for (x, y), c in cost.items():
        adj[x].append((y, c))
    for s in adj:
        adj[s].sort(key=lambda t: natural_key(t[0]))
    return adj


class Node:
    def __init__(self, state, parent=None, g=0.0, depth=0):
        self.state, self.parent, self.g, self.depth = state, parent, g, depth

    def path(self):
        node, out = self, []
        while node:
            out.append(node.state)
            node = node.parent
        return out[::-1]


def h(state):
    return H.get(state, 0)


def best_first(adj, kind):
    """Uniform-cost (f = g), greedy (f = h) or A* (f = g + h) with a priority queue."""
    f = {"ucs": lambda n: n.g, "greedy": lambda n: h(n.state), "astar": lambda n: n.g + h(n.state)}[kind]
    counter = itertools.count()

    def key(node, c):
        if TIE_BREAK == "alphabetical":
            return (f(node), natural_key(node.state), c)
        return (f(node), c if TIE_BREAK == "fifo" else -c)

    heap, alive, in_frontier, explored = [], {}, {}, []

    def push(node):
        c = next(counter)
        heapq.heappush(heap, (key(node, c), c, node))
        alive[c] = node
        if MODE == "graph":
            in_frontier[node.state] = c

    push(Node(START))
    step = 0
    while alive and step < MAX_STEPS:
        while heap[0][1] not in alive:          # skip entries replaced by a cheaper path
            heapq.heappop(heap)
        _, c, node = heapq.heappop(heap)
        del alive[c]
        in_frontier.pop(node.state, None)
        step += 1
        print(f"Step {step}: select {node.state} (f = {fmt(f(node))})")
        if node.state == GOAL:                   # goal test on selection
            return node
        if MODE == "graph":
            explored.append(node.state)
        for child_state, cost in adj.get(node.state, []):
            child = Node(child_state, node, node.g + cost, node.depth + 1)
            if MODE == "graph":
                if child_state in explored:
                    continue
                if child_state in in_frontier:
                    old = alive[in_frontier[child_state]]
                    if kind in ("ucs", "astar") and child.g < old.g:
                        del alive[in_frontier[child_state]]
                        push(child)
                    continue
            push(child)
        frontier = sorted(alive.values(), key=lambda n: (f(n), natural_key(n.state)))
        print("        frontier: " + " ".join(f"{n.state}({fmt(f(n))})" for n in frontier))
    return None


def breadth_or_depth_first(adj, kind):
    """BFS (FIFO queue, goal test on generation) or DFS (LIFO stack, goal test on selection)."""
    root = Node(START)
    if kind == "bfs" and START == GOAL:
        return root
    frontier, explored, step = [root], [], 0
    while frontier and step < MAX_STEPS:
        node = frontier.pop(0) if kind == "bfs" else frontier.pop()
        step += 1
        print(f"Step {step}: select {node.state}")
        if kind == "dfs" and node.state == GOAL:
            return node
        if MODE == "graph":
            explored.append(node.state)
        children = []
        for child_state, cost in adj.get(node.state, []):
            seen = [n.state for n in frontier + children]
            if MODE == "graph" and (child_state in explored or child_state in seen):
                continue
            child = Node(child_state, node, node.g + cost, node.depth + 1)
            children.append(child)
            if kind == "bfs" and child_state == GOAL:     # goal test on generation
                return child
        frontier.extend(children if kind == "bfs" else reversed(children))
    return None


def depth_limited(adj, node, limit, visited):
    """Recursive depth-limited tree search. Returns a goal Node, 'cutoff' or None."""
    if len(visited) >= MAX_STEPS:
        return "cutoff"
    visited.append(node.state)
    if node.state == GOAL:
        return node
    if node.depth == limit:
        return "cutoff"
    cutoff = False
    for child_state, cost in adj.get(node.state, []):
        result = depth_limited(adj, Node(child_state, node, node.g + cost, node.depth + 1), limit, visited)
        if result == "cutoff":
            cutoff = True
        elif result is not None:
            return result
    return "cutoff" if cutoff else None


def iterative_deepening(adj, max_depth=10):
    for limit in range(max_depth + 1):
        visited = []
        result = depth_limited(adj, Node(START), limit, visited)
        print(f"Depth limit {limit}: visited {' '.join(visited)}")
        if result != "cutoff":
            return result
    return None


def ida_star(adj):
    """Depth-first search inside an f-cost contour; raise the contour to the smallest f that exceeded it."""
    def search(node, bound):
        f = node.g + h(node.state)
        if f > bound:
            return f, None
        if node.state == GOAL:
            return f, node
        smallest = float("inf")
        on_path = set(node.path())
        for child_state, cost in adj.get(node.state, []):
            if child_state in on_path:
                continue
            t, found = search(Node(child_state, node, node.g + cost, node.depth + 1), bound)
            if found:
                return t, found
            smallest = min(smallest, t)
        return smallest, None

    bound = h(START)
    while True:
        print(f"f-cost threshold {fmt(bound)}")
        t, found = search(Node(START), bound)
        if found or t == float("inf"):
            return found
        bound = t


def fmt(x):
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")


def main():
    adj = build_graph()
    if ALGORITHM in ("ucs", "greedy", "astar"):
        goal = best_first(adj, ALGORITHM)
    elif ALGORITHM in ("bfs", "dfs"):
        goal = breadth_or_depth_first(adj, ALGORITHM)
    elif ALGORITHM == "dls":
        visited = []
        result = depth_limited(adj, Node(START), DEPTH_LIMIT, visited)
        print("Visited: " + " ".join(visited))
        goal = result if isinstance(result, Node) else None
    elif ALGORITHM == "ids":
        goal = iterative_deepening(adj)
    else:
        goal = ida_star(adj)
    if goal:
        print(f"Answer: path {' -> '.join(goal.path())}, cost {fmt(goal.g)}")
    else:
        print("Answer: no solution")


if __name__ == "__main__":
    main()
