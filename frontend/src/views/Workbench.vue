<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { deployStatus, instanceStatus } from '../utils/plugin'

const router = useRouter()
const hosts = ref([])
const instances = ref([])
const jobs = ref([])
const healthMap = ref({})
const error = ref('')
let timer = null

const runningJobs = computed(() =>
  [...jobs.value]
    .filter((j) => {
      const k = deployStatus(j).key
      return k === 'queued' || k === 'deploying' || k === 'failed'
    })
    .sort((a, b) => {
      const af = deployStatus(a).key === 'failed' ? 0 : 1
      const bf = deployStatus(b).key === 'failed' ? 0 : 1
      if (af !== bf) return af - bf
      return (b.id || 0) - (a.id || 0)
    }),
)

const alerts = computed(() => {
  const list = []
  for (const c of instances.value) {
    const h = healthMap.value[c.id]?.platforms || {}
    for (const pid of c.platforms || []) {
      if (h[pid] && h[pid].ok === false) {
        list.push({
          level: '告警',
          instance: c.name,
          content: `${pid} 运行异常`,
          time: new Date().toLocaleString(),
          id: c.id,
        })
      }
    }
  }
  return list
})

const stats = computed(() => ({
  hosts: hosts.value.length,
  freeHosts: hosts.value.filter((h) => h.enabled !== false).length,
  instances: instances.value.length,
  deploying: jobs.value.filter((j) => ['queued', 'deploying'].includes(deployStatus(j).key)).length,
  alerts: alerts.value.length,
}))

async function refresh() {
  try {
    hosts.value = await api.hosts()
    instances.value = await api.clusters()
    jobs.value = await api.jobs()
    const map = {}
    await Promise.all(
      instances.value.slice(0, 20).map(async (c) => {
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
  timer = setInterval(refresh, 8000)
})
onUnmounted(() => timer && clearInterval(timer))
</script>

<template>
  <section>
    <div class="panel" style="margin-bottom:12px">
      <div class="panel-title">
        <div>
          <h2>工作台</h2>
          <p class="muted" style="margin:6px 0 0">编排部署优先；部署任务与实例运行状态严格分离。</p>
        </div>
        <div class="toolbar">
          <button class="btn ghost" @click="refresh">刷新</button>
          <button class="btn primary" @click="router.push('/orchestrate')">新建编排</button>
        </div>
      </div>
      <div class="stat-row">
        <div class="stat-card"><div class="label">主机 / 可用</div><div class="value">{{ stats.hosts }} / {{ stats.freeHosts }}</div></div>
        <div class="stat-card"><div class="label">实例总数</div><div class="value">{{ stats.instances }}</div></div>
        <div class="stat-card"><div class="label">运行中部署任务</div><div class="value">{{ stats.deploying }}</div></div>
        <div class="stat-card"><div class="label">活跃告警</div><div class="value">{{ stats.alerts }}</div></div>
      </div>
    </div>

    <div class="panel" style="margin-bottom:12px">
      <div class="panel-title">
        <h2>进行中的部署任务</h2>
        <button class="btn" @click="router.push('/tasks')">全部任务</button>
      </div>
      <div class="empty" v-if="!runningJobs.length">暂无进行中 / 失败任务。点击「新建编排」开始。</div>
      <table class="table" v-else>
        <thead>
          <tr><th>任务</th><th>组件</th><th>进度</th><th>部署状态</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="j in runningJobs" :key="j.id" :style="deployStatus(j).key === 'failed' ? 'background:#ffece8' : ''">
            <td>#{{ j.id }} · {{ j.action }}</td>
            <td>{{ instances.find(c => c.id === j.cluster_id)?.platforms?.join(', ') || '-' }}</td>
            <td>
              <div class="progress-bar" style="width:120px;display:inline-block;vertical-align:middle">
                <div class="progress-fill" :style="{ width: `${j.progress ?? 0}%` }"></div>
              </div>
              {{ j.progress ?? 0 }}%
            </td>
            <td><span class="status-pill" :class="deployStatus(j).cls">{{ deployStatus(j).text }}</span></td>
            <td><button class="btn" @click="router.push(`/tasks/${j.id}`)">查看详情</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="panel" style="margin-bottom:12px">
      <div class="panel-title">
        <h2>已部署实例</h2>
        <button class="btn" @click="router.push('/instances')">实例管理</button>
      </div>
      <div class="empty" v-if="!instances.length">暂无实例。编排部署成功后自动生成。</div>
      <div class="grid" v-else>
        <div class="svc-card" v-for="c in instances" :key="c.id" @click="router.push(`/instances/${c.id}`)">
          <div style="display:flex;justify-content:space-between;gap:8px">
            <h3>{{ c.name }}</h3>
            <span class="status-pill" :class="instanceStatus(c, healthMap[c.id]?.platforms || {}).cls">
              {{ instanceStatus(c, healthMap[c.id]?.platforms || {}).text }}
            </span>
          </div>
          <p style="margin-top:8px">组件：{{ (c.platforms || []).join(', ') }}</p>
          <p>状态字段：实例运行态（非部署任务态）</p>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">
        <h2>高优先级告警</h2>
        <button class="btn" @click="router.push('/alerts')">告警中心</button>
      </div>
      <div class="empty" v-if="!alerts.length">暂无活跃告警</div>
      <table class="table" v-else>
        <thead><tr><th>等级</th><th>实例</th><th>内容</th><th>时间</th><th></th></tr></thead>
        <tbody>
          <tr v-for="(a, i) in alerts" :key="i">
            <td><span class="health-tag warn">{{ a.level }}</span></td>
            <td>{{ a.instance }}</td>
            <td>{{ a.content }}</td>
            <td>{{ a.time }}</td>
            <td><button class="btn" @click="router.push(`/instances/${a.id}`)">跳转</button></td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
