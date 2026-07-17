<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as d3 from 'd3'
import { makeCategoryColorScale } from '../utils/colorScale'
import { attachZoom } from '../utils/zoom'

const props = defineProps({
  genres: { type: Array, default: () => [] }, // ordered list of genre names
  matrix: { type: Array, default: () => [] }, // square matrix aligned to genres
  // Cross-widget link: when set, that genre's arc/ribbons are highlighted and
  // everything else dims, so clicking here and seeing it reflected in another
  // widget (e.g. the Sankey) reads as one connected view, not two accidents.
  selectedGenre: { type: String, default: null },
})
const emit = defineEmits(['genre-click'])

const chartEl = ref(null)
let resizeObserver = null



function render() {
  if (!chartEl.value) return
  const el = chartEl.value
  el.innerHTML = ''

  if (!props.genres.length) {
    d3.select(el).append('p').attr('class', 'empty').text('No data for the current filters.')
    return
  }

  const size = Math.min(el.clientWidth || 700, 640)
  const outerRadius = size / 2 - 90
  const innerRadius = outerRadius - 16

  const svgRoot = d3.select(el).append('svg').attr('width', size).attr('height', size)
  const { layer } = attachZoom(svgRoot)
  const svg = layer.append('g').attr('transform', `translate(${size / 2},${size / 2})`)

  const chordLayout = d3.chord().padAngle(0.03).sortSubgroups(d3.descending)
  const chords = chordLayout(props.matrix)
  const colorScale = makeCategoryColorScale(props.genres)

  const arc = d3.arc().innerRadius(innerRadius).outerRadius(outerRadius)
  const ribbon = d3.ribbon().radius(innerRadius)

  const dimmed = (g) => (props.selectedGenre ? g !== props.selectedGenre : false)

  svg
    .append('g')
    .selectAll('path')
    .data(chords.groups)
    .join('path')
    .attr('d', arc)
    .attr('fill', (d) => colorScale(props.genres[d.index]))
    .attr('stroke', (d) => (props.genres[d.index] === props.selectedGenre ? '#0f172a' : '#fff'))
    .attr('stroke-width', (d) => (props.genres[d.index] === props.selectedGenre ? 2 : 1))
    .attr('opacity', (d) => (dimmed(props.genres[d.index]) ? 0.35 : 1))
    .style('cursor', 'pointer')
    .on('click', (ev, d) => emit('genre-click', props.genres[d.index]))
    .append('title')
    .text((d) => `${props.genres[d.index]}: ${d.value} (click to focus in Top Influenced Artists)`)

  svg
    .append('g')
    .selectAll('text')
    .data(chords.groups)
    .join('text')
    .each((d) => (d.angle = (d.startAngle + d.endAngle) / 2))
    .attr('dy', '0.35em')
    .attr(
      'transform',
      (d) => `
        rotate(${(d.angle * 180) / Math.PI - 90})
        translate(${outerRadius + 8})
        ${d.angle > Math.PI ? 'rotate(180)' : ''}
      `
    )
    .attr('text-anchor', (d) => (d.angle > Math.PI ? 'end' : null))
    .attr('font-size', 9)
    .attr('fill', '#333')
    .attr('font-weight', (d) => (props.genres[d.index] === props.selectedGenre ? 700 : 400))
    .style('cursor', 'pointer')
    .on('click', (ev, d) => emit('genre-click', props.genres[d.index]))
    .text((d) => props.genres[d.index])

  svg
    .append('g')
    .attr('fill-opacity', 0.65)
    .selectAll('path')
    .data(chords)
    .join('path')
    .attr('d', ribbon)
    .attr('fill', (d) => colorScale(props.genres[d.source.index]))
    .attr('stroke', '#fff')
    .attr('stroke-width', 0.3)
    .attr('opacity', (d) =>
      dimmed(props.genres[d.source.index]) && dimmed(props.genres[d.target.index]) ? 0.15 : 1
    )
    .append('title')
    .text(
      (d) =>
        `${props.genres[d.source.index]} → ${props.genres[d.target.index]}: ${d.source.value}`
    )
}

onMounted(() => {
  render()
  resizeObserver = new ResizeObserver(() => render())
  resizeObserver.observe(chartEl.value)
})
onBeforeUnmount(() => {
  if (resizeObserver) resizeObserver.disconnect()
})
watch(() => [props.genres, props.matrix, props.selectedGenre], render)
</script>

<template>
  <div ref="chartEl" class="chord-chart"></div>
</template>

<style scoped>
.chord-chart {
  width: 100%;
  display: flex;
  justify-content: center;
}
.empty {
  color: #999;
  font-size: 0.85rem;
  padding: 2rem 0;
  text-align: center;
}
</style>
