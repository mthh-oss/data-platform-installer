<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const clusterId = computed(() => Number(route.params.clusterId))
const overview = ref(null)
const health = ref(null)
const q = ref('')
const statusFilter = ref('all')
const error = ref('')
let timer = null

const rows = computed(() => {
  const nodes = overview.value?.nodes || []
  const h = health.value?.platforms || {}
  return nodes
    .map((n) => {
      const ph = h[n.id] || {}
      return {
        ...n,
        ok: ph.ok ?? n.ok,
        status: ph.status || n.status,
        alerts: (ph.ok ?? n.ok) ? 0 : 1,
        roles: (n.dependencies || []).length + 1,
        metric: n.id === 'doris' ? 'FE/BE' : n.id === 'flink' ? 'JM/TM' : '实例',
      }
    })
    .filter((r) => {
      if (statusFilter.value === 'ok' && !r.ok) return false
      if (statusFilter.value === 'bad' && r.ok) return false
      if (q.value && !`${r.name}${r.id}`.includes(q.value.trim())) return false
      return true
    })
    .sort((a, b) => Number(a.ok) - Number(b.ok))
})

async function refresh() {
  try {
    overview.value = await api.overview(clusterId.value)
    health.value = await api.clusterHealth(clusterId.value)
  } catch (e) {
    error.value = e.message
  }
}

async function act(action) {
  error.value = ''
  try {
    if (action === 'start') await api.deploy(clusterId.value)
    if (action === 'stop') await api.stop(clusterId.value)
    if (action === 'restart') await api.restart(clusterId.value)
    router.push(`/c/${clusterId.value}/tasks`)
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
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>服务管理</h2>
        <p class="muted" style="margin:6px 0 0">组件：Doris / Flink / MySQL / Flink CDC / DolphinScheduler</p>
      </div>
      <div class="toolbar">
        <input v-model="q" class="select" style="width:180px" placeholder="搜索服务" />
        <select v-model="statusFilter" class="select" style="width:120px">
          <option value="all">全部状态</option>
          <option value="ok">正常</option>
          <option value="bad">异常</option>
        </select>
        <button class="btn ghost" @click="refresh">刷新</button>
        <button class="btn primary" @click="router.push(`/deploy?clusterId=${clusterId}`)">新增服务</button>
      </div>
    </div>

    <table class="table">
      <thead>
        <tr>
          <th>服务名称</th>
          <th>类型</th>
          <th>状态</th>
          <th>角色数</th>
          <th>核心指标</th>
          <th>告警</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r.id">
          <td><strong>{{ r.name }}</strong><div class="muted">{{ r.id }}</div></td>
          <td>{{ r.id.includes('mysql') ? '存储' : r.id.includes('flink') || r.id.includes('doris') ? '计算' : '调度' }}</td>
          <td><span class="status-pill" :class="r.ok ? 'healthy' : 'unhealthy'">{{ r.status }}</span></td>
          <td>{{ r.roles }}</td>
          <td>{{ r.metric }}</td>
          <td>{{ r.alerts }}</td>
          <td>
            <div class="toolbar">
              <button class="btn" @click="router.push(`/c/${clusterId}/services/${r.id}`)">详情</button>
              <button class="btn" @click="act('restart')">重启</button>
              <button class="btn danger" @click="act('stop')">停止</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <div class="empty" v-if="!rows.length">暂无服务，请「新增服务」部署组件。</div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
