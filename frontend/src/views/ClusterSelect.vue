<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'

const router = useRouter()
const clusters = ref([])
const healthMap = ref({})
const q = ref('')
const error = ref('')
const loading = ref(false)

const filtered = computed(() => {
  const s = q.value.trim()
  if (!s) return clusters.value
  return clusters.value.filter((c) => c.name.includes(s) || c.status.includes(s))
})

async function load() {
  error.value = ''
  try {
    clusters.value = await api.clusters()
    const map = {}
    await Promise.all(
      clusters.value.map(async (c) => {
        try {
          map[c.id] = await api.clusterHealth(c.id)
        } catch {
          map[c.id] = null
        }
      }),
    )
    healthMap.value = map
  } catch (e) {
    error.value = e.message
  }
}

function healthTag(c) {
  const h = healthMap.value[c.id]
  if (!h) return { cls: 'warn', text: '未知' }
  const vals = Object.values(h.platforms || {})
  if (!vals.length) return { cls: 'warn', text: c.status || '未知' }
  if (vals.every((p) => p.ok)) return { cls: 'ok', text: '正常' }
  if (vals.some((p) => p.ok)) return { cls: 'warn', text: '警告' }
  return { cls: 'bad', text: '异常' }
}

function stats(c) {
  const h = healthMap.value[c.id]
  const platforms = c.platforms || []
  const ok = h ? Object.values(h.platforms || {}).filter((p) => p.ok).length : 0
  return {
    services: platforms.length,
    healthy: ok,
    alerts: Math.max(platforms.length - ok, 0),
  }
}

async function createQuick() {
  loading.value = true
  error.value = ''
  try {
    // go to deploy wizard in a temp flow: create empty path via services add
    router.push('/deploy')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section>
    <div class="panel" style="margin-bottom:12px">
      <div class="panel-title">
        <div>
          <h2>集群选择</h2>
          <p class="muted" style="margin:6px 0 0">多套集群统一入口（生产/测试）。点击进入对应集群管控。</p>
        </div>
        <div class="toolbar">
          <input v-model="q" class="select" style="width:220px" placeholder="搜索集群名称/状态" />
          <button class="btn ghost" @click="load">刷新</button>
          <button class="btn primary" :disabled="loading" @click="createQuick">部署新集群</button>
        </div>
      </div>
    </div>

    <div class="empty" v-if="!filtered.length">暂无集群。请先「部署新集群」。</div>

    <div class="grid" v-else>
      <div class="cluster-card" v-for="c in filtered" :key="c.id" @click="router.push(`/c/${c.id}/overview`)">
        <div style="display:flex;justify-content:space-between;gap:8px;align-items:center">
          <h3>{{ c.name }}</h3>
          <span class="health-tag" :class="healthTag(c).cls">{{ healthTag(c).text }}</span>
        </div>
        <div class="meta">
          <span class="env-tag test">纳管集群</span>
          <span class="status-pill unknown">{{ c.status }}</span>
        </div>
        <p>服务 {{ stats(c).services }} · 健康 {{ stats(c).healthy }} · 异常 {{ stats(c).alerts }}</p>
        <p style="margin-top:8px">组件：{{ (c.platforms || []).join(', ') || '-' }}</p>
        <div class="actions" style="margin-top:12px" @click.stop>
          <button class="btn primary" @click="router.push(`/c/${c.id}/overview`)">进入集群</button>
          <button class="btn" @click="router.push(`/c/${c.id}/services`)">服务管理</button>
        </div>
      </div>
    </div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
