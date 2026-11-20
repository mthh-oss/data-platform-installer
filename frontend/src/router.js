import { createRouter, createWebHistory } from 'vue-router'
import { api, getToken, setToken, setUser } from './api/client'
import Wizard from './views/Wizard.vue'
import DeployJobs from './views/DeployJobs.vue'
import Monitor from './views/Monitor.vue'
import Overview from './views/Overview.vue'
import Settings from './views/Settings.vue'
import Login from './views/Login.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: Login, meta: { public: true } },
    { path: '/setup', name: 'setup', component: Login, meta: { public: true } },
    { path: '/', name: 'wizard', component: Wizard },
    { path: '/overview', name: 'overview', component: Overview },
    { path: '/jobs', name: 'jobs', component: DeployJobs },
    { path: '/jobs/:id', name: 'job-detail', component: DeployJobs, props: true },
    { path: '/monitor', name: 'monitor', component: Monitor },
    { path: '/settings', name: 'settings', component: Settings },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  const token = getToken()
  try {
    const st = await api.authStatus()
    if (!st.initialized) return '/login'
    if (!token) return '/login'
    const me = await api.me()
    setUser(me)
    return true
  } catch {
    setToken('')
    setUser(null)
    return '/login'
  }
})

export default router
