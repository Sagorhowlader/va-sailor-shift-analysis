<script setup>
import { ref, computed, onMounted } from 'vue'
import TrendLineChart from '../components/TrendLineChart.vue'
import { makeCategoryColorScale } from '../utils/colorScale'

// Task 3.2: "Using this characterization, give three predictions of who the
// next Oceanus Folk stars will be over the next five years."
//
// Methodology (computed live from real data, not hand-picked):
//   1. Start from Talent Radar's Oceanus Folk candidate pool (Sailor already
//      excluded there) and its default-weighted score -- the same PageRank /
//      Degree / StyleSim / NotableCount blend used in the Talent Radar view.
//   2. Add a "momentum" signal from the Career Timeline data: the share of
//      an artist's total output released in the dataset's final 5 years.
//      A candidate who's already well-scored AND still actively releasing
//      (rather than someone whose catalog is entirely from decades ago) is
//      the better bet for "next five years" -- this mirrors the shape of
//      Sailor's own trajectory, whose output share accelerated sharply after
//      her 2028 breakout rather than tapering off.
//   3. finalScore = 0.6 * radarScore + 0.4 * recentOutputShare. Weights are
//      a modeling choice, not a fact -- shown here so they're inspectable/
//      tunable rather than baked into a hardcoded answer.
const RADAR_WEIGHTS = { pagerank: 0.3, degree: 0.2, style_sim: 0.3, notable_count_norm: 0.2 }
const MOMENTUM_WINDOW = 5
const FINAL_WEIGHTS = { radar: 0.6, momentum: 0.4 }
const GENRE = 'Oceanus Folk'

const loading = ref(true)
const error = ref(null)
const talentData = ref({})
const careerRows = ref([])

