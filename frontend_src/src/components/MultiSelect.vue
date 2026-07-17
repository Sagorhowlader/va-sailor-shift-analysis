<script setup>
// Generic checkbox dropdown used by every module's filter panel (node/edge
// type, genre, etc). Deliberately dumb/reusable: it just holds an array of
// currently-checked option strings and emits the new array on every change
// (standard Vue v-model contract via update:modelValue) -- all the actual
// filtering logic lives in the parent view/component, not here.
import { ref, computed } from 'vue'

const props = defineProps({
  label: String,
  options: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)

const summary = computed(() => {
  if (props.modelValue.length === 0) return 'None'
  if (props.modelValue.length === props.options.length) return 'All'
  return props.modelValue.join(', ')
})

function toggle(opt) {
  const set = new Set(props.modelValue)
  if (set.has(opt)) set.delete(opt)
  else set.add(opt)
  emit('update:modelValue', props.options.filter((o) => set.has(o)))
}

function selectAll() {
  emit('update:modelValue', [...props.options])
}
function selectNone() {
  emit('update:modelValue', [])
}
</script>

<template>
  <div class="multiselect">
    <label>{{ label }}</label>
    <button type="button" class="ms-trigger" @click="open = !open">
      <span class="ms-summary">{{ summary }}</span>
      <span class="ms-caret">&#9662;</span>
    </button>
    <div v-if="open" class="ms-panel">
      <div class="ms-actions">
        <button type="button" @click="selectAll">All</button>
        <button type="button" @click="selectNone">None</button>
      </div>
      <label v-for="opt in options" :key="opt" class="ms-option">
        <input
          type="checkbox"
          :checked="modelValue.includes(opt)"
          @change="toggle(opt)"
        />
        {{ opt }}
      </label>
    </div>
  </div>
</template>

<style scoped>
.multiselect {
  position: relative;
  margin-bottom: 1rem;
  font-size: 0.85rem;
}
label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.3rem;
  color: #333;
}
.ms-trigger {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  border: 1px solid #ccd2d8;
  border-radius: 3px;
  padding: 0.4rem 0.6rem;
  cursor: pointer;
  text-align: left;
}
.ms-summary {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 220px;
}
.ms-panel {
  position: absolute;
  z-index: 20;
  background: #fff;
  border: 1px solid #ccd2d8;
  border-radius: 3px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  padding: 0.4rem 0.6rem;
  width: 100%;
  max-height: 220px;
  overflow-y: auto;
}
.ms-actions {
  display: flex;
  gap: 0.6rem;
  margin-bottom: 0.4rem;
}
.ms-actions button {
  border: none;
  background: none;
  color: #147d75;
  cursor: pointer;
  padding: 0;
  font-size: 0.8rem;
}
.ms-option {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 400;
  padding: 0.15rem 0;
}
</style>
