<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AiFloat from './components/AiFloat.vue'
import { getUser, setToken, setUser } from './api/client'

const route = useRoute()
const router = useRouter()
const user = ref(getUser())
const sideFilter = ref('')

const isAuth = computed(() => route.path === '/login' || route.path === '/setup')

const modules = [
  {
    key: 'platform',
    label: '平台',
    icon: 'grid',
    children: [
      { path: '/', label: '组件部署' },
      { path: '/overview', label: '集群总览' },
      { path: '/jobs', label: '任务进度' },
      { path: '/monitor', label: '运行监控' },
    ],
  },
  {
    key: 'admin',
    label: '管理',
    icon: 'gear',
    children: [
      { path: '/personnel', label: '人员关系' },
      { path: '/settings', label: '系统设置' },
    ],
  },
]

const activeModule = computed(() => {
  const p = route.path
  if (p.startsWith('/personnel') || p.startsWith('/settings')) return 'admin'
  return 'platform'
})

const sideItems = computed(() => {
  const mod = modules.find((m) => m.key === activeModule.value)
  const list = mod?.children || []
  const q = sideFilter.value.trim()
  if (!q) return list
  return list.filter((i) => i.label.includes(q))
})

const crumb = computed(() => {
  const mod = modules.find((m) => m.key === activeModule.value)
  const child = (mod?.children || []).find((c) => c.path === route.path || route.path.startsWith(c.path + '/'))
  return {
    module: mod?.label || '平台',
    page: child?.label || '工作台',
  }
})

watch(
  () => route.path,
  () => {
    user.value = getUser()
  },
)

function goModule(key) {
  const mod = modules.find((m) => m.key === key)
  if (mod?.children?.[0]) router.push(mod.children[0].path)
}

function go(path) {
  router.push(path)
}

function logout() {
  setToken('')
  setUser(null)
  router.push('/login')
}

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<template>
  <div class="app-shell" :class="{ auth: isAuth }">
    <template v-if="!isAuth">
      <header class="topbar">
        <div class="brand">
          <div class="brand-mark">数</div>
          <div class="brand-name">数据平台</div>
        </div>
        <div class="top-right">
          <span>{{ user?.display_name || user?.username || '未登录' }}</span>
          <div class="avatar">{{ (user?.display_name || user?.username || 'U').slice(0, 1) }}</div>
          <button class="link-btn" @click="logout">退出</button>
        </div>
      </header>

      <div class="body">
        <aside class="rail">
          <button
            class="rail-item"
            :class="{ active: activeModule === 'platform' }"
            title="平台"
            @click="goModule('platform')"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <rect x="3" y="3" width="7" height="7" rx="1.5" />
              <rect x="14" y="3" width="7" height="7" rx="1.5" />
              <rect x="3" y="14" width="7" height="7" rx="1.5" />
              <rect x="14" y="14" width="7" height="7" rx="1.5" />
            </svg>
            平台
          </button>
          <button
            class="rail-item"
            :class="{ active: activeModule === 'admin' }"
            title="管理系统"
            @click="goModule('admin')"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <circle cx="12" cy="12" r="3" />
              <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4L7 17M17 7l1.4-1.4" />
            </svg>
            管理
          </button>
          <div class="rail-spacer"></div>
        </aside>

        <aside class="side">
          <div class="side-head">
            <h2>{{ activeModule === 'admin' ? '管理系统' : '平台资源' }}</h2>
          </div>
          <input v-model="sideFilter" class="side-search" placeholder="搜索菜单" />
          <div class="side-group">功能目录</div>
          <nav class="side-nav">
            <button
              v-for="item in sideItems"
              :key="item.path"
              :class="{ active: isActive(item.path) }"
              @click="go(item.path)"
            >
              {{ item.label }}
            </button>
          </nav>
        </aside>

        <main class="main">
          <div class="crumb">{{ crumb.module }} / <b>{{ crumb.page }}</b></div>
          <router-view />
        </main>
      </div>

      <AiFloat />
    </template>

    <router-view v-else />
  </div>
</template>
