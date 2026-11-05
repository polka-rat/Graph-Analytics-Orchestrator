"""Motif count: how often each small pattern (motif) of 3 or 4 nodes occurs in a graph.

Size 3 (the default) is the triad census: every set of three nodes is classified by the links
among them. Directed graphs have the 16 Holland-Leinhardt types of NetworkX's triadic_census,
coded by their numbers of Mutual, Asymmetric (one-way) and Null pairs plus a letter for the
shape: for example 030T is the feed-forward loop A->B->C, A->C and 030C the 3-cycle. Undirected
graphs have four types: empty, single edge, open triad (A-B-C) and triangle. The Batagelj-Mrvar
algorithm visits each connected triad exactly once, which also gives every node's counts; triads
with a single linked pair are counted by formula and the empty ones by subtraction from C(n, 3).
Runs in O(m * max_degree) time.

Size 4 counts the six connected 4-node graphlets, ignoring direction: 4_path, 4_star, 4_cycle,
tailed_triangle, diamond and 4_clique. For each node it counts the copies of every pattern
through the node, allowing extra links among the four nodes, from degrees, triangles per edge,
common neighbours and the 4-cliques. A denser 4-node pattern contains a fixed number of copies of
each sparser one, so subtracting those, densest first, gives exact counts of the patterns that
4-node sets induce. Runs in O(m * max_degree^2) time at worst.

Each count is compared with its expected value in a random graph with the same numbers of mutual,
one-way and unlinked pairs (for undirected graphs: the same density). Self-loops and weights are
ignored.
"""
import json
from collections import Counter
from math import comb

from graphkit.contract import MAX_OUTPUT_BYTES, check_node, check_top_k, error, get_graph, node_ref, ok

SIZE_MARGIN = 1024      # room left under the 8 KB limit for the summary and keys
SUMMARY_NODES = 3       # top nodes named in the summary

# The 16 directed triad types, in NetworkX's order: code -> (name, pattern).
TRIADS = {
    "003": ("empty", "no links"),
    "012": ("single_edge", "A->B, C unlinked"),
    "102": ("mutual_edge", "A<->B, C unlinked"),
    "021D": ("out_star", "A<-B->C"),
    "021U": ("in_star", "A->B<-C"),
    "021C": ("chain", "A->B->C"),
    "111D": ("mutual_with_in", "A<->B<-C"),
    "111U": ("mutual_with_out", "A<->B->C"),
    "030T": ("feed_forward_loop", "A->B->C, A->C"),
    "030C": ("cycle", "A->B->C->A"),
    "201": ("mutual_wedge", "A<->B<->C, A and C unlinked"),
    "120D": ("out_star_mutual", "A<-B->C, A<->C"),
    "120U": ("in_star_mutual", "A->B<-C, A<->C"),
    "120C": ("chain_mutual", "A->B->C, A<->C"),
    "210": ("near_mutual_triangle", "A->B<->C, A<->C"),
    "300": ("mutual_triangle", "A<->B<->C<->A"),
}
DISCONNECTED = ("003", "012", "102")                               # at most one pair linked
OPEN = ("021D", "021U", "021C", "111D", "111U", "201")             # exactly two pairs linked
CLOSED = ("030T", "030C", "120D", "120U", "120C", "210", "300")   # all three pairs linked
NOUNS = {"030T": "feed-forward loop", "030C": "3-cycle"}

# Triangles and open triads: the undirected types, or groups of directed types (direction ignored).
# name -> (directed codes, undirected pattern, directed pattern)
GROUPS = {
    "open_triad": (OPEN, "A-B-C, A and C unlinked", "A-B-C linked in any direction, A and C unlinked"),
    "triangle": (CLOSED, "A-B-C-A", "all three pairs linked, in any direction"),
}
# Names of the undirected triad types; every link of an undirected graph counts as mutual.
UNDIRECTED = {"003": "empty", "102": "single_edge", "201": "open_triad", "300": "triangle"}

# Connected 4-node graphlets: name -> (pattern, links, labelled copies on four given nodes).
GRAPHLETS = {
    "4_path": ("A-B-C-D", 3, 12),
    "4_star": ("A linked to B, C and D, which are unlinked", 3, 4),
    "4_cycle": ("A-B-C-D-A, no diagonal", 4, 3),
    "tailed_triangle": ("triangle A-B-C plus D linked only to C", 4, 12),
    "diamond": ("A-B-C-D-A plus the diagonal A-C", 5, 6),
    "4_clique": ("all six pairs linked", 6, 1),
}

