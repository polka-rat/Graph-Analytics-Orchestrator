# topological_sort

**Author:** c7c2ef65 · **Tier:** medium · **Category:** paths

## What it computes
An order of the nodes of a directed acyclic graph (DAG) in which every edge A→B puts A before B. On `courses`
(an edge A→B means A is a prerequisite of B), this is an order in which all courses can be taken. Uses Kahn's
algorithm: repeatedly take a node with no remaining incoming edges. Time O((V + E) log V).

## Highlights
- **Deterministic, and equal to NetworkX:** when several nodes are ready, a min-heap picks the smallest id,
  following the course rule that ties are broken by ascending node id. The order is exactly
  `nx.lexicographical_topological_sort`.
- **Levels in the same pass:** each node gets a `level`, the length of its longest chain of predecessors.
  Level 0 means no prerequisites, and nodes on the same level don't depend on each other, so they can be done
  in parallel. This answers "how many semesters do I need?" directly (courses: 5 levels).
- **Names the cycle:** if the graph is not a DAG, the error shows an actual cycle (airports:
  `ABJ -> ACC -> ABJ`), so the user sees *why* there is no order.
- **Bounded output:** at most 100 nodes are listed, to stay under 8 KB; the summary says when the list is cut.

## When to use it
Dependency and scheduling questions on a DAG:
- "In what order should I take these courses?"
- "Which courses have no prerequisites?" (level 0)
- "How many semesters does the longest prerequisite chain need?" (highest level + 1)

## Parameters
| Name | Type | Default | Meaning |
| --- | --- | --- | --- |
| graph_id | string | (required) | Id of a directed acyclic graph |

## Output
`result` is the list of nodes in order. Example for `{"graph_id": "courses"}`:

```json
[{"id": "CS101", "label": "Programming Basics", "position": 1, "level": 0},
 {"id": "CS102", "label": "Data Structures", "position": 2, "level": 1},
 {"id": "CS202", "label": "Computer Organisation", "position": 3, "level": 1}, "..."]
```
Summary: *Topological order of 21 nodes in 'courses' starts with Programming Basics and ends with Network
Science; the longest chain has 5 levels.*

`position` counts from 1. No `result_graph_id`.

## Graphs it supports
Directed acyclic graphs, weighted or not (weights ignored): `courses`, or any acyclic subgraph registered by
another tool. Undirected graphs and graphs with cycles have no topological order (see Errors).

## Errors
Each returns `status: "error"` with a message saying how to fix the call:
- Unknown `graph_id`: use `list_graphs`.
- Undirected graph: no topological order exists; use a directed acyclic graph such as `courses`.
- Graph with a cycle: the message names one cycle, e.g. `ABJ -> ACC -> ABJ` in airports.
- Unknown parameter, or a graph with no nodes.

## How it is tested
10 tests in `tests/`:
- order equals `nx.lexicographical_topological_sort`;
- every edge goes forward;
- levels equal the longest predecessor chains;
- works on a registered subgraph;
- the cycle in the error is a real cycle in the graph, even when a node after the cycle has the smallest id;
- every error case and determinism.
