<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AiFloat from './components/AiFloat.vue'
import { api, getUser, setToken, setUser } from './api/client'

const route = useRoute()
const router = useRouter()
const user = ref(getUser())
const clusters = ref([])
const sideFilter = ref('')

const isAuth = computed(() => ['/login', '/setup'].includes(route.path))
const clusterId = computed(() => route.params.clusterId ? Number(route.params.clusterId) : null)
const inCluster = computed(() => !!clusterId.value)
const inAdmin = computed(() => route.path.startsWith('/admin'))

const clusterNav = [
  { path: 'overview', label: '集群总览' },
  { path: 'services', label: '服务管理' },
  { path: 'hosts', label: '主机管理' },
  { path: 'alerts', label: '告警中心' },
  { path: 'logs', label: '日志检索' },
  { path: 'parcels', label: '版本包管理' },
  { path: 'tasks', label: '任务中心' },
  { path: 'client', label: '客户端配置' },
  { path: 'config', label: '配置中心' },
]

const adminNav = [
  { path: '/admin/users', label: '人员关系' },
  { path: '/admin/audit', label: '审计日志' },
  { path: '/admin/settings', label: '平台设置' },
]

const sideTitle = computed(() => {
  if (inAdmin.value) return '系统管理'
  if (inCluster.value) return '集群功能'
  return '平台入口'
})

const sideItems = computed(() => {
  let items = []
  if (inAdmin.value) items = adminNav
  else if (inCluster.value) {
    items = clusterNav.map((n) => ({
      path: `/c/${clusterId.value}/${n.path}`,
      label: n.label,
    }))
  } else {
    items = [
      { path: '/clusters', label: '集群选择' },
      { path: '/admin/users', label: '系统管理' },
    ]
  }
  const q = sideFilter.value.trim()
  return q ? items.filter((i) => i.label.includes(q)) : items
})

const currentCluster = computed(() => clusters.value.find((c) => c.id === clusterId.value))

const crumb = computed(() => {
  if (inAdmin.value) return { a: '平台', b: sideItems.value.find((i) => i.path === route.path)?.label || '系统管理' }
  if (inCluster.value) {
    const page = clusterNav.find((n) => route.path.includes(`/c/${clusterId.value}/${n.path}`))
    return { a: currentCluster.value?.name || `集群#${clusterId.value}`, b: page?.label || '详情' }
  }
  return { a: '平台', b: '集群选择' }
})

async function loadClusters() {
  try {
    clusters.value = await api.clusters()
  } catch {
    clusters.value = []
  }
}

watch(
  () => route.path,
  async () => {
    user.value = getUser()
    if (!isAuth.value) await loadClusters()
  },
  { immediate: true },
)

function go(path) {
  router.push(path)
}

function logout() {
  setToken('')
  setUser(null)
  router.push('/login')
}

function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<template>
  <div class="app-shell" :class="{ auth: isAuth }">
    <template v-if="!isAuth">
      <header class="topbar">
        <div class="brand">
          <div class="brand-mark">D</div>
          <div class="brand-name">DataCluster 管控平台</div>
        </div>
        <div class="top-center" v-if="inCluster">
          <select class="cluster-switch" style="width:auto" :value="clusterId" @change="(e) => router.push(`/c/${e.target.value}/overview`)">
            <option v-for="c in clusters" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="top-right">
          <button class="link-btn" @click="go('/clusters')">集群</button>
          <span>{{ user?.display_name || user?.username }}</span>
          <div class="avatar">{{ (user?.display_name || user?.username || 'U').slice(0,1) }}</div>
          <button class="link-btn" @click="logout">退出</button>
        </div>
      </header>

      <div class="body">
        <aside class="rail">
          <button class="rail-item" :class="{ active: !inAdmin }" title="集群" @click="go(inCluster ? `/c/${clusterId}/overview` : '/clusters')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
          </button>
          <button class="rail-item" :class="{ active: inAdmin }" title="系统管理" @click="go('/admin/users')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4L7 17M17 7l1.4-1.4"/></svg>
          </button>
          <div class="rail-spacer"></div>
        </aside>

        <aside class="side">
          <div class="side-head">{{ sideTitle }}</div>
          <input v-model="sideFilter" class="side-search" placeholder="搜索菜单" />
          <nav class="side-nav">
            <button
              v-for="item in sideItems"
              :key="item.path"
              :class="{ active: isActive(item.path) }"
              @click="go(item.path)"
            >{{ item.label }}</button>
          </nav>
        </aside>

        <main class="main">
          <div class="crumb">{{ crumb.a }} / <b>{{ crumb.b }}</b></div>
          <router-view />
        </main>
      </div>

      <AiFloat />
    </template>
    <router-view v-else />
  </div>
</template>
