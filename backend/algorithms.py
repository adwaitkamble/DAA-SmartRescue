"""
SmartRescue EMS - Core Algorithm Engine
=========================================
Contains pure implementations of DAA algorithms:
  1. Floyd-Warshall  (All-Pairs Shortest Path)  — O(V³)      [Unit III]
  2. 0/1 Knapsack    (Ambulance Load Optimizer)  — O(n·W)    [Unit III]
  3. TSP via Branch & Bound (LC Search)                       [Unit IV]

These functions are intentionally kept stateless and pure so they
can be unit-tested independently of Flask or any UI layer.
"""

import heapq
import copy

from data import city_graph, inventory_db, LOCATIONS, INF


# ═══════════════════════════════════════════════════════════════
#  1. FLOYD-WARSHALL  —  Dynamic Programming (Unit III)
#     Time Complexity : O(V³)
#     Space Complexity: O(V²)
# ═══════════════════════════════════════════════════════════════

def compute_city_routes(graph):
    """
    Computes the shortest travel time between every pair of PCMC
    locations using the Floyd-Warshall algorithm.

    Parameters
    ----------
    graph : list[list[float]]
        V×V adjacency matrix where graph[i][j] is the direct travel
        time (minutes) from location i to j.  float('inf') means no
        direct connection.

    Returns
    -------
    dist : list[list[float]]
        V×V matrix where dist[i][j] is the shortest travel time from
        location i to j across all possible intermediate stops.

    next_node : list[list[int | None]]
        V×V matrix used for path reconstruction.
        next_node[i][j] stores the first intermediate node on the
        shortest path from i → j.  None means no path exists.

    Algorithm (3 nested loops — O(V³))
    -----------------------------------
    For every possible intermediate vertex k (0 … V-1):
        For every source i:
            For every destination j:
                If dist[i][k] + dist[k][j] < dist[i][j]:
                    Update dist[i][j] and record that the path
                    from i to j now goes through k first.
    """
    V = len(graph)

    # --- Step 1: Initialize distance and next_node matrices ---
    # Deep copy the input so the original data is never mutated.
    dist = [[graph[i][j] for j in range(V)] for i in range(V)]

    # next_node[i][j] = j  means "from i, go directly to j"
    # next_node[i][j] = None means "no path from i to j"
    next_node = [
        [j if graph[i][j] != INF and i != j else None for j in range(V)]
        for i in range(V)
    ]

    # --- Step 2: Core DP — Try every vertex as an intermediate ---
    for k in range(V):                       # intermediate vertex
        for i in range(V):                   # source vertex
            for j in range(V):               # destination vertex
                # Can we improve the i→j path by routing through k?
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    next_node[i][j] = next_node[i][k]

    return dist, next_node


def reconstruct_path(next_node, source, destination):
    """
    Traces the shortest path from source → destination using the
    next_node matrix produced by Floyd-Warshall.

    Parameters
    ----------
    next_node : list[list[int | None]]
        Path-reconstruction matrix from compute_city_routes().
    source : int
        Index of the starting location.
    destination : int
        Index of the ending location.

    Returns
    -------
    path : list[int]
        Ordered list of location indices forming the shortest path.
        Empty list if no path exists.
    """
    if next_node[source][destination] is None:
        return []

    path = [source]
    current = source

    while current != destination:
        current = next_node[current][destination]
        if current is None:
            return []          # Safety check — no valid path
        path.append(current)

    return path


# ═══════════════════════════════════════════════════════════════
#  2. 0/1 KNAPSACK  —  Dynamic Programming (Unit III)
#     Time Complexity : O(n · W)
#     Space Complexity: O(n · W)
# ═══════════════════════════════════════════════════════════════

