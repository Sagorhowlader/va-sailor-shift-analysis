<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as d3 from 'd3'
import { attachZoom } from '../utils/zoom'

const props = defineProps({
  axes: { type: Array, required: true }, // [{key, label}]
  // series: [{ name, color, values: { [axisKey]: 0..1 } }]
  series: { type: Array, default: () => [] },
})

const chartEl = ref(null)
let resizeObserver = null

function render() {
  if (!chartEl.value) return
  const el = chartEl.value
  el.innerHTML = ''

  const size = Math.min(el.clientWidth || 520, 520)
  const margin = 60
  const radius = size / 2 - margin
  const cx = size / 2
  const cy = size / 2
  const n = props.axes.length
  const angleFor = (i) => (Math.PI * 2 * i) / n - Math.PI / 2

  const svg = d3.select(el).append('svg').attr('width', size).attr('height', size)
  const { layer } = attachZoom(svg)
  const g = layer.append('g').attr('transform', `translate(${cx},${cy})`)

  const rScale = d3.scaleLinear().domain([0, 1]).range([0, radius])
  const rings = [0.2, 0.4, 0.6, 0.8, 1]

  rings.forEach((r) => {
    g.append('circle')
      .attr('r', rScale(r))
      .attr('fill', 'none')
      .attr('stroke', '#e0e3e6')
      .attr('stroke-width', 1)
  })

  props.axes.forEach((axis, i) => {
    const angle = angleFor(i)
    const x = radius * Math.cos(angle)
    const y = radius * Math.sin(angle)
    g.append('line').attr('x1', 0).attr('y1', 0).attr('x2', x).attr('y2', y).attr('stroke', '#c9d1d8')

    g.append('text')
      .attr('x', (radius + 18) * Math.cos(angle))
      .attr('y', (radius + 18) * Math.sin(angle))
      .attr('text-anchor', 'middle')
      .attr('dy', '0.32em')
      .attr('font-size', 11)
      .attr('font-weight', 600)
      .attr('fill', '#333')
      .text(axis.label)
  })

  // Build each polygon's points with the exact same angleFor()/cos/sin used
  // for the axis lines above, rather than d3.lineRadial's own angle
  // convention -- keeps the two guaranteed consistent instead of having to
  // reconcile two different "angle zero" definitions.
  const lineGen = d3
    .line()
    .x((d) => d[0])
    .y((d) => d[1])
    .curve(d3.curveLinearClosed)

  props.series.forEach((s) => {
    const values = props.axes.map((a) => Math.max(0, Math.min(1, s.values[a.key] || 0)))
    const points = values.map((v, i) => {
      const angle = angleFor(i)
      return [rScale(v) * Math.cos(angle), rScale(v) * Math.sin(angle)]
    })
    g.append('path')
      .datum(points)
      .attr('d', lineGen)
      .attr('fill', s.color)
      .attr('fill-opacity', 0.2)
      .attr('stroke', s.color)
      .attr('stroke-width', 2)

    values.forEach((v, i) => {
      const angle = angleFor(i)
      g.append('circle')
        .attr('cx', rScale(v) * Math.cos(angle))
        .attr('cy', rScale(v) * Math.sin(angle))
        .attr('r', 3)
        .attr('fill', s.color)
        .append('title')
        .text(`${s.name} — ${props.axes[i].label}: ${v.toFixed(2)}`)
    })
  })
}

onMounted(() => {
  render()
  resizeObserver = new ResizeObserver(() => render())
  resizeObserver.observe(chartEl.value)
})
onBeforeUnmount(() => {
  if (resizeObserver) resizeObserver.disconnect()
})
watch(() => [props.axes, props.series], render, { deep: true })
</script>

<template>
  <div ref="chartEl" class="radar-chart"></div>
</template>

<style scoped>
.radar-chart {
  width: 100%;
  display: flex;
  justify-content: center;
}
</style>
