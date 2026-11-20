<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { setToken } from './api/client'

const route = useRoute()
const router = useRouter()
const isAuthPage = computed(() => route.path === '/login' || route.path === '/setup')

function logout() {
  setToken('')
  router.push('/login')
}
</script>

<template>
  <div class="shell">
    <header class="topbar" v-if="!isAuthPage">
      <div class="brand">
        <strong>Data Platform Installer</strong>
        <span>轻量 CDH 体验：挑选 · 一键启动 · 总览 · AI 自检</span>
      </div>
      <nav class="nav">
        <router-link to="/">一键启动</router-link>
        <router-link to="/overview">集群总览</router-link>
        <router-link to="/jobs">下载/启动进度</router-link>
        <router-link to="/monitor">监控看板</router-link>
        <router-link to="/ai">AI 自检</router-link>
        <button class="btn" style="padding:8px 14px;border-radius:999px" @click="logout">退出</button>
      </nav>
    </header>
    <router-view />
  </div>
</template>
