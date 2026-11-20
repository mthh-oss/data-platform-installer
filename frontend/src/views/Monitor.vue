<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api/client'
import { instanceStatus } from '../utils/plugin'

const instances = ref([])
const healthMap = ref({})
const error = ref('')

onMounted(async () => {
  try {
    instances.value = await api.clusters()
    const map = {}
    for (const c of instances.value) {
      try {
        map[c.id] = await api.clusterHealth(c.id)
      } catch {
        map[c.id] = null
      }
    }
    healthMap.value = map
  } catch (e) {
    error.value = e.message
  }
})
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>监控大盘</h2>
        <p class="muted" style="margin:6px 0 0">全局实例运行态概览；细粒度指标由插件 metrics.json 驱动（P1）。</p>
      </div>
    </div>
    <div class="monitor-grid">
      <div class="monitor-card" v-for="c in instances" :key="c.id">
        <div class="topo-title">{{ c.name }}</div>
        <div class="topo-deps">{{ (c.platforms || []).join(', ') }}</div>
        <p style="margin-top:8px">
          <span class="status-pill" :class="instanceStatus(c, healthMap[c.id]?.platforms || {}).cls">
            {{ instanceStatus(c, healthMap[c.id]?.platforms || {}).text }}
          </span>
        </p>
      </div>
    </div>
    <div class="empty" v-if="!instances.length">暂无实例可监控</div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
