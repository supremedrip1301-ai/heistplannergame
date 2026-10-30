"""Reference algorithms taken from my DAA worksheets, used ONLY by the tests.

None of this code is imported by the game. It exists so the tests can check
the game's algorithms against independent versions I wrote in class:

* dijkstra_matrix()  - DAA Experiment 4 (adjacency matrix, O(V^2)), with the
                       indentation bug from my worksheet fixed.
* find() / union()   - DAA Experiment 3 (Kruskal's Union-Find helpers).
* bellman_ford()     - an independent shortest-path check (no priority queue).
* grid_to_matrix()   - turns a mission map into the adjacency matrix that
                       dijkstra_matrix() expects.
"""


# ======================================================================
# DAA Experiment 4 - Dijkstra with an adjacency matrix (O(V^2))
# ======================================================================
def dijkstra_matrix(graph, source):
    """Return the list of minimum distances from source to every vertex.

    graph[u][v] > 0 is the cost of the edge u -> v, and 0 means "no edge".

    BUG FIX compared with my worksheet: in the printed version,
    `if current == -1: break`, `visited[current] = True` and the whole
    relaxation loop were indented INSIDE the `for v` loop that searches for
    the closest unvisited vertex, and `if new_distance < distance[v]` was not
    nested under the `graph[current][v] > 0` check. That meant the algorithm
    relaxed edges before it had finished finding the minimum. Here the search
    loop finishes first, and only then is the chosen vertex visited and its
    edges relaxed.
    """
    vertices = len(graph)
    distance = [float('inf')] * vertices
    visited = [False] * vertices
    distance[source] = 0

    for _ in range(vertices):
        # Step 1: linear scan for the closest vertex not yet visited.
        min_distance = float('inf')
        current = -1
        for v in range(vertices):
            if not visited[v] and distance[v] < min_distance:
                min_distance = distance[v]
                current = v

        # Step 2 (now OUTSIDE the scan loop): stop if nothing is reachable.
        if current == -1:
            break
        visited[current] = True

        # Step 3: relax every edge leaving the chosen vertex.
        for v in range(vertices):
            if graph[current][v] > 0 and not visited[v]:
                new_distance = distance[current] + graph[current][v]
                if new_distance < distance[v]:
                    distance[v] = new_distance

    return distance


def grid_to_matrix(grid, tile_costs, blocked=frozenset()):
    """Convert a tile map into (matrix, index_of) for dijkstra_matrix().

    Every walkable tile gets a vertex number. matrix[u][v] is the cost of
    entering tile v from its neighbour u (the game's entered-tile model).
    """
    index_of = {}
    tiles = []
    for r, line in enumerate(grid):
        for c, ch in enumerate(line):
            if ch in tile_costs and (r, c) not in blocked:
                index_of[(r, c)] = len(tiles)
                tiles.append((r, c))

    n = len(tiles)
    matrix = [[0] * n for _ in range(n)]
    for (r, c), u in index_of.items():
        for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            nxt = (r + dr, c + dc)
            if nxt in index_of:
                v = index_of[nxt]
                matrix[u][v] = tile_costs[grid[nxt[0]][nxt[1]]]
    return matrix, index_of


# ======================================================================
# DAA Experiment 3 - Union-Find helpers from my Kruskal program
# ======================================================================
# Function to find the parent of a vertex
def find(parent, vertex):

    if parent[vertex] != vertex:
        parent[vertex] = find(parent, parent[vertex])   # path compression

    return parent[vertex]


# Function to join two sets
def union(parent, rank, u, v):

    root_u = find(parent, u)
    root_v = find(parent, v)
    if root_u != root_v:

        # Attach smaller rank tree under larger rank tree
        if rank[root_u] < rank[root_v]:
            parent[root_u] = root_v
        elif rank[root_u] > rank[root_v]:
            parent[root_v] = root_u
        else:
            parent[root_v] = root_u
            rank[root_u] += 1

        return True
    return False


def count_walkable_groups(grid, walkable_chars):
    """How many separate connected groups of walkable tiles the map has.

    Uses find()/union() exactly like Kruskal does: every tile starts as its
    own set, and every pair of neighbouring walkable tiles is joined.
    """
    tiles = [(r, c) for r, line in enumerate(grid)
             for c, ch in enumerate(line) if ch in walkable_chars]
    parent = {t: t for t in tiles}
    rank = {t: 0 for t in tiles}
    for (r, c) in tiles:
        for nxt in ((r, c + 1), (r + 1, c)):      # right and down cover every pair
            if nxt in parent:
                union(parent, rank, (r, c), nxt)
    roots = {find(parent, t) for t in tiles}
    return len(roots)


# ======================================================================
# Bellman-Ford on an implicit graph - an independent check for the
# state-graph Dijkstra in core/state_planner.py (used only by tests).
# ======================================================================
def bellman_ford(start, successors_fn):
    """Minimum cost from start to every reachable state.

    successors_fn(state) returns [(next_state, cost), ...]. All states are
    collected first (breadth-first), then every edge is relaxed repeatedly
    until nothing changes (at most V - 1 rounds) - O(V * E), much slower than
    Dijkstra, but it does not rely on a priority queue at all.
    """
    states = [start]
    seen = {start}
    edges = []
    i = 0
    while i < len(states):
        state = states[i]
        i += 1
        for nxt, cost in successors_fn(state):
            edges.append((state, nxt, cost))
            if nxt not in seen:
                seen.add(nxt)
                states.append(nxt)

    dist = {state: float("inf") for state in states}
    dist[start] = 0
    for _ in range(len(states) - 1):
        changed = False
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                changed = True
        if not changed:
            break
    return dist
