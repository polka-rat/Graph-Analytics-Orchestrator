from graphkit.contract import error, get_graph, ok

ALL_TRIAD_TYPES = [
    "003", "012", "102", "021D", "021U", "021C", "111D", "111U",
    "030T", "030C", "201", "120D", "120U", "120C", "210", "300"
]


def build_triad_table():
    table = {}
    for mask in range(64):
        vu = bool(mask & 1)
        uv = bool(mask & 2)
        vw = bool(mask & 4)
        wv = bool(mask & 8)
        uw = bool(mask & 16)
        wu = bool(mask & 32)

        dyads = [(vu, uv), (vw, wv), (uw, wu)]
        m_count = 0
        a_count = 0
        for d1, d2 in dyads:
            if d1 and d2:
                m_count += 1
            elif d1 or d2:
                a_count += 1

        if m_count == 0 and a_count == 0:
            label = "003"
        elif m_count == 0 and a_count == 1:
            label = "012"
        elif m_count == 1 and a_count == 0:
            label = "102"
        elif m_count == 2 and a_count == 0:
            label = "201"
        elif m_count == 2 and a_count == 1:
            label = "210"
        elif m_count == 3 and a_count == 0:
            label = "300"
        elif m_count == 0 and a_count == 2:
            out_deg = {"v": 0, "u": 0, "w": 0}
            in_deg = {"v": 0, "u": 0, "w": 0}
            if vu and not uv:
                out_deg["v"] += 1
                in_deg["u"] += 1
            if uv and not vu:
                out_deg["u"] += 1
                in_deg["v"] += 1
            if vw and not wv:
                out_deg["v"] += 1
                in_deg["w"] += 1
            if wv and not vw:
                out_deg["w"] += 1
                in_deg["v"] += 1
            if uw and not wu:
                out_deg["u"] += 1
                in_deg["w"] += 1
            if wu and not uw:
                out_deg["w"] += 1
                in_deg["u"] += 1

            if out_deg["v"] == 2 or out_deg["u"] == 2 or out_deg["w"] == 2:
                label = "021D"
            elif in_deg["v"] == 2 or in_deg["u"] == 2 or in_deg["w"] == 2:
                label = "021U"
            else:
                label = "021C"
        elif m_count == 1 and a_count == 1:
            if vu and uv:
                mut_pair = {"v", "u"}
            elif vw and wv:
                mut_pair = {"v", "w"}
            else:
                mut_pair = {"u", "w"}

            src = None
            if vu and not uv:
                src = "v"
            elif uv and not vu:
                src = "u"
            elif vw and not wv:
                src = "v"
            elif wv and not vw:
                src = "w"
            elif uw and not wu:
                src = "u"
            elif wu and not uw:
                src = "w"

            if src in mut_pair:
                label = "111U"
            else:
                label = "111D"
        elif m_count == 0 and a_count == 3:
            out_deg = {"v": 0, "u": 0, "w": 0}
            if vu and not uv:
                out_deg["v"] += 1
            if uv and not vu:
                out_deg["u"] += 1
            if vw and not wv:
                out_deg["v"] += 1
            if wv and not vw:
                out_deg["w"] += 1
            if uw and not wu:
                out_deg["u"] += 1
            if wu and not uw:
                out_deg["w"] += 1

            if out_deg["v"] == 1 and out_deg["u"] == 1 and out_deg["w"] == 1:
                label = "030C"
            else:
                label = "030T"
        elif m_count == 1 and a_count == 2:
            out_deg = {"v": 0, "u": 0, "w": 0}
            in_deg = {"v": 0, "u": 0, "w": 0}
            if vu and not uv:
                out_deg["v"] += 1
                in_deg["u"] += 1
            if uv and not vu:
                out_deg["u"] += 1
                in_deg["v"] += 1
            if vw and not wv:
                out_deg["v"] += 1
                in_deg["w"] += 1
            if wv and not vw:
                out_deg["w"] += 1
                in_deg["v"] += 1
            if uw and not wu:
                out_deg["u"] += 1
                in_deg["w"] += 1
            if wu and not uw:
                out_deg["w"] += 1
                in_deg["u"] += 1

            if out_deg["v"] == 2 or out_deg["u"] == 2 or out_deg["w"] == 2:
                label = "120D"
            elif in_deg["v"] == 2 or in_deg["u"] == 2 or in_deg["w"] == 2:
                label = "120U"
            else:
                label = "120C"
        else:
            label = "003"

        table[mask] = label
    return table


TRIAD_TABLE = build_triad_table()


def classify_mask(mask):
    return TRIAD_TABLE[mask]


def count_undirected(g):
    nodes = sorted(g.nodes())
    n = len(nodes)

    # adjacency sets without self loops
    adj = {u: set() for u in nodes}
    for u in nodes:
        for v in g.out_neighbors(u):
            if u != v:
                adj[u].add(v)
                adj[v].add(u)

    m = sum(len(s) for s in adj.values()) // 2
    if n < 3:
        return n, m, 0, 0, 0.0

    deg = {u: len(adj[u]) for u in nodes}
    forward = {u: set() for u in nodes}
    edges = []
    for u in nodes:
        u_key = (deg[u], u)
        for v in adj[u]:
            v_key = (deg[v], v)
            if u_key < v_key:
                forward[u].add(v)
                edges.append((u, v))

    triangles = 0
    for u, v in edges:
        triangles += len(forward[u] & forward[v])

    total_wedges = 0
    for d in deg.values():
        total_wedges += (d * (d - 1)) // 2

    open_wedges = total_wedges - 3 * triangles
    if total_wedges > 0:
        transitivity = round(3.0 * triangles / total_wedges, 6)
    else:
        transitivity = 0.0

    return n, m, triangles, open_wedges, transitivity


