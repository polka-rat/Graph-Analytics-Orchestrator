"""max_flow_min_cut: maximum flow from a source to a sink by Edmonds-Karp, and the minimum cut.

Edmonds-Karp is Ford-Fulkerson where each augmenting path is a shortest one (fewest edges),
found by breadth-first search in the residual graph. When no path is left, the nodes still
reachable from the source form one side of a minimum cut; the edges leaving that side are
the bottleneck, and their capacities add up to the maximum flow.
"""
import json
from collections import deque

from graphkit.contract import MAX_OUTPUT_BYTES, MAX_TOP_K, error, get_graph, node_ref, ok

RESULT_BUDGET = MAX_OUTPUT_BYTES - 1500
EPS = 1e-9  # residual capacities at or below this count as used up (guards float round-off)


# ----- input handling: LLMs send "3", 3.0 or "M1"; accept what is unambiguous, explain what is not
def _whole_number(value, name, lo, hi):
    """(int, None) if value is a whole number from lo to hi (also as "5" or 5.0), else (None, error)."""
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        value = int(value.strip())
    elif isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        return None, error(f"{name} must be a whole number from {lo} to {hi}; got {value!r}.")
    return value, None


def _resolve_node(g, value, param):
    """(node id, None) for an id of g, matched exactly or ignoring case, else (None, error)."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, error(f"Parameter '{param}' is missing: give the id of a node in '{g.graph_id}'. "
                           f"Use lookup_node to find node ids from names.")
    if not isinstance(value, str):
        return None, error(f"Parameter '{param}' must be a node id (a string); got {value!r}. "
                           f"Use lookup_node to find node ids.")
    value = value.strip()
    if g.has_node(value):
        return value, None
    same = [n for n in g.nodes() if n.lower() == value.lower()]
    if len(same) == 1:
        return same[0], None
    return None, error(f"Node '{value}' (parameter '{param}') is not in graph '{g.graph_id}'. "
                       f"Use lookup_node to find node ids.")


def _resolve_capacity(g, capacity):
    """('weight' | 'unit' | an edge attribute name of g, None), else (None, error)."""
    if not isinstance(capacity, str) or not capacity.strip():
        return None, error("capacity must be 'weight', 'unit', or the name of a numeric edge attribute "
                           "(e.g. 'airlines' in airports).")
    capacity = capacity.strip()
    if capacity.lower() in ("weight", "unit"):
        return capacity.lower(), None
    attrs = set()
    for u, v, _ in g.edges():
        attrs.update(g.edge_attrs(u, v))
        break  # every edge of a dataset has the same attribute names
    for a in sorted(attrs):
        if a.lower() == capacity.lower():
            return a, None
    options = ", ".join(f"'{a}'" for a in sorted(attrs)) or "none in this graph"
    return None, error(f"'{capacity}' is not an edge attribute of '{g.graph_id}'. Use capacity='weight', "
                       f"'unit', or one of its edge attributes: {options}.")


# ----- the residual network
class _Network:
    """Residual network with arcs stored in parallel lists; arc i ^ 1 is the reverse of arc i."""

    def __init__(self, n):
        self.adj = [[] for _ in range(n)]
        self.to, self.res = [], []

    def add(self, u, v, cap_forward, cap_backward):
        for a, b, c in ((u, v, cap_forward), (v, u, cap_backward)):
            self.adj[a].append(len(self.to))
            self.to.append(b)
            self.res.append(c)

    def shortest_augmenting_path(self, s, t):
        """BFS from s over arcs with residual capacity; returns the arcs of the path to t, or None."""
        via = {s: None}
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for arc in self.adj[u]:
                v = self.to[arc]
                if v not in via and self.res[arc] > EPS:
                    via[v] = arc
                    if v == t:
                        path = []
                        while v != s:
                            arc = via[v]
                            path.append(arc)
                            v = self.to[arc ^ 1]
                        return path
                    queue.append(v)
        return None

    def reachable(self, s):
        seen = {s}
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for arc in self.adj[u]:
                v = self.to[arc]
                if v not in seen and self.res[arc] > EPS:
                    seen.add(v)
                    queue.append(v)
        return seen


def _capacities(g, capacity):
    """[(u, v, cap)] for every edge, or an error dict."""
    edges = []
    for u, v, w in g.edges():
        if capacity == "weight":
            c = w
        elif capacity == "unit":
            c = 1.0
        else:
            c = g.edge_attrs(u, v).get(capacity)
            if isinstance(c, bool) or not isinstance(c, (int, float)):
                return None, error(f"Edge {u}->{v} has no numeric '{capacity}' attribute. Use capacity='weight', "
                                   f"'unit', or a numeric edge attribute of '{g.graph_id}' (see list_graphs).")
        if c < 0:
            return None, error(f"Edge {u}->{v} has negative capacity {c}; capacities must be zero or more.")
        edges.append((u, v, float(c)))
    return edges, None


def _fmt(x):
    return f"{x:,.0f}" if x == int(x) else f"{x:,.6g}"


def run(store, graph_id, source=None, sink=None, capacity="weight", top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"max_flow_min_cut takes graph_id, source, sink, capacity and top_k.")
    source, err = _resolve_node(g, source, "source")
    if err:
        return err
    sink, err = _resolve_node(g, sink, "sink")
    if err:
        return err
    if source == sink:
        return error("source and sink must be different nodes.")
    capacity, err = _resolve_capacity(g, capacity)
    if err:
        return err
    top_k, err = _whole_number(top_k, "top_k", 1, MAX_TOP_K)
    if err:
        return err
    edges, err = _capacities(g, capacity)
    if err:
        return err

    nodes = sorted(g.nodes())
    index = {n: i for i, n in enumerate(nodes)}
    net = _Network(len(nodes))
    # An undirected edge can carry flow either way, so both of its arcs get the full capacity.
    for u, v, c in sorted(edges):
        net.add(index[u], index[v], c, 0.0 if g.directed else c)

    s, t = index[source], index[sink]
    flow, rounds = 0.0, 0
    while True:
        path = net.shortest_augmenting_path(s, t)
        if path is None:
            break
        push = min(net.res[arc] for arc in path)
        for arc in path:
            net.res[arc] -= push
            net.res[arc ^ 1] += push
        flow += push
        rounds += 1

    side = {nodes[i] for i in net.reachable(s)}
    cut = []
    for u, v, c in edges:
        if u in side and v not in side:
            cut.append((c, u, v))
        elif not g.directed and v in side and u not in side:
            cut.append((c, v, u))
    cut.sort(key=lambda e: (-e[0], e[1], e[2]))
    listed = [{"source": node_ref(g, u), "target": node_ref(g, v), "capacity": round(c, 6)} for c, u, v in cut[:top_k]]

    result = {"source": node_ref(g, source), "sink": node_ref(g, sink), "capacity": capacity,
              "max_flow": round(flow, 6), "augmenting_paths": rounds,
              "cut_size": len(cut), "cut_capacity": round(sum(c for c, _, _ in cut), 6),
              "source_side_size": len(side), "sink_side_size": len(nodes) - len(side),
              "cut_edges": listed, "cut_edges_truncated": len(listed) < len(cut)}
    while listed and len(json.dumps(result).encode("utf-8")) > RESULT_BUDGET:
        listed.pop()
        result["cut_edges_truncated"] = True

    src, snk = f"{g.label(source)} ({source})", f"{g.label(sink)} ({sink})"
    measure = {"weight": "edge weight" if g.weighted else "1 per edge, since the graph is unweighted",
               "unit": "1 per edge, so this counts edge-disjoint paths"}.get(capacity, f"edge attribute '{capacity}'")
    if flow <= EPS:
        return ok(result, f"No flow can get from {src} to {snk} in '{graph_id}': there is no path with spare "
                          f"capacity, so the maximum flow is 0.")
    if len(cut) == 1:
        c, u, v = cut[0]
        where = f"the single edge {u}->{v}"
    else:
        shown = ", ".join(f"{e['source']['id']}->{e['target']['id']}" for e in listed[:5])
        more = f" and {len(cut) - 5} more" if len(cut) > 5 else ""
        where = f"{len(cut)} edges ({shown}{more})"
    return ok(result, f"The maximum flow from {src} to {snk} is {_fmt(flow)} (capacity = {measure}). "
                      f"The minimum cut, the bottleneck, is {where}, with total capacity {_fmt(flow)}.")