def optimize_ambulance_loadout(capacity, items):
    """
    Selects the optimal combination of medical equipment for an
    ambulance, maximizing total life-saving priority value without
    exceeding the weight capacity.

    Parameters
    ----------
    capacity : int
        Maximum weight (kg) the ambulance can carry.
    items : list[dict]
        Each dict has keys: 'name' (str), 'weight' (int), 'value' (int).

    Returns
    -------
    max_value : int
        The highest achievable total priority value.
    selected_items : list[dict]
        The specific items chosen (in original order), each dict
        containing 'name', 'weight', and 'value'.

    Algorithm
    ---------
    Build a 2D DP table  dp[i][w]  where:
        i = number of items considered (0 … n)
        w = remaining capacity     (0 … W)

    Recurrence:
        If item i's weight > w:
            dp[i][w] = dp[i-1][w]          (can't include item i)
        Else:
            dp[i][w] = max(
                dp[i-1][w],                 (skip item i)
                dp[i-1][w - weight_i] + value_i   (take item i)
            )

    Backtracking:
        Walk backwards through the table to find which items were
        actually selected.
    """
    n = len(items)

    # --- Step 1: Build the DP table ---
    # dp[i][w] = max value achievable using items 0..i-1 with capacity w
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]

    for i in range(1, n + 1):
        item_weight = items[i - 1]["weight"]
        item_value  = items[i - 1]["value"]

        for w in range(capacity + 1):
            if item_weight > w:
                # Item is too heavy — carry forward the previous best
                dp[i][w] = dp[i - 1][w]
            else:
                # Choose the better option: skip or take the item
                dp[i][w] = max(
                    dp[i - 1][w],                           # skip
                    dp[i - 1][w - item_weight] + item_value  # take
                )

    max_value = dp[n][capacity]

    # --- Step 2: Backtrack to find the selected items ---
    selected_items = []
    w = capacity

    for i in range(n, 0, -1):
        # If dp[i][w] differs from dp[i-1][w], item i was included
        if dp[i][w] != dp[i - 1][w]:
            selected_items.append(items[i - 1])
            w -= items[i - 1]["weight"]

    # Reverse so items appear in their original order
    selected_items.reverse()

    return max_value, selected_items


# ═══════════════════════════════════════════════════════════════
#  3. TRAVELING SALESPERSON PROBLEM  —  Branch & Bound (Unit IV)
#     Strategy: Least Cost (LC) Search with Min-Priority Queue
# ═══════════════════════════════════════════════════════════════

def reduce_matrix(matrix):
    """
    Reduces a cost matrix by subtracting the row minimum from every
    row and then the column minimum from every column.

    Parameters
    ----------
    matrix : list[list[float]]
        Square cost matrix (may contain INF for blocked edges).

    Returns
    -------
    reduced : list[list[float]]
        The fully reduced matrix.
    reduction_cost : float
        Sum of all row and column minimums subtracted — this is the
        lower bound contribution from this reduction step.
    """
    n = len(matrix)
    reduced = copy.deepcopy(matrix)
    reduction_cost = 0

    # --- Row reduction ---
    for i in range(n):
        row_min = min(reduced[i])
        if row_min != INF and row_min > 0:
            reduction_cost += row_min
            for j in range(n):
                if reduced[i][j] != INF:
                    reduced[i][j] -= row_min

    # --- Column reduction ---
    for j in range(n):
        col_min = min(reduced[i][j] for i in range(n))
        if col_min != INF and col_min > 0:
            reduction_cost += col_min
            for i in range(n):
                if reduced[i][j] != INF:
                    reduced[i][j] -= col_min

    return reduced, reduction_cost


class Node:
    """
    Represents a state in the Branch & Bound search tree for TSP.

    Attributes
    ----------
    path : list[int]
        Sequence of visited location indices so far.
    reduced_matrix : list[list[float]]
        The cost matrix after reductions for this state.
    cost : float
        Lower bound cost for this node (accumulated edge costs +
        all reduction costs).
    level : int
        Depth in the search tree (number of cities visited - 1).
    """

    def __init__(self, path, reduced_matrix, cost, level):
        self.path = path
        self.reduced_matrix = reduced_matrix
        self.cost = cost
        self.level = level

    def __lt__(self, other):
        """Min-heap comparison — node with lower cost has higher priority."""
        return self.cost < other.cost


