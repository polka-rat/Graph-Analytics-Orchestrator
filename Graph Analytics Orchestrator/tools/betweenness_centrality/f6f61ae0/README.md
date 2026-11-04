# betweenness_centrality

Author: f6f61ae0 | Tier: hard | Category: centrality

Ranks nodes by exact Brandes betweenness: the fraction of shortest paths between other nodes passing through each node. Use to find brokers between groups. Supports directed and undirected graphs. By default weights are ignored; weighted=true treats finite positive weights as distances. Returns up to top_k node references with six-decimal scores, ordered by descending score then ascending ID. Endpoints are excluded.

## Parameters

| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | required | ID of the graph to analyse. |
| top_k | integer | 10 | Maximum entries per result list; byte limit may reduce this further. |
| normalized | boolean | true | Normalize by possible endpoint pairs, including unreachable pairs. |
| weighted | boolean | false | Treat edge weights as positive distances; false counts hops. |

## Algorithm and complexity
Exact Brandes accumulation runs a shortest-path search from every source,
records all shortest-path predecessors and path counts, then propagates
fractional dependencies backwards. BFS handles hop counts; heap-based Dijkstra
handles positive weighted distances. Endpoints are excluded. No sampling is used.
Undirected raw scores are divided by two; normalized scores use ordered
accumulations divided by (n-1)(n-2). Graphs with fewer than three nodes score zero.
Disconnected pairs contribute zero but remain in the normalization denominator.

Unweighted time is O(V(V + E)); weighted time is O(V(V + E) log V) with a binary
heap. Auxiliary space is O(V + E). Path counts use Python integers. Weighted
path ties use exact floating-point equality (as in the reference implementation);
integer edge lengths are preferable when exact ties matter. Weights mean
lengths, not strengths: co-occurrence counts may be better analysed unweighted.

## Example questions
- Which karate club members connect otherwise separate groups?
- Which airports lie on the most shortest-distance routes?

## Output
`result` is a list such as `[{"id":"m1","label":"Mr. Hi (instructor)","score":0.437635}]`.
Scores are rounded to six decimals before descending-score/ascending-ID sorting,
so ties at reported precision are stable. At most top_k entries are returned;
the byte budget may shorten the list further. Empty graphs return an empty list.
`result_graph_id` is null.

## Errors
Unknown/invalid graph ID, unknown parameters, invalid top_k, non-boolean options,
and (when weighted=true) zero, negative, or non-finite weights return errors.
Overflowing path distances or a single node label exceeding the output budget
also return errors. With weighted=false all edge weights are ignored.

## Verification

```bash
python -m graphkit.validate registry/tools/betweenness_centrality/f6f61ae0
python -m pytest registry/tools/betweenness_centrality/f6f61ae0/tests
```

Tests use NetworkX only as an independent reference; runtime code uses the standard library and graphkit.
