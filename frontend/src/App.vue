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

/** 一级模块：一 tap 一工作区，侧栏只显示当前模块菜单 */
const modules = [
  {
    id: 'ops',
    label: '编排部署',
    title: '编排部署',
    home: '/workbench',
    match: (p) =>
      ['/workbench', '/orchestrate', '/instances', '/tasks', '/hosts'].some(
        (x) => p === x || p.startsWith(x + '/'),
      ) || p === '/',
    items: [
      { path: '/workbench', label: '工作台' },
      { path: '/orchestrate', label: '组件编排' },
      { path: '/instances', label: '实例管理' },
      { path: '/tasks', label: '部署任务' },
      { path: '/hosts', label: '主机资源' },
    ],
  },
  {
    id: 'observe',
    label: '观测中心',
    title: '观测中心',
    home: '/alerts',
    match: (p) => ['/alerts', '/logs', '/monitor'].some((x) => p === x || p.startsWith(x + '/')),
    items: [
      { path: '/alerts', label: '告警中心' },
      { path: '/logs', label: '日志检索' },
      { path: '/monitor', label: '监控大盘' },
    ],
  },
  {
    id: 'plugins',
    label: '插件市场',
    title: '插件市场',
    home: '/plugins',
    match: (p) => p === '/plugins' || p.startsWith('/plugins/'),
    items: [
      { path: '/plugins', label: '插件列表' },
    ],
  },
  {
    id: 'admin',
    label: '系统管理',
    title: '系统管理',
    home: '/admin/users',
    match: (p) => p.startsWith('/admin'),
    items: [
      { path: '/admin/users', label: '用户权限' },
      { path: '/admin/audit', label: '审计日志' },
      { path: '/admin/settings', label: '平台设置' },
    ],
  },
]

const activeModule = computed(() => {
  const hit = modules.find((m) => m.match(route.path))
  return hit || modules[0]
})

const sideItems = computed(() => {
  const q = sideFilter.value.trim()
  const items = activeModule.value.items
  return q ? items.filter((i) => i.label.includes(q)) : items
})

const crumb = computed(() => {
  const mod = activeModule.value
  const hit = mod.items.find((i) => route.path === i.path || route.path.startsWith(i.path + '/'))
  if (route.path.startsWith('/instances/')) return { a: mod.title, b: '实例详情' }
  if (route.path.startsWith('/tasks/')) return { a: mod.title, b: '任务详情' }
  if (route.path.startsWith('/plugins/') && route.path !== '/plugins') return { a: mod.title, b: '插件详情' }
  if (route.path.startsWith('/hosts/')) return { a: mod.title, b: '主机详情' }
  return { a: mod.title, b: hit?.label || mod.title }
})

watch(
  () => route.path,
  () => {
    user.value = getUser()
    sideFilter.value = ''
  },
  { immediate: true },
)

function go(path) {
  router.push(path)
}

function switchModule(mod) {
  if (mod.match(route.path)) return
  router.push(mod.home)
}

function logout() {
  setToken('')
  setUser(null)
  router.push('/login')
}

function isActive(path) {
  if (path === '/workbench') return route.path === '/workbench' || route.path === '/'
  if (path === '/plugins') return route.path === '/plugins'
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<template>
  <div class="app-shell" :class="{ auth: isAuth }">
    <template v-if="!isAuth">
      <header class="topbar">
        <div class="brand">
          <div class="brand-name">Data<span>Stack</span></div>
        </div>
        <div class="top-center">
          <span class="top-tagline">{{ activeModule.title }}</span>
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
        <aside class="rail" aria-label="一级模块">
          <div class="rail-logo" title="DataStack">DS</div>
          <button
            v-for="m in modules"
            :key="m.id"
            type="button"
            class="rail-item"
            :class="{ active: activeModule.id === m.id }"
            :title="m.title"
            @click="switchModule(m)"
          >
            <span class="rail-ico" v-if="m.id === 'ops'">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M4 10l8-6 8 6v9a1 1 0 01-1 1h-5v-5H10v5H5a1 1 0 01-1-1v-9z"/></svg>
            </span>
            <span class="rail-ico" v-else-if="m.id === 'observe'">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M3 12h4l2-6 4 12 2-6h6"/><circle cx="12" cy="12" r="9"/></svg>
            </span>
            <span class="rail-ico" v-else-if="m.id === 'plugins'">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M8 8h3V5a2 2 0 114 0v3h3a2 2 0 110 4h-3v3a2 2 0 11-4 0v-3H8a2 2 0 110-4z"/></svg>
            </span>
            <span class="rail-ico" v-else>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="12" cy="12" r="3"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4L7 17M17 7l1.4-1.4"/></svg>
            </span>
            <span class="rail-label">{{ m.label }}</span>
          </button>
          <div class="rail-spacer"></div>
        </aside>

        <aside class="side">
          <div class="side-head">{{ activeModule.title }}</div>
          <input v-model="sideFilter" class="side-search" :placeholder="`搜索${activeModule.label}菜单…`" />
          <nav class="side-nav">
            <button
              v-for="item in sideItems"
              :key="item.path"
              type="button"
              :class="{ active: isActive(item.path) }"
              @click="go(item.path)"
            >{{ item.label }}</button>
          </nav>
          <p class="side-hint" v-if="!sideItems.length">无匹配菜单</p>
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
