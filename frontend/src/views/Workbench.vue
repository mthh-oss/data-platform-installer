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
    <div class="page-hero">
      <div>
        <h1>工作台</h1>
        <p class="lead">编排部署优先。上方看任务进度，下方看实例运行态——两套状态互不混用。</p>
      </div>
      <div class="toolbar">
        <button class="btn ghost" @click="refresh">刷新</button>
        <button class="btn primary" @click="router.push('/orchestrate')">新建编排</button>
      </div>
    </div>

    <div class="stat-row" style="margin-bottom:14px">
      <div class="stat-card">
        <div class="label">主机 / 可用</div>
        <div class="value">{{ stats.hosts }}<span style="font-size:14px;color:var(--sub);font-weight:500"> / {{ stats.freeHosts }}</span></div>
      </div>
      <div class="stat-card">
        <div class="label">实例总数</div>
        <div class="value">{{ stats.instances }}</div>
      </div>
      <div class="stat-card">
        <div class="label">运行中部署任务</div>
        <div class="value">{{ stats.deploying }}</div>
      </div>
      <div class="stat-card">
        <div class="label">活跃告警</div>
        <div class="value">{{ stats.alerts }}</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">
        <div>
          <h2>进行中的部署任务</h2>
          <p class="muted">失败任务标红置顶 · 状态：排队 / 部署中 / 成功 / 失败</p>
        </div>
        <button class="btn" @click="router.push('/tasks')">全部任务</button>
      </div>
      <div class="empty" v-if="!runningJobs.length">
        <span class="empty-title">暂无进行中或失败任务</span>
        点击右上角「新建编排」开始首次部署
      </div>
      <div class="table-wrap" v-else>
        <table class="table">
          <thead>
            <tr><th>任务</th><th>组件</th><th>进度</th><th>部署状态</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="j in runningJobs" :key="j.id" :class="{ 'is-failed': deployStatus(j).key === 'failed' }">
              <td><strong>#{{ j.id }}</strong> · {{ j.action }}</td>
              <td>{{ instances.find(c => c.id === j.cluster_id)?.platforms?.join(', ') || '-' }}</td>
              <td style="min-width:140px">
                <div class="progress-bar" style="margin-bottom:4px">
                  <div class="progress-fill" :style="{ width: `${j.progress ?? 0}%` }"></div>
                </div>
                <span class="muted">{{ j.progress ?? 0 }}%</span>
              </td>
              <td><span class="status-pill" :class="deployStatus(j).cls">{{ deployStatus(j).text }}</span></td>
              <td><button class="btn" @click="router.push(`/tasks/${j.id}`)">查看详情</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">
        <div>
          <h2>已部署实例</h2>
          <p class="muted">展示实例运行状态（正常 / 告警 / 离线 / 停止）</p>
        </div>
        <button class="btn" @click="router.push('/instances')">实例管理</button>
      </div>
      <div class="empty" v-if="!instances.length">
        <span class="empty-title">还没有实例</span>
        编排部署成功后会自动出现在这里
      </div>
      <div class="grid" v-else>
        <div class="svc-card" v-for="c in instances" :key="c.id" @click="router.push(`/instances/${c.id}`)">
          <div class="card-icon">{{ (c.platforms?.[0] || 'IN').slice(0, 2).toUpperCase() }}</div>
          <div style="display:flex;justify-content:space-between;gap:8px;align-items:flex-start">
            <h3>{{ c.name }}</h3>
            <span class="status-pill" :class="instanceStatus(c, healthMap[c.id]?.platforms || {}).cls">
              {{ instanceStatus(c, healthMap[c.id]?.platforms || {}).text }}
            </span>
          </div>
          <p style="margin-top:8px">{{ (c.platforms || []).join(' · ') || '无组件' }}</p>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">
        <div>
          <h2>高优先级告警</h2>
          <p class="muted">来自实例健康探针</p>
        </div>
        <button class="btn" @click="router.push('/alerts')">告警中心</button>
      </div>
      <div class="empty" v-if="!alerts.length">
        <span class="empty-title">暂无活跃告警</span>
        实例运行正常
      </div>
      <div class="table-wrap" v-else>
        <table class="table">
          <thead><tr><th>等级</th><th>实例</th><th>内容</th><th>时间</th><th></th></tr></thead>
          <tbody>
            <tr v-for="(a, i) in alerts" :key="i">
              <td><span class="health-tag warn">{{ a.level }}</span></td>
              <td>{{ a.instance }}</td>
              <td>{{ a.content }}</td>
              <td class="muted">{{ a.time }}</td>
              <td><button class="btn" @click="router.push(`/instances/${a.id}`)">跳转</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
