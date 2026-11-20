<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const clusterId = computed(() => Number(route.params.clusterId))
const jobs = ref([])
const current = ref(null)
const logs = ref('')
const error = ref('')
let timer = null

const phases = [
  { key: 'preparing', label: '准备配置' },
  { key: 'downloading', label: '下载镜像' },
  { key: 'starting', label: '启动组件' },
  { key: 'ready', label: '就绪' },
]

const phaseIndex = computed(() => {
  const phase = current.value?.phase || 'pending'
  if (phase === 'failed') return -1
  if (phase === 'pending') return 0
  const idx = phases.findIndex((p) => p.key === phase)
  return idx >= 0 ? idx : 0
})

async function refresh() {
  try {
    jobs.value = await api.jobs(clusterId.value)
    const jid = route.params.jobId || current.value?.id || jobs.value[0]?.id
    if (jid) {
      current.value = await api.job(jid)
      logs.value = await api.jobLogs(jid)
    }
  } catch (e) {
    error.value = e.message
  }
}

function openJob(id) {
  router.push(`/c/${clusterId.value}/tasks/${id}`)
}

function phaseClass(idx) {
  if (!current.value) return ''
  if (current.value.phase === 'failed') return idx === 0 ? 'failed' : ''
  if (idx < phaseIndex.value) return 'done'
  if (idx === phaseIndex.value) {
    return current.value.status === 'succeeded' || current.value.phase === 'ready' ? 'done' : 'active'
  }
  return ''
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 1500)
})
onUnmounted(() => timer && clearInterval(timer))
watch(() => [clusterId.value, route.params.jobId], refresh)
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>任务中心</h2>
        <p class="muted" style="margin:6px 0 0">重启、分发、部署等慢操作统一异步跟踪</p>
      </div>
      <button class="btn ghost" @click="refresh">刷新</button>
    </div>

    <div class="jobs-layout">
      <div>
        <button
          v-for="j in jobs"
          :key="j.id"
          class="choice"
          style="width:100%;margin-bottom:8px"
          :class="{ selected: String(current?.id) === String(j.id) }"
          @click="openJob(j.id)"
        >
          <h3>#{{ j.id }} · {{ j.action }}</h3>
          <p>{{ j.phase || j.status }} · {{ j.progress ?? 0 }}%</p>
        </button>
        <p class="muted" v-if="!jobs.length">暂无任务</p>
      </div>

      <div v-if="current">
        <div class="progress-head">
          <div>
            任务 #{{ current.id }}
            <span
              class="status-pill"
              :class="current.status === 'succeeded' ? 'healthy' : current.status === 'failed' ? 'unhealthy' : 'unknown'"
            >{{ current.phase || current.status }}</span>
          </div>
          <strong>{{ current.progress ?? 0 }}%</strong>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${current.progress ?? 0}%` }"></div>
        </div>
        <div class="phase-row">
          <div v-for="(p, idx) in phases" :key="p.key" class="phase-item" :class="phaseClass(idx)">
            <div class="dot"></div>
            <span>{{ p.label }}</span>
          </div>
        </div>
        <p class="error" v-if="current.error">{{ current.error }}</p>
        <div class="actions">
          <button class="btn" @click="api.downloadJobLogs(current.id)">下载任务日志</button>
          <button class="btn primary" v-if="current.status === 'succeeded'" @click="router.push(`/c/${clusterId}/overview`)">去总览</button>
        </div>
        <div class="log">{{ logs || '（等待日志…）' }}</div>
      </div>
      <div v-else class="muted">选择左侧任务查看进度</div>
    </div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
