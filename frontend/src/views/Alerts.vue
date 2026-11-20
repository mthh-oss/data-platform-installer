<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const clusterId = computed(() => Number(route.params.clusterId))
const tab = ref('live')
const health = ref(null)
const overview = ref(null)
const error = ref('')
let timer = null

const alerts = computed(() => {
  const platforms = health.value?.platforms || {}
  const nodes = overview.value?.nodes || []
  const list = []
  for (const n of nodes) {
    const ph = platforms[n.id]
    const ok = ph?.ok ?? n.ok
    if (!ok) {
      list.push({
        level: '严重',
        levelCls: 'bad',
        object: n.name,
        content: `${n.id} 健康检查失败：${ph?.status || n.status || 'unhealthy'}`,
        time: new Date().toLocaleString(),
        sid: n.id,
        recovered: false,
      })
    }
  }
  return list
})

const rules = [
  { name: '服务健康探针失败', metric: 'health.ok', threshold: 'false', duration: '1m', level: '严重', channel: 'Webhook', enabled: true },
  { name: '任务部署失败', metric: 'job.status', threshold: 'failed', duration: '即时', level: '高危', channel: 'Webhook', enabled: true },
]

async function refresh() {
  try {
    overview.value = await api.overview(clusterId.value)
    health.value = await api.clusterHealth(clusterId.value)
  } catch (e) {
    error.value = e.message
  }
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 10000)
})
onUnmounted(() => timer && clearInterval(timer))
watch(clusterId, refresh)
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>告警中心</h2>
        <p class="muted" style="margin:6px 0 0">实时告警由服务健康探针派生；规则可视化一期骨架</p>
      </div>
      <button class="btn ghost" @click="refresh">刷新</button>
    </div>

    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'live' }" @click="tab = 'live'">实时告警</button>
      <button class="tab" :class="{ active: tab === 'rules' }" @click="tab = 'rules'">告警规则</button>
    </div>

    <template v-if="tab === 'live'">
      <table class="table" v-if="alerts.length">
        <thead>
          <tr><th>等级</th><th>告警对象</th><th>内容</th><th>触发时间</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="(a, i) in alerts" :key="i">
            <td><span class="health-tag" :class="a.levelCls">{{ a.level }}</span></td>
            <td>{{ a.object }}</td>
            <td>{{ a.content }}</td>
            <td>{{ a.time }}</td>
            <td>
              <button class="btn" @click="router.push(`/c/${clusterId}/services/${a.sid}`)">跳转服务</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="empty" v-else>暂无未恢复告警</div>
    </template>

    <template v-else>
      <table class="table">
        <thead>
          <tr><th>名称</th><th>指标</th><th>阈值</th><th>持续</th><th>级别</th><th>接收</th><th>状态</th></tr>
        </thead>
        <tbody>
          <tr v-for="r in rules" :key="r.name">
            <td>{{ r.name }}</td>
            <td>{{ r.metric }}</td>
            <td>{{ r.threshold }}</td>
            <td>{{ r.duration }}</td>
            <td>{{ r.level }}</td>
            <td>{{ r.channel }}</td>
            <td><span class="status-pill" :class="r.enabled ? 'healthy' : 'unknown'">{{ r.enabled ? '启用' : '停用' }}</span></td>
          </tr>
        </tbody>
      </table>
      <p class="muted" style="margin-top:10px">新增/编辑规则与 Webhook 对接在二期完善；平台设置中可配通知地址。</p>
    </template>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
