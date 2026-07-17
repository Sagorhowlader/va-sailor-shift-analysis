import * as d3 from 'd3'

// Build a stable ordinal color scale across a rainbow palette, with an
// explicit domain covering every category up front. (A previous version
// created a brand-new scaleOrdinal() per lookup with no domain set --
// since scaleOrdinal builds its domain from values it has already seen,
// a fresh scale only ever sees one value per call and always returns the
// first color in its range. That bug is why charts rendered a single color
// instead of one per category.)
export function makeCategoryColorScale(categories) {
  return d3
    .scaleOrdinal()
    .domain(categories)
    .range(d3.quantize(d3.interpolateRainbow, Math.max(categories.length, 3) + 1))
}
