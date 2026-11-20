<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { api } from '../api/client'

const clusters = ref([])
const selectedId = ref(null)
const health = ref(null)
const error = ref('')
const busy = ref(false)
let timer = null

async function refresh() {
  try {
    clusters.value = await api.clusters()
    if (!selectedId.value && clusters.value.length) {
      selectedId.value = clusters.value[0].id
    }
    if (selectedId.value) {
      health.value = await api.clusterHealth(selectedId.value)
    }
  } catch (e) {
    error.value = e.message
  }
}

async function act(fn) {
  if (!selectedId.value) return
  busy.value = true
  error.value = ''
  try {
    const job = await fn(selectedId.value)
    error.value = `已触发任务 #${job.id}（${job.action}）`
    await refresh()
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 5000)
})
onUnmounted(() => timer && clearInterval(timer))
</script>

<template>
  <section class="panel">
    <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:center;">
      <div>
        <h2 style="margin:0">监控看板</h2>
        <p class="muted" style="margin:6px 0 0">TCP / HTTP / Docker 健康探测聚合 · Prometheus: <code>/metrics</code></p>
      </div>
      <div class="actions" style="margin:0">
        <select v-model.number="selectedId" @change="refresh" style="background:#0d1524;border:1px solid var(--line);border-radius:10px;padding:8px 10px;">
          <option v-for="c in clusters" :key="c.id" :value="c.id">{{ c.name }} ({{ c.status }})</option>
        </select>
        <button class="btn" :disabled="busy || !selectedId" @click="act(api.restart)">重启</button>
        <button class="btn danger" :disabled="busy || !selectedId" @click="act(api.stop)">停止</button>
      </div>
    </div>

    <p class="muted" v-if="!clusters.length" style="margin-top:16px">还没有集群。请先通过配置向导部署。</p>

    <div class="monitor-grid" style="margin-top:18px" v-if="health">
      <div class="monitor-card" v-for="(info, pid) in health.platforms" :key="pid">
        <div style="display:flex; justify-content:space-between; gap:8px; align-items:center;">
          <h3>{{ pid }}</h3>
          <span class="status-pill" :class="info.ok ? 'healthy' : 'unhealthy'">{{ info.status }}</span>
        </div>
        <p class="muted" style="margin:0; font-size:0.8rem">{{ info.checked_at }}</p>
        <ul class="check-list">
          <li v-for="c in info.checks" :key="c.name">
            <span>{{ c.name }}</span>
            <span :class="c.ok ? 'ok' : 'error'">{{ c.ok ? 'UP' : 'DOWN' }} · {{ c.detail }}</span>
          </li>
        </ul>
      </div>
    </div>

    <p class="error" v-if="error" style="margin-top:14px">{{ error }}</p>
  </section>
</template>