ALIASES = {
    "triangles": "triangle", "closed_triad": "triangle", "3_clique": "triangle",
    "open_triads": "open_triad", "wedge": "open_triad", "open_triangle": "open_triad", "2_path": "open_triad",
    "ffl": "feed_forward_loop", "feedforward_loop": "feed_forward_loop", "feed_forward": "feed_forward_loop",
    "3_cycle": "cycle", "feedback_loop": "cycle", "cyclic_triad": "cycle",
    "3_path": "4_path", "p4": "4_path", "3_star": "4_star", "claw": "4_star",
    "square": "4_cycle", "c4": "4_cycle", "paw": "tailed_triangle", "chordal_cycle": "diamond",
    "k4": "4_clique",
}

# Bit i of a triad code is set when arc ARCS[i] is present, for the nodes (v, u, w) = (0, 1, 2).
ARCS = ((0, 1), (1, 0), (0, 2), (2, 0), (1, 2), (2, 1))


def _classify(code):
    """The MAN type of the triad whose arcs are the set bits of `code`."""
    arcs = {arc for i, arc in enumerate(ARCS) if code >> i & 1}
    mutual = [(a, b) for a, b in arcs if a < b and (b, a) in arcs]
    oneway = [(a, b) for a, b in arcs if (b, a) not in arcs]
    man = f"{len(mutual)}{len(oneway)}{3 - len(mutual) - len(oneway)}"
    if man in ("021", "120"):   # two one-way arcs: same tail (Down), same head (Up) or a Chain
        (s1, t1), (s2, t2) = oneway
        return man + ("D" if s1 == s2 else "U" if t1 == t2 else "C")
    if man == "111":            # the one-way arc leaves the mutual pair (Up) or enters it (Down)
        return man + ("U" if oneway[0][0] in mutual[0] else "D")
    if man == "030":            # a Cycle if every node sends one arc, else Transitive
        return man + ("C" if len({s for s, _ in oneway}) == 3 else "T")
    return man


TYPE = [_classify(code) for code in range(64)]


def _adjacency(g):
    """Number the nodes 0..n-1 and return (out, nbr): each node's out-neighbours and neighbours.

    Self-loops are dropped, since a pattern needs distinct nodes. In an undirected graph each
    edge is a link in both directions, so out and nbr are the same.
    """
    nodes = g.nodes()
    index = {v: i for i, v in enumerate(nodes)}
    out = [{index[w] for w in g.out_neighbors(v) if w != v} for v in nodes]
    nbr = [out[i] | {index[w] for w in g.in_neighbors(v) if w != v} for i, v in enumerate(nodes)]
    return out, nbr


def _triads(out, nbr):
    """Batagelj-Mrvar triad census.

    Returns (census, per_node): census[code] counts the triads of each type, and
    per_node[i][code] the connected triads of that type that contain node i.
    """
    n = len(out)
    census = Counter()
    per_node = [Counter() for _ in range(n)]
    for v in range(n):
        nv, ov = nbr[v], out[v]
        for u in nv:
            if u < v:
                continue
            ou = out[u]
            third = (nv | nbr[u]) - {v, u}
            # Every node outside `third` makes a triad in which only the pair v-u is linked.
            census["102" if u in ov and v in ou else "012"] += n - 2 - len(third)
            vu = (u in ov) | (v in ou) << 1
            for w in third:
                # Count each connected triad once: v is its smallest node, and u the next
                # smallest unless that one (w) is not linked to v.
                if u < w or (v < w and w not in nv):
                    ow = out[w]
                    code = TYPE[vu | (w in ov) << 2 | (v in ow) << 3 | (w in ou) << 4 | (u in ow) << 5]
                    census[code] += 1
                    per_node[v][code] += 1
                    per_node[u][code] += 1
                    per_node[w][code] += 1
    census["003"] = comb(n, 3) - sum(census.values())
    return census, per_node


