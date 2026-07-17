"""Build Sailor Shift-centered network subgraphs for influence analysis.

Creates three JSON network files centered on the artist "Sailor Shift":

1. sailor_ego_network.json: Generic 2-hop neighborhood (all neighbors)
2. sailor_influenced_by.json: Works/people that influenced Sailor's work
3. sailor_her_impact.json: Works/people influenced by Sailor's work + collaborators

Each includes nodes and edges with depth metadata (distance from Sailor).

Schema notes:
  - Creation edges (PerformerOf, ComposerOf, etc.): artist → work they created
  - Influence edges (InStyleOf, InterpolatesFrom, etc.): newer work → older work it draws from
"""

import json
import collections
import networkx as nx

SOURCE = "data/raw/MC1_graph.json"  # Full music graph

SAILOR_NAME = "Sailor Shift"  # Central artist
EGO_RADIUS = 2  # Hops for ego network

# Edge types representing artist creation
CREATION_TYPES = {
    "PerformerOf",
    "ComposerOf",
    "LyricistOf",
    "ProducerOf",
}

# Edge types representing influence (source influenced by target)
INFLUENCE_TYPES = {
    "InStyleOf",
    "InterpolatesFrom",
    "CoverOf",
    "LyricalReferenceTo",
    "DirectlySamples",
}


# ---------- LOAD GRAPH ----------
with open(SOURCE, "r", encoding="utf-8") as f:
    data = json.load(f)

# Index nodes by ID
nodes_by_id = {n["id"]: n for n in data["nodes"]}
links = data["links"]

# Find Sailor Shift in the graph
sailor = next(
    (n for n in data["nodes"] if n.get("name") == SAILOR_NAME),
    None,
)

if sailor is None:
    raise ValueError(f'Artist "{SAILOR_NAME}" not found.')

sailor_id = sailor["id"]


# ---------- HELPER FUNCTIONS ----------

def node_record(node_id):
    """Convert a node to export format."""
    node = nodes_by_id[node_id]
    return {
        "id": node_id,
        "name": node.get("name"),
        "type": node.get("Node Type"),
        "genre": node.get("genre"),
        "release_date": node.get("release_date"),
        "notable": node.get("notable"),
    }


def edge_record(edge):
    """Convert an edge to export format."""
    return {
        "source": edge["source"],
        "target": edge["target"],
        "type": edge.get("Edge Type"),
    }


def creation_edges_from(person_id):
    """Get all creation edges from a person."""
    return [
        e
        for e in links
        if e.get("source") == person_id
        and e.get("Edge Type") in CREATION_TYPES
    ]


def creators_of(work_id):
    """Get all creators of a work."""
    return [
        e
        for e in links
        if e.get("target") == work_id
        and e.get("Edge Type") in CREATION_TYPES
    ]


def export(filename, node_ids, edges):
    """Export a network as JSON with deduped edges."""

    edge_keys = set()
    unique_edges = []

    # Deduplicate edges (same source, target, type)
    for edge in edges:
        key = (
            edge["source"],
            edge["target"],
            edge.get("Edge Type"),
        )

        if key in edge_keys:
            continue

        edge_keys.add(key)
        unique_edges.append(edge)

    # Build payload
    payload = {
        "center": sailor_id,
        "nodes": [node_record(n) for n in sorted(node_ids)],
        "edges": [edge_record(e) for e in unique_edges],
    }

    # Write to file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(
        f"{filename}: "
        f"{len(payload['nodes'])} nodes, "
        f"{len(payload['edges'])} edges"
    )


# ---------- BUILD NETWORK 1: EGO NETWORK ----------
# All neighbors within 2 hops (generic 2-hop neighborhood)
G = nx.MultiDiGraph()

for node in data["nodes"]:
    G.add_node(node["id"], **node)

for edge in links:
    attrs = {
        k: v
        for k, v in edge.items()
        if k not in ("source", "target", "key")
    }

    G.add_edge(
        edge["source"],
        edge["target"],
        key=edge.get("key"),
        **attrs,
    )

# Get ego network (undirected to find 2-hop neighbors)
ego_nodes = set(
    nx.ego_graph(
        G.to_undirected(),
        sailor_id,
        radius=EGO_RADIUS,
    ).nodes()
)

