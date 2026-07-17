<script setup>
import { ref, onMounted, watch, onBeforeUnmount, computed } from 'vue'
import * as d3 from 'd3'
import { EDGE_COLORS } from '../constants/graphStyle'
import { attachZoom } from '../utils/zoom'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  centerId: { type: [Number, String, null], default: null },
})

const chartEl = ref(null)
let resizeObserver = null

// title mirrors the reference: counts edges by (node type of endpoint, edge type),
// crediting the edge to both endpoints' node types when they differ.
function buildMatrix() {
  const byId = new Map(props.nodes.map((n) => [n.id, n]))
  const categories = ['Person', 'Song', 'Album', 'MusicalGroup', 'RecordLabel']
  const counts = new Map(categories.map((c) => [c, new Map()]))
  const typesPresent = new Set()

  props.edges.forEach((e) => {
    const s = byId.get(e.source)
    const t = byId.get(e.target)
    if (!s || !t) return
    typesPresent.add(e.type)
    ;[s, t].forEach((endpoint, i) => {
      // avoid double counting when both endpoints share the same category
      if (i === 1 && s.type === t.type) return
      const bucket = counts.get(endpoint.type)
      if (!bucket) return
      bucket.set(e.type, (bucket.get(e.type) || 0) + 1)
    })
  })

  const edgeTypeOrder = Object.keys(EDGE_COLORS).filter((t) => typesPresent.has(t))
  const rows = categories.map((cat) => {
    const bucket = counts.get(cat)
    const row = { category: cat }
    edgeTypeOrder.forEach((t) => (row[t] = bucket.get(t) || 0))
    return row
  })
  return { rows, edgeTypeOrder, categories }
}

const topConnected = computed(() => {
  const degree = new Map()
  props.edges.forEach((e) => {
    degree.set(e.source, (degree.get(e.source) || 0) + 1)
    degree.set(e.target, (degree.get(e.target) || 0) + 1)
  })
  const byId = new Map(props.nodes.map((n) => [n.id, n]))
  return [...degree.entries()]
    .map(([id, deg]) => ({ node: byId.get(id), deg }))
    .filter((x) => x.node && x.node.id !== props.centerId)
    .sort((a, b) => b.deg - a.deg)
    .slice(0, 8)
})

function render() {
  if (!chartEl.value) return
  const el = chartEl.value
  el.innerHTML = ''

  const { rows, edgeTypeOrder, categories } = buildMatrix()
  const width = el.clientWidth || 700
  const height = 380
  const margin = { top: 10, right: 10, bottom: 40, left: 45 }

  const svg = d3.select(el).append('svg').attr('width', width).attr('height', height)
  const { layer } = attachZoom(svg)

  const x = d3
    .scaleBand()
    .domain(categories)
    .range([margin.left, width - margin.right])
    .padding(0.35)

  const maxTotal = d3.max(rows, (r) => edgeTypeOrder.reduce((sum, t) => sum + r[t], 0)) || 1
  const y = d3
    .scaleLinear()
    .domain([0, maxTotal])
    .nice()
    .range([height - margin.bottom, margin.top])

  const stackGen = d3.stack().keys(edgeTypeOrder)
  const series = stackGen(rows)

  layer
    .append('g')
    .selectAll('g')
    .data(series)
    .join('g')
    .attr('fill', (d) => EDGE_COLORS[d.key] || '#999')
    .selectAll('rect')
    .data((d) => d.map((v) => ({ ...v, key: d.key })))
    .join('rect')
    .attr('x', (d) => x(d.data.category))
    .attr('y', (d) => y(d[1]))
    .attr('height', (d) => y(d[0]) - y(d[1]))
    .attr('width', x.bandwidth())
    .append('title')
    .text((d) => `${d.key}: ${d[1] - d[0]}`)

  layer
    .append('g')
    .attr('transform', `translate(0,${height - margin.bottom})`)
    .call(d3.axisBottom(x))
    .call((g) => g.select('.domain').remove())

  layer
    .append('g')
    .attr('transform', `translate(${margin.left},0)`)
    .call(d3.axisLeft(y).ticks(5))
    .call((g) => g.select('.domain').remove())

  layer
    .append('text')
    .attr('x', width / 2)
    .attr('y', height - 4)
    .attr('text-anchor', 'middle')
    .attr('font-size', 11)
    .attr('fill', '#555')
    .text('Node Type')

  layer
    .append('text')
    .attr('transform', 'rotate(-90)')
    .attr('x', -height / 2)
    .attr('y', 12)
    .attr('text-anchor', 'middle')
    .attr('font-size', 11)
    .attr('fill', '#555')
    .text('Count')
}

onMounted(() => {
  render()
  resizeObserver = new ResizeObserver(() => render())
  resizeObserver.observe(chartEl.value)
})
onBeforeUnmount(() => {
  if (resizeObserver) resizeObserver.disconnect()
})
watch(() => [props.nodes, props.edges], render)
</script>

<template>
  <div class="stats">
    <h3>Influences on Sailor Shift by Node Category and Relationship</h3>
    <div ref="chartEl" class="chart"></div>

    <div class="chart-legend">
      <div v-for="(color, type) in EDGE_COLORS" :key="type" class="legend-item">
        <span class="swatch" :style="{ background: color }"></span>{{ type }}
      </div>
    </div>

    <div class="stat-block">
      <h4>Most Connected Nodes (in this view)</h4>
      <table class="top-table">
        <tbody>
          <tr v-for="row in topConnected" :key="row.node.id">
            <td>{{ row.node.name }}</td>
            <td class="muted">{{ row.node.type }}</td>
            <td class="deg">{{ row.deg }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.stats {
  padding: 0.5rem 0.75rem;
  font-size: 0.82rem;
}
h3 {
  font-size: 0.95rem;
  color: #12282a;
  margin: 0.2rem 0 0.75rem;
}
.chart {
  width: 100%;
}
.chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 1rem;
  margin: 0.75rem 0 1.5rem;
  font-size: 0.72rem;
  color: #444;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
.swatch {
  width: 10px;
  height: 10px;
  display: inline-block;
}
.stat-block h4 {
  margin: 0 0 0.6rem;
  font-size: 0.85rem;
  color: #12282a;
}
.top-table {
  width: 100%;
  border-collapse: collapse;
}
.top-table td {
  padding: 0.3rem 0.4rem;
  border-bottom: 1px solid #f0f0f0;
}
.muted {
  color: #888;
  font-size: 0.75rem;
}
.deg {
  text-align: right;
  font-weight: 600;
  color: #147d75;
}
</style>
