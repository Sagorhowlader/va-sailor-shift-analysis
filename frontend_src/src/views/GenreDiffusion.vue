<script setup>
import { ref, computed, onMounted } from 'vue'
import * as d3 from 'd3'
import MultiSelect from '../components/MultiSelect.vue'
import TrendLineChart from '../components/TrendLineChart.vue'
import DataTable from '../components/DataTable.vue'
import SankeyChart from '../components/SankeyChart.vue'
import RangeSlider from '../components/RangeSlider.vue'
import ChordDiagram from '../components/ChordDiagram.vue'
import { makeCategoryColorScale } from '../utils/colorScale'

const CREATION_TYPES = ['PerformerOf', 'ComposerOf', 'LyricistOf', 'ProducerOf']
const INFLUENCE_TYPES = ['InStyleOf', 'InterpolatesFrom', 'CoverOf', 'LyricalReferenceTo', 'DirectlySamples']
const SAILOR_FAME_YEAR = 2028

const subtabs = ['Influence Trend', 'Genre to Genre', 'Top Influenced Artists']
const activeSubtab = ref('Influence Trend')

const loading = ref(true)
const error = ref(null)
const allRows = ref([])
const workCreators = ref({}) // to_id (string) -> [{artist_id, artist_name, artist_type, edge_type}]

const genres = computed(() => [...new Set(allRows.value.map((r) => r.to_genre).filter(Boolean))].sort())
const allGenres = computed(() =>
  [...new Set(allRows.value.flatMap((r) => [r.from_genre, r.to_genre]).filter(Boolean))].sort()
)

// --- Genre to Genre state ---
const yearBounds = ref([1980, 2040])
const preRange = ref([1980, SAILOR_FAME_YEAR])
const postRange = ref([SAILOR_FAME_YEAR, 2040])
const chordFromNodeTypes = ref(['Song', 'Album'])
const chordToNodeTypes = ref(['Song', 'Album'])
const chordEdgeTypes = ref([...INFLUENCE_TYPES])
const chordFromGenres = ref([])
const chordToGenres = ref([])

// --- Influence Trend state ---
const influenceGenre = ref('Oceanus Folk')
const fromNodeType = ref('Both') // 'Both' | 'Song' | 'Album'

// --- Top Influenced Artists state ---
const sankeyGenre = ref('Oceanus Folk')
const topN = ref(25)
const sankeyEdgeTypes = ref([...CREATION_TYPES])

