import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import InfluenceAnalysis from '../views/InfluenceAnalysis.vue'
import GenreDiffusion from '../views/GenreDiffusion.vue'
import TalentRadar from '../views/TalentRadar.vue'
import TrendDashboard from '../views/TrendDashboard.vue'
import CareerTimeline from '../views/CareerTimeline.vue'
import Findings from '../views/Findings.vue'

// One route per module, each mapped to a sub-question of the MC1 brief
// (see README.md's "MC1 Task Map" for the full task -> module breakdown):
//   InfluenceAnalysis  -> Task 1 (Sailor's influence profile)
//   GenreDiffusion     -> Task 2 (how Oceanus Folk's influence spread)
//   TalentRadar / CareerTimeline / Findings -> Task 3 (rising-star profile + predictions)
const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/influence-analysis', name: 'InfluenceAnalysis', component: InfluenceAnalysis },
  { path: '/genre-diffusion', name: 'GenreDiffusion', component: GenreDiffusion },
  { path: '/talent-radar', name: 'TalentRadar', component: TalentRadar },
  { path: '/trend-dashboard', name: 'TrendDashboard', component: TrendDashboard },
  { path: '/career-timeline', name: 'CareerTimeline', component: CareerTimeline },
  { path: '/findings', name: 'Findings', component: Findings },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
