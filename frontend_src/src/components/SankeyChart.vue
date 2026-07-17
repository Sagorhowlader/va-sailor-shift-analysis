<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as d3 from 'd3'
import { sankey, sankeyLinkHorizontal } from 'd3-sankey'
import { makeCategoryColorScale } from '../utils/colorScale'
import { attachZoom } from '../utils/zoom'

const props = defineProps({
  // nodes: [{id, name, category}]  categories: 'Artist' | 'Genre' | 'Target'
  // links: [{source: id, target: id, value}]
  nodes: { type: Array, default: () => [] },
  links: { type: Array, default: () => [] },
  title: { type: String, default: '' },
})

const chartEl = ref(null)
let resizeObserver = null

// Artist and Target nodes get fixed colors; each Genre gets its own color
// from the shared rainbow scale (built fresh per render from whatever
// genres are actually present), so the fan-out reads like the reference:
// distinct genre bands, with each ribbon tinted to match the genre it
// flows into.
const FIXED_COLORS = {
  Artist: '#b0b7bd',
  Target: '#2ecc71',
}

function nodeColor(d, genreScale) {
  if (d.category === 'Genre') return genreScale(d.name)
  return FIXED_COLORS[d.category] || '#999'
}

function linkColor(d, genreScale) {
  // color each ribbon by whichever endpoint is a genre, so artist->genre
  // and genre->target links both take on that genre's color
  if (d.source.category === 'Genre') return genreScale(d.source.name)
  if (d.target.category === 'Genre') return genreScale(d.target.name)
  return '#ccc'
}

