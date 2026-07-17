"""Build artist career timelines (output vs. influence per year).

This script creates a detailed career profile for each artist, tracking:
  - Output: how many works they created per year
  - Influence: how many works created by others drew from their works per year
  - Notable total: total count of their notable works

Output files:
  - artist_careers.json: one row per (artist, year) pair with counts
  - artist_careers_index.json: sorted list of all artists
"""

import json
from collections import defaultdict

SOURCE = "data/raw/MC1_graph.json"  # Main music graph data
DIFFUSION = "data/processed/genre_diffusion_edges.json"  # Pre-computed influence edges
CREATORS = "data/processed/work_creators.json"  # Mapping of works to their creators

OUT = "data/processed/artist_careers.json"  # Timeline of output + influence per artist
OUT_INDEX = "data/processed/artist_careers_index.json"  # Artist reference index

# Only these edge types represent artist creation
CREATION_TYPES = {
    "PerformerOf",
    "ComposerOf",
    "LyricistOf",
    "ProducerOf",
}

# ---------- LOAD DATA ----------
# Load the main music graph
with open(SOURCE, "r", encoding="utf-8") as f:
    data = json.load(f)

# Load pre-computed influence edges (which works influenced which works)
with open(DIFFUSION, "r", encoding="utf-8") as f:
    diffusion_edges = json.load(f)

# Load the work-to-creator mapping
with open(CREATORS, "r", encoding="utf-8") as f:
    work_creators = json.load(f)

# Index nodes by ID for O(1) lookup
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
                return int(value[:4])  # Extract YYYY from YYYY-MM-DD format
            except ValueError:
                continue

    return None


# ---------- COUNT ARTIST OUTPUT ----------
# Track: for each (artist, year), how many works they created
# Also track notable works and collect artist metadata
artist_meta = {}  # Store artist info (id, name, type)
artist_work_pairs = set()  # Dedup: artist might have multiple roles on same work

output_counts = defaultdict(lambda: defaultdict(int))  # output_counts[artist_id][year] = count
influence_counts = defaultdict(lambda: defaultdict(int))  # influence_counts[artist_id][year] = count
notable_totals = defaultdict(int)  # notable_totals[artist_id] = count

# Iterate through creation edges to count artist outputs
for edge in data["links"]:

    edge_type = edge.get("Edge Type")
    if edge_type not in CREATION_TYPES:
        continue

    artist = nodes_by_id.get(edge.get("source"))
    work = nodes_by_id.get(edge.get("target"))

    if not artist or not work:
        continue

    if artist.get("Node Type") not in ("Person", "MusicalGroup"):
        continue

    if work.get("Node Type") not in ("Song", "Album"):
        continue

    artist_id = artist.get("id")
    work_id = work.get("id")

    if artist_id is None or work_id is None:
        continue

    pair = (artist_id, work_id)

    # Skip if we've already counted this artist-work pair
    if pair in artist_work_pairs:
        continue

    artist_work_pairs.add(pair)

    # Count the work by its year
    y = year_of(work)

    if y is not None:
        output_counts[artist_id][y] += 1

    # Track if work is marked as notable
    if work.get("notable"):
        notable_totals[artist_id] += 1

    # Store artist metadata
    artist_meta[artist_id] = {
        "id": artist_id,
        "name": artist.get("name"),
        "type": artist.get("Node Type"),
    }

# ---------- COUNT INFLUENCE (How many works drew from each artist) ----------
# For each work, find its creators and count how many works influenced it
for row in diffusion_edges:

    try:
        year = int(str(row["year"])[:4])
    except (KeyError, TypeError, ValueError):
        continue

    # Get the creators of the TARGET work (the work being influenced)
    creators = (
            work_creators.get(str(row.get("to_id")))
            or work_creators.get(row.get("to_id"))
    )

    if not creators:
        continue

    seen = set()

    # For each creator of the influenced work, increment their influence count
    for creator in creators:

        artist_id = creator["artist_id"]

        if artist_id in seen:
            continue

        seen.add(artist_id)

        influence_counts[artist_id][year] += 1

        # Update artist metadata if not already known
        artist_meta.setdefault(
            artist_id,
            {
                "id": artist_id,
                "name": creator.get("artist_name"),
                "type": creator.get("artist_type"),
            },
        )

# ---------- BUILD OUTPUT ROWS ----------
# Combine all artists that appear in either output_counts or influence_counts
all_artist_ids = set(output_counts.keys()) | set(influence_counts.keys())

rows = []

for artist_id in all_artist_ids:

    meta = artist_meta.get(
        artist_id,
        {
            "id": artist_id,
            "name": None,
            "type": None,
        },
    )

    # Get all years where this artist had either output or influence
    years = sorted(
        set(output_counts.get(artist_id, {}).keys())
        | set(influence_counts.get(artist_id, {}).keys())
    )

    # Create one row per year
    for year in years:
        rows.append(
            {
                "artist_id": artist_id,
                "artist_name": meta["name"],
                "artist_type": meta["type"],
                "notable_total": notable_totals.get(artist_id, 0),
                "year": year,
                "output": output_counts.get(artist_id, {}).get(year, 0),
                "influence": influence_counts.get(artist_id, {}).get(year, 0),
            }
        )

# Sort by artist name, then year
rows.sort(
    key=lambda r: (
        (r["artist_name"] or "").lower(),
        r["year"],
    )
)

# ---------- BUILD ARTIST INDEX ----------
# Create a sorted reference of all artists for quick lookup
index = sorted(
    [
        {
            "id": meta["id"],
            "name": meta["name"],
            "type": meta["type"],
        }
        for meta in artist_meta.values()
        if meta["id"] in all_artist_ids
    ],
    key=lambda x: (x["name"] or "").lower(),
)

# ---------- SAVE OUTPUT ----------
# Write both the timeline rows and the artist index
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2)

with open(OUT_INDEX, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2)

print(f"{OUT}: {len(rows)} rows, {len(all_artist_ids)} artists")
print(f"{OUT_INDEX}: {len(index)} artists")
