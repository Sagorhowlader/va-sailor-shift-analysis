<script setup>
// Reusable card used on the Home page's module grid. Renders as a clickable
// <router-link> when a `to` path is given, or a plain <article> otherwise --
// same component either way, just a different root tag (see the
// :is="to ? ... : ..." in the template).
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, required: true },
  to: { type: String, default: null },
})
</script>

<template>
  <component :is="to ? 'router-link' : 'article'" :to="to" class="group block rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-teal-300 hover:shadow-md">
    <p class="text-xs font-semibold uppercase tracking-wider text-slate-500">{{ subtitle }}</p>
    <h3 class="mt-1 text-base font-semibold text-slate-900">{{ title }}</h3>
    <div class="mt-4 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600">
      <slot />
    </div>
    <p v-if="to" class="mt-3 text-sm font-semibold text-teal-700 opacity-0 transition group-hover:opacity-100">
      Open &rarr;
    </p>
  </component>
</template>
