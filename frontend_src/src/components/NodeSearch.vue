<script setup>
// Single-select autocomplete/search box (type-ahead over a name field),
// used for "search a node/artist by name" across the app. Only renders the
// first 30 matches at a time -- with datasets in the thousands, rendering
// every match on every keystroke would be wasteful and the user only
// scans a handful of results anyway.
import { ref, computed } from 'vue'

const props = defineProps({
  options: { type: Array, default: () => [] }, // [{id, name}]
  modelValue: { type: [Number, String, null], default: null },
})
const emit = defineEmits(['update:modelValue'])

const query = ref('')
const open = ref(false)

const filtered = computed(() => {
  if (!query.value) return props.options.slice(0, 30)
  const q = query.value.toLowerCase()
  return props.options.filter((o) => o.name?.toLowerCase().includes(q)).slice(0, 30)
})

function pick(opt) {
  query.value = opt.name
  open.value = false
  emit('update:modelValue', opt.id)
}

function clear() {
  query.value = ''
  emit('update:modelValue', null)
}
</script>

<template>
  <div class="node-search">
    <input
      type="text"
      v-model="query"
      placeholder="Type or select a node name"
      @focus="open = true"
      @input="open = true"
    />
    <button v-if="modelValue !== null" type="button" class="clear-btn" @click="clear">&times;</button>
    <div v-if="open && filtered.length" class="search-panel" @mouseleave="open = false">
      <div v-for="opt in filtered" :key="opt.id" class="search-option" @click="pick(opt)">
        {{ opt.name }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.node-search {
  position: relative;
}
input {
  width: 100%;
  border: 1px solid #ccd2d8;
  border-radius: 3px;
  padding: 0.4rem 1.6rem 0.4rem 0.6rem;
  font-size: 0.85rem;
  box-sizing: border-box;
}
.clear-btn {
  position: absolute;
  right: 0.4rem;
  top: 0.3rem;
  border: none;
  background: none;
  font-size: 1rem;
  cursor: pointer;
  color: #888;
}
.search-panel {
  position: absolute;
  z-index: 30;
  width: 100%;
  max-height: 200px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #ccd2d8;
  border-radius: 3px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}
.search-option {
  padding: 0.35rem 0.6rem;
  font-size: 0.82rem;
  cursor: pointer;
}
.search-option:hover {
  background: #eef4f9;
}
</style>