# Get edges between nodes in ego network
ego_edges = [
    {
        "source": u,
        "target": v,
        "Edge Type": d.get("Edge Type"),
    }
    for u, v, _, d in G.edges(keys=True, data=True)
    if u in ego_nodes and v in ego_nodes
]

export("data/processed/sailor_ego_network.json", ego_nodes, ego_edges)


# ---------- GET SAILOR'S WORKS ----------
# Find all works Sailor created
sailor_creation_edges = creation_edges_from(sailor_id)

her_works = {
    e["target"]
    for e in sailor_creation_edges
}


# ---------- BUILD NETWORK 2: INFLUENCED BY ----------
# What/who fed into Sailor's work
ib_nodes = {sailor_id} | her_works
ib_edges = list(sailor_creation_edges)

# Influence edges pointing FROM Sailor
direct = [
    e
    for e in links
    if e.get("source") == sailor_id
    and e.get("Edge Type") in INFLUENCE_TYPES
]

# Influence edges pointing FROM Sailor's works
via_work = [
    e
    for e in links
    if e.get("source") in her_works
    and e.get("Edge Type") in INFLUENCE_TYPES
]

ib_edges.extend(direct)
ib_edges.extend(via_work)

# Collect works that influenced Sailor
influencing_works = {
    e["target"]
    for e in direct + via_work
}

ib_nodes |= influencing_works

# Add creators of influencing works
for work in influencing_works:
    for edge in creators_of(work):
        ib_nodes.add(edge["source"])
        ib_edges.append(edge)

export(
    "data/processed/sailor_influenced_by.json",
    ib_nodes,
    ib_edges,
)


# ---------- BUILD NETWORK 3: HER IMPACT ----------
# Who Sailor's work influenced + her collaborators
hi_nodes = {sailor_id} | her_works
hi_edges = list(sailor_creation_edges)

# Influence edges pointing TO Sailor (direct)
direct = [
    e
    for e in links
    if e.get("target") == sailor_id
    and e.get("Edge Type") in INFLUENCE_TYPES
]

# Influence edges pointing TO Sailor's works (via work)
via_work = [
    e
    for e in links
    if e.get("target") in her_works
    and e.get("Edge Type") in INFLUENCE_TYPES
]

hi_edges.extend(direct)
hi_edges.extend(via_work)

# Collect works impacted by Sailor
impacted_works = {
    e["source"]
    for e in direct + via_work
}

hi_nodes |= impacted_works

# Add creators of impacted works
for work in impacted_works:
    for edge in creators_of(work):
        hi_nodes.add(edge["source"])
        hi_edges.append(edge)

# Add collaborators (other artists who worked on Sailor's works)
collaborators = [
    e
    for e in links
    if e.get("target") in her_works
    and e.get("Edge Type") in CREATION_TYPES
    and e.get("source") != sailor_id
]

hi_edges.extend(collaborators)

hi_nodes |= {
    e["source"]
    for e in collaborators
}

export(
    "data/processed/sailor_her_impact.json",
    hi_nodes,
    hi_edges,
)


# ---------- ADD BFS DEPTH METADATA ----------
# For each network, add depth field: distance from Sailor using BFS
def add_depth(filename):
    """Add depth metadata (distance from center) to all nodes."""

    # Load the network
    with open(filename, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Build adjacency list (treating as undirected)
    graph = collections.defaultdict(set)

    for edge in payload["edges"]:
        graph[edge["source"]].add(edge["target"])
        graph[edge["target"]].add(edge["source"])

    # BFS from center to compute depth
    depth = {payload["center"]: 0}

    queue = collections.deque([payload["center"]])

    while queue:

        current = queue.popleft()

        for neighbour in graph[current]:

            if neighbour in depth:
                continue

            depth[neighbour] = depth[current] + 1
            queue.append(neighbour)

    # Add depth to each node
    for node in payload["nodes"]:
        node["depth"] = depth.get(node["id"], -1)

    # Save updated network
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(
        f"{filename}: max depth {max(depth.values(), default=0)}"
    )


# Add depth to all three networks
for filename in (
    "data/processed/sailor_ego_network.json",
    "data/processed/sailor_influenced_by.json",
    "data/processed/sailor_her_impact.json",
):
    add_depth(filename)