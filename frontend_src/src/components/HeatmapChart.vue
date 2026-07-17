<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as d3 from 'd3'
import { attachZoom } from '../utils/zoom'

const props = defineProps({
  genres: { type: Array, default: () => [] }, // row order, top to bottom
  years: { type: Array, default: () => [] }, // column order, left to right
  // valueAt(genre, year) -> number
  valueAt: { type: Function, required: true },
  legendLabel: { type: String, default: 'Count' },
})

const chartEl = ref(null)
let resizeObserver = null

function render() {
  if (!chartEl.value) return
  const el = chartEl.value
  el.innerHTML = ''

  if (!props.genres.length || !props.years.length) {
    d3.select(el).append('p').attr('class', 'empty').text('No data for the current filters.')
    return
  }

  const margin = { top: 10, right: 70, bottom: 40, left: 130 }
  const cellWidth = Math.max(6, Math.min(18, 900 / props.years.length))
  const cellHeight = Math.max(10, Math.min(20, 480 / props.genres.length))
  const width = props.years.length * cellWidth + margin.left + margin.right
  const height = props.genres.length * cellHeight + margin.top + margin.bottom

  const svg = d3.select(el).append('svg').attr('width', width).attr('height', height)
  const { layer } = attachZoom(svg)
  const g = layer.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const maxVal = d3.max(props.genres.flatMap((genre) => props.years.map((y) => props.valueAt(genre, y)))) || 1
  const color = d3.scaleSequential(d3.interpolateViridis).domain([0, maxVal])

  const x = d3.scaleBand().domain(props.years).range([0, props.years.length * cellWidth])
  const y = d3.scaleBand().domain(props.genres).range([0, props.genres.length * cellHeight])

  props.genres.forEach((genre) => {
    props.years.forEach((year) => {
      const v = props.valueAt(genre, year)
      g.append('rect')
        .attr('x', x(year))
        .attr('y', y(genre))
        .attr('width', x.bandwidth())
        .attr('height', y.bandwidth())
        .attr('fill', v > 0 ? color(v) : '#f4f4f4')
        .append('title')
        .text(`${genre}, ${year}: ${v}`)
    })
  })

  // row labels
  g.append('g')
    .selectAll('text')
    .data(props.genres)
    .join('text')
    .attr('x', -6)
    .attr('y', (d) => y(d) + y.bandwidth() / 2)
    .attr('dy', '0.32em')
    .attr('text-anchor', 'end')
    .attr('font-size', 9)
    .attr('fill', '#333')
    .text((d) => d)

  // column labels (every few years to avoid crowding)
  const tickEvery = Math.ceil(props.years.length / 30)
  g.append('g')
    .selectAll('text')
    .data(props.years.filter((_, i) => i % tickEvery === 0))
    .join('text')
    .attr('x', (d) => x(d) + x.bandwidth() / 2)
    .attr('y', props.genres.length * cellHeight + 12)
    .attr('text-anchor', 'end')
    .attr('transform', (d) => `rotate(-45, ${x(d) + x.bandwidth() / 2}, ${props.genres.length * cellHeight + 12})`)
    .attr('font-size', 8)
    .attr('fill', '#333')
    .text((d) => d)

  // legend
  const legendHeight = Math.min(160, props.genres.length * cellHeight)
  const legendScale = d3.scaleLinear().domain([0, maxVal]).range([legendHeight, 0])
  const legendX = props.years.length * cellWidth + 20

  const defs = svg.append('defs')
  const gradId = 'heatmap-gradient'
  const gradient = defs.append('linearGradient').attr('id', gradId).attr('x1', '0').attr('x2', '0').attr('y1', '1').attr('y2', '0')
  d3.range(0, 1.01, 0.1).forEach((t) => {
    gradient.append('stop').attr('offset', `${t * 100}%`).attr('stop-color', d3.interpolateViridis(t))
  })

  const legendG = layer.append('g').attr('transform', `translate(${legendX + margin.left},${margin.top})`)
  legendG.append('rect').attr('width', 14).attr('height', legendHeight).attr('fill', `url(#${gradId})`)
  legendG
    .append('g')
    .attr('transform', 'translate(14,0)')
    .call(d3.axisRight(legendScale).ticks(4))
    .call((gAxis) => gAxis.select('.domain').remove())
  legendG
    .append('text')
    .attr('x', -4)
    .attr('y', -8)
    .attr('font-size', 10)
    .attr('font-weight', 600)
    .attr('fill', '#333')
    .text(props.legendLabel)
}

onMounted(() => {
  render()
  resizeObserver = new ResizeObserver(() => render())
  resizeObserver.observe(chartEl.value)
})
onBeforeUnmount(() => {
  if (resizeObserver) resizeObserver.disconnect()
})
watch(() => [props.genres, props.years, props.valueAt], render)
</script>

<template>
  <div ref="chartEl" class="heatmap"></div>
</template>

<style scoped>
.heatmap {
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
