import { createRouter, createWebHistory } from 'vue-router'
import { api, getToken, setToken, setUser } from './api/client'
import Login from './views/Login.vue'
import ClusterSelect from './views/ClusterSelect.vue'
import ClusterDashboard from './views/ClusterDashboard.vue'
import Services from './views/Services.vue'
import ServiceDetail from './views/ServiceDetail.vue'
import Hosts from './views/Hosts.vue'
import HostDetail from './views/HostDetail.vue'
import Alerts from './views/Alerts.vue'
import Logs from './views/Logs.vue'
import Parcels from './views/Parcels.vue'
import ClientConfig from './views/ClientConfig.vue'
import Tasks from './views/Tasks.vue'
import ConfigCenter from './views/ConfigCenter.vue'
import Wizard from './views/Wizard.vue'
import Personnel from './views/Personnel.vue'
import Settings from './views/Settings.vue'
import Audit from './views/Audit.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: Login, meta: { public: true } },
    { path: '/setup', name: 'setup', component: Login, meta: { public: true } },

    { path: '/', redirect: '/clusters' },
    { path: '/clusters', name: 'clusters', component: ClusterSelect },
    { path: '/deploy', name: 'deploy', component: Wizard },

    { path: '/c/:clusterId/overview', name: 'overview', component: ClusterDashboard },
    { path: '/c/:clusterId/services', name: 'services', component: Services },
    { path: '/c/:clusterId/services/:sid', name: 'service-detail', component: ServiceDetail },
    { path: '/c/:clusterId/hosts', name: 'hosts', component: Hosts },
    { path: '/c/:clusterId/hosts/:hid', name: 'host-detail', component: HostDetail },
    { path: '/c/:clusterId/alerts', name: 'alerts', component: Alerts },
    { path: '/c/:clusterId/logs', name: 'logs', component: Logs },
    { path: '/c/:clusterId/parcels', name: 'parcels', component: Parcels },
    { path: '/c/:clusterId/client', name: 'client', component: ClientConfig },
    { path: '/c/:clusterId/tasks', name: 'tasks', component: Tasks },
    { path: '/c/:clusterId/tasks/:jobId', name: 'task-detail', component: Tasks },
    { path: '/c/:clusterId/config', name: 'config', component: ConfigCenter },

    { path: '/admin/users', name: 'admin-users', component: Personnel },
    { path: '/admin/audit', name: 'admin-audit', component: Audit },
    { path: '/admin/settings', name: 'admin-settings', component: Settings },

    // legacy redirects
    { path: '/overview', redirect: '/clusters' },
    { path: '/jobs/:id?', redirect: (to) => (to.params.id ? `/clusters` : '/clusters') },
    { path: '/monitor', redirect: '/clusters' },
    { path: '/personnel', redirect: '/admin/users' },
    { path: '/settings', redirect: '/admin/settings' },
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