def count_directed(g):
    nodes = sorted(g.nodes())
    n = len(nodes)
    node_to_idx = {node: i for i, node in enumerate(nodes)}

    out_sets = [set() for _ in range(n)]
    in_sets = [set() for _ in range(n)]
    nbrs = [set() for _ in range(n)]

    for u_idx, u in enumerate(nodes):
        for v in g.out_neighbors(u):
            if u != v and g.has_node(v):
                v_idx = node_to_idx[v]
                out_sets[u_idx].add(v_idx)
                in_sets[v_idx].add(u_idx)
                nbrs[u_idx].add(v_idx)
                nbrs[v_idx].add(u_idx)

    m = sum(len(s) for s in out_sets)
    census = {k: 0 for k in ALL_TRIAD_TYPES}

    if n < 3:
        return n, m, census, 0, 0, 0, 0, 0, 0

    # count mutual dyads
    mutual_dyads = 0
    for v in range(n):
        for u in out_sets[v]:
            if v < u and v in out_sets[u]:
                mutual_dyads += 1

    # non induced ffl via arc intersection
    ffl_arc_sum = 0
    for a in range(n):
        for b in out_sets[a]:
            ffl_arc_sum += len(out_sets[a] & out_sets[b])

    # Batagelj-Mrvar triadic census
    for v in range(n):
        for u in sorted(nbrs[v]):
            if u > v:
                s = (nbrs[u] | nbrs[v]) - {u, v}
                vu = u in out_sets[v]
                uv = v in out_sets[u]
                if vu and uv:
                    census["102"] += n - len(s) - 2
                else:
                    census["012"] += n - len(s) - 2

                for w in s:
                    if u < w or (v < w < u and w not in nbrs[v]):
                        mask = 0
                        if u in out_sets[v]:
                            mask |= 1
                        if v in out_sets[u]:
                            mask |= 2
                        if w in out_sets[v]:
                            mask |= 4
                        if v in out_sets[w]:
                            mask |= 8
                        if w in out_sets[u]:
                            mask |= 16
                        if u in out_sets[w]:
                            mask |= 32
                        census[TRIAD_TABLE[mask]] += 1

    total_triples = (n * (n - 1) * (n - 2)) // 6
    other_sum = sum(v for k, v in census.items() if k != "003")
    census["003"] = total_triples - other_sum

    # derived counts
    ffl_induced = census["030T"]
    cycle_induced = census["030C"]
    ffl_formula = (
        census["030T"]
        + 2 * census["120U"]
        + census["120C"]
        + 2 * census["120D"]
        + 3 * census["210"]
        + 6 * census["300"]
    )

    if ffl_arc_sum != ffl_formula:
        raise ValueError("feed-forward loop count mismatch")

    cycle_instances = census["030C"] + census["120C"] + census["210"] + 2 * census["300"]
    cycle_node_sets = census["030C"] + census["120C"] + census["210"] + census["300"]

    return (
        n, m, census, ffl_induced, cycle_induced,
        ffl_arc_sum, cycle_instances, cycle_node_sets, mutual_dyads
    )


def run(store, graph_id, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err

    if params:
        return error(f"Unknown parameter(s): {', '.join(sorted(params))}.")

    try:
        if g.directed:
            (
                n, m, census, ffl_ind, cyc_ind,
                ffl_non, cyc_inst, cyc_sets, mut_dyads
            ) = count_directed(g)

            res = {
                "graph_type": "directed",
                "node_count": n,
                "edge_count": m,
                "triad_census": census,
                "feed_forward_loop_induced": ffl_ind,
                "directed_cycle_3_induced": cyc_ind,
                "feed_forward_loop_non_induced": ffl_non,
                "directed_cycle_3_non_induced_instances": cyc_inst,
                "node_sets_with_directed_cycle": cyc_sets,
                "mutual_dyads": mut_dyads,
            }

            if n < 3:
                summary = f"Graph '{graph_id}' has {n} nodes (fewer than 3), so all 3-node motif counts are 0."
            else:
                summary = (
                    f"Graph '{graph_id}' has {ffl_ind} induced FFLs, {ffl_non} non-induced FFLs, "
                    f"{cyc_ind} induced 3-cycles, and {cyc_inst} non-induced cycle instances across {cyc_sets} node sets. "
                    f"Induced counts are often small in dense networks due to mutual connections."
                )

            return ok(res, summary, result_graph_id=None)

        # undirected graph
        n, m, triangles, open_wedges, transitivity = count_undirected(g)
        res = {
            "graph_type": "undirected",
            "node_count": n,
            "edge_count": m,
            "triangle_count": triangles,
            "open_wedge_count": open_wedges,
            "transitivity": transitivity,
        }

        if n < 3:
            summary = f"Graph '{graph_id}' has {n} nodes (fewer than 3), so it contains 0 triangles and 0 open wedges."
        else:
            summary = (
                f"Graph '{graph_id}' has {triangles} triangles (sets of 3 mutually connected nodes) "
                f"and {open_wedges} open wedges (2-hop paths without a closing edge), giving a transitivity of {transitivity:.6f}."
            )

        return ok(res, summary, result_graph_id=None)
    except Exception as exc:
        return error(f"Computation failed: {exc}")
