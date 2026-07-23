<script setup>
// App shell: sticky top nav (brand + links) with a router-view below it for
// the active page. Styled with Tailwind utility classes rather than a scoped
// <style> block, matching the layout conventions of the reference project
// this was redesigned from (see README.md).
import { useRoute } from 'vue-router'
const route = useRoute()

const navItems = [
  { label: 'Home', to: '/' },
  { label: 'Influence Analysis', to: '/influence-analysis' },
  { label: 'Genre Diffusion', to: '/genre-diffusion' },
  { label: 'Talent Radar', to: '/talent-radar' },
  { label: 'Trend Dashboard', to: '/trend-dashboard' },
  { label: 'Career Timeline', to: '/career-timeline' },
  // { label: 'Findings & Predictions', to: '/findings' },
]
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <header class="sticky top-0 z-10 border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur md:px-6">
      <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3">
        <div>
          <p class="text-xs font-semibold uppercase tracking-widest text-slate-500">VAST MC1 &middot; Oceanus Folk</p>
          <h1 class="text-base font-semibold text-slate-900 md:text-lg">VA_SAGOR</h1>
        </div>

        <nav class="flex flex-wrap items-center gap-2">
          <router-link
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="rounded-md px-3 py-2 text-sm transition"
            :class="route.path === item.to
              ? 'bg-teal-50 text-teal-700 font-semibold'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
          >
            {{ item.label }}
          </router-link>
        </nav>
      </div>
    </header>

    <main class="mx-auto w-full max-w-7xl p-4 md:p-6">
      <router-view />
    </main>
  </div>
</template>
