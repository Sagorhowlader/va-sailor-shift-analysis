"""Build a flat table of work-to-work influence edges for genre diffusion analysis.

This script extracts all "influence" edges (e.g., work A is in the style of work B)
and formats them as a table where:
  - FROM: the newer/derivative work
  - TO: the work it draws from
  - year: release year of the FROM work (when the diffusion event occurred)

Used to analyze how Oceanus Folk music influenced other genres and vice versa.

Output: genre_diffusion_edges.json - array of {year, from_id, from_name, from_genre, ...}
"""

import json

SOURCE = "data/raw/MC1_graph.json"  # Main music graph
OUT = "data/processed/genre_diffusion_edges.json"  # Output table

# Influence edge types: FROM work is influenced by TO work
INFLUENCE_TYPES = {
    "InStyleOf",
    "InterpolatesFrom",
    "CoverOf",
    "LyricalReferenceTo",
    "DirectlySamples",
}

# Only work-to-work edges (songs and albums)
WORK_TYPES = {"Song", "Album"}


# ---------- LOAD GRAPH ----------
with open(SOURCE, "r", encoding="utf-8") as f:
    data = json.load(f)

# Index nodes by ID for quick lookup
nodes_by_id = {node["id"]: node for node in data["nodes"]}


# ---------- HELPER FUNCTION ----------
def year_of(node):
    """Extract a 4-digit year from a node, checking multiple date fields."""
    for field in ("release_date", "written_date", "notoriety_date"):
        value = node.get(field)

        if not value:
            continue

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            try:
                return int(value[:4])  # Handles YYYY and YYYY-MM-DD
            except ValueError:
                continue

    return None


# ---------- BUILD INFLUENCE TABLE ----------
# Extract all work-to-work influence edges
rows = []

for edge in data["links"]:

    # Filter for influence edges only
    if edge.get("Edge Type") not in INFLUENCE_TYPES:
        continue

    # Get source (FROM: newer work) and target (TO: older work)
    source = nodes_by_id.get(edge.get("source"))
    target = nodes_by_id.get(edge.get("target"))

    if source is None or target is None:
        continue

    # Ensure both are works (not persons or labels)
    if source.get("Node Type") not in WORK_TYPES:
        continue

    if target.get("Node Type") not in WORK_TYPES:
        continue

    # Add row with all relevant metadata
    rows.append(
        {
            "year": year_of(source),  # When the FROM work was created
            "from_id": source["id"],  # Newer work
            "from_name": source.get("name"),
            "from_type": source.get("Node Type"),
            "from_genre": source.get("genre"),
            "to_id": target["id"],  # Older work (source of influence)
            "to_name": target.get("name"),
            "to_type": target.get("Node Type"),
            "to_genre": target.get("genre"),
            "to_release_date": target.get("release_date"),
            "edge_type": edge.get("Edge Type"),
        }
    )


# ---------- SORT BY YEAR AND NAME ----------
rows.sort(
    key=lambda r: (
        r["year"] if r["year"] is not None else 9999,  # Nulls last
        r["from_name"] or "",
        r["to_name"] or "",
    )
)


# ---------- SAVE OUTPUT ----------
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2)

print(f"{OUT}: {len(rows)} rows")