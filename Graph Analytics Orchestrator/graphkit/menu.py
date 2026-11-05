"""The Assignment 3 tool menu: name -> (tier, category, returns_subgraph)."""

CATEGORIES = ("paths", "centrality", "community", "structure", "subgraph", "infrastructure")
TIERS = ("easy", "medium", "hard", "infra")
POINTS = {"easy": 1, "medium": 2, "hard": 3}

MENU = {
    # Easy (1 point)
    "graph_summary": ("easy", "structure", False),
    "degree_centrality": ("easy", "centrality", False),
    "degree_distribution": ("easy", "structure", False),
    "k_hop_neighborhood": ("easy", "subgraph", True),
    "ego_network": ("easy", "subgraph", True),
    "reachability": ("easy", "paths", False),
    "shortest_path_unweighted": ("easy", "paths", False),
    "connected_components": ("easy", "community", True),
    "clustering_coefficient": ("easy", "structure", False),
    "node_similarity": ("easy", "structure", False),
    # Medium (2 points)
    "shortest_path_weighted": ("medium", "paths", False),
    "pagerank": ("medium", "centrality", False),
    "personalized_pagerank": ("medium", "centrality", False),
    "hits": ("medium", "centrality", False),
    "closeness_centrality": ("medium", "centrality", False),
    "strongly_connected_components": ("medium", "community", True),
    "topological_sort": ("medium", "paths", False),
    "minimum_spanning_tree": ("medium", "structure", True),
    "diameter_eccentricity": ("medium", "paths", False),
    "bipartite_check": ("medium", "structure", True),
    "articulation_points_bridges": ("medium", "structure", False),
    "k_core": ("medium", "community", True),
    "label_propagation": ("medium", "community", True),
    "link_prediction": ("medium", "structure", False),
    "greedy_coloring": ("medium", "structure", False),
    # Hard (3 points)
    "betweenness_centrality": ("hard", "centrality", False),
    "louvain": ("hard", "community", True),
    "girvan_newman": ("hard", "community", True),
    "max_flow_min_cut": ("hard", "paths", False),
    "bipartite_matching": ("hard", "structure", False),
    "maximal_cliques": ("hard", "community", True),
    "motif_count": ("hard", "structure", False),
    "node_embedding_similarity": ("hard", "structure", False),
}

# Provided by the instructors; not on the menu.
INFRA_TOOLS = ("list_graphs", "lookup_node", "node_attributes", "filter_nodes")