onMounted(async () => {
  try {
    const [tRes, cRes] = await Promise.all([
      fetch('/data/talent_radar.json'),
      fetch('/data/artist_careers.json'),
    ])
    if (!tRes.ok || !cRes.ok) throw new Error('Failed to load prediction data')
    talentData.value = await tRes.json()
    careerRows.value = await cRes.json()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

function radarScore(c) {
  const sum = Object.keys(RADAR_WEIGHTS).reduce((s, k) => s + RADAR_WEIGHTS[k], 0)
  if (sum <= 0) return 0
  return Object.keys(RADAR_WEIGHTS).reduce((s, k) => s + RADAR_WEIGHTS[k] * (c[k] || 0), 0) / sum
}

const maxYear = computed(() => (careerRows.value.length ? Math.max(...careerRows.value.map((r) => r.year)) : 2040))

function momentumFor(artistId) {
  const rows = careerRows.value.filter((r) => r.artist_id === artistId)
  const total = rows.reduce((s, r) => s + r.output, 0)
  if (!total) return 0
  const recent = rows.filter((r) => r.year > maxYear.value - MOMENTUM_WINDOW).reduce((s, r) => s + r.output, 0)
  return recent / total
}

const shortlist = computed(() => {
  const pool = talentData.value[GENRE]?.candidates || []
  return pool
    .map((c) => ({
      ...c,
      radarScore: radarScore(c),
      momentum: momentumFor(c.id),
    }))
    .map((c) => ({ ...c, finalScore: FINAL_WEIGHTS.radar * c.radarScore + FINAL_WEIGHTS.momentum * c.momentum }))
    .sort((a, b) => b.finalScore - a.finalScore)
})

const predictions = computed(() => shortlist.value.slice(0, 3))

const predictionSeries = computed(() =>
  predictions.value.map((p) => {
    const rows = careerRows.value.filter((r) => r.artist_id === p.id).sort((a, b) => a.year - b.year)
    let running = 0
    const points = rows.map((r) => {
      running += r.output
      return { year: r.year, count: running }
    })
    return { genre: p.name, points }
  })
)
const colorScale = computed(() => makeCategoryColorScale(predictions.value.map((p) => p.name)))

function rationale(p, rank) {
  const pct = Math.round(p.momentum * 100)
  return `Ranks #${rank} of ${shortlist.value.length} in the Oceanus Folk candidate pool (blended score ${p.finalScore.toFixed(
    2
  )}: PageRank ${p.pagerank.toFixed(2)}, Degree ${p.degree.toFixed(2)}, StyleSim ${p.style_sim.toFixed(
    2
  )}, NotableCount ${p.notable_count_norm.toFixed(2)}). ${pct}% of their catalog was released in the dataset's final ${MOMENTUM_WINDOW} years, so they're still actively producing rather than coasting on older work -- the same shape Sailor's own output took right after her 2028 breakout.`
}

function exportWriteup() {
  const lines = [
    '# Task 3.2 -- Three Predictions for the Next Oceanus Folk Stars', '',
    ...predictions.value.map((p, i) => `${i + 1}. **${p.name}** -- ${rationale(p, i + 1)}`), '',
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const el = document.createElement('a')
  el.href = url
  el.download = 'findings_predictions.md'
  el.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="panel">
    <div class="panel-header">Findings &amp; Predictions</div>

    <div class="panel-body">
      <p v-if="loading">Loading&hellip;</p>
      <p v-else-if="error" class="error">{{ error }}</p>

      <template v-else>
        <section>
          <h3>Task 3.2 &mdash; Three Predictions for the Next Oceanus Folk Stars</h3>
          <p class="methodology">
            Computed live from the Talent Radar scoring (PageRank/Degree/StyleSim/NotableCount, weighted
            {{ FINAL_WEIGHTS.radar }}) blended with recent-output momentum (weighted {{ FINAL_WEIGHTS.momentum }}) from
            the Career Timeline data. See code comments for the exact formula -- these are modeling choices, not fixed facts.
          </p>

          <div class="prediction-cards">
            <div v-for="(p, i) in predictions" :key="p.id" class="prediction-card">
              <div class="rank-badge">#{{ i + 1 }}</div>
              <div class="name">{{ p.name }}</div>
              <div class="rationale">{{ rationale(p, i + 1) }}</div>
            </div>
          </div>

          <h4 class="chart-title">Cumulative Output &mdash; the Three Predicted Artists</h4>
          <TrendLineChart :series="predictionSeries" y-label="Cumulative Works" />
          <div class="legend">
            <div v-for="p in predictions" :key="p.id" class="legend-row">
              <span class="swatch" :style="{ background: colorScale(p.name) }"></span>{{ p.name }}
            </div>
          </div>
        </section>

        <button type="button" class="export-btn" @click="exportWriteup">&#8681; Export Predictions (Markdown)</button>
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
.panel-body {
  padding: 1rem 1.25rem 1.5rem;
}
section {
  margin-bottom: 2rem;
}
h3 {
  color: #12282a;
  font-size: 1rem;
  margin: 0 0 0.4rem;
}
h4.chart-title {
  font-size: 0.9rem;
  color: #12282a;
  text-align: center;
  margin: 1rem 0 0.5rem;
}
.methodology {
  font-size: 0.8rem;
  color: #777;
  margin: 0 0 0.9rem;
}
.prediction-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.9rem;
  margin-bottom: 0.5rem;
}
.prediction-card {
  border: 1px solid #e5e8ea;
  border-radius: 4px;
  padding: 0.8rem;
  position: relative;
}
.rank-badge {
  position: absolute;
  top: 0.6rem;
  right: 0.7rem;
  background: #147d75;
  color: #fff;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.1rem 0.45rem;
  border-radius: 10px;
}
.name {
  font-weight: 700;
  color: #12282a;
  margin-bottom: 0.4rem;
  padding-right: 2rem;
}
.rationale {
  font-size: 0.78rem;
  color: #555;
  line-height: 1.4;
}
.legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 1rem;
  margin: 0.5rem 0;
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
.export-btn {
  border: 1px solid #147d75;
  background: #e3f3ef;
  color: #147d75;
  border-radius: 3px;
  padding: 0.6rem 1.2rem;
  font-size: 0.85rem;
  cursor: pointer;
  font-weight: 600;
}
.error {
  color: #c0392b;
}
</style>
