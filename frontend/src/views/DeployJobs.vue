<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
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

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 2000)
})
onUnmounted(() => timer && clearInterval(timer))
watch(() => route.params.id, () => refresh())
</script>

<template>
  <section class="panel">
    <h2 style="margin-top:0">部署任务</h2>
    <p class="muted">每 2 秒刷新状态与日志。</p>

    <div style="display:grid; gap:16px; grid-template-columns: minmax(240px, 320px) 1fr;">
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
          <p>cluster={{ j.cluster_id }} · {{ j.status }}</p>
        </button>
        <p class="muted" v-if="!jobs.length">暂无任务，先去配置向导创建集群。</p>
      </div>

      <div v-if="current">
        <p>
          任务 #{{ current.id }}
          <span class="status-pill" :class="current.status === 'succeeded' ? 'healthy' : current.status === 'failed' ? 'unhealthy' : 'unknown'">
            {{ current.status }}
          </span>
        </p>
        <p class="error" v-if="current.error">{{ current.error }}</p>
        <div class="log">{{ logs || '（暂无日志）' }}</div>
      </div>
      <div v-else class="muted">选择左侧任务查看日志。</div>
    </div>

    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
