<script setup>
// Task 1 (Sailor's influence profile): thin wrapper around ONE reusable
// NetworkTab component, re-mounted (via :key) against three different
// pre-computed subgraphs -- see src/build_sailor_network.py for how each
// JSON file below was derived from the raw graph.
import { ref } from 'vue'
import NetworkTab from '../components/NetworkTab.vue'

const tabs = [
  {
    name: 'Influenced by',
    dataUrl: '/data/sailor_influenced_by.json',
    subtabLabel: 'Sources of Influence',
    description:
      "Sailor's own creative-influence edges (in the style of / interpolates from / covers / samples / lyrically references), plus who created the works and people behind them.",
  },
  {
    name: 'Her Impact',
    dataUrl: '/data/sailor_her_impact.json',
    subtabLabel: 'Influenced Artists & Collaborators',
    description:
      'Works and artists that draw on Sailor (directly or via her songs), plus the collaborators who created her music with her.',
  },
  {
    name: 'Community Influence',
    dataUrl: '/data/sailor_ego_network.json',
    subtabLabel: 'Community Network',
    description:
      "Sailor's broader 2-hop neighborhood in the Oceanus Folk community — filter by node/edge type to explore.",
  },
]

const activeTab = ref(tabs[0].name)
const activeTabData = () => tabs.find((t) => t.name === activeTab.value)
</script>

<template>
  <div class="panel">
    <div class="panel-header">Sailor Shift Influence Analysis</div>

    <div class="tabs">
      <button
        v-for="t in tabs"
        :key="t.name"
        class="tab"
        :class="{ active: activeTab === t.name }"
        @click="activeTab = t.name"
      >
        {{ t.name }}
      </button>
    </div>

    <div class="panel-body">
      <NetworkTab
        :key="activeTabData().dataUrl"
        :data-url="activeTabData().dataUrl"
        :subtab-label="activeTabData().subtabLabel"
        :description="activeTabData().description"
      />
    </div>
  </div>
</template>

<style scoped>
.panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}
.panel-header {
  background: #fff;
  color: #0f172a;
  padding: 1rem 1.25rem;
  font-weight: 600;
  font-size: 1.05rem;
  border-bottom: 1px solid #e2e8f0;
  text-transform: none;
}
.tabs {
  display: flex;
  border-bottom: 1px solid #e0e3e6;
  background: #f7f8f9;
}
.tab {
  border: none;
  background: none;
  padding: 0.7rem 1.1rem;
  cursor: pointer;
  font-size: 0.88rem;
  color: #555;
  border-bottom: 2px solid transparent;
}
.tab.active {
  color: #147d75;
  font-weight: 600;
  border-bottom-color: #147d75;
}
.panel-body {
  padding: 1rem 1.25rem 1.5rem;
}
</style>
