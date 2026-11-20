<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import { deployStatus } from '../utils/plugin'

const route = useRoute()
const router = useRouter()
const jobs = ref([])
const instances = ref([])
const current = ref(null)
const logs = ref('')
const keyword = ref('')
const error = ref('')
let timer = null

const phases = [
  { key: 'preparing', label: '准备' },
  { key: 'downloading', label: '下载' },
  { key: 'starting', label: '启动' },
  { key: 'ready', label: '完成' },
]

const phaseIndex = computed(() => {
  const phase = current.value?.phase || 'pending'
  if (phase === 'failed') return -1
  if (phase === 'pending') return 0
  const idx = phases.findIndex((p) => p.key === phase)
  return idx >= 0 ? idx : 0
})

const logView = computed(() => {
  if (!keyword.value.trim()) return logs.value
  const k = keyword.value.trim()
  return logs.value.split(k).join(`【${k}】`)
})

const tree = computed(() => {
  const c = instances.value.find((x) => x.id === current.value?.cluster_id)
  return (c?.platforms || []).map((pid) => ({
    id: pid,
    status: deployStatus(current.value).text,
    progress: current.value?.progress ?? 0,
  }))
})

async function refresh() {
  try {
    jobs.value = await api.jobs()
    instances.value = await api.clusters()
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
  router.push(`/tasks/${id}`)
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
watch(() => route.params.jobId, refresh)
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>部署任务</h2>
        <p class="muted" style="margin:6px 0 0">状态仅使用：排队 / 部署中 / 成功 / 失败 / 已取消（勿与实例运行态混用）</p>
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
          <p>
            <span class="status-pill" :class="deployStatus(j).cls">{{ deployStatus(j).text }}</span>
            · {{ j.progress ?? 0 }}%
          </p>
        </button>
        <p class="muted" v-if="!jobs.length">暂无部署任务</p>
      </div>

      <div v-if="current">
        <div class="progress-head">
          <div>
            任务 #{{ current.id }}
            <span class="status-pill" :class="deployStatus(current).cls">{{ deployStatus(current).text }}</span>
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

        <h3 style="font-size:14px">组件进度</h3>
        <table class="table">
          <thead><tr><th>组件</th><th>部署状态</th><th>进度</th></tr></thead>
          <tbody>
            <tr v-for="n in tree" :key="n.id">
              <td>{{ n.id }}</td>
              <td>{{ n.status }}</td>
              <td>{{ n.progress }}%</td>
            </tr>
          </tbody>
        </table>

        <p class="error" v-if="current.error">{{ current.error }}</p>
        <div class="actions">
          <button class="btn" @click="api.downloadJobLogs(current.id)">下载全部日志</button>
          <button class="btn" disabled title="一期占位">取消任务</button>
          <button class="btn" disabled title="一期占位">重试失败节点</button>
          <button class="btn" v-if="deployStatus(current).key === 'failed'">AI 分析</button>
          <button
            class="btn primary"
            v-if="deployStatus(current).key === 'success'"
            @click="router.push(`/instances/${current.cluster_id}`)"
          >进入实例</button>
        </div>

        <div class="toolbar" style="margin:10px 0">
          <input v-model="keyword" class="select" style="width:200px" placeholder="日志关键词高亮" />
        </div>
        <div class="log">{{ logView || '（等待日志…）' }}</div>
      </div>
      <div v-else class="muted">选择左侧任务查看部署进度与日志</div>
    </div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
