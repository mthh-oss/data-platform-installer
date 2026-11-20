<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AiFloat from './components/AiFloat.vue'
import { getUser, setToken, setUser } from './api/client'

const route = useRoute()
const router = useRouter()
const user = ref(getUser())

const isAuth = computed(() => route.path === '/login' || route.path === '/setup')

const menus = [
  { key: 'launch', path: '/', label: '一键启动', icon: '启' },
  { key: 'overview', path: '/overview', label: '集群总览', icon: '览' },
  { key: 'jobs', path: '/jobs', label: '任务进度', icon: '任' },
  { key: 'monitor', path: '/monitor', label: '监控', icon: '监' },
  { key: 'settings', path: '/settings', label: '设置', icon: '设' },
]

const active = computed(() => {
  const p = route.path
  if (p.startsWith('/jobs')) return 'jobs'
  if (p.startsWith('/overview')) return 'overview'
  if (p.startsWith('/monitor')) return 'monitor'
  if (p.startsWith('/settings')) return 'settings'
  return 'launch'
})

const sideTitle = computed(() => menus.find((m) => m.key === active.value)?.label || '工作台')

watch(
  () => route.path,
  () => {
    user.value = getUser()
  },
)

function go(path) {
  router.push(path)
}

function logout() {
  setToken('')
  setUser(null)
  router.push('/login')
}
</script>

<template>
  <div class="bi-layout" :class="{ 'auth-only': isAuth }">
    <template v-if="!isAuth">
      <aside class="bi-rail">
        <div class="logo">DP</div>
        <button
          v-for="m in menus"
          :key="m.key"
          class="rail-btn"
          :class="{ active: active === m.key }"
          :title="m.label"
          @click="go(m.path)"
        >
          {{ m.icon }}
        </button>
        <div style="flex:1"></div>
        <button class="rail-btn" title="退出" @click="logout">退</button>
      </aside>

      <aside class="bi-side">
        <h2>{{ sideTitle }}</h2>
        <button
          v-for="m in menus"
          :key="m.key"
          class="side-item"
          :class="{ active: active === m.key }"
          @click="go(m.path)"
        >
          {{ m.label }}
        </button>
      </aside>

      <section class="bi-main">
        <header class="bi-top">
          <div class="title">数据平台控制台</div>
          <div class="user">
            {{ user?.display_name || user?.username || '-' }}
            · {{ user?.role || '-' }}
          </div>
        </header>
        <div class="bi-content">
          <router-view />
        </div>
      </section>

      <AiFloat />
    </template>

    <div v-else class="bi-content" style="padding:0">
      <router-view />
    </div>
  </div>
</template>
