<script setup>
// Small read-only "inspector" card: shows whichever node was last clicked
// or searched for in the Influence Analysis network graph (see NetworkTab's
// selectedNode). Purely presentational -- no logic beyond "show what's there".
defineProps({
  node: { type: Object, default: null },
})
defineEmits(['close'])
</script>

<template>
  <div v-if="node" class="detail-panel">
    <button class="close-btn" @click="$emit('close')">&times;</button>
    <h4>{{ node.name }}</h4>
    <table>
      <tbody>
        <tr><td class="k">Type</td><td>{{ node.type }}</td></tr>
        <tr v-if="node.genre"><td class="k">Genre</td><td>{{ node.genre }}</td></tr>
        <tr v-if="node.release_date"><td class="k">Release</td><td>{{ node.release_date }}</td></tr>
        <tr v-if="node.notable !== undefined"><td class="k">Notable</td><td>{{ node.notable ? 'Yes' : 'No' }}</td></tr>
        <tr v-if="node.depth >= 0"><td class="k">Hops from Sailor</td><td>{{ node.depth }}</td></tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.detail-panel {
  position: relative;
  background: #f7fbfe;
  border: 1px solid #cfe2ee;
  border-radius: 4px;
  padding: 0.7rem 0.8rem;
  margin-top: 0.75rem;
  font-size: 0.8rem;
}
.detail-panel h4 {
  margin: 0 0 0.4rem;
  color: #1e2733;
  padding-right: 1rem;
}
.close-btn {
  position: absolute;
  right: 0.4rem;
  top: 0.4rem;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 1rem;
  color: #888;
}
table {
  width: 100%;
}
.k {
  color: #888;
  width: 45%;
  padding: 0.1rem 0;
}
</style>
