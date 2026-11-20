<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { api } from '../api/client'

const clusters = ref([])
const selectedId = ref(null)
const overview = ref(null)
const error = ref('')
const downloading = ref(false)
let timer = null

async function refresh() {
  try {
    clusters.value = await api.clusters()
    if (!selectedId.value && clusters.value.length) selectedId.value = clusters.value[0].id
    if (selectedId.value) overview.value = await api.overview(selectedId.value)
  } catch (e) {
    error.value = e.message
  }
}

async function downloadLogs() {
  if (!selectedId.value) return
  downloading.value = true
  error.value = ''
  try {
    await api.downloadAbnormal(selectedId.value)
  } catch (e) {
    error.value = e.message
  } finally {
    downloading.value = false
  }
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 8000)
})
onUnmounted(() => timer && clearInterval(timer))
</script>

<template>
  <section class="panel">
    <div class="progress-head">
      <div>
        <h2 style="margin:0">集群总览</h2>
        <p class="muted" style="margin:6px 0 0">一张图看清组件依赖与健康状态</p>
      </div>
      <div class="actions" style="margin:0">
        <select v-model.number="selectedId" @change="refresh" class="select">
          <option v-for="c in clusters" :key="c.id" :value="c.id">{{ c.name }} ({{ c.status }})</option>
        </select>
        <button class="btn" :disabled="!selectedId || downloading" @click="downloadLogs">
          {{ downloading ? '打包中…' : '下载异常日志' }}
        </button>
      </div>
    </div>

    <p class="muted" v-if="!clusters.length" style="margin-top:16px">还没有集群，先去一键启动部署。</p>

    <div v-if="overview" class="overview-wrap">
      <p class="muted">
        {{ overview.cluster_name }} · {{ overview.cluster_status }} · {{ overview.checked_at }}
      </p>

      <div class="topo">
        <div
          v-for="n in overview.nodes"
          :key="n.id"
          class="topo-node"
          :class="n.ok ? 'ok-node' : 'bad-node'"
        >
          <div class="topo-title">{{ n.name }}</div>
          <div class="topo-id">{{ n.id }}</div>
          <div class="status-pill" :class="n.ok ? 'healthy' : 'unhealthy'">{{ n.status }}</div>
          <div class="topo-deps" v-if="n.dependencies.length">依赖：{{ n.dependencies.join(', ') }}</div>
        </div>
      </div>

      <div class="edge-list" v-if="overview.edges.length">
        <h3>依赖关系</h3>
        <ul class="summary-list">
          <li v-for="(e, i) in overview.edges" :key="i">{{ e.from }} → {{ e.to }}</li>
        </ul>
      </div>
    </div>

    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
