# Sailor Shift Analysis (VAST Challenge 2025 – MC1)

A data visualization and network analysis project for the Oceanus music scene,
centered on artist Sailor Shift. This repository contains the graph data pipeline,
web-based Vue frontend, and output artifacts for analysis and reporting.

## Project structure

- `data/raw/`
  - Original input files from the challenge, including `MC1_graph.json`.
- `data/processed/`
  - Generated exports and cleaned project datasets used by the frontend.
- `frontend_src/`
  - Vue 3 + Vite application for interactive dashboards and visualizations.
- `src/`
  - Python build scripts for graph processing and dataset generation.
- `outputs/`
  - `figures/` — saved charts and images
  - `reports/` — write-ups, summaries, and final answers

## Setup

### Python

1. Create and activate a virtual environment.
2. Install Python dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the processing scripts as needed, for example:

```powershell
python src/build_sailor_network.py
python src/build_genre_diffusion.py
python src/build_genre_trends.py
python src/build_artist_careers.py
python src/build_talent_radar.py
python src/build_work_creators.py
```

### Frontend

1. Change to the frontend directory:

```powershell
cd frontend_src
```

2. Install frontend dependencies:

```powershell
npm install
```

3. Start the development server:

```powershell
npm run dev
```

## What this project includes

- Network analysis of Sailor Shift and her influence relationships
- Genre diffusion visualizations across the Oceanus music ecosystem
- Rising artist scoring and timeline comparisons
- A Vue-based dashboard with interactive charts, tables, and filters
- Exported build artifacts for use in reports and presentations

## Notes

- The repository currently uses a brand-new Git history after reinitialization.
- The frontend uses `d3`, `d3-sankey`, `vue`, `vue-router`, and `vite`.
- The Python pipeline uses `networkx`, `pandas`, `numpy`, `matplotlib`, and `scipy`.

## Contact

For project questions or troubleshooting, inspect the build scripts in `src/` and
the dashboard components in `frontend_src/src/components/`.
