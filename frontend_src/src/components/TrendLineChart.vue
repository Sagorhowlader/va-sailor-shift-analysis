<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as d3 from 'd3'
import { makeCategoryColorScale } from '../utils/colorScale'
import { attachZoom } from '../utils/zoom'

const props = defineProps({
  // series: [{ genre, points: [{year, count}] }]
  series: { type: Array, default: () => [] },
  title: { type: String, default: '' },
  yLabel: { type: String, default: 'Count' },
})

const chartEl = ref(null)
let resizeObserver = null



function render() {
  if (!chartEl.value) return
  const el = chartEl.value
  el.innerHTML = ''

  const width = el.clientWidth || 700
  const height = 380
  const margin = { top: 15, right: 15, bottom: 40, left: 45 }

  const allGenres = props.series.map((s) => s.genre)
  const allPoints = props.series.flatMap((s) => s.points)
  if (!allPoints.length) {
    d3.select(el).append('p').attr('class', 'empty').text('No data for the current filters.')
    return
  }

  const svg = d3.select(el).append('svg').attr('width', width).attr('height', height)
  const { layer } = attachZoom(svg)

  const x = d3
    .scaleLinear()
    .domain(d3.extent(allPoints, (d) => d.year))
    .range([margin.left, width - margin.right])

  const y = d3
    .scaleLinear()
    .domain([0, d3.max(allPoints, (d) => d.count) || 1])
    .nice()
    .range([height - margin.bottom, margin.top])

  layer
    .append('g')
    .attr('transform', `translate(0,${height - margin.bottom})`)
    .call(d3.axisBottom(x).tickFormat(d3.format('d')))

  layer.append('g').attr('transform', `translate(${margin.left},0)`).call(d3.axisLeft(y).ticks(5))

  const line = d3
    .line()
    .x((d) => x(d.year))
    .y((d) => y(d.count))
    .curve(d3.curveMonotoneX)

  const g = layer.append('g')
  const colorScale = makeCategoryColorScale(allGenres)

  // Lines first (a series with only 1 point draws no visible line here,
  // which is expected -- you can't connect a single point).
  props.series.forEach((s) => {
    const c = colorScale(s.genre)
    g.append('path')
      .datum(s.points)
      .attr('fill', 'none')
      .attr('stroke', c)
      .attr('stroke-width', 2)
      .attr('d', line)
  })

  // Dots: built as one flat list (instead of one .selectAll() per series)
  // so we can (a) draw a bigger, outlined marker for any series that has
  // only a single data point -- otherwise a lone dot the same tiny size as
  // every other point is easy to miss or mistake for a rendering gap -- and
  // (b) detect when two different series land on the exact same pixel
  // (same year + same count, e.g. two artists who each released their only
  // work in the same year) and nudge them apart slightly so one doesn't
  // silently sit underneath and hide the other.
  const allDots = []
  props.series.forEach((s) => {
    const c = colorScale(s.genre)
    s.points.forEach((d) => {
      allDots.push({ genre: s.genre, color: c, year: d.year, count: d.count, isSingle: s.points.length === 1 })
    })
  })

  const overlapGroups = new Map()
  allDots.forEach((d) => {
    const key = `${d.year}|${d.count}`
    if (!overlapGroups.has(key)) overlapGroups.set(key, [])
    overlapGroups.get(key).push(d)
  })
  overlapGroups.forEach((group) => {
    if (group.length < 2) return
    const nudge = 5
    group.forEach((d, i) => {
      const angle = (i / group.length) * 2 * Math.PI
      d.offsetX = Math.cos(angle) * nudge
      d.offsetY = Math.sin(angle) * nudge
    })
  })

  g.selectAll('.data-dot')
    .data(allDots)
    .join('circle')
    .attr('class', 'data-dot')
    .attr('cx', (d) => x(d.year) + (d.offsetX || 0))
    .attr('cy', (d) => y(d.count) + (d.offsetY || 0))
    .attr('r', (d) => (d.isSingle ? 6 : 2.5))
    .attr('fill', (d) => d.color)
    .attr('stroke', (d) => (d.isSingle ? '#fff' : 'none'))
    .attr('stroke-width', (d) => (d.isSingle ? 1.5 : 0))
    .append('title')
    .text((d) => `${d.genre}, ${d.year}: ${d.count}${d.isSingle ? ' (only data point for this series)' : ''}`)

  layer
    .append('text')
    .attr('x', width / 2)
    .attr('y', height - 4)
    .attr('text-anchor', 'middle')
    .attr('font-size', 11)
    .attr('fill', '#555')
    .text('Year')

  layer
    .append('text')
    .attr('transform', 'rotate(-90)')
    .attr('x', -height / 2)
    .attr('y', 12)
    .attr('text-anchor', 'middle')
    .attr('font-size', 11)
    .attr('fill', '#555')
    .text(props.yLabel)
}

onMounted(() => {
  render()
  resizeObserver = new ResizeObserver(() => render())
  resizeObserver.observe(chartEl.value)
})
onBeforeUnmount(() => {
  if (resizeObserver) resizeObserver.disconnect()
})
watch(() => props.series, render)

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
}
.chart {
  width: 100%;
}
.empty {
  color: #999;
  font-size: 0.85rem;
  padding: 2rem 0;
  text-align: center;
}
</style>
