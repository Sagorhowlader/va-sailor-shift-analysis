# Sailor Shift Analysis (VAST Challenge 2025 – MC1)

Directed multigraph of the Oceanus music scene: 17,412 nodes (Person, Song,
RecordLabel, Album, MusicalGroup) and 37,857 edges (PerformerOf, ComposerOf,
MemberOf, InStyleOf, InterpolatesFrom, etc.), centered on the artist Sailor Shift.

## Structure

- `data/raw/` — original files as provided (do not edit): `MC1_graph.json`,
  the official data description docx, and the answer sheet template.
- `data/processed/` — cleaned/derived data we generate during the project
  (e.g. filtered subgraphs, exported tables).
- `notebooks/` — exploratory analysis (Jupyter notebooks or scripts).
- `src/` — reusable Python modules/functions (loading, graph helpers, metrics).
- `outputs/figures/` — saved charts/plots.
- `outputs/reports/` — write-ups, summaries, final answers.

## Frontend (`frontend_src/`)

Vue 3 + Vite prototype ("VA_SAGOR"), sidebar + 7 modules, mapped to the official
MC1 tasks below.

## MC1 Task Map

| Brief task | Question | Frontend module |
|---|---|---|
| 1. Sailor's profile | Who influenced Sailor over time? Who has she collaborated with / influenced (directly & indirectly)? How has she influenced the wider Oceanus Folk community? | Influence Analysis |
| 2. Spread of Oceanus Folk | Gradual or intermittent rise? Which genres/artists most influenced by it? What does Oceanus Folk itself now draw on? | Genre Diffusion |
| 3. Rising-star profile | Compare 3 artists' rise in popularity/influence. Predict 3 future Oceanus Folk stars. | Talent Radar, Career Timeline, Findings &amp; Predictions |

Reflection questions (process, not visualization) will be answered separately in
`outputs/reports/`.

## Status

- [x] Dataset located and verified (VAST Challenge 2025 MC1).
- [x] Project directory structure set up.
- [x] Vue frontend skeleton (sidebar + routing + 5 placeholder modules).
- [x] Data dictionary / schema exploration (see `src/build_sailor_network.py` docstring
      for edge semantics: creation edges vs. influence edges).
- [x] Load graph and basic sanity checks (Python/networkx).
- [x] Task 1 analysis — Sailor's influence profile. All three Influence Analysis tabs
      live with real data: "Influenced by" (what fed into her work), "Her Impact"
      (who she influenced + collaborators), "Community Influence" (broader 2-hop network).
      Each tab has: node type / edge type / genre filters, name search with zoom-to-node,
      Notable radio filter, release-year range slider, network-depth slider, a radial
      layout by hop distance from Sailor, click-for-detail on nodes, and a Summary
      Statistics sub-tab (counts by type + most-connected nodes).
- [x] Task 2 analysis — Oceanus Folk diffusion. All three Genre Diffusion sub-tabs live:
      "Influence Trend" (multi-line chart of unique influencing works per year by genre),
      "Genre to Genre" (d3.chord diagram over a full genre-by-genre adjacency matrix, with
      pre/post-2028 "Sailor Shift Fame" year filters plus node/edge/genre filters), and
      "Top Influenced Artists" (d3-sankey Artist → Genre → selected-genre flow, ranked by
      Top N). All three reuse the same whole-graph export (`build_genre_diffusion.py`) and
      the artist attribution table (`build_work_creators.py`).
- [~] Task 3 analysis — rising-star profile. Talent Radar module live:
      `build_talent_radar.py` computes global PageRank/degree centrality (networkx),
      per-genre style similarity and notable-count, all normalized within each genre's
      candidate pool (Sailor Shift excluded from ranking — an "emerging artist" tool
      trivially always ranking the reigning superstar #1 isn't useful — but she's kept
      as a fixed radar baseline). Scoreboard + Radar Comparison (D3 spider chart) with
      user-adjustable score weights. Trend Dashboard module also live: `build_genre_trends.py`
      aggregates Song/Album counts per (genre, year) straight from node attributes (no edges
      needed) — Yearly Heatmap (D3, viridis scale) + Cumulative Curve, with genre/year-range
      filters, Song/Album layer toggle, and CSV export. Task 3.1 (compare 3 artists' rise
      in popularity/influence over time) is answered by the new Career Timeline module:
      `build_artist_careers.py` derives per-artist-per-year output (distinct Song/Album
      releases) and influence-received (incoming influence edges on their works, attributed
      via `work_creators.json`), for every artist with at least one work (11,581 artists).
      The view lets the user search/compare up to 3 artists (defaults to Sailor Shift vs.
      two ex-Ivy-Echoes bandmates) across two cumulative-curve charts (Popularity, Influence)
      plus a career-summary table. Note: ~1% of influence edges target a Person/MusicalGroup
      node directly rather than a specific work, and those artist nodes carry no date field,
      so that sliver of influence events can't be placed on the timeline (documented in the
      script's docstring, not silently dropped).
- [x] Task 3.2 — predictions. Findings & Predictions view: ranks the Oceanus Folk Talent
      Radar candidate pool by a blended score (0.6 x radar score + 0.4 x "recent output
      momentum" from the Career Timeline data), surfaces the top 3 as predicted next stars
      with a data-backed rationale sentence generated from their actual numbers, and plots
      their cumulative output. Weights are shown in the UI as tunable modeling choices, not
      hardcoded facts.
- [~] Reflection write-up. Drafted in the Findings & Predictions view (editable textareas,
      exportable to Markdown) from the real build process. The "did you do this challenge
      last year" question is left as a personal placeholder for the user to fill in.
- [x] Course project report (`outputs/reports/VA_SAGOR_Project_Report.docx`), 8 pages,
      covering the 5 points required by the exam rules: data description, design choices,
      state-of-the-art, detailed visualization/interaction description, and a use-case
      example. Fill in the student name/ID placeholders on the title page before sending.