onMounted(async () => {
  try {
    const [edgesRes, creatorsRes] = await Promise.all([
      fetch('/data/genre_diffusion_edges.json'),
      fetch('/data/work_creators.json'),
    ])
    if (!edgesRes.ok) throw new Error('Failed to load genre diffusion data')
    if (!creatorsRes.ok) throw new Error('Failed to load artist attribution data')
    allRows.value = await edgesRes.json()
    workCreators.value = await creatorsRes.json()
    if (!genres.value.includes(influenceGenre.value)) influenceGenre.value = genres.value[0] || ''
    if (!genres.value.includes(sankeyGenre.value)) sankeyGenre.value = genres.value[0] || ''

    const years = allRows.value.map((r) => r.year).filter((y) => y != null)
    if (years.length) {
      const lo = Math.min(...years)
      const hi = Math.max(...years)
      yearBounds.value = [lo, hi]
      preRange.value = [lo, SAILOR_FAME_YEAR]
      postRange.value = [SAILOR_FAME_YEAR, hi]
    }
    chordFromGenres.value = [...allGenres.value]
    chordToGenres.value = [...allGenres.value]
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

// ============================== Influence Trend ==============================
const filteredRows = computed(() => {
  return allRows.value.filter((r) => {
    if (r.to_genre !== influenceGenre.value) return false
    if (fromNodeType.value !== 'Both' && r.from_type !== fromNodeType.value) return false
    return true
  })
})

const series = computed(() => {
  const byGenreYear = new Map()
  filteredRows.value.forEach((r) => {
    if (!r.year || !r.from_genre) return
    if (!byGenreYear.has(r.from_genre)) byGenreYear.set(r.from_genre, new Map())
    const yearMap = byGenreYear.get(r.from_genre)
    if (!yearMap.has(r.year)) yearMap.set(r.year, new Set())
    yearMap.get(r.year).add(r.from_id)
  })

  return [...byGenreYear.entries()]
    .map(([genre, yearMap]) => ({
      genre,
      points: [...yearMap.entries()]
        .map(([year, ids]) => ({ year, count: ids.size }))
        .sort((a, b) => a.year - b.year),
    }))
    .sort((a, b) => d3.sum(b.points, (p) => p.count) - d3.sum(a.points, (p) => p.count))
})

const legendGenres = computed(() => series.value.map((s) => s.genre))
const legendColorScale = computed(() => makeCategoryColorScale(legendGenres.value))
function legendColor(genre) {
  return legendColorScale.value(genre)
}

const tableColumns = [
  { key: 'year', label: 'Year' },
  { key: 'from_name', label: 'From_Node' },
  { key: 'from_type', label: 'From_Type' },
  { key: 'to_name', label: 'To_Node' },
  { key: 'to_type', label: 'To_Type' },
  { key: 'edge_type', label: 'Edge_Type' },
  { key: 'to_release_date', label: 'To_Release_Date' },
  { key: 'to_genre', label: 'To_Genre' },
]

// ============================== Genre to Genre ==============================
const chordFilteredRows = computed(() => {
  return allRows.value.filter((r) => {
    if (!r.from_genre || !r.to_genre) return false
    if (!chordFromNodeTypes.value.includes(r.from_type)) return false
    if (!chordToNodeTypes.value.includes(r.to_type)) return false
    if (!chordEdgeTypes.value.includes(r.edge_type)) return false
    if (!chordFromGenres.value.includes(r.from_genre)) return false
    if (!chordToGenres.value.includes(r.to_genre)) return false
    if (r.year == null) return false
    const inPre = r.year >= preRange.value[0] && r.year <= preRange.value[1]
    const inPost = r.year >= postRange.value[0] && r.year <= postRange.value[1]
    return inPre || inPost
  })
})

// aggregated rows for the data table: one row per (from_genre, from_type, to_genre, to_type, edge_type)
const chordTableRows = computed(() => {
  const counts = new Map()
  chordFilteredRows.value.forEach((r) => {
    const key = [r.from_genre, r.from_type, r.to_genre, r.to_type, r.edge_type].join('|')
    if (!counts.has(key)) {
      counts.set(key, {
        from_genre: r.from_genre,
        from_type: r.from_type,
        to_genre: r.to_genre,
        to_type: r.to_type,
        edge_type: r.edge_type,
        count: 0,
      })
    }
    counts.get(key).count += 1
  })
  return [...counts.values()].sort((a, b) => b.count - a.count)
})

const chordTableColumns = [
  { key: 'from_genre', label: 'From Genre' },
  { key: 'from_type', label: 'From Node Type' },
  { key: 'to_genre', label: 'To Genre' },
  { key: 'to_type', label: 'To Node Type' },
  { key: 'edge_type', label: 'Edge Type' },
  { key: 'count', label: 'Count' },
]

// genre-by-genre adjacency matrix for the chord diagram
const chordGenreList = computed(() => {
  const present = new Set()
  chordFilteredRows.value.forEach((r) => {
    present.add(r.from_genre)
    present.add(r.to_genre)
  })
  return [...present].sort()
})

const chordMatrix = computed(() => {
  const idx = new Map(chordGenreList.value.map((g, i) => [g, i]))
  const n = chordGenreList.value.length
  const m = Array.from({ length: n }, () => new Array(n).fill(0))
  chordFilteredRows.value.forEach((r) => {
    const i = idx.get(r.from_genre)
    const j = idx.get(r.to_genre)
    if (i === undefined || j === undefined) return
    m[i][j] += 1
  })
  return m
})

// =========================== Top Influenced Artists ===========================
// Flow: Artist --(created a work of genre G)--> Genre G --> sankeyGenre
// Rows where FROM is a sankeyGenre work, drawing from a DIFFERENT genre's work (the "to" side).
// The "to" work's creators are the artists who fed into sankeyGenre.
const inboundRows = computed(() =>
  allRows.value.filter((r) => r.from_genre === sankeyGenre.value && r.to_genre && r.to_genre !== sankeyGenre.value)
)

const sankeyData = computed(() => {
  const artistTotals = new Map() // artist_id -> { name, total, byGenre: Map(genre -> value) }

  inboundRows.value.forEach((r) => {
    const creators = workCreators.value[String(r.to_id)] || []
    // A work can list the same artist under multiple roles (e.g. both
    // PerformerOf and ProducerOf) -- dedupe to one credit per artist per
    // influencing work, so an artist's total reflects the number of
    // distinct influence events they're behind, not how many of their
    // credited roles happen to match the edge-type filter.
    const matchingArtists = new Map()
    creators
      .filter((c) => sankeyEdgeTypes.value.includes(c.edge_type))
      .forEach((c) => {
        if (!matchingArtists.has(c.artist_id)) matchingArtists.set(c.artist_id, c.artist_name)
      })
    matchingArtists.forEach((name, artistId) => {
      if (!artistTotals.has(artistId)) {
        artistTotals.set(artistId, { name, total: 0, byGenre: new Map() })
      }
      const entry = artistTotals.get(artistId)
      entry.total += 1
      entry.byGenre.set(r.to_genre, (entry.byGenre.get(r.to_genre) || 0) + 1)
    })
  })

  const topArtists = [...artistTotals.entries()]
    .sort((a, b) => b[1].total - a[1].total)
    .slice(0, topN.value)

  const nodes = []
  const genreSet = new Set()
  topArtists.forEach(([, a]) => a.byGenre.forEach((_, g) => genreSet.add(g)))

  topArtists.forEach(([id, a]) => nodes.push({ id: `artist:${id}`, name: a.name, category: 'Artist' }))
  ;[...genreSet].forEach((g) => nodes.push({ id: `genre:${g}`, name: g, category: 'Genre' }))
  nodes.push({ id: `target:${sankeyGenre.value}`, name: sankeyGenre.value, category: 'Target' })

  const links = []
  const genreToTarget = new Map()
  topArtists.forEach(([id, a]) => {
    a.byGenre.forEach((value, genre) => {
      links.push({ source: `artist:${id}`, target: `genre:${genre}`, value })
      genreToTarget.set(genre, (genreToTarget.get(genre) || 0) + value)
    })
  })
  genreToTarget.forEach((value, genre) => {
    links.push({ source: `genre:${genre}`, target: `target:${sankeyGenre.value}`, value })
  })

  return { nodes, links }
})

// Cross-widget link: clicking a genre's arc in the chord diagram jumps the
// Sankey to that genre and switches to its tab, so the two D3 views read as
// one connected exploration instead of two separate charts sharing a page.
function onChordGenreClick(genre) {
  sankeyGenre.value = genre
  activeSubtab.value = 'Top Influenced Artists'
}
</script>

<template>
  <div class="panel">
    <div class="panel-header">Genre Diffusion Tracker</div>

    <div class="tabs">
      <button
        v-for="t in subtabs"
        :key="t"
        class="tab"
        :class="{ active: activeSubtab === t }"
        @click="activeSubtab = t"
      >
        {{ t }}
      </button>
    </div>

    <div class="panel-body">
      <p v-if="loading">Loading genre diffusion data&hellip;</p>
      <p v-else-if="error" class="error">{{ error }}</p>

      <template v-else-if="activeSubtab === 'Influence Trend'">
        <div class="filters-row">
          <div class="field">
            <label>Select Influence Genre:</label>
            <select v-model="influenceGenre">
              <option v-for="g in genres" :key="g" :value="g">{{ g }}</option>
            </select>
          </div>
          <div class="field">
            <label>From Node Type</label>
            <select v-model="fromNodeType">
              <option value="Both">Both</option>
              <option value="Song">Song</option>
              <option value="Album">Album</option>
            </select>
          </div>
        </div>

        <div class="chart-wrap">
          <TrendLineChart
            :series="series"
            :title="`Number of Unique Influencing Works by ${influenceGenre}`"
          />
          <div class="legend">
            <h4>Genre</h4>
            <div v-for="g in legendGenres" :key="g" class="legend-row">
              <span class="swatch" :style="{ background: legendColor(g) }"></span>{{ g }}
            </div>
          </div>
        </div>

        <DataTable :columns="tableColumns" :rows="filteredRows" />
      </template>

      <template v-else-if="activeSubtab === 'Genre to Genre'">
        <div class="g2g-layout">
          <div class="g2g-filters">
            <label class="field-label">Pre Sailor Shift Fame (to {{ SAILOR_FAME_YEAR }})</label>
            <RangeSlider :min="yearBounds[0]" :max="SAILOR_FAME_YEAR" v-model="preRange" />

            <label class="field-label">Post Sailor Shift Fame (from {{ SAILOR_FAME_YEAR }})</label>
            <RangeSlider :min="SAILOR_FAME_YEAR" :max="yearBounds[1]" v-model="postRange" />

            <MultiSelect label="Filter by From Node Type" :options="['Song', 'Album']" v-model="chordFromNodeTypes" />
            <MultiSelect
              label="Filter by To Node Type(influence)"
              :options="['Song', 'Album']"
              v-model="chordToNodeTypes"
            />
            <MultiSelect label="Filter by Edge Type" :options="INFLUENCE_TYPES" v-model="chordEdgeTypes" />
            <MultiSelect label="Filter by From Genre" :options="allGenres" v-model="chordFromGenres" />
            <MultiSelect
              label="Filter by To Genre(Be influenced by)"
              :options="allGenres"
              v-model="chordToGenres"
            />
          </div>

          <div class="g2g-chart">
            <ChordDiagram
              :genres="chordGenreList"
              :matrix="chordMatrix"
              :selected-genre="sankeyGenre"
              @genre-click="onChordGenreClick"
            />
            <p class="link-hint">Click a genre&rsquo;s arc to focus it in &ldquo;Top Influenced Artists.&rdquo;</p>
          </div>
        </div>

        <DataTable :columns="chordTableColumns" :rows="chordTableRows" />
      </template>

      <template v-else-if="activeSubtab === 'Top Influenced Artists'">
        <div class="filters-row">
          <div class="field">
            <label>Select Influence Genre:</label>
            <select v-model="sankeyGenre">
              <option v-for="g in genres" :key="g" :value="g">{{ g }}</option>
            </select>
          </div>
          <div class="field">
            <label>Top N Influencers:</label>
            <select v-model.number="topN">
              <option :value="10">Top 10</option>
              <option :value="25">Top 25</option>
              <option :value="50">Top 50</option>
            </select>
          </div>
          <div class="field wide">
            <MultiSelect
              label="Edge Type (Artists Associated with Influencing Genres):"
              :options="CREATION_TYPES"
              v-model="sankeyEdgeTypes"
            />
          </div>
        </div>

        <SankeyChart
          :nodes="sankeyData.nodes"
          :links="sankeyData.links"
          :title="`Artists → Genres → ${sankeyGenre}`"
        />
      </template>

      <template v-else>
        <p class="placeholder-note">
          "{{ activeSubtab }}" is next up &mdash; will be built once we get to it.
        </p>
      </template>
    </div>
  </div>
</template>

<style scoped>
.panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}
.panel-header {
  background: #fff;
  color: #0f172a;
  padding: 1rem 1.25rem;
  font-weight: 600;
  font-size: 1.05rem;
  border-bottom: 1px solid #e2e8f0;
  text-transform: none;
}
.tabs {
  display: flex;
  border-bottom: 1px solid #e0e3e6;
  background: #f7f8f9;
}
.tab {
  border: none;
  background: none;
  padding: 0.7rem 1.1rem;
  cursor: pointer;
  font-size: 0.88rem;
  color: #555;
  border-bottom: 2px solid transparent;
}
.tab.active {
  color: #147d75;
  font-weight: 600;
  border-bottom-color: #147d75;
}
.panel-body {
  padding: 1rem 1.25rem 1.5rem;
}
.filters-row {
  display: flex;
  gap: 2rem;
  margin-bottom: 1rem;
  align-items: flex-start;
}
.field label {
  display: block;
  font-weight: 600;
  font-size: 0.82rem;
  margin-bottom: 0.3rem;
  color: #333;
}
.field select {
  border: 1px solid #ccd2d8;
  border-radius: 3px;
  padding: 0.35rem 0.5rem;
  min-width: 220px;
  font-size: 0.85rem;
}
.field.wide {
  min-width: 280px;
}
.chart-wrap {
  display: grid;
  grid-template-columns: 1fr 160px;
  gap: 1rem;
  border: 1px solid #e5e8ea;
  padding: 1rem;
  margin-bottom: 1.5rem;
}
.legend {
  font-size: 0.75rem;
  border-left: 1px solid #eee;
  padding-left: 0.9rem;
}
.legend h4 {
  margin: 0 0 0.4rem;
  font-size: 0.8rem;
}
.legend-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.3rem;
  color: #444;
}
.swatch {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}
.g2g-layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 1.25rem;
  border: 1px solid #e5e8ea;
  padding: 1rem;
  margin-bottom: 1.5rem;
}
.g2g-filters {
  max-height: 620px;
  overflow-y: auto;
  padding-right: 0.5rem;
}
.field-label {
  display: block;
  font-weight: 600;
  font-size: 0.82rem;
  margin: 0.6rem 0 0.3rem;
  color: #333;
}
.g2g-chart {
  display: flex;
  align-items: center;
  justify-content: center;
}
.link-hint {
  text-align: center;
  font-size: 0.72rem;
  color: #888;
  margin-top: 0.4rem;
}
.placeholder-note {
  color: #888;
  font-style: italic;
}
.error {
  color: #c0392b;
}
</style>
