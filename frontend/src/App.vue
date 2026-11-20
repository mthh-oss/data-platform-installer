<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AiFloat from './components/AiFloat.vue'
import { getUser, setToken, setUser } from './api/client'

const route = useRoute()
const router = useRouter()
const user = ref(getUser())
const sideFilter = ref('')

const isAuth = computed(() => ['/login', '/setup'].includes(route.path))

const primaryNav = [
  { path: '/workbench', label: '工作台' },
  { path: '/orchestrate', label: '组件编排' },
  { path: '/instances', label: '实例管理' },
  { path: '/tasks', label: '部署任务' },
  { path: '/hosts', label: '主机资源' },
  { path: '/plugins', label: '插件市场' },
]

const observeNav = [
  { path: '/alerts', label: '告警中心' },
  { path: '/logs', label: '日志检索' },
  { path: '/monitor', label: '监控大盘' },
]

const adminNav = [
  { path: '/admin/users', label: '用户权限' },
  { path: '/admin/audit', label: '审计日志' },
  { path: '/admin/settings', label: '平台设置' },
]

const sideGroups = computed(() => {
  const q = sideFilter.value.trim()
  const filter = (items) => (q ? items.filter((i) => i.label.includes(q)) : items)
  return [
    { title: '主流程', items: filter(primaryNav) },
    { title: '观测', items: filter(observeNav) },
    { title: '系统', items: filter(adminNav) },
  ].filter((g) => g.items.length)
})

const crumb = computed(() => {
  const all = [...primaryNav, ...observeNav, ...adminNav]
  const hit = all.find((i) => route.path === i.path || route.path.startsWith(i.path + '/'))
  if (route.path.startsWith('/orchestrate')) return { a: 'DataStack', b: '组件编排' }
  if (route.path.startsWith('/instances/')) return { a: '实例管理', b: '实例详情' }
  if (route.path.startsWith('/tasks/')) return { a: '部署任务', b: '任务详情' }
  if (route.path.startsWith('/plugins/')) return { a: '插件市场', b: '插件详情' }
  if (route.path.startsWith('/hosts/')) return { a: '主机资源', b: '主机详情' }
  return { a: 'DataStack', b: hit?.label || '工作台' }
})

watch(
  () => route.path,
  () => {
    user.value = getUser()
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
  if (path === '/workbench') return route.path === '/workbench' || route.path === '/'
  return route.path === path || route.path.startsWith(path + '/')
}

const railMode = computed(() => {
  if (route.path.startsWith('/admin')) return 'admin'
  if (route.path.startsWith('/plugins')) return 'plugins'
  return 'home'
})
</script>

<template>
  <div class="app-shell" :class="{ auth: isAuth }">
    <template v-if="!isAuth">
      <header class="topbar">
        <div class="brand">
          <div class="brand-mark">DS</div>
          <div class="brand-name">Data<span>Stack</span></div>
        </div>
        <div class="top-center">
          <span class="top-tagline">插件化大数据底座编排</span>
        </div>
        <div class="top-right">
          <button class="btn primary" @click="go('/orchestrate')">新建编排</button>
          <div class="user-chip">
            <div class="avatar">{{ (user?.display_name || user?.username || 'U').slice(0, 1) }}</div>
            <span>{{ user?.display_name || user?.username }}</span>
          </div>
          <button class="link-btn" @click="logout">退出</button>
        </div>
      </header>

      <div class="body">
        <aside class="rail">
          <button class="rail-item" :class="{ active: railMode === 'home' }" title="工作台" @click="go('/workbench')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 10l8-6 8 6v9a1 1 0 01-1 1h-5v-5H10v5H5a1 1 0 01-1-1v-9z"/></svg>
          </button>
          <button class="rail-item" :class="{ active: railMode === 'plugins' }" title="插件市场" @click="go('/plugins')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3v3M12 18v3M3 12h3M18 12h3M6.2 6.2l2.1 2.1M15.7 15.7l2.1 2.1M6.2 17.8l2.1-2.1M15.7 8.3l2.1-2.1"/><circle cx="12" cy="12" r="3"/></svg>
          </button>
          <button class="rail-item" :class="{ active: railMode === 'admin' }" title="系统管理" @click="go('/admin/settings')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2"/></svg>
          </button>
          <div class="rail-spacer"></div>
        </aside>

        <aside class="side">
          <div class="side-head">导航</div>
          <input v-model="sideFilter" class="side-search" placeholder="搜索菜单…" />
          <div v-for="g in sideGroups" :key="g.title">
            <div class="side-group-title">{{ g.title }}</div>
            <nav class="side-nav">
              <button
                v-for="item in g.items"
                :key="item.path"
                :class="{ active: isActive(item.path) }"
                @click="go(item.path)"
              >{{ item.label }}</button>
            </nav>
          </div>
        </aside>

        <main class="main">
          <div class="crumb">
            <span>{{ crumb.a }}</span>
            <span class="crumb-sep">/</span>
            <b>{{ crumb.b }}</b>
          </div>
          <router-view />
        </main>
      </div>

      <AiFloat />
    </template>
    <router-view v-else />
  </div>
</template>
