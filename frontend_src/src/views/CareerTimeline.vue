<script setup>
import { ref, computed, onMounted } from 'vue'
import NodeSearch from '../components/NodeSearch.vue'
import RangeSlider from '../components/RangeSlider.vue'
import TrendLineChart from '../components/TrendLineChart.vue'
import DataTable from '../components/DataTable.vue'
import { makeCategoryColorScale } from '../utils/colorScale'

// Task 3.1: "Visualize the careers of three artists. Compare and contrast
// their rise in popularity and influence." Two independent signals per
// artist, both accumulated year-over-year like the Trend Dashboard curve:
//   - output: how many Song/Album works they released that year (popularity/
//     activity proxy)
//   - influence: how many later works drew on their catalog that year, via
//     InStyleOf/CoverOf/DirectlySamples/etc (influence proxy)
// See build_artist_careers.py for exact derivation.

const loading = ref(true)
const error = ref(null)
const artistIndex = ref([])
const allRows = ref([])

const slot1 = ref(null)
const slot2 = ref(null)
const slot3 = ref(null)

const yearBounds = ref([1975, 2040])
const yearRange = ref([1975, 2040])

onMounted(async () => {
  try {
    const [idxRes, rowsRes] = await Promise.all([
      fetch('/data/artist_careers_index.json'),
      fetch('/data/artist_careers.json'),
    ])
    if (!idxRes.ok || !rowsRes.ok) throw new Error('Failed to load career data')
    artistIndex.value = await idxRes.json()
    allRows.value = await rowsRes.json()

    const byName = (n) => artistIndex.value.find((a) => a.name === n)
    // Default comparison: Sailor Shift vs. two of her ex-Ivy Echoes bandmates
    // who took very different post-band paths (independent vocalist vs.
    // record-label producer) -- a natural "three careers" story straight out
    // of the brief's background. Fully re-pickable via the search boxes.
    const defaults = ['Sailor Shift', 'Maya Jensen', 'Sophie Ramirez'].map(byName).filter(Boolean)
    slot1.value = defaults[0]?.id ?? null
    slot2.value = defaults[1]?.id ?? null
    slot3.value = defaults[2]?.id ?? null

    const years = allRows.value.map((r) => r.year)
    if (years.length) {
      yearBounds.value = [Math.min(...years), Math.max(...years)]
      yearRange.value = [...yearBounds.value]
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

const selectedArtists = computed(() => {
  const ids = [slot1.value, slot2.value, slot3.value].filter((id) => id !== null && id !== undefined)
  const uniqueIds = [...new Set(ids)]
  return uniqueIds.map((id) => artistIndex.value.find((a) => a.id === id)).filter(Boolean)
})

const rowsInRange = computed(() =>
  allRows.value.filter((r) => r.year >= yearRange.value[0] && r.year <= yearRange.value[1])
)

function cumulativeSeriesFor(metricKey) {
  return selectedArtists.value.map((a) => {
    const rows = rowsInRange.value.filter((r) => r.artist_id === a.id).sort((x, y) => x.year - y.year)
    let running = 0
    const points = rows.map((r) => {
      running += r[metricKey]
      return { year: r.year, count: running }
    })
    return { genre: a.name, points }
  })
}

const outputSeries = computed(() => cumulativeSeriesFor('output'))
const influenceSeries = computed(() => cumulativeSeriesFor('influence'))
const colorScale = computed(() => makeCategoryColorScale(selectedArtists.value.map((a) => a.name)))

const summaryColumns = [
  { key: 'label', label: 'Artist' },
  { key: 'firstActive', label: 'First Active Year' },
  { key: 'totalWorks', label: 'Total Works' },
  { key: 'totalNotable', label: 'Total Notable' },
  { key: 'peakYear', label: 'Peak Output Year' },
  { key: 'totalInfluence', label: 'Total Influence Received' },
]
const summaryRows = computed(() =>
  selectedArtists.value.map((a) => {
    const rows = rowsInRange.value.filter((r) => r.artist_id === a.id)
    const totalWorks = rows.reduce((s, r) => s + r.output, 0)
    const totalInfluence = rows.reduce((s, r) => s + r.influence, 0)
    const activeYears = rows.filter((r) => r.output > 0).map((r) => r.year)
    const peak = rows.reduce((best, r) => (r.output > (best?.output ?? -1) ? r : best), null)
    return {
      label: a.name,
      firstActive: activeYears.length ? Math.min(...activeYears) : '—',
      totalWorks,
      totalNotable: rows[0]?.notable_total ?? 0,
      peakYear: peak && peak.output > 0 ? peak.year : '—',
      totalInfluence,
    }
  })
)

function exportCareerData() {
  const header = 'artist,year,output,influence\n'
  const body = selectedArtists.value
    .flatMap((a) =>
      rowsInRange.value
        .filter((r) => r.artist_id === a.id)
        .sort((x, y) => x.year - y.year)
        .map((r) => `${a.name},${r.year},${r.output},${r.influence}`)
    )
    .join('\n')
  const blob = new Blob([header + body], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const el = document.createElement('a')
  el.href = url
  el.download = 'career_timeline_data.csv'
  el.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="panel">
    <div class="panel-header">Career Timeline &mdash; Rising Star Profile</div>

    <div class="panel-body">
      <p v-if="loading">Loading career data&hellip;</p>
      <p v-else-if="error" class="error">{{ error }}</p>

      <div v-else class="layout">
        <div class="filters">
          <label class="field-label">Compare up to 3 Artists</label>
          <div class="artist-slot">
            <span class="slot-label">Artist 1</span>
            <NodeSearch :options="artistIndex" v-model="slot1" />
          </div>
          <div class="artist-slot">
            <span class="slot-label">Artist 2</span>
            <NodeSearch :options="artistIndex" v-model="slot2" />
          </div>
          <div class="artist-slot">
            <span class="slot-label">Artist 3</span>
            <NodeSearch :options="artistIndex" v-model="slot3" />
          </div>

          <label class="field-label">Year Range</label>
          <RangeSlider :min="yearBounds[0]" :max="yearBounds[1]" v-model="yearRange" />

          <button type="button" class="export-btn" @click="exportCareerData">
            &#8681; Export Career Data
          </button>
        </div>

        <div class="content">
          <p v-if="!selectedArtists.length" class="empty">Pick at least one artist to compare.</p>
          <template v-else>
            <h3 class="chart-title">Popularity &mdash; Cumulative Works Released</h3>
            <div class="chart-wrap">
              <TrendLineChart :series="outputSeries" y-label="Cumulative Works" />
            </div>

            <!-- Influence chart commented out per request -->
            <!--
            <h3 class="chart-title">Influence &mdash; Cumulative Times Their Work Was Drawn On</h3>
            <div class="chart-wrap">
              <TrendLineChart :series="influenceSeries" y-label="Cumulative Influence" />
            </div>
            -->

            <div class="legend">
              <div v-for="a in selectedArtists" :key="a.id" class="legend-row">
                <span class="swatch" :style="{ background: colorScale(a.name) }"></span>{{ a.name }}
              </div>
            </div>

            <h3 class="chart-title">Career Summary</h3>
            <DataTable :columns="summaryColumns" :rows="summaryRows" />
          </template>
        </div>
      </div>
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
.panel-body {
  padding: 1rem 1.25rem 1.5rem;
}
.layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 1.25rem;
}
.filters {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.9rem;
}
.field-label {
  display: block;
  font-weight: 600;
  font-size: 0.82rem;
  margin: 0.7rem 0 0.3rem;
  color: #333;
}
.artist-slot {
  margin-bottom: 0.6rem;
}
.slot-label {
  display: block;
  font-size: 0.72rem;
  color: #888;
  margin-bottom: 0.15rem;
}
.export-btn {
  margin-top: 1.2rem;
  width: 100%;
  border: 1px solid #147d75;
  background: #e3f3ef;
  color: #147d75;
  border-radius: 3px;
  padding: 0.5rem;
  font-size: 0.82rem;
  cursor: pointer;
  font-weight: 600;
}
.content {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.9rem;
}
.chart-title {
  font-size: 0.9rem;
  color: #12282a;
  text-align: center;
  margin: 0.3rem 0 0.5rem;
}
.chart-wrap {
  margin-bottom: 1rem;
}
.legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 1rem;
  margin: 0.5rem 0 1.5rem;
  font-size: 0.78rem;
}
.legend-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.swatch {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.empty {
  color: #999;
  text-align: center;
  padding: 2rem 0;
}
.error {
  color: #c0392b;
}
</style>
