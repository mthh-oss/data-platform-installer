import { createRouter, createWebHistory } from 'vue-router'
import Wizard from './views/Wizard.vue'
import DeployJobs from './views/DeployJobs.vue'
import Monitor from './views/Monitor.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'wizard', component: Wizard },
    { path: '/jobs', name: 'jobs', component: DeployJobs },
    { path: '/jobs/:id', name: 'job-detail', component: DeployJobs, props: true },
    { path: '/monitor', name: 'monitor', component: Monitor },
  ],
})

export default router
