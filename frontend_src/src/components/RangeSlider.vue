<script setup>
// Dual-handle range slider (two overlapping native <input type="range">
// elements, styled so only their thumbs are clickable -- see .thumb rules
// below) used for every "Year Range" filter in the app. Emits [low, high]
// as a single array; each handler clamps so the low/high thumbs can't cross.
const props = defineProps({
  min: { type: Number, required: true },
  max: { type: Number, required: true },
  modelValue: { type: Array, required: true }, // [low, high]
})
const emit = defineEmits(['update:modelValue'])

function onLow(e) {
  const low = Math.min(Number(e.target.value), props.modelValue[1])
  emit('update:modelValue', [low, props.modelValue[1]])
}
function onHigh(e) {
  const high = Math.max(Number(e.target.value), props.modelValue[0])
  emit('update:modelValue', [props.modelValue[0], high])
}
</script>

<template>
  <div class="range-slider">
    <div class="range-labels">
      <span>{{ modelValue[0] }}</span>
      <span>{{ modelValue[1] }}</span>
    </div>
    <div class="track-wrap">
      <input
        type="range"
        :min="min"
        :max="max"
        :value="modelValue[0]"
        @input="onLow"
        class="thumb thumb-low"
      />
      <input
        type="range"
        :min="min"
        :max="max"
        :value="modelValue[1]"
        @input="onHigh"
        class="thumb thumb-high"
      />
    </div>
    <div class="range-bounds">
      <span>{{ min }}</span>
      <span>{{ max }}</span>
    </div>
  </div>
</template>

<style scoped>
.range-slider {
  padding: 0.2rem 0;
}
.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  font-weight: 600;
  color: #147d75;
  margin-bottom: 0.2rem;
}
.range-bounds {
  display: flex;
  justify-content: space-between;
  font-size: 0.68rem;
  color: #999;
}
.track-wrap {
  position: relative;
  height: 20px;
}
.thumb {
  position: absolute;
  width: 100%;
  top: 6px;
  margin: 0;
  appearance: none;
  background: transparent;
  pointer-events: none;
}
.thumb::-webkit-slider-runnable-track {
  height: 4px;
  background: #dfe3e6;
  border-radius: 2px;
}
.thumb::-webkit-slider-thumb {
  appearance: none;
  pointer-events: auto;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: #147d75;
  cursor: pointer;
  margin-top: -4.5px;
}
.thumb::-moz-range-track {
  height: 4px;
  background: #dfe3e6;
  border-radius: 2px;
}
.thumb::-moz-range-thumb {
  pointer-events: auto;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: #147d75;
  cursor: pointer;
  border: none;
}
</style>
