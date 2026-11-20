<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'

const router = useRouter()
const tab = ref('live')
const instances = ref([])
const healthMap = ref({})
const error = ref('')
let timer = null

const alerts = computed(() => {
  const list = []
  for (const c of instances.value) {
    const h = healthMap.value[c.id]?.platforms || {}
    for (const pid of c.platforms || []) {
      if (h[pid] && h[pid].ok === false) {
        list.push({
          level: '告警',
          object: `${c.name} / ${pid}`,
          content: `插件健康检查失败：${h[pid].status || 'unhealthy'}`,
          time: new Date().toLocaleString(),
          id: c.id,
        })
      }
    }
  }
  return list
})

const rules = [
  { name: '插件健康探针失败', source: '插件 alert.json 模板', level: '告警', enabled: true },
  { name: '部署任务失败', source: '平台内置', level: '严重', enabled: true },
]

async function refresh() {
  try {
    instances.value = await api.clusters()
    const map = {}
    await Promise.all(
      instances.value.map(async (c) => {
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

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 10000)
})
onUnmounted(() => timer && clearInterval(timer))
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>告警中心</h2>
        <p class="muted" style="margin:6px 0 0">告警模板来自插件包；此处为实例运行态告警，不是部署任务态。</p>
      </div>
      <button class="btn ghost" @click="refresh">刷新</button>
    </div>
    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'live' }" @click="tab = 'live'">实时告警</button>
      <button class="tab" :class="{ active: tab === 'rules' }" @click="tab = 'rules'">告警模板</button>
    </div>
    <template v-if="tab === 'live'">
      <table class="table" v-if="alerts.length">
        <thead><tr><th>等级</th><th>对象</th><th>内容</th><th>时间</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="(a, i) in alerts" :key="i">
            <td><span class="health-tag warn">{{ a.level }}</span></td>
            <td>{{ a.object }}</td>
            <td>{{ a.content }}</td>
            <td>{{ a.time }}</td>
            <td>
              <button class="btn" @click="router.push(`/instances/${a.id}`)">跳转实例</button>
              <button class="btn">AI 分析</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="empty" v-else>暂无告警</div>
    </template>
    <template v-else>
      <table class="table">
        <thead><tr><th>名称</th><th>来源</th><th>级别</th><th>状态</th></tr></thead>
        <tbody>
          <tr v-for="r in rules" :key="r.name">
            <td>{{ r.name }}</td><td>{{ r.source }}</td><td>{{ r.level }}</td>
            <td><span class="status-pill healthy">启用</span></td>
          </tr>
        </tbody>
      </table>
    </template>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
