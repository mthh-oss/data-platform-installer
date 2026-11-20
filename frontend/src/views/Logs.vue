<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'

const route = useRoute()
const clusterId = computed(() => Number(route.params.clusterId))
const jobs = ref([])
const currentId = ref(null)
const logs = ref('')
const keyword = ref('')
const error = ref('')

const highlighted = computed(() => {
  if (!keyword.value.trim()) return logs.value
  const k = keyword.value.trim()
  return logs.value.split(k).join(`【${k}】`)
})

async function load() {
  try {
    jobs.value = await api.jobs(clusterId.value)
    if (!currentId.value && jobs.value.length) currentId.value = jobs.value[0].id
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
watch(clusterId, load)
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>日志检索</h2>
        <p class="muted" style="margin:6px 0 0">跨任务统一检索部署/启停日志；支持关键词高亮与下载</p>
      </div>
      <div class="toolbar">
        <input v-model="keyword" class="select" style="width:180px" placeholder="关键词过滤" />
        <button class="btn ghost" @click="load">刷新</button>
        <button class="btn" :disabled="!currentId" @click="api.downloadJobLogs(currentId)">下载当前日志</button>
        <button class="btn" @click="api.downloadAbnormal(clusterId)">下载异常包</button>
      </div>
    </div>

    <div class="jobs-layout">
      <div>
        <button
          v-for="j in jobs"
          :key="j.id"
          class="choice"
          style="width:100%;margin-bottom:8px"
          :class="{ selected: currentId === j.id }"
          @click="openJob(j.id)"
        >
          <h3>#{{ j.id }} · {{ j.action }}</h3>
          <p>{{ j.phase || j.status }}</p>
        </button>
        <p class="muted" v-if="!jobs.length">暂无任务日志</p>
      </div>
      <div class="log">{{ highlighted || '选择左侧任务查看日志' }}</div>
    </div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
