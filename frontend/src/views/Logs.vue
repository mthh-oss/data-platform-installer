<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api/client'

const jobs = ref([])
const instances = ref([])
const currentId = ref(null)
const logs = ref('')
const keyword = ref('')
const instanceFilter = ref('all')
const error = ref('')

const highlighted = computed(() => {
  if (!keyword.value.trim()) return logs.value
  const k = keyword.value.trim()
  return logs.value.split(k).join(`【${k}】`)
})

const filteredJobs = computed(() => {
  if (instanceFilter.value === 'all') return jobs.value
  const cid = Number(instanceFilter.value)
  return jobs.value.filter((j) => j.cluster_id === cid)
})

async function load() {
  try {
    jobs.value = await api.jobs()
    instances.value = await api.clusters()
    if (!currentId.value && filteredJobs.value.length) currentId.value = filteredJobs.value[0].id
    if (currentId.value) logs.value = await api.jobLogs(currentId.value)
  } catch (e) {
    error.value = e.message
  }
}

async function openJob(id) {
  currentId.value = id
  logs.value = await api.jobLogs(id)
}

onMounted(load)
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>全局日志检索</h2>
        <p class="muted" style="margin:6px 0 0">按实例 / 任务 / 关键词检索部署与运维日志</p>
      </div>
      <div class="toolbar">
        <select v-model="instanceFilter" class="select" style="width:160px" @change="load">
          <option value="all">全部实例</option>
          <option v-for="c in instances" :key="c.id" :value="String(c.id)">{{ c.name }}</option>
        </select>
        <input v-model="keyword" class="select" style="width:180px" placeholder="关键词" />
        <button class="btn ghost" @click="load">刷新</button>
      </div>
    </div>
    <div class="jobs-layout">
      <div>
        <button
          v-for="j in filteredJobs"
          :key="j.id"
          class="choice"
          style="width:100%;margin-bottom:8px"
          :class="{ selected: currentId === j.id }"
          @click="openJob(j.id)"
        >
          <h3>#{{ j.id }} · {{ j.action }}</h3>
          <p>实例 #{{ j.cluster_id }}</p>
        </button>
        <p class="muted" v-if="!filteredJobs.length">暂无日志</p>
      </div>
      <div class="log">{{ highlighted || '选择任务查看日志' }}</div>
    </div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
