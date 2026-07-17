import * as d3 from 'd3'

// Wraps an SVG's plotted content in a <g> that can be panned (drag) and
// zoomed (wheel / pinch), the same interaction the Influence Network graph
// uses. Call this right after creating the outer <svg>, then append all
// chart content into the returned `layer` instead of onto the svg directly.
export function attachZoom(svg, { scaleExtent = [0.5, 8] } = {}) {
  const layer = svg.append('g').attr('class', 'zoom-layer')
  const zoomBehavior = d3
    .zoom()
    .scaleExtent(scaleExtent)
    .on('zoom', (ev) => layer.attr('transform', ev.transform))
  svg.call(zoomBehavior)
  svg.style('cursor', 'grab')
  return { layer, zoomBehavior }
}
