<script setup>
// Supporting context for Task 2/3: genre-level release activity over time,
// straight from each Song/Album's own genre + release_date (no influence
// edges involved -- see src/build_genre_trends.py). Two views of the same
// filtered rows: a Yearly Heatmap (raw counts per genre/year) and a
// Cumulative Curve (running total, reusing TrendLineChart like Career
// Timeline does).
import { ref, computed, onMounted } from 'vue'
import MultiSelect from '../components/MultiSelect.vue'
import RangeSlider from '../components/RangeSlider.vue'
import HeatmapChart from '../components/HeatmapChart.vue'
import TrendLineChart from '../components/TrendLineChart.vue'
import { makeCategoryColorScale } from '../utils/colorScale'

const loading = ref(true)
const error = ref(null)
const allRows = ref([])

const activeSubtab = ref('Yearly Heatmap')
const layer = ref('song_count') // 'song_count' | 'album_count'

const genres = computed(() => [...new Set(allRows.value.map((r) => r.genre))].sort())
const selectedGenres = ref([])
const yearBounds = ref([1975, 2040])
const yearRange = ref([1975, 2040])

onMounted(async () => {
  try {
    const res = await fetch('/data/genre_trends.json')
    if (!res.ok) throw new Error('Failed to load genre trend data')
    allRows.value = await res.json()
    selectedGenres.value = [...genres.value]
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

const filteredRows = computed(() =>
  allRows.value.filter(
    (r) =>
      selectedGenres.value.includes(r.genre) &&
      r.year >= yearRange.value[0] &&
      r.year <= yearRange.value[1]
  )
)

const valueByGenreYear = computed(() => {
  const m = new Map()
  filteredRows.value.forEach((r) => {
    m.set(`${r.genre}|${r.year}`, r[layer.value])
  })
  return m
})

function valueAt(genre, year) {
  return valueByGenreYear.value.get(`${genre}|${year}`) || 0
}

const heatmapYears = computed(() => {
  const [lo, hi] = yearRange.value
  const arr = []
  for (let y = lo; y <= hi; y++) arr.push(y)
  return arr
})
const heatmapGenres = computed(() => [...selectedGenres.value].sort())

const cumulativeSeries = computed(() => {
  return selectedGenres.value
    .map((genre) => {
      const rows = filteredRows.value
        .filter((r) => r.genre === genre)
        .sort((a, b) => a.year - b.year)
      let running = 0
      const points = rows.map((r) => {
        running += r[layer.value]
        return { year: r.year, count: running }
      })
      return { genre, points, total: running }
    })
    .filter((s) => s.points.length)
    .sort((a, b) => b.total - a.total)
})

const cumulativeColorScale = computed(() =>
  makeCategoryColorScale(cumulativeSeries.value.map((s) => s.genre))
)

function exportTrendData() {
  const header = 'genre,year,song_count,album_count\n'
  const body = filteredRows.value.map((r) => `${r.genre},${r.year},${r.song_count},${r.album_count}`).join('\n')
  const blob = new Blob([header + body], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'genre_trend_data.csv'
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="panel">
    <div class="panel-header">Genre Diffusion &amp; Artist Trend Explorer</div>

    <div class="panel-body">
      <p v-if="loading">Loading trend data&hellip;</p>
      <p v-else-if="error" class="error">{{ error }}</p>

      <div v-else class="layout">
        <div class="filters">
          <MultiSelect label="Select Genre(s)" :options="genres" v-model="selectedGenres" />

          <label class="field-label">Year Range</label>
          <RangeSlider :min="yearBounds[0]" :max="yearBounds[1]" v-model="yearRange" />

          <label class="field-label">Show Layer</label>
          <div class="radio-row">
            <label><input type="radio" value="song_count" v-model="layer" /> Song Count</label>
            <label><input type="radio" value="album_count" v-model="layer" /> Album Count</label>
          </div>

          <button type="button" class="export-btn" @click="exportTrendData">
            &#8681; Export Trend Data
          </button>
        </div>

        <div class="content">
          <div class="subtabs">
            <button
              v-for="t in ['Yearly Heatmap', 'Cumulative Curve']"
              :key="t"
              class="subtab"
              :class="{ active: activeSubtab === t }"
              @click="activeSubtab = t"
            >
              {{ t }}
            </button>
          </div>

          <template v-if="activeSubtab === 'Yearly Heatmap'">
            <HeatmapChart
              :genres="heatmapGenres"
              :years="heatmapYears"
              :value-at="valueAt"
              legend-label="Count"
            />
          </template>
          <template v-else>
            <h3 class="chart-title">Cumulative Number of Works</h3>
            <div class="chart-wrap">
              <TrendLineChart :series="cumulativeSeries" y-label="Cumulative Works" />
              <div class="legend">
                <h4>Genre</h4>
                <div v-for="s in cumulativeSeries" :key="s.genre" class="legend-row">
                  <span class="swatch" :style="{ background: cumulativeColorScale(s.genre) }"></span>{{ s.genre }}
                </div>
              </div>
            </div>
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
  grid-template-columns: 240px 1fr;
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
.radio-row {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.82rem;
  color: #444;
}
.radio-row label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
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
.subtabs {
  margin-bottom: 0.75rem;
}
.subtab {
  border: 1px solid #dfe3e6;
  background: #f4f5f6;
  padding: 0.35rem 0.9rem;
  font-size: 0.82rem;
  cursor: pointer;
  color: #555;
}
.subtab.active {
  background: #e3f3ef;
  color: #147d75;
  font-weight: 600;
}
.chart-title {
  font-size: 0.9rem;
  color: #12282a;
  text-align: center;
  margin: 0.3rem 0 0.7rem;
}
.chart-wrap {
  display: grid;
  grid-template-columns: 1fr 180px;
  gap: 1rem;
}
.legend {
  font-size: 0.72rem;
  border-left: 1px solid #eee;
  padding-left: 0.9rem;
  max-height: 400px;
  overflow-y: auto;
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
.error {
  color: #c0392b;
}
</style>
