<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'


const props = defineProps({ id: { type: [String, Number], default: null } })
const route = useRoute()
const router = useRouter()

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

async function refreshList() {
  jobs.value = await api.jobs()
}

async function loadJob(jobId) {
  if (!jobId) {
    current.value = null
    logs.value = ''
    return
  }
  current.value = await api.job(jobId)
  logs.value = await api.jobLogs(jobId)
}

async function refresh() {
  try {
    await refreshList()
    const jobId = props.id || route.params.id
    if (jobId) await loadJob(jobId)
  } catch (e) {
    error.value = e.message
  }
}

function openJob(id) {
  router.push(`/jobs/${id}`)
}

async function downloadCurrent() {
  if (!current.value) return
  try {
    await api.downloadJobLogs(current.value.id)
  } catch (e) {
    error.value = e.message
  }
}

function phaseClass(idx) {
  if (!current.value) return ''
  if (current.value.phase === 'failed') return idx === 0 ? 'failed' : ''
  if (idx < phaseIndex.value) return 'done'
  if (idx === phaseIndex.value) return current.value.status === 'succeeded' || current.value.phase === 'ready' ? 'done' : 'active'
  return ''
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 1500)
})
onUnmounted(() => timer && clearInterval(timer))
watch(() => route.params.id, () => refresh())
</script>

<template>
  <section class="panel">
    <h2 style="margin-top:0">下载与启动进度</h2>
    <p class="muted">实时刷新：镜像下载 → 容器启动 → 就绪。完成后可去监控页查看健康状态。</p>

    <div class="jobs-layout">
      <div>
        <button
          v-for="j in jobs"
          :key="j.id"
          class="choice"
          style="width:100%; margin-bottom:8px"
          :class="{ selected: String(current?.id) === String(j.id) }"
          type="button"
          @click="openJob(j.id)"
        >
          <h3>#{{ j.id }} · {{ j.action }}</h3>
          <p>{{ j.phase || j.status }} · {{ j.progress ?? 0 }}%</p>
        </button>
        <p class="muted" v-if="!jobs.length">暂无任务，先去向导一键启动。</p>
      </div>

      <div v-if="current">
        <div class="progress-head">
          <div>
            任务 #{{ current.id }}
            <span
              class="status-pill"
              :class="current.status === 'succeeded' ? 'healthy' : current.status === 'failed' ? 'unhealthy' : 'unknown'"
            >
              {{ current.phase || current.status }}
            </span>
          </div>
          <strong>{{ current.progress ?? 0 }}%</strong>
        </div>

        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${current.progress ?? 0}%` }"></div>
        </div>

        <div class="phase-row">
          <div
            v-for="(p, idx) in phases"
            :key="p.key"
            class="phase-item"
            :class="phaseClass(idx)"
          >
            <div class="dot"></div>
            <span>{{ p.label }}</span>
          </div>
        </div>

        <p class="error" v-if="current.error">{{ current.error }}</p>

        <div class="actions">
          <button class="btn" v-if="current" @click="downloadCurrent">下载本任务日志</button>
          <router-link class="btn primary" v-if="current.status === 'succeeded'" to="/overview">去集群总览</router-link>
          <router-link class="btn" v-if="current.status === 'failed'" to="/ai">AI 自检</router-link>
        </div>

        <div class="log">{{ logs || '（等待日志…）' }}</div>
      </div>
      <div v-else class="muted">选择左侧任务查看下载/启动进度。</div>
    </div>

    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
