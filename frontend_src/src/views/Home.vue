<script setup>
// Landing page: a hero blurb plus one DashboardCard per module, each linking
// straight to that module's route. Purely static/presentational -- no data
// fetching here, every card's own view loads its own data on mount.
import DashboardCard from '../components/DashboardCard.vue'

const cards = [
  {
    title: 'Influence Analysis',
    subtitle: 'Node-link diagram',
    to: '/influence-analysis',
    content: "Who shaped Sailor Shift's career, and who has she shaped in turn -- explored as an ego network centered on her.",
  },
  {
    title: 'Genre Diffusion',
    subtitle: 'Trend + chord + sankey',
    to: '/genre-diffusion',
    content: 'How Oceanus Folk spread through the wider music world over time, and what it now draws on in return.',
  },
  {
    title: 'Talent Radar',
    subtitle: 'Scoring + radar chart',
    to: '/talent-radar',
    content: 'Score any Oceanus Folk artist against Sailor on the traits that made her rise, with adjustable weights.',
  },
  {
    title: 'Trend Dashboard',
    subtitle: 'Heatmap + cumulative curve',
    to: '/trend-dashboard',
    content: 'Genre-by-genre release activity, year over year, with CSV export.',
  },
  {
    title: 'Career Timeline',
    subtitle: 'Ego network over time',
    to: '/career-timeline',
    content: "Compare up to three artists' rise in output and influence, side by side.",
  },
  // {
  //   title: 'Findings & Predictions',
  //   subtitle: 'Connected components',
  //   to: '/findings',
  //   content: 'Three data-backed picks for the next Oceanus Folk star, plus reflection notes.',
  // },
]
</script>

<template>
  <div class="mb-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
    <p class="text-xs font-semibold uppercase tracking-widest text-teal-700">VAST Challenge 2025 &middot; Mini-Challenge 1</p>
    <h2 class="mt-1 text-2xl font-semibold text-slate-900">Tracing Sailor Shift &amp; the rise of Oceanus Folk</h2>
    <p class="mt-2 max-w-2xl text-sm text-slate-600">
      A visual analytics workspace built to trace how Sailor Shift rose from a small island tradition
      &mdash; Oceanus Folk &mdash; into a global influence, and to spot who might follow the same path next.
    </p>
  </div>

  <section class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
    <DashboardCard
      v-for="card in cards"
      :key="card.title"
      :title="card.title"
      :subtitle="card.subtitle"
      :to="card.to"
    >
      {{ card.content }}
    </DashboardCard>
  </section>
</template>
