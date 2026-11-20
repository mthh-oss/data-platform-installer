import { createRouter, createWebHistory } from 'vue-router'
import { api, getToken, setToken, setUser } from './api/client'
import Login from './views/Login.vue'
import Workbench from './views/Workbench.vue'
import Orchestrate from './views/Orchestrate.vue'
import Tasks from './views/Tasks.vue'
import Instances from './views/Instances.vue'
import InstanceDetail from './views/InstanceDetail.vue'
import Hosts from './views/Hosts.vue'
import HostDetail from './views/HostDetail.vue'
import PluginMarket from './views/PluginMarket.vue'
import PluginDetail from './views/PluginDetail.vue'
import Alerts from './views/Alerts.vue'
import Logs from './views/Logs.vue'
import Monitor from './views/Monitor.vue'
import Personnel from './views/Personnel.vue'
import Settings from './views/Settings.vue'
import Audit from './views/Audit.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: Login, meta: { public: true } },
    { path: '/setup', name: 'setup', component: Login, meta: { public: true } },

    { path: '/', redirect: '/workbench' },
    { path: '/workbench', name: 'workbench', component: Workbench },
    { path: '/orchestrate', name: 'orchestrate', component: Orchestrate },
    { path: '/tasks', name: 'tasks', component: Tasks },
    { path: '/tasks/:jobId', name: 'task-detail', component: Tasks },
    { path: '/instances', name: 'instances', component: Instances },
    { path: '/instances/:id', name: 'instance-detail', component: InstanceDetail },
    { path: '/hosts', name: 'hosts', component: Hosts },
    { path: '/hosts/:hid', name: 'host-detail', component: HostDetail },
    { path: '/plugins', name: 'plugins', component: PluginMarket },
    { path: '/plugins/:pid', name: 'plugin-detail', component: PluginDetail },
    { path: '/alerts', name: 'alerts', component: Alerts },
    { path: '/logs', name: 'logs', component: Logs },
    { path: '/monitor', name: 'monitor', component: Monitor },

    { path: '/admin/users', name: 'admin-users', component: Personnel },
    { path: '/admin/audit', name: 'admin-audit', component: Audit },
    { path: '/admin/settings', name: 'admin-settings', component: Settings },

    // 旧 CDH 路径收敛到 DataStack
    { path: '/clusters', redirect: '/workbench' },
    { path: '/deploy', redirect: '/orchestrate' },
    { path: '/c/:clusterId/:rest(.*)*', redirect: '/workbench' },
    { path: '/overview', redirect: '/workbench' },
    { path: '/jobs/:id?', redirect: (to) => (to.params.id ? `/tasks/${to.params.id}` : '/tasks') },
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