function render() {
  if (!chartEl.value) return
  const el = chartEl.value
  el.innerHTML = ''

  if (!props.nodes.length) {
    d3.select(el).append('p').attr('class', 'empty').text('No data for the current filters.')
    return
  }

  const width = el.clientWidth || 900
  const nodeCount = props.nodes.length
  // Node height is normally proportional to its flow value, so with a lot
  // of low-value artists (e.g. Top 50) most rows shrink to a couple of
  // pixels -- far too thin for a 9px label, which is what caused the
  // overlapping/illegible names. We run the layout against a generous
  // guessed height first, then (below) clamp every row to a minimum height
  // and re-measure how tall the busiest column actually ended up -- the
  // final <svg> is sized to fit that, not the initial guess, so enforcing
  // a minimum can't push rows past the bottom of the canvas.
  const MIN_NODE_HEIGHT = 11
  const ROW_GAP = 4
  const initialHeightGuess = Math.max(420, nodeCount * (MIN_NODE_HEIGHT + ROW_GAP))

  const idIndex = new Map(props.nodes.map((n, i) => [n.id, i]))
  const sankeyNodes = props.nodes.map((n) => ({ ...n }))
  const sankeyLinks = props.links.map((l) => ({
    source: idIndex.get(l.source),
    target: idIndex.get(l.target),
    value: l.value,
  }))

  const layout = sankey()
    .nodeId((d, i) => i)
    .nodeWidth(14)
    .nodePadding(ROW_GAP)
    .extent([[10, 10], [width - 160, initialHeightGuess - 10]])

  let graph
  try {
    graph = layout({ nodes: sankeyNodes, links: sankeyLinks })
  } catch (err) {
    d3.select(el).append('p').attr('class', 'empty').text('Unable to render Sankey for this selection.')
    return
  }

  // Post-process: clamp every node to at least MIN_NODE_HEIGHT tall, then
  // re-stack nodes within each column (grouped by x0, i.e. Artist / Genre /
  // Target) top-to-bottom preserving their layout order and a fixed gap,
  // so the enforced minimum height can't make rows overlap each other.
  // This trades a bit of value-proportionality for legibility, which the
  // original per-value sizing didn't have room for once there are 50+ rows.
  const byColumn = new Map()
  graph.nodes.forEach((n) => {
    if (!byColumn.has(n.x0)) byColumn.set(n.x0, [])
    byColumn.get(n.x0).push(n)
  })
  let maxCursor = initialHeightGuess
  byColumn.forEach((colNodes) => {
    colNodes.sort((a, b) => a.y0 - b.y0)
    let cursor = colNodes[0].y0
    colNodes.forEach((n) => {
      const naturalHeight = n.y1 - n.y0
      const h = Math.max(MIN_NODE_HEIGHT, naturalHeight)
      n.y0 = cursor
      n.y1 = cursor + h
      cursor += h + ROW_GAP
    })
    maxCursor = Math.max(maxCursor, cursor)
  })
  // The clamp above can make a column taller than our initial guess (e.g.
  // Top 50 with a few high-value artists already claiming a lot of natural
  // height, plus 46 more needing the minimum). Grow the canvas to fit.
  const height = maxCursor + 10
  // Sankey link paths are generated from each end's vertical position
  // within its node (sy0/sy1/ty0/ty1 etc.), which d3-sankey precomputes
  // relative to the original (now-stale) y0/y1. Re-run just the link
  // vertical placement so ribbons still meet the node edges we just moved.
  graph.nodes.forEach((n) => {
    const total = d3.sum(n.sourceLinks, (l) => l.value) || 1
    let y = n.y0
    n.sourceLinks
      .slice()
      .sort((a, b) => a.target.y0 - b.target.y0)
      .forEach((l) => {
        const h = ((n.y1 - n.y0) * l.value) / total
        l.y0 = y + h / 2
        y += h
      })
  })
  graph.nodes.forEach((n) => {
    const total = d3.sum(n.targetLinks, (l) => l.value) || 1
    let y = n.y0
    n.targetLinks
      .slice()
      .sort((a, b) => a.source.y0 - b.source.y0)
      .forEach((l) => {
        const h = ((n.y1 - n.y0) * l.value) / total
        l.y1 = y + h / 2
        y += h
      })
  })

  const svg = d3.select(el).append('svg').attr('width', width).attr('height', height)
  const { layer } = attachZoom(svg)

  const genreNames = props.nodes.filter((n) => n.category === 'Genre').map((n) => n.name)
  const genreScale = makeCategoryColorScale(genreNames)

  layer
    .append('g')
    .attr('fill', 'none')
    .selectAll('path')
    .data(graph.links)
    .join('path')
    .attr('d', sankeyLinkHorizontal())
    .attr('stroke', (d) => linkColor(d, genreScale))
    .attr('stroke-opacity', 0.45)
    .attr('stroke-width', (d) => Math.max(1, d.width))
    .append('title')
    .text((d) => `${d.source.name} → ${d.target.name}: ${d.value}`)

  const node = layer
    .append('g')
    .selectAll('g')
    .data(graph.nodes)
    .join('g')

  node
    .append('rect')
    .attr('x', (d) => d.x0)
    .attr('y', (d) => d.y0)
    .attr('width', (d) => d.x1 - d.x0)
    .attr('height', (d) => Math.max(1, d.y1 - d.y0))
    .attr('fill', (d) => nodeColor(d, genreScale))
    .append('title')
    .text((d) => `${d.name}: ${d.value}`)

  node
    .append('text')
    .attr('x', (d) => (d.category === 'Artist' ? d.x0 - 6 : d.x1 + 6))
    .attr('y', (d) => (d.y0 + d.y1) / 2)
    .attr('dy', '0.32em')
    .attr('text-anchor', (d) => (d.category === 'Artist' ? 'end' : 'start'))
    .attr('font-size', 9)
    .attr('fill', '#333')
    .text((d) => d.name)
}

onMounted(() => {
  render()
  resizeObserver = new ResizeObserver(() => render())
  resizeObserver.observe(chartEl.value)
})
onBeforeUnmount(() => {
  if (resizeObserver) resizeObserver.disconnect()
})
watch(() => [props.nodes, props.links], render)
</script>

<template>
  <div>
    <h3 v-if="title">{{ title }}</h3>
    <div ref="chartEl" class="chart"></div>
  </div>
</template>

<style scoped>
h3 {
  font-size: 0.9rem;
  color: #12282a;
  margin: 0.2rem 0 0.6rem;
  text-align: center;
}
.chart {
  width: 100%;
  overflow-x: auto;
}
.empty {
  color: #999;
  font-size: 0.85rem;
  padding: 2rem 0;
  text-align: center;
}
</style>
