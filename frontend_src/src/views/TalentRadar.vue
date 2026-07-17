<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import DataTable from '../components/DataTable.vue'
import RadarChart from '../components/RadarChart.vue'
import MultiSelect from '../components/MultiSelect.vue'

const AXES = [
  { key: 'pagerank', label: 'PageRank' },
  { key: 'degree', label: 'Degree' },
  { key: 'style_sim', label: 'StyleSim' },
  { key: 'notable_count_norm', label: 'NotableCount' },
]
const SAILOR_COLOR = '#e8837f'
const COMPARE_COLORS = ['#27ae60', '#e67e22', '#8e44ad', '#2980b9']
const MAX_COMPARE = 4

const loading = ref(true)
const error = ref(null)
const talentData = ref({})

const activeSubtab = ref('Scoreboard')

const genre = ref('Oceanus Folk')
const topN = ref(5)
const compareNames = ref([])

const weights = ref({ pagerank: 0.3, degree: 0.2, style_sim: 0.3, notable_count_norm: 0.2 })

onMounted(async () => {
  try {
    const res = await fetch('/data/talent_radar.json')
    if (!res.ok) throw new Error('Failed to load talent radar data')
    talentData.value = await res.json()
    if (!genres.value.includes(genre.value)) genre.value = genres.value[0] || ''
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

const genres = computed(() => Object.keys(talentData.value).sort())

const currentGenreData = computed(() => talentData.value[genre.value] || { candidates: [], sailor: null })

const weightSum = computed(() => AXES.reduce((s, a) => s + (weights.value[a.key] || 0), 0))

function scoreOf(c) {
  if (weightSum.value <= 0) return 0
  return AXES.reduce((sum, a) => sum + (weights.value[a.key] || 0) * (c[a.key] || 0), 0) / weightSum.value
}

const rankedCandidates = computed(() =>
  currentGenreData.value.candidates
    .map((c) => ({ ...c, score: scoreOf(c) }))
    .sort((a, b) => b.score - a.score)
)

const topCandidates = computed(() => rankedCandidates.value.slice(0, topN.value))

// keep the comparison selection valid as genre/topN change, and cap how
// many artists can be overlaid on the radar at once (past ~4 the polygons
// become unreadable on top of each other)
watch([genre, topN], () => {
  const validNames = new Set(topCandidates.value.map((c) => c.name))
  compareNames.value = compareNames.value.filter((name) => validNames.has(name))
})
watch(compareNames, (names) => {
  if (names.length > MAX_COMPARE) {
    compareNames.value = names.slice(0, MAX_COMPARE)
  }
})

const compareOptionsByName = computed(() => new Map(topCandidates.value.map((c) => [c.name, c])))

const scoreboardRows = computed(() =>
  topCandidates.value.map((c) => ({
    label: c.name,
    PageRank: c.pagerank.toFixed(2),
    Degree: c.degree.toFixed(2),
    StyleSim: c.style_sim.toFixed(2),
    NotableCountNorm: c.notable_count_norm.toFixed(2),
    Score: c.score.toFixed(2),
  }))
)
const scoreboardColumns = [
  { key: 'label', label: 'label' },
  { key: 'PageRank', label: 'PageRank' },
  { key: 'Degree', label: 'Degree' },
  { key: 'StyleSim', label: 'StyleSim' },
  { key: 'NotableCountNorm', label: 'NotableCountNorm' },
  { key: 'Score', label: 'Score' },
]

// Cross-widget link: clicking a Scoreboard row toggles that artist onto
// the D3 radar chart (and jumps you there when adding one), so the table
// and the chart read as one linked view instead of two separate widgets
// that happen to share data.
function toggleCompare(row) {
  const name = row.label
  if (compareNames.value.includes(name)) {
    compareNames.value = compareNames.value.filter((n) => n !== name)
  } else {
    compareNames.value = [...compareNames.value, name]
    activeSubtab.value = 'Radar Comparison'
  }
}

const radarSeries = computed(() => {
  const series = []
  const sailor = currentGenreData.value.sailor
  if (sailor) {
    series.push({ name: 'Sailor Shift', color: SAILOR_COLOR, values: sailor })
  }
  compareNames.value.forEach((name, i) => {
    const c = compareOptionsByName.value.get(name)
    if (c) series.push({ name: c.name, color: COMPARE_COLORS[i % COMPARE_COLORS.length], values: c })
  })
  return series
})
</script>

<template>
  <div class="panel">
    <div class="panel-header">Talent Scoring &amp; Emerging Artist Radar</div>

    <div class="tabs">
      <button
        v-for="t in ['Scoreboard', 'Radar Comparison']"
        :key="t"
        class="tab"
        :class="{ active: activeSubtab === t }"
        @click="activeSubtab = t"
        type="button"
      >
        {{ t }}
      </button>
    </div>

    <div class="panel-body">
      <p v-if="loading">Loading talent data&hellip;</p>
      <p v-else-if="error" class="error">{{ error }}</p>

      <div v-else class="layout">
        <div class="filters">
          <label class="field-label">Filter by Genre</label>
          <select v-model="genre" class="select-full">
            <option v-for="g in genres" :key="g" :value="g">{{ g }}</option>
          </select>

          <label class="field-label">Show Top N Artists</label>
          <select v-model.number="topN" class="select-full">
            <option :value="5">Top 5</option>
            <option :value="10">Top 10</option>
            <option :value="25">Top 25</option>
            <option :value="50">Top 50</option>
          </select>

          <MultiSelect
            label="Select Artists to Compare"
            :options="topCandidates.map((c) => c.name)"
            v-model="compareNames"
          />

          <hr />
          <h4>Customize Score Weights</h4>
          <div v-for="a in AXES" :key="a.key" class="weight-field">
            <label>{{ a.label }}</label>
            <div class="weight-row">
              <span>0</span>
              <input type="range" min="0" max="1" step="0.05" v-model.number="weights[a.key]" />
              <span>1</span>
            </div>
            <div class="weight-value">{{ weights[a.key].toFixed(2) }}</div>
          </div>
        </div>

        <div class="content">
          <div class="subtabs">
            <button
              v-for="t in ['Scoreboard', 'Radar Comparison']"
              :key="t"
              class="subtab"
              :class="{ active: activeSubtab === t }"
              @click="activeSubtab = t"
            >
              {{ t }}
            </button>
          </div>

          <template v-if="activeSubtab === 'Scoreboard'">
            <p class="link-hint">Click a row to add or remove that artist from the Radar Comparison.</p>
            <DataTable
              :columns="scoreboardColumns"
              :rows="scoreboardRows"
              clickable
              :is-row-active="(row) => compareNames.includes(row.label)"
              @row-click="toggleCompare"
            />
          </template>
          <template v-else>
            <RadarChart :axes="AXES" :series="radarSeries" />
            <div class="radar-legend">
              <div v-for="s in radarSeries" :key="s.name" class="legend-row">
                <span class="swatch" :style="{ background: s.color }"></span>{{ s.name }}
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
  margin: 0.6rem 0 0.3rem;
  color: #333;
}
.select-full {
  width: 100%;
  border: 1px solid #ccd2d8;
  border-radius: 3px;
  padding: 0.35rem 0.5rem;
  font-size: 0.85rem;
}
.hint {
  font-size: 0.72rem;
  color: #888;
  margin: 0.3rem 0 0;
}
hr {
  border: none;
  border-top: 1px solid #eee;
  margin: 1rem 0;
}
.weight-field {
  margin-bottom: 0.7rem;
}
.weight-field label {
  font-size: 0.8rem;
  color: #333;
  font-weight: 600;
}
.weight-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.7rem;
  color: #999;
}
.weight-row input {
  flex: 1;
}
.weight-value {
  font-size: 0.72rem;
  color: #147d75;
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
.link-hint {
  font-size: 0.72rem;
  color: #888;
  margin: 0 0 0.6rem;
}
.radar-legend {
  display: flex;
  justify-content: center;
  gap: 1.2rem;
  margin-top: 0.5rem;
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
.error {
  color: #c0392b;
}
</style>
