"""Build a mapping of works to their creators for quick lookup.

For each work that is a target of an influence edge:
  - Find all creators (artists with creation edges)
  - Map work ID → [{artist_id, artist_name, artist_type, edge_type}, ...]

Used to quickly look up who created any influenced work.

Output: work_creators.json - {work_id: [{artist_id, artist_name, ...}, ...]}
"""

import json

SOURCE = "data/raw/MC1_graph.json"  # Main music graph
DIFFUSION = "data/processed/genre_diffusion_edges.json"  # Pre-computed influence edges
OUT = "data/processed/work_creators.json"  # Output mapping

# Edge types representing artist creation
CREATION_TYPES = {
    "PerformerOf",
    "ComposerOf",
    "LyricistOf",
    "ProducerOf",
}

# Valid artist types
ARTIST_TYPES = {"Person", "MusicalGroup"}


# ---------- LOAD DATA ----------
with open(SOURCE, "r", encoding="utf-8") as f:
    data = json.load(f)

with open(DIFFUSION, "r", encoding="utf-8") as f:
    diffusion_edges = json.load(f)

# Index nodes by ID
nodes_by_id = {node["id"]: node for node in data["nodes"]}

# Only works that are targets of influence edges (works that were influenced)
target_work_ids = {
    row["to_id"]
    for row in diffusion_edges
}


# ---------- BUILD CREATOR MAPPING ----------
result = {}

# Track seen (work, artist, role) combinations to prevent duplicates
seen = set()

# For each creation edge, map the work to its creator
for edge in data["links"]:

    if edge.get("Edge Type") not in CREATION_TYPES:
        continue

    work_id = edge.get("target")

    # Only track creators of works that were influenced
    if work_id not in target_work_ids:
        continue

    artist = nodes_by_id.get(edge.get("source"))

    if artist is None:
        continue

    if artist.get("Node Type") not in ARTIST_TYPES:
        continue

    # Create a unique key to prevent duplicates
    key = (
        work_id,
        artist["id"],
        edge.get("Edge Type"),
    )

    if key in seen:
        continue

    seen.add(key)

    # Add creator to the work's creator list
    result.setdefault(str(work_id), []).append(
        {
            "artist_id": artist["id"],
            "artist_name": artist.get("name"),
            "artist_type": artist.get("Node Type"),
            "edge_type": edge.get("Edge Type"),
        }
    )


# ---------- SORT FOR DETERMINISTIC OUTPUT ----------
# Sort creators for each work by name and role
for creators in result.values():
    creators.sort(
        key=lambda x: (
            x["artist_name"] or "",
            x["edge_type"],
        )
    )


# ---------- SAVE OUTPUT ----------
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

total_links = sum(len(creators) for creators in result.values())

print(f"{OUT}: {len(result)} works, {total_links} creator links")