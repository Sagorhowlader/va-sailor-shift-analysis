<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as d3 from 'd3'
import { NODE_COLORS, EDGE_COLORS } from '../constants/graphStyle'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  centerId: { type: Number, default: null },
  focusId: { type: [Number, String, null], default: null },
})
const emit = defineEmits(['select-node'])

const container = ref(null)
let simulation = null
let resizeObserver = null
let zoomBehavior = null
let svgSel = null
let zoomLayer = null
let nodeSel = null

function render() {
  if (!container.value) return
  const el = container.value
  el.innerHTML = ''

  const width = el.clientWidth || 800
  const height = el.clientHeight || 520
  const cx = width / 2
  const cy = height / 2

  const nodesCopy = props.nodes.map((n) => ({ ...n }))
  const edgesCopy = props.edges.map((e) => ({ ...e }))
  const maxDepth = Math.max(1, ...nodesCopy.map((n) => (n.depth >= 0 ? n.depth : 0)))
  const ringGap = Math.min(width, height) / 2 / (maxDepth + 1)

  // seed initial position on a ring per depth so the layout reads radially
  const byDepth = {}
  nodesCopy.forEach((n) => {
    const d = n.depth >= 0 ? n.depth : maxDepth
    byDepth[d] = byDepth[d] || []
    byDepth[d].push(n)
  })
  Object.entries(byDepth).forEach(([d, arr]) => {
    const r = Number(d) * ringGap
    arr.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / arr.length
      n.x = cx + r * Math.cos(angle)
      n.y = cy + r * Math.sin(angle)
    })
  })

  const svg = d3.select(el).append('svg').attr('width', width).attr('height', height)
  svgSel = svg

  svg
    .append('defs')
    .selectAll('marker')
    .data(Object.keys(EDGE_COLORS))
    .join('marker')
    .attr('id', (d) => `arrow-${d}`)
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 18)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', (d) => EDGE_COLORS[d] || '#999')

  zoomLayer = svg.append('g')
  zoomBehavior = d3.zoom().scaleExtent([0.2, 5]).on('zoom', (ev) => {
    zoomLayer.attr('transform', ev.transform)
  })
  svg.call(zoomBehavior)

  // faint depth rings for visual context
  const ringsGroup = zoomLayer.append('g').attr('opacity', 0.25)
  for (let d = 1; d <= maxDepth; d++) {
    ringsGroup
      .append('circle')
      .attr('cx', cx)
      .attr('cy', cy)
      .attr('r', d * ringGap)
      .attr('fill', 'none')
      .attr('stroke', '#c9d1d8')
      .attr('stroke-dasharray', '2,3')
  }

  simulation = d3
    .forceSimulation(nodesCopy)
    .force(
      'link',
      d3.forceLink(edgesCopy).id((d) => d.id).distance(45).strength(0.25)
    )
    .force('charge', d3.forceManyBody().strength(-70))
    .force(
      'radial',
      d3
        .forceRadial((d) => (d.depth >= 0 ? d.depth : maxDepth) * ringGap, cx, cy)
        .strength(0.9)
    )
    .force('collide', d3.forceCollide(16))

  const link = zoomLayer
    .append('g')
    .selectAll('line')
    .data(edgesCopy)
    .join('line')
    .attr('stroke', (d) => EDGE_COLORS[d.type] || '#999')
    .attr('stroke-width', 1.2)
    .attr('marker-end', (d) => `url(#arrow-${d.type})`)
    .attr('opacity', 0.65)

  const node = zoomLayer
    .append('g')
    .selectAll('g')
    .data(nodesCopy)
    .join('g')
    .style('cursor', 'pointer')
    .call(
      d3
        .drag()
        .on('start', (ev, d) => {
          if (!ev.active) simulation.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (ev, d) => {
          d.fx = ev.x
          d.fy = ev.y
        })
        .on('end', (ev, d) => {
          if (!ev.active) simulation.alphaTarget(0)
          d.fx = null
          d.fy = null
        })
    )
    .on('click', (ev, d) => emit('select-node', d))

  nodeSel = node

  node
    .append('circle')
    .attr('class', 'node-shape')
    .attr('r', (d) => (d.id === props.centerId ? 14 : 8))
    .attr('fill', (d) => NODE_COLORS[d.type] || '#bbb')
    .attr('stroke', (d) => (d.id === props.centerId ? '#12282a' : '#fff'))
    .attr('stroke-width', (d) => (d.id === props.centerId ? 2.5 : 1))

  if (props.centerId !== null) {
    node
      .filter((d) => d.id === props.centerId)
      .append('path')
      .attr('class', 'node-shape')
      .attr(
        'd',
        d3.symbol().type(d3.symbolStar).size(400)
      )
      .attr('fill', '#3d8bd4')
      .attr('stroke', '#12282a')
      .attr('stroke-width', 1.5)
    node.filter((d) => d.id === props.centerId).select('circle').remove()
  }

  node.append('title').text((d) => `${d.name} (${d.type})`)

  node
    .append('text')
    .text((d) => d.name)
    .attr('x', 11)
    .attr('y', 4)
    .attr('font-size', 8.5)
    .attr('fill', '#333')
    .attr('pointer-events', 'none')

  simulation.on('tick', () => {
    link
      .attr('x1', (d) => d.source.x)
      .attr('y1', (d) => d.source.y)
      .attr('x2', (d) => d.target.x)
      .attr('y2', (d) => d.target.y)
    node.attr('transform', (d) => `translate(${d.x},${d.y})`)
  })

  applyFocus()
}

function applyFocus() {
  if (!nodeSel) return
  nodeSel.selectAll('.node-shape').attr('stroke', (d) =>
    d.id === props.focusId ? '#e67e22' : d.id === props.centerId ? '#12282a' : '#fff'
  )
  nodeSel.selectAll('.node-shape').attr('stroke-width', (d) => (d.id === props.focusId ? 3.5 : d.id === props.centerId ? 2.5 : 1))

  if (props.focusId !== null && svgSel && zoomBehavior) {
    // Look up the target among the simulation's actual node objects (which
    // carry live .x/.y), not props.nodes -- render() runs the simulation on
    // its own copy of the array, so the original prop objects never get
    // coordinates written to them.
    const target = nodeSel.data().find((n) => n.id === props.focusId)
    if (target && target.x !== undefined) {
      const el = container.value
      const width = el.clientWidth
      const height = el.clientHeight
      const scale = 1.6
      const transform = d3.zoomIdentity
        .translate(width / 2, height / 2)
        .scale(scale)
        .translate(-target.x, -target.y)
      svgSel.transition().duration(500).call(zoomBehavior.transform, transform)
    }
  }
}

onMounted(() => {
  render()
  resizeObserver = new ResizeObserver(() => render())
  resizeObserver.observe(container.value)
})

onBeforeUnmount(() => {
  if (simulation) simulation.stop()
  if (resizeObserver) resizeObserver.disconnect()
})

watch(() => [props.nodes, props.edges], render, { deep: false })
watch(() => props.focusId, applyFocus)
</script>

<template>
  <div ref="container" class="graph-canvas"></div>
</template>

<style scoped>
.graph-canvas {
  width: 100%;
  height: 100%;
  min-height: 480px;
}
</style>
