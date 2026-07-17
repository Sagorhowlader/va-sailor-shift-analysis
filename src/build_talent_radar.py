"""Build talent radar: rising stars in each genre for comparison with Sailor.

For each genre with sufficient artists:
  - Rank artists by pagerank (influence) and notability
  - Compute normalized metrics: pagerank, degree centrality, style similarity, notability
  - Compare Sailor's metrics to candidates in that genre

Output: talent_radar.json - {genre: {candidates: [...], sailor: {...}}}
"""

import json
import networkx as nx
from collections import defaultdict

SOURCE = "data/raw/MC1_graph.json"  # Main music graph
OUT = "data/processed/talent_radar.json"  # Output candidates

# Edge types representing artist creation
CREATION_TYPES = {
    "PerformerOf",
    "ComposerOf",
    "LyricistOf",
    "ProducerOf",
}

SAILOR_NAME = "Sailor Shift"  # Reference artist
MIN_POOL_SIZE = 3  # Minimum artists required to include genre


# ---------- LOAD GRAPH ----------
with open(SOURCE, "r", encoding="utf-8") as f:
    data = json.load(f)

# Index nodes by ID
nodes_by_id = {node["id"]: node for node in data["nodes"]}

# Find Sailor Shift
sailor = next(
    (node for node in data["nodes"] if node.get("name") == SAILOR_NAME),
    None,
)

if sailor is None:
    raise ValueError(f'Artist "{SAILOR_NAME}" not found.')

sailor_id = sailor["id"]


# ---------- COMPUTE GLOBAL NETWORK METRICS ----------
# Build directed graph and compute pagerank and degree centrality
G = nx.DiGraph()

for node in data["nodes"]:
    G.add_node(node["id"])

for edge in data["links"]:
    G.add_edge(edge["source"], edge["target"])

# Pagerank: importance based on incoming links
pagerank = nx.pagerank(G)
# Degree centrality: normalized in/out degree
degree_centrality = nx.degree_centrality(G)


# ---------- BUILD PERSON-TO-WORKS MAPPING ----------
# Index all works created by each person
person_works = defaultdict(dict)

for edge in data["links"]:

    if edge.get("Edge Type") not in CREATION_TYPES:
        continue

    person = nodes_by_id.get(edge.get("source"))
    work = nodes_by_id.get(edge.get("target"))

    if person is None or work is None:
        continue

    if person.get("Node Type") != "Person":
        continue

    if work.get("Node Type") not in ("Song", "Album"):
        continue

    # Use dict to avoid duplicate works (one person may have multiple roles)
    person_works[person["id"]][work["id"]] = work

# Convert to lists
person_works = {
    pid: list(works.values())
    for pid, works in person_works.items()
}


# ---------- EXTRACT ALL GENRES ----------
all_genres = sorted(
    {
        work.get("genre")
        for works in person_works.values()
        for work in works
        if work.get("genre")
    }
)


# ---------- METRIC COMPUTATION FUNCTION ----------
def metrics_for(pid, genre, max_pr, max_dc, max_notable):
    """Compute normalized metrics for an artist in a specific genre."""

    works = person_works.get(pid, [])

    # Filter works to this genre
    genre_works = [
        work
        for work in works
        if work.get("genre") == genre
    ]

    # Style similarity: what fraction of this person's works are in this genre
    style_similarity = (
        len(genre_works) / len(works)
        if works
        else 0
    )

    # Count notable works in this genre
    notable_count = sum(
        1
        for work in genre_works
        if work.get("notable")
    )

    return {
        "id": pid,
        "name": nodes_by_id[pid].get("name"),
        "pagerank": round(
            pagerank.get(pid, 0) / max_pr,
            4,
        ) if max_pr else 0,
        "degree": round(
            degree_centrality.get(pid, 0) / max_dc,
            4,
        ) if max_dc else 0,
        "style_sim": round(style_similarity, 4),
        "notable_count": notable_count,
        "notable_count_norm": round(
            notable_count / max_notable,
            4,
        ) if max_notable else 0,
        "work_count": len(genre_works),
    }


# ---------- BUILD OUTPUT FOR EACH GENRE ----------
output = {}

for genre in all_genres:

    # Get all artists with works in this genre
    pool = [
        pid
        for pid, works in person_works.items()
        if any(work.get("genre") == genre for work in works)
    ]

    # Exclude Sailor Shift from candidate pool
    candidate_pool = [
        pid
        for pid in pool
        if pid != sailor_id
    ]

    # Skip if genre doesn't have enough artists
    if len(candidate_pool) < MIN_POOL_SIZE:
        continue

    # Compute max values for normalization
    max_pr = max(
        (pagerank.get(pid, 0) for pid in pool),
        default=0,
    )

    max_dc = max(
        (degree_centrality.get(pid, 0) for pid in pool),
        default=0,
    )

    max_notable = max(
        (
            sum(
                1
                for work in person_works[pid]
                if work.get("genre") == genre
                and work.get("notable")
            )
            for pid in pool
        ),
        default=0,
    )

    # Compute metrics for all candidates
    candidates = [
        metrics_for(
            pid,
            genre,
            max_pr,
            max_dc,
            max_notable,
        )
        for pid in candidate_pool
    ]

    # Sort by importance: pagerank desc, notability desc, name asc
    candidates.sort(
        key=lambda x: (
            -x["pagerank"],
            -x["notable_count"],
            x["name"] or "",
        )
    )

    # Compute Sailor's metrics in this genre (if she has works in it)
    sailor_metrics = (
        metrics_for(
            sailor_id,
            genre,
            max_pr,
            max_dc,
            max_notable,
        )
        if sailor_id in pool
        else None
    )

    output[genre] = {
        "candidates": candidates,
        "sailor": sailor_metrics,
    }


# ---------- SAVE OUTPUT ----------
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

total_candidates = sum(
    len(value["candidates"])
    for value in output.values()
)

print(
    f"{OUT}: {len(output)} genres, "
    f"{total_candidates} candidate rows"
)