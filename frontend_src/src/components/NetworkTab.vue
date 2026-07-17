<script setup>
import { ref, computed, watch } from 'vue'
import MultiSelect from './MultiSelect.vue'
import NodeSearch from './NodeSearch.vue'
import RangeSlider from './RangeSlider.vue'
import NetworkGraph from './NetworkGraph.vue'
import SummaryStats from './SummaryStats.vue'
import NodeDetailPanel from './NodeDetailPanel.vue'
import { ALL_NODE_TYPES, ALL_EDGE_TYPES, NODE_COLORS, EDGE_COLORS } from '../constants/graphStyle'

const props = defineProps({
  dataUrl: { type: String, required: true },
  subtabLabel: { type: String, default: 'Network' },
  description: { type: String, default: '' },
})

const loading = ref(true)
const error = ref(null)
const rawNodes = ref([])
const rawEdges = ref([])
const centerId = ref(null)

const activeSubtab = ref('Influence Network')
const selectedNode = ref(null)

const nodeTypes = ref([...ALL_NODE_TYPES])
const edgeTypes = ref([...ALL_EDGE_TYPES])
const notableFilter = ref('TRUE') // 'All' | 'TRUE' | 'FALSE'
const genres = ref([])
const selectedGenres = ref([])
const yearBounds = ref([1980, 2040])
const yearRange = ref([1980, 2040])
const maxDepth = ref(3)
const depthLimit = ref(3)
const searchNodeId = ref(null)