def _graphlets(nbr):
    """Per-node counts of the six connected 4-node graphlets (induced), ignoring direction.

    First, for each node v, the copies of each pattern through v are counted allowing extra
    links among their four nodes, by v's position in the pattern. With d = degree, t_v =
    triangles at v, t_va = triangles on edge v-a and c_vw = common neighbours of v and w:
      4_star           C(d_v, 3) as the hub + C(d_a - 1, 2) as a leaf of each neighbour a
      4_path           paths v-a-b-c and a-v-b-c: neighbour degrees, minus closed triangles
      4_cycle          C(c_vw, 2) for each w != v: two common neighbours of v and the far corner
      tailed_triangle  t_v (d_v - 2) + sum over neighbours a of t_va (d_a - 2) + (t_a - t_va)
      diamond          C(t_va, 2) with v on the diagonal + (t_ab - 1) for each triangle v-a-b
      4_clique         listed from the common neighbours of each triangle
    A denser pattern contains fixed numbers of the sparser ones (a 4-clique holds 6 diamonds,
    3 4-cycles, 12 tailed triangles, 4 stars and 12 paths), so subtracting those, densest first,
    leaves the exact numbers of 4-node sets that induce each pattern.
    """
    n = len(nbr)
    deg = [len(s) for s in nbr]
    tri_edge = {}
    tri = [0] * n
    for a in range(n):
        for b in nbr[a]:
            if a < b:
                t = len(nbr[a] & nbr[b])
                tri_edge[a, b] = tri_edge[b, a] = t
                tri[a] += t
                tri[b] += t
    tri = [t // 2 for t in tri]  # each triangle at a node lies on two of the node's edges
    far = [sum(deg[b] - 1 for b in nbr[a]) for a in range(n)]  # paths a-b-c that start at a

    star, path, cycle, tailed, diamond = ([0] * n for _ in range(5))
    for v in range(n):
        d = deg[v]
        walks = Counter()  # walks[w] = number of common neighbours of v and w
        for a in nbr[v]:
            t = tri_edge[v, a]
            star[v] += comb(deg[a] - 1, 2)
            path[v] += far[a] - (d - 1) - t + (d - 1) * (deg[a] - 1) - t
            tailed[v] += t * (deg[a] - 2) + tri[a] - t
            diamond[v] += comb(t, 2)
            walks.update(nbr[a])
        walks.pop(v, None)
        star[v] += comb(d, 3)
        tailed[v] += tri[v] * (d - 2)
        cycle[v] = sum(comb(c, 2) for c in walks.values())

    clique = [0] * n
    for a in range(n):
        for b in nbr[a]:
            if a < b:
                common = nbr[a] & nbr[b]
                for c in common:
                    if b < c:  # each triangle a < b < c once
                        diamond[a] += tri_edge[b, c] - 1
                        diamond[b] += tri_edge[a, c] - 1
                        diamond[c] += tri_edge[a, b] - 1
                        for x in common & nbr[c]:
                            if c < x:  # each 4-clique a < b < c < x once
                                clique[a] += 1
                                clique[b] += 1
                                clique[c] += 1
                                clique[x] += 1

    counts = []
    for v in range(n):
        k4 = clique[v]
        dia = diamond[v] - 6 * k4
        c4 = cycle[v] - dia - 3 * k4
        tt = tailed[v] - 4 * dia - 12 * k4
        st = star[v] - tt - 2 * dia - 4 * k4
        p4 = path[v] - 2 * tt - 4 * c4 - 6 * dia - 12 * k4
        counts.append({"4_path": p4, "4_star": st, "4_cycle": c4, "tailed_triangle": tt,
                       "diamond": dia, "4_clique": k4})
    return counts


def _expected_triads(n, mutual, oneway):
    """Expected number of triads of each type if every pair of nodes were, independently, mutual,
    one-way (in a random direction) or unlinked with the observed proportions."""
    pairs = comb(n, 2)
    if not pairs:
        return Counter()
    p = {(1, 1): mutual / pairs, (1, 0): oneway / pairs / 2, (0, 1): oneway / pairs / 2,
         (0, 0): 1 - (mutual + oneway) / pairs}
    expected = Counter()
    for code in range(64):
        b = [code >> i & 1 for i in range(6)]
        expected[TYPE[code]] += comb(n, 3) * p[b[0], b[1]] * p[b[2], b[3]] * p[b[4], b[5]]
    return expected


def _expected_graphlets(n, links):
    """Expected number of 4-node sets inducing each graphlet in a random graph of the same density."""
    pairs = comb(n, 2)
    p = links / pairs if pairs else 0.0
    return {name: comb(n, 4) * copies * p ** e * (1 - p) ** (6 - e)
            for name, (_, e, copies) in GRAPHLETS.items()}


def _counts(count, total, expected):
    """A motif's count, its share of all connected subgraphs and the random-graph baseline."""
    return {"count": count, "share": round(count / total, 6) if total else 0.0,
            "expected_random": round(expected, 6),
            "ratio_to_random": round(count / expected, 6) if expected >= 1e-6 else None}


def _census3(g, out, nbr, links):
    """The triad census.

    Returns (fields, catalogue, per_node, total): result fields; catalogue[key] = (pattern,
    count, expected) for every motif that can be asked for (a triad code of a directed graph,
    'triangle' or 'open_triad'); each node's count of every catalogue motif; and the number of
    connected triads.
    """
    n = len(out)
    census, per_node = _triads(out, nbr)
    mutual = sum(1 for v in range(n) for u in out[v] if v in out[u]) // 2 if g.directed else links
    expected = _expected_triads(n, mutual, links - mutual)
    connected = [c for c in TRIADS if c not in DISCONNECTED] if g.directed else ["201", "300"]
    total = sum(census[c] for c in connected)

    # Every motif that can be asked for, with the triad codes it is made of and its pattern.
    members = {key: (codes, directed_pattern if g.directed else pattern)
               for key, (codes, pattern, directed_pattern) in GROUPS.items()}
    if g.directed:
        members.update((c, ((c,), TRIADS[c][1])) for c in connected)
    catalogue = {key: (pattern, sum(census[c] for c in codes), sum(expected[c] for c in codes))
                 for key, (codes, pattern) in members.items()}
    nodes = [{key: sum(cnt[c] for c in codes) for key, (codes, _) in members.items()} for cnt in per_node]

    if g.directed:
        rows = [{"code": c, "motif": TRIADS[c][0], "pattern": TRIADS[c][1],
                 **_counts(census[c], total, expected[c])} for c in connected]
    else:
        rows = [{"motif": key, "pattern": catalogue[key][0],
                 **_counts(catalogue[key][1], total, catalogue[key][2])} for key in GROUPS]
    rows.sort(key=lambda r: -r["count"])  # stable, so ties keep the census order

    fields = {}
    if g.directed:
        fields["dyads"] = {"mutual": mutual, "asymmetric": links - mutual, "null": comb(n, 2) - links}
    tri, opn = catalogue["triangle"][1], catalogue["open_triad"][1]
    fields.update({
        "census": {c: census[c] for c in TRIADS} if g.directed else {UNDIRECTED[c]: census[c] for c in UNDIRECTED},
        "connected_subgraphs": total,
        "motifs": rows,
        "triangles": tri,
        "open_triads": opn,
        "transitivity": round(3 * tri / (3 * tri + opn), 6) if tri else 0.0,
    })
    return fields, catalogue, nodes, total


def _census4(g, nbr, links):
    """The graphlet census, returned like _census3's."""
    nodes = _graphlets(nbr)
    totals = {name: sum(cnt[name] for cnt in nodes) // 4 for name in GRAPHLETS}  # 4 nodes in each
    expected = _expected_graphlets(len(nbr), links)
    total = sum(totals.values())
    catalogue = {name: (GRAPHLETS[name][0], totals[name], expected[name]) for name in GRAPHLETS}
    rows = [{"motif": name, "pattern": GRAPHLETS[name][0], **_counts(totals[name], total, expected[name])}
            for name in GRAPHLETS]
    rows.sort(key=lambda r: -r["count"])
    fields = {"direction_ignored": g.directed, "census": totals, "connected_subgraphs": total, "motifs": rows}
    return fields, catalogue, nodes, total


def _resolve(g, motif):
    """(size, key) for a motif name, or (None, error). The key is a triad code (directed graphs),
    'triangle', 'open_triad' or a graphlet name."""
    choices = list(GROUPS)
    if g.directed:
        choices += [f"{TRIADS[c][0]} ({c})" for c in TRIADS if c not in DISCONNECTED]
    hint = f"Use one of: {', '.join(choices + list(GRAPHLETS))}."
    if not isinstance(motif, str):
        return None, error(f"motif must be a pattern name such as 'triangle'; got {motif!r}. {hint}")
    name = "_".join(motif.lower().replace("-", " ").replace("_", " ").split())  # 'Feed-forward loop' -> feed_forward_loop
    name = ALIASES.get(name, name)
    if name in GRAPHLETS:
        return (4, name), None
    if name in GROUPS:
        return (3, name), None
    code = {nm: c for c, (nm, _) in TRIADS.items()}.get(name, name.upper())
    if code not in TRIADS:
        return None, error(f"Unknown motif '{motif}'. {hint}")
    if code in DISCONNECTED:
        return None, error(f"motif '{motif}' is not a connected pattern (at most one pair of its nodes is "
                           f"linked); its count is in the census of a call without motif. {hint}")
    if not g.directed:
        return None, error(f"motif '{motif}' is a pattern of directed graphs, but graph '{g.graph_id}' is "
                           f"undirected. {hint}")
    return (3, code), None


def _amount(count, key):
    """'3 triangles', '1 4-clique', 'no feed-forward loops (030T: A->B->C, A->C)'."""
    number, s = f"{count:,}" if count else "no", "" if count == 1 else "s"
    if key in NOUNS:
        return f"{number} {NOUNS[key]}{s} ({key}: {TRIADS[key][1]})"
    if key in TRIADS:
        return f"{number} triad{s} of type {key} ({TRIADS[key][1]})"
    return f"{number} {key.replace('_', ' ').replace('4 ', '4-')}{s}"


def _plural(key):
    """'triangles', '4-cliques', 'feed-forward loops', '201 triads'."""
    if key in NOUNS:
        return NOUNS[key] + "s"
    if key in TRIADS:
        return f"{key} triads"
    return key.replace("_", " ").replace("4 ", "4-") + "s"


def _pct(count, total):
    """A share as a percentage; a share that is not zero never shows as 0.0%."""
    pct = 100 * count / total if total else 0.0
    return "0%" if not count else f"{pct:.1f}%" if pct >= 0.1 else f"{pct:.1g}%"


def _join(items):
    """'', 'a', 'a and b', 'a, b and c'."""
    return ", ".join(items[:-1]) + " and " + items[-1] if len(items) > 1 else "".join(items)


def _fits(payload):
    return len(json.dumps(payload).encode("utf-8")) <= MAX_OUTPUT_BYTES - SIZE_MARGIN


def run(store, graph_id, size=None, motif=None, node=None, top_k=10, **params):
    g, err = get_graph(store, graph_id)
    if err:
        return err
    if params:
        return error(f"Unknown parameter(s): {', '.join(params)}. "
                     f"motif_count takes graph_id, size, motif, node and top_k.")
    k, err = check_top_k(top_k)
    if err:
        return err
    if size is not None and (isinstance(size, bool) or not isinstance(size, int) or size not in (3, 4)):
        return error(f"size must be 3 or 4 (the number of nodes in each pattern); got {size!r}.")
    key = None
    if motif is not None:
        found, err = _resolve(g, motif)
        if err:
            return err
        motif_size, key = found
        if size is not None and size != motif_size:
            return error(f"motif '{motif}' has {motif_size} nodes but size is {size}; "
                         f"leave size out or set it to {motif_size}.")
        size = motif_size
    size = size or 3
    if node is not None:
        err = check_node(g, node)
        if err:
            return err
    n = g.number_of_nodes()
    if n == 0:
        return error(f"Graph '{graph_id}' has no nodes, so it has no patterns to count. "
                     f"Use list_graphs to pick another graph.")

    nodes = g.nodes()
    out, nbr = _adjacency(g)
    links = sum(len(s) for s in nbr) // 2  # linked pairs of distinct nodes, ignoring direction
    census = _census3(g, out, nbr, links) if size == 3 else _census4(g, nbr, links)
    fields, catalogue, per_node, total = census
    focus_key = key or ("triangle" if size == 3 else "4_clique")
    pattern, count, expected = catalogue[focus_key]

    # The nodes in the most copies of the focus motif; ties are broken by node id.
    scores = sorted((-cnt[focus_key], v) for v, cnt in zip(nodes, per_node) if cnt[focus_key])
    top = [node_ref(g, v, count=-s) for s, v in scores[:k]]
    focus = {"motif": TRIADS[focus_key][0] if focus_key in TRIADS else focus_key}
    if focus_key in TRIADS:
        focus["code"] = focus_key
    elif g.directed and focus_key in GROUPS:
        focus["includes"] = list(GROUPS[focus_key][0])
    focus.update({"pattern": pattern, **_counts(count, total, expected), "nodes_with_motif": len(scores),
                  "top_nodes": top, "returned": len(top), "truncated": len(top) < len(scores)})

    target = None
    if node is not None:
        mine = per_node[nodes.index(node)]
        rank = 1 + sum(1 for s, _ in scores if -s > mine[focus_key])
        target = node_ref(g, node, counts=dict(mine), rank=rank)

    result = {"graph_id": graph_id, "directed": g.directed, "size": size, "number_of_nodes": n,
              "number_of_edges": g.number_of_edges(), **fields, "focus": focus, "node": target}
    shrunk = False
    while not _fits(result) and focus["top_nodes"]:
        focus["top_nodes"].pop()
        focus["returned"] -= 1
        focus["truncated"] = shrunk = True

    where = f"'{graph_id}'"
    kind = "triads" if size == 3 else "4-node subgraphs"
    named = _join([f"{e['label']} ({e['count']:,})" for e in focus["top_nodes"][:SUMMARY_NODES]])
    ratio = focus["ratio_to_random"] if count else None
    if n < size:
        summary = f"Graph {where} has only {n} node(s), so it has no {size}-node patterns; every count is 0."
    elif target is not None:
        summary = (f"{target['label']} takes part in {_amount(mine[focus_key], focus_key)}, rank {rank} of "
                   f"{n} nodes ({where} has {count:,} in all).")
        if size == 3:
            others = [o for o in GROUPS if o != focus_key]
        else:
            others = sorted((o for o in GRAPHLETS if o != focus_key and mine[o]), key=lambda o: -mine[o])[:3]
        if others:
            summary += f" It is also in {_join([_amount(mine[o], o) for o in others])}."
    elif key is not None:
        if count:
            summary = f"{where} has {_amount(count, key)}: {_pct(count, total)} of its {total:,} connected {kind}"
            if ratio is not None:
                summary += f" and {ratio:.1f} times the number expected in a random graph with the same number of links"
            summary += f". The nodes in the most are {named}." if named else "."
        else:
            shown = "" if key in TRIADS else f" ({pattern})"  # _amount already shows a code's pattern
            summary = f"{where} has {_amount(0, key)}{shown} among its {total:,} connected {kind}."
    elif not total:
        summary = f"{where} has no connected {kind}, so every pattern count is 0."
    elif size == 3 and not g.directed:
        tri, opn = fields["triangles"], fields["open_triads"]
        summary = (f"{where} has {_amount(tri, 'triangle')} and {_amount(opn, 'open_triad')} (A-B-C with A and "
                   f"C unlinked), so {_pct(3 * tri, 3 * tri + opn)} of connected triples are closed "
                   f"(transitivity {fields['transitivity']})")
        if ratio is not None:
            summary += f"; triangles are {ratio:.1f} times as common as in a random graph with the same number of links"
        summary += "."
    else:
        rows = [r for r in fields["motifs"][:3] if r["count"]]
        common = _join([f"{r.get('code', r['motif'])} ({r['pattern']}) with {r['count']:,} "
                        f"({_pct(r['count'], total)})" for r in rows])
        verb = "are" if len(rows) > 1 else "is"
        summary = f"The most common of the {total:,} connected {kind} in {where} {verb} {common}."
        if size == 3:
            summary += (f" It has {_amount(catalogue['030T'][1], '030T')}, {_amount(catalogue['030C'][1], '030C')}"
                        f" and, ignoring direction, {_amount(fields['triangles'], 'triangle')}"
                        f" (transitivity {fields['transitivity']}).")
        else:
            summary += (f" It has {_amount(catalogue['4_clique'][1], '4_clique')} and "
                        f"{_amount(catalogue['4_cycle'][1], '4_cycle')}.")
    if key is None and target is None and named:
        summary += f" The nodes in the most {_plural(focus_key)} are {named}."
    if size == 4 and g.directed:
        summary += " Directions were ignored for 4-node patterns."
    if shrunk:
        summary += f" Only the top {focus['returned']} nodes are listed to keep the output small."
    return ok(result, summary)
