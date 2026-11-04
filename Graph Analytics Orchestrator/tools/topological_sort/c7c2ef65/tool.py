"""Topological sort: orders the nodes of a directed acyclic graph so every edge goes from earlier to later.

Highlights:
- Kahn's algorithm with a min-heap, O((V + E) log V): ties go to the smallest node id, so the order is
  deterministic and equals nx.lexicographical_topological_sort.
- Each node also gets a level: its longest chain of predecessors, computed in the same pass. Nodes on the
  same level can be done in parallel (e.g. courses in the same semester).
- On a graph with a cycle, the error names an actual cycle (e.g. ABJ -> ACC -> ABJ), found by walking the
  nodes Kahn's algorithm could not place, instead of only saying "not a DAG".
- Undirected graphs and unknown parameters get clear errors; at most 100 nodes are listed to stay under 8 KB.
"""
import heapq

from graphkit.contract import error, get_graph, node_ref, ok

MAX_NODES = 100  # keeps the output under 8 KB


def _count(n, word, plural=None):
    """'1 node', '2 nodes'."""
    return f"{n} {word if n == 1 else plural or word + 's'}"


def _find_cycle(g, remaining):
    """A cycle among `remaining` (nodes Kahn's algorithm could not place), as a list of ids."""
    # Every unplaced node still has an unplaced predecessor, so walking backwards must revisit a node.
    node = min(remaining)
    seen = {}
    path = []
    while node not in seen:
        seen[node] = len(path)
        path.append(node)
        node = min(u for u in g.in_neighbors(node) if u in remaining)
    return (path[seen[node]:] + [node])[::-1]  # reverse: follow the edges forwards


def run(store, graph_id, **params):
    # Validate the call before doing any work.
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. topological_sort takes only graph_id.")
    if not g.directed:
        return error(f"'{graph_id}' is undirected; a topological order only exists for directed acyclic graphs "
                     f"(e.g. 'courses'). Use list_graphs to find one.")

    # Kahn's algorithm. A min-heap breaks ties by the smallest node id; level is the length of the
    # longest chain of predecessors (0 = no prerequisites).
    in_deg = {n: len(g.in_neighbors(n)) for n in g.nodes()}
    level = {n: 0 for n in g.nodes()}
    ready = [n for n, d in in_deg.items() if d == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        u = heapq.heappop(ready)
        order.append(u)
        for v in g.out_neighbors(u):  # u is placed: release its successors
            level[v] = max(level[v], level[u] + 1)
            in_deg[v] -= 1
            if in_deg[v] == 0:
                heapq.heappush(ready, v)

    # Nodes left unplaced are on a cycle or after one.
    if len(order) < g.number_of_nodes():
        cycle = _find_cycle(g, {n for n, d in in_deg.items() if d > 0})
        return error(f"'{graph_id}' has a cycle ({' -> '.join(cycle)}), so no topological order exists. "
                     f"Topological sort needs a directed acyclic graph such as 'courses'.")
    if not order:
        return error(f"Graph '{graph_id}' has no nodes to sort.")

    result = [node_ref(g, n, position=i, level=level[n]) for i, n in enumerate(order[:MAX_NODES], 1)]
    shown = "" if len(order) <= MAX_NODES else f" Showing the first {MAX_NODES} of {len(order)} nodes."
    summary = (f"Topological order of {_count(len(order), 'node')} in '{graph_id}' starts with {result[0]['label']} and ends "
               f"with {g.label(order[-1])}; the longest chain has {_count(max(level.values()) + 1, 'level')}.{shown}")
    return ok(result, summary)
