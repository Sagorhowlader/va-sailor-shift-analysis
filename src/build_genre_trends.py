"""Build genre trend timelines by counting releases per genre per year.

Tracks how many songs and albums were released in each genre each year.
Used to visualize the rise and fall of musical genres over time.

Output: genre_trends.json - array of {genre, year, song_count, album_count}
"""

import json
from collections import defaultdict

SOURCE = "data/raw/MC1_graph.json"  # Main music graph
OUT = "data/processed/genre_trends.json"  # Output trends


# ---------- LOAD GRAPH ----------
with open(SOURCE, "r", encoding="utf-8") as f:
    data = json.load(f)


# ---------- HELPER FUNCTION ----------
def year_of(node):
    """Extract a 4-digit release year."""
    value = node.get("release_date")

    if not value:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        try:
            return int(value[:4])  # Handles YYYY and YYYY-MM-DD
        except ValueError:
            return None

    return None


# ---------- COUNT RELEASES BY GENRE AND YEAR ----------
counts = defaultdict(lambda: {"song_count": 0, "album_count": 0})

# Iterate through all nodes and count by type, genre, year
for node in data["nodes"]:

    node_type = node.get("Node Type")

    # Only count songs and albums
    if node_type not in ("Song", "Album"):
        continue

    genre = node.get("genre")
    year = year_of(node)

    # Skip if missing genre or year
    if not genre or year is None:
        continue

    key = (genre, year)

    # Increment the appropriate counter
    if node_type == "Song":
        counts[key]["song_count"] += 1
    else:
        counts[key]["album_count"] += 1


# ---------- CONVERT TO OUTPUT FORMAT ----------
rows = []

for (genre, year), values in counts.items():
    rows.append(
        {
            "genre": genre,
            "year": year,
            "song_count": values["song_count"],
            "album_count": values["album_count"],
        }
    )

# Sort by genre name, then year
rows.sort(key=lambda r: (r["genre"].lower(), r["year"]))


# ---------- SAVE OUTPUT ----------
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2)

print(
    f"{OUT}: {len(rows)} (genre, year) rows across "
    f"{len({r['genre'] for r in rows})} genres"
)