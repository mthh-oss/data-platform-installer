<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const clusterId = computed(() => Number(route.params.clusterId))
const overview = ref(null)
const cluster = ref(null)
const error = ref('')
let timer = null

const health = computed(() => {
  const nodes = overview.value?.nodes || []
  if (!nodes.length) return { cls: 'warn', text: '未知', summary: '暂无服务数据' }
  const bad = nodes.filter((n) => !n.ok)
  if (!bad.length) return { cls: 'ok', text: '正常', summary: '全部服务健康检查通过' }
  if (bad.length < nodes.length) return { cls: 'warn', text: '警告', summary: `${bad.map((b) => b.name).join('、')} 异常` }
  return { cls: 'bad', text: '故障', summary: '全部服务异常，请检查任务中心与主机' }
})

async function refresh() {
  try {
    cluster.value = await api.clusters().then((list) => list.find((c) => c.id === clusterId.value))
    overview.value = await api.overview(clusterId.value)
  } catch (e) {
    error.value = e.message
  }
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 8000)
})
onUnmounted(() => timer && clearInterval(timer))
watch(clusterId, refresh)
</script>

<template>
  <section>
    <div class="health-hero">
      <div>
        <div class="health-tag" :class="health.cls">{{ health.text }}</div>
        <p style="margin:10px 0 0;font-size:14px">{{ health.summary }}</p>
        <p class="muted" style="margin:8px 0 0">集群：{{ overview?.cluster_name || cluster?.name || clusterId }}</p>
      </div>
      <div class="stat-row" style="margin:0">
        <div class="stat-card">
          <div class="label">服务总数</div>
          <div class="value">{{ overview?.nodes?.length || 0 }}</div>
        </div>
        <div class="stat-card">
          <div class="label">健康服务</div>
          <div class="value">{{ (overview?.nodes || []).filter(n => n.ok).length }}</div>
        </div>
        <div class="stat-card">
          <div class="label">异常服务</div>
          <div class="value">{{ (overview?.nodes || []).filter(n => !n.ok).length }}</div>
        </div>
        <div class="stat-card">
          <div class="label">依赖边</div>
          <div class="value">{{ overview?.edges?.length || 0 }}</div>
        </div>
      </div>
    </div>

    <div class="panel" style="margin-bottom:12px">
      <div class="panel-title">
        <h2>服务健康</h2>
        <div class="toolbar">
          <button class="btn ghost" @click="refresh">刷新</button>
          <button class="btn" @click="router.push(`/c/${clusterId}/tasks`)">任务中心</button>
          <button class="btn primary" @click="router.push(`/deploy?clusterId=${clusterId}`)">新增服务</button>
        </div>
      </div>
      <div class="grid">
        <div
          class="svc-card"
          v-for="n in [...(overview?.nodes || [])].sort((a,b) => Number(a.ok) - Number(b.ok))"
          :key="n.id"
          @click="router.push(`/c/${clusterId}/services/${n.id}`)"
        >
          <div style="display:flex;justify-content:space-between;gap:8px">
            <h3>{{ n.name }}</h3>
            <span class="status-pill" :class="n.ok ? 'healthy' : 'unhealthy'">{{ n.status }}</span>
          </div>
          <p style="margin-top:8px">{{ n.id }}</p>
          <p class="topo-deps" v-if="n.dependencies?.length">依赖：{{ n.dependencies.join(', ') }}</p>
        </div>
      </div>
      <div class="empty" v-if="!(overview?.nodes || []).length">暂无服务，请先部署组件。</div>
    </div>

    <div class="panel">
      <div class="panel-title">
        <h2>快捷操作</h2>
      </div>
      <div class="toolbar">
        <button class="btn" @click="router.push(`/c/${clusterId}/hosts`)">主机管理</button>
        <button class="btn" @click="router.push(`/c/${clusterId}/alerts`)">告警中心</button>
        <button class="btn" @click="router.push(`/c/${clusterId}/logs`)">日志检索</button>
        <button class="btn" @click="api.downloadAbnormal(clusterId)">下载异常日志</button>
      </div>
    </div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