async function load(url) {
  loading.value = true
  error.value = null
  selectedNode.value = null
  searchNodeId.value = null
  try {
    const res = await fetch(url)
    if (!res.ok) throw new Error('Failed to load network data')
    const data = await res.json()
    rawNodes.value = data.nodes
    rawEdges.value = data.edges
    centerId.value = data.center

    nodeTypes.value = [...ALL_NODE_TYPES]
    edgeTypes.value = [...ALL_EDGE_TYPES]
    notableFilter.value = 'TRUE'

    const genreSet = new Set(data.nodes.map((n) => n.genre).filter(Boolean))
    genres.value = [...genreSet].sort()
    selectedGenres.value = [...genres.value]

    const years = data.nodes
      .map((n) => parseInt(n.release_date, 10))
      .filter((y) => !Number.isNaN(y))
    const lo = years.length ? Math.min(...years) : 1980
    const hi = years.length ? Math.max(...years) : 2040
    yearBounds.value = [lo, hi]
    yearRange.value = [lo, hi]

    const depths = data.nodes.map((n) => n.depth).filter((d) => d >= 0)
    maxDepth.value = depths.length ? Math.max(...depths) : 1
    depthLimit.value = maxDepth.value
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

watch(() => props.dataUrl, (url) => load(url), { immediate: true })

const nodeById = computed(() => {
  const m = new Map()
  rawNodes.value.forEach((n) => m.set(n.id, n))
  return m
})

function passesNodeFilters(n) {
  // Sailor Shift (the center node) is always shown, regardless of the other
  // filters -- e.g. deselecting "Person" in the node type filter shouldn't
  // remove her, since every other node in the view is positioned relative
  // to her.
  if (n.id === centerId.value) return true
  if (!nodeTypes.value.includes(n.type)) return false
  if (notableFilter.value !== 'All' && n.notable !== null && n.notable !== undefined) {
    const wantTrue = notableFilter.value === 'TRUE'
    if (Boolean(n.notable) !== wantTrue) return false
  }
  if (n.genre && !selectedGenres.value.includes(n.genre)) return false
  const yr = parseInt(n.release_date, 10)
  if (!Number.isNaN(yr) && (yr < yearRange.value[0] || yr > yearRange.value[1])) return false
  if (n.depth >= 0 && n.depth > depthLimit.value) return false
  return true
}

const filteredEdges = computed(() => {
  return rawEdges.value.filter((e) => {
    const s = nodeById.value.get(e.source)
    const t = nodeById.value.get(e.target)
    if (!s || !t) return false
    if (!edgeTypes.value.includes(e.type)) return false
    return passesNodeFilters(s) && passesNodeFilters(t)
  })
})

const filteredNodes = computed(() => {
  const ids = new Set()
  filteredEdges.value.forEach((e) => {
    ids.add(e.source)
    ids.add(e.target)
  })
  if (centerId.value !== null) ids.add(centerId.value)
  return rawNodes.value.filter((n) => ids.has(n.id))
})

const searchOptions = computed(() =>
  [...rawNodes.value].sort((a, b) => (a.name || '').localeCompare(b.name || ''))
)

function onSearchSelect(id) {
  searchNodeId.value = id
  selectedNode.value = id !== null ? nodeById.value.get(id) : null
}

function onNodeClick(node) {
  selectedNode.value = node
  searchNodeId.value = node.id
}
</script>

<template>
  <div>
    <div class="subtabs">
      <button
        v-for="t in ['Influence Network', 'Summary Statistics']"
        :key="t"
        class="subtab"
        :class="{ active: activeSubtab === t }"
        @click="activeSubtab = t"
      >
        {{ t }}
      </button>
    </div>

    <p v-if="description" class="description">{{ description }}</p>

    <div class="layout">
      <div class="filters">
        <MultiSelect label="Select Node Type" :options="ALL_NODE_TYPES" v-model="nodeTypes" />

        <label class="field-label">Search Artists Name</label>
        <NodeSearch :options="searchOptions" :model-value="searchNodeId" @update:modelValue="onSearchSelect" />
        <p class="hint">
          Selecting a node will zoom in and highlight it in the network graph.
          Tip: click on a node to reveal more detailed information.
        </p>

        <MultiSelect label="Select Edge Type" :options="ALL_EDGE_TYPES" v-model="edgeTypes" />

        <label class="field-label">Is Notable?</label>
        <div class="radio-row">
          <label><input type="radio" value="All" v-model="notableFilter" /> All</label>
          <label><input type="radio" value="TRUE" v-model="notableFilter" /> TRUE</label>
          <label><input type="radio" value="FALSE" v-model="notableFilter" /> FALSE</label>
        </div>

        <MultiSelect label="Select Genre(s)" :options="genres" v-model="selectedGenres" />

        <label class="field-label">Release Year Range</label>
        <RangeSlider :min="yearBounds[0]" :max="yearBounds[1]" v-model="yearRange" />

        <label class="field-label">Select Network Depth (Layers from Sailor Shift)</label>
        <input type="range" min="1" :max="maxDepth" step="1" v-model.number="depthLimit" class="depth-slider" />
        <div class="depth-ticks">
          <span v-for="d in maxDepth" :key="d">{{ d }}</span>
        </div>
      </div>

      <div class="graph-area">
        <p v-if="loading">Loading network&hellip;</p>
        <p v-else-if="error" class="error">{{ error }}</p>
        <template v-else-if="activeSubtab === 'Influence Network'">
          <NetworkGraph
            :nodes="filteredNodes"
            :edges="filteredEdges"
            :center-id="centerId"
            :focus-id="searchNodeId"
            @select-node="onNodeClick"
          />
        </template>
        <SummaryStats v-else :nodes="filteredNodes" :edges="filteredEdges" :center-id="centerId" />
      </div>

      <div class="legend">
        <p class="stat">{{ filteredNodes.length }} nodes / {{ filteredEdges.length }} edges shown</p>

        <NodeDetailPanel :node="selectedNode" @close="selectedNode = null" />

        <h4>Node Legend</h4>
        <div v-for="(color, type) in NODE_COLORS" :key="type" class="legend-row">
          <span class="swatch" :style="{ background: color, borderRadius: '50%' }"></span>
          {{ type }}
        </div>
        <h4>Edge Legend</h4>
        <div v-for="(color, type) in EDGE_COLORS" :key="type" class="legend-row">
          <span class="swatch line" :style="{ background: color }"></span>
          {{ type }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.subtabs {
  margin-bottom: 0.5rem;
}
.subtab {
  display: inline-block;
  padding: 0.35rem 0.9rem;
  border: 1px solid #dfe3e6;
  border-bottom: none;
  border-radius: 3px 3px 0 0;
  font-size: 0.82rem;
  background: #f4f5f6;
  cursor: pointer;
  color: #555;
}
.subtab.active {
  background: #e3f3ef;
  color: #147d75;
  font-weight: 600;
}
.description {
  font-size: 0.82rem;
  color: #666;
  margin: 0 0 0.75rem;
}
.layout {
  display: grid;
  grid-template-columns: 240px 1fr 180px;
  gap: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
}
.filters {
  padding: 0.9rem;
  border-right: 1px solid #e2e8f0;
  max-height: 640px;
  overflow-y: auto;
  background: #f8fafc;
}
.field-label {
  display: block;
  font-weight: 600;
  font-size: 0.85rem;
  margin: 0.7rem 0 0.3rem;
  color: #333;
}
.hint {
  font-size: 0.7rem;
  color: #999;
  margin: 0.3rem 0 0.6rem;
  line-height: 1.35;
}
.radio-row {
  display: flex;
  gap: 0.8rem;
  font-size: 0.82rem;
  color: #444;
  margin-bottom: 0.4rem;
}
.radio-row label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.depth-slider {
  width: 100%;
}
.depth-ticks {
  display: flex;
  justify-content: space-between;
  font-size: 0.68rem;
  color: #999;
  padding: 0 2px;
}
.stat {
  font-size: 0.75rem;
  color: #777;
  margin: 0 0 0.6rem;
}
.graph-area {
  min-height: 500px;
  padding: 0.5rem;
}
.legend {
  padding: 0.9rem;
  border-left: 1px solid #e2e8f0;
  font-size: 0.78rem;
  background: #f8fafc;
}
.legend h4 {
  margin: 0.4rem 0 0.3rem;
  font-size: 0.8rem;
}
.legend-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.25rem;
  color: #444;
}
.swatch {
  width: 10px;
  height: 10px;
  display: inline-block;
}
.swatch.line {
  height: 2px;
  border-radius: 0;
}
.error {
  color: #c0392b;
}
</style>