def plan_multi_stop_route(graph):
    """
    Solves TSP using Least Cost Branch & Bound to find the minimum-
    cost Hamiltonian cycle starting and ending at node 0 (Base).

    The algorithm explores the state-space tree using a min-priority
    queue (heapq).  At each node it:
      1. Picks the live node with the smallest lower bound.
      2. Generates children by extending the path to each unvisited city.
      3. For each child, computes a new reduced matrix and lower bound.
      4. Prunes any child whose lower bound ≥ current best complete tour.

    Parameters
    ----------
    graph : list[list[float]]
        V×V adjacency matrix (travel times in minutes).

    Returns
    -------
    best_path : list[int]
        Optimal route as a list of location indices (starts and ends
        at 0).  Empty list if no valid tour exists.
    best_cost : float
        Total travel time of the optimal tour.  INF if no tour exists.
    """
    n = len(graph)

    # --- Step 1: Create the root node (start at Base, index 0) ---
    root_matrix, root_cost = reduce_matrix(graph)
    root = Node(
        path=[0],
        reduced_matrix=root_matrix,
        cost=root_cost,
        level=0
    )

    # Min-priority queue (heap) — always expand the cheapest node first
    pq = []
    heapq.heappush(pq, root)

    best_cost = INF
    best_path = []

    # --- Step 2: LC Search loop ---
    while pq:
        # Pop the node with the smallest lower bound
        current = heapq.heappop(pq)

        # Pruning: skip if this node can't beat the current best
        if current.cost >= best_cost:
            continue

        current_city = current.path[-1]

        # --- Step 3: Check if we have a complete tour ---
        if current.level == n - 1:
            # All cities visited — try returning to Base
            return_cost = current.reduced_matrix[current_city][0]
            if return_cost != INF:
                total_cost = current.cost + return_cost
                if total_cost < best_cost:
                    best_cost = total_cost
                    best_path = current.path + [0]
            continue

        # --- Step 4: Generate child nodes for each unvisited city ---
        for next_city in range(n):
            if next_city in current.path:
                continue   # Already visited

            edge_cost = current.reduced_matrix[current_city][next_city]
            if edge_cost == INF:
                continue   # No direct connection

            # Build child's matrix: block row current_city, col next_city,
            # and the reverse edge next_city → 0 (start)
            child_matrix = copy.deepcopy(current.reduced_matrix)

            # Set entire row of current_city to INF (we're leaving it)
            for j in range(n):
                child_matrix[current_city][j] = INF

            # Set entire column of next_city to INF (we're arriving)
            for i in range(n):
                child_matrix[i][next_city] = INF

            # Block the reverse edge to prevent premature return,
            # but ONLY for intermediate nodes — the last city must
            # be able to return to Base to complete the cycle.
            if current.level + 1 < n - 1:
                child_matrix[next_city][0] = INF

            # Reduce the child matrix and compute new lower bound
            child_matrix, child_reduction = reduce_matrix(child_matrix)
            child_cost = current.cost + edge_cost + child_reduction

            # Pruning: only add if lower bound is promising
            if child_cost < best_cost:
                child = Node(
                    path=current.path + [next_city],
                    reduced_matrix=child_matrix,
                    cost=child_cost,
                    level=current.level + 1
                )
                heapq.heappush(pq, child)

    return best_path, best_cost


# ═══════════════════════════════════════════════════════════════
#  Quick Self-Test  (run:  python algorithms.py)
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # ---- Floyd-Warshall Test ----
    print("=" * 55)
    print("  FLOYD-WARSHALL — All-Pairs Shortest Paths")
    print("=" * 55)

    dist, next_node = compute_city_routes(city_graph)

    # Print optimized distance matrix
    header = "          " + "  ".join(f"{loc[:6]:>6}" for loc in LOCATIONS)
    print(header)
    for i, row in enumerate(dist):
        row_str = "  ".join(
            f"{'∞':>6}" if v == INF else f"{v:>6.0f}" for v in row
        )
        print(f"{LOCATIONS[i][:8]:<10}{row_str}")

    # Show a sample path reconstruction
    src, dst = 0, 3   # Base → PCCOE
    path = reconstruct_path(next_node, src, dst)
    path_names = " → ".join(LOCATIONS[p] for p in path)
    print(f"\nShortest path Base → PCCOE: {path_names}  ({dist[src][dst]:.0f} min)")

    # ---- 0/1 Knapsack Test ----
    print("\n" + "=" * 55)
    print("  0/1 KNAPSACK — Ambulance Loadout Optimizer")
    print("=" * 55)

    test_capacity = 15
    max_val, selected = optimize_ambulance_loadout(test_capacity, inventory_db)

    print(f"Capacity : {test_capacity} kg")
    print(f"Max Value: {max_val}")
    print(f"Selected :")
    for item in selected:
        print(f"   • {item['name']}  (wt: {item['weight']} kg, val: {item['value']})")

    # ---- TSP Branch & Bound Test ----
    print("\n" + "=" * 55)
    print("  TSP — Branch & Bound (LC Search)")
    print("=" * 55)

    tsp_path, tsp_cost = plan_multi_stop_route(city_graph)

    if tsp_path:
        route_names = " → ".join(LOCATIONS[i] for i in tsp_path)
        print(f"Optimal Route : {route_names}")
        print(f"Total Cost    : {tsp_cost:.0f} min")
    else:
        print("No valid Hamiltonian cycle found.")
