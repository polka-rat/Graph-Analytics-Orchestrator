"""louvain: modularity-based community detection (Louvain method), weighted, directed or undirected."""
import json
import random

from graphkit.contract import MAX_OUTPUT_BYTES, error, get_graph, node_ref, ok

RESTARTS = 5
MIN_GAIN = 1e-9
MEMBER_SAMPLE = 3


def _arcs(g, nodes):
    """Arc weights as index-based dicts: out[i][j] = weight of arc i->j (undirected edges become two arcs)."""
    index = {v: i for i, v in enumerate(nodes)}
    out = [dict() for _ in nodes]
    for u, v, w in g.edges():
        i, j = index[u], index[v]
        out[i][j] = out[i].get(j, 0.0) + w
        if not g.directed and i != j:
            out[j][i] = out[j].get(i, 0.0) + w
        elif not g.directed:
            out[i][i] = out[i].get(i, 0.0) + w
    return out


def _modularity(out, comm, gamma):
    n = len(out)
    total = sum(sum(a.values()) for a in out)
    if total == 0:
        return 0.0
    kout = [sum(a.values()) for a in out]
    kin = [0.0] * n
    for i in range(n):
        for j, w in out[i].items():
            kin[j] += w
    inside = 0.0
    sout, sin = {}, {}
    for i in range(n):
        c = comm[i]
        sout[c] = sout.get(c, 0.0) + kout[i]
        sin[c] = sin.get(c, 0.0) + kin[i]
        for j, w in out[i].items():
            if comm[j] == c:
                inside += w
    expected = sum(sout[c] * sin[c] for c in sout) / total
    return (inside - gamma * expected) / total


def _one_level(out, rng, gamma):
    """Local moving phase on arc dicts. Returns (community list, improved?)."""
    n = len(out)
    total = sum(sum(a.values()) for a in out)
    inn = [dict() for _ in range(n)]
    for i in range(n):
        for j, w in out[i].items():
            inn[j][i] = w
    kout = [sum(a.values()) for a in out]
    kin = [sum(a.values()) for a in inn]
    comm = list(range(n))
    tot_out = kout[:]
    tot_in = kin[:]
    order = list(range(n))
    improved = False
    moved = True
    while moved:
        moved = False
        rng.shuffle(order)
        for i in order:
            ci = comm[i]
            links = {}
            for j, w in out[i].items():
                if j != i:
                    links[comm[j]] = links.get(comm[j], 0.0) + w
            for j, w in inn[i].items():
                if j != i:
                    links[comm[j]] = links.get(comm[j], 0.0) + w
            tot_out[ci] -= kout[i]
            tot_in[ci] -= kin[i]
            best_c = ci
            best_gain = links.get(ci, 0.0) / total - gamma * (kout[i] * tot_in[ci] + kin[i] * tot_out[ci]) / (total * total)
            for c in sorted(links):
                gain = links[c] / total - gamma * (kout[i] * tot_in[c] + kin[i] * tot_out[c]) / (total * total)
                if gain > best_gain + MIN_GAIN:
                    best_gain = gain
                    best_c = c
            tot_out[best_c] += kout[i]
            tot_in[best_c] += kin[i]
            if best_c != ci:
                comm[i] = best_c
                moved = True
                improved = True
    return comm, improved


def _aggregate(out, comm):
    labels = {}
    for c in comm:
        if c not in labels:
            labels[c] = len(labels)
    new = [dict() for _ in labels]
    for i, arcs in enumerate(out):
        a = labels[comm[i]]
        for j, w in arcs.items():
            b = labels[comm[j]]
            new[a][b] = new[a].get(b, 0.0) + w
    return new, [labels[c] for c in comm]


def _louvain(out, seed, gamma):
    n = len(out)
    rng = random.Random(seed)
    membership = list(range(n))
    level = out
    while True:
        comm, improved = _one_level(level, rng, gamma)
        if not improved:
            break
        level, relabel = _aggregate(level, comm)
        membership = [relabel[m] for m in membership]
        if len(level) == 1:
            break
    return membership


def _fit_size(entries, wrap):
    """Drop member samples, then trailing entries, until the response is small enough."""
    def size(items):
        return len(json.dumps(wrap(items), sort_keys=True).encode("utf-8"))
    limit = MAX_OUTPUT_BYTES - 1200
    if size(entries) > limit:
        for e in entries:
            e["members"] = e["members"][:1]
    while len(entries) > 1 and size(entries) > limit:
        entries.pop()
    return entries


def run(store, graph_id, resolution=1.0, seed=0, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. louvain takes graph_id, resolution, seed and top_k.")
    if isinstance(top_k, float) and top_k.is_integer():
        top_k = int(top_k)   # an LLM may send 10.0 for an integer
    if isinstance(seed, float) and seed.is_integer():
        seed = int(seed)
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 100:
        return error(f"top_k must be a whole number from 1 to 100; got {top_k!r}.")
    if isinstance(resolution, bool) or not isinstance(resolution, (int, float)) or not resolution > 0:
        return error(f"resolution must be a positive number; got {resolution!r}.")
    if isinstance(seed, bool) or not isinstance(seed, int):
        return error(f"seed must be a whole number; got {seed!r}.")

    nodes = g.nodes()
    if not nodes:
        return error(f"Graph '{graph_id}' has no nodes, so there are no communities to find.")
    if g.number_of_edges() == 0:
        return error(f"Graph '{graph_id}' has no edges, so Louvain cannot find communities (every node is alone). "
                     f"Choose a graph with edges.")

    out = _arcs(g, nodes)
    best = None
    for r in range(RESTARTS):
        membership = _louvain(out, seed + r, resolution)
        q = _modularity(out, membership, 1.0)
        qr = _modularity(out, membership, resolution)
        if best is None or qr > best[0] + 1e-12:
            best = (qr, q, membership)
    _, modularity, membership = best

    groups = {}
    for node, c in zip(nodes, membership):
        groups.setdefault(c, []).append(node)
    ordered = sorted((sorted(members) for members in groups.values()), key=lambda m: (-len(m), m[0]))
    modularity = round(modularity, 6)
    shown = ordered[:top_k]

    def strength(v):
        return len(g.undirected_neighbors(v))

    entries = []
    for idx, members in enumerate(shown):
        top = sorted(members, key=lambda v: (-strength(v), v))[:MEMBER_SAMPLE]
        entries.append({"community": idx, "size": len(members), "graph_id": None,
                        "members": [node_ref(g, v, degree=strength(v)) for v in top],
                        "partition_modularity": modularity})

    def wrap(items):
        return {"result": items, "summary": "x" * 400}

    entries = _fit_size(entries, wrap)
    for entry in entries:
        members = ordered[entry["community"]]
        entry["graph_id"] = store.subgraph(graph_id, members,
                                           f"Louvain community {entry['community']} of '{graph_id}' ({len(members)} nodes)")

    n_comm = len(ordered)
    sizes = ", ".join(str(len(m)) for m in ordered[:5])
    more = "" if n_comm <= 5 else ", ..."
    kind = "directed " if g.directed else ""
    summary = (f"Louvain found {n_comm} communities in the {kind}graph '{graph_id}' with modularity {modularity} "
               f"(largest sizes: {sizes}{more}). Showing the {len(entries)} largest; each has its own subgraph id "
               f"in 'graph_id', and result_graph_id is the largest community.")
    return ok(entries, summary, result_graph_id=entries[0]["graph_id"])
