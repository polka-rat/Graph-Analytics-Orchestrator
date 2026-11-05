# Datasets

Load these only through the graph store: `GraphStore().get("<graph_id>")`. `graphs.json` describes each graph.

| graph_id | Nodes | Edges | Directed | Weighted | Nodes are | Source |
| --- | --- | --- | --- | --- | --- | --- |
| airports | 500 | 20,058 | yes | yes (km) | Airports, id = IATA code | OpenFlights, 2014 snapshot |
| karate | 34 | 78 | no | no | Members of a karate club | Zachary (1977) |
| lesmis | 77 | 254 | no | yes | Characters in Les Misérables | Knuth, Stanford GraphBase (1993) |
| courses | 21 | 29 | yes (acyclic) | no | Courses; edge = prerequisite | Synthetic sample |
| projects | 26 | 28 | no (bipartite) | no | Students and projects | Synthetic sample |

**airports.** The 500 airports with the most non-stop routes in OpenFlights; routes to other airports are left out, so counts are lower than in the full data. An edge A→B is a non-stop route; `weight` is the great-circle distance in km and the edge attribute `airlines` is the number of airlines flying it. Node attributes: `city`, `country`, `lat`, `lon`. The data is a 2014 snapshot, so answers describe the network then, not today's schedules. Source: [OpenFlights](https://openflights.org/data.html), under the Open Database License (ODbL).

**karate.** Friendships among the 34 members of a university karate club before it split in two; node attribute `club` records which side each member joined. Member 1 is the instructor and member 34 the administrator. Source: W. W. Zachary, "An information flow model for conflict and fission in small groups" (1977).

**lesmis.** Characters who appear together in chapters of Victor Hugo's *Les Misérables*; `weight` is the number of shared chapters. Source: D. E. Knuth, *The Stanford GraphBase* (1993).

**courses** and **projects** are small synthetic samples for algorithms that need a directed acyclic graph (topological sort) or a bipartite graph (matching). They are illustrative, not real data.

Small graphs are for checking correctness; airports is the largest dataset and sets the 30-second time limit.
