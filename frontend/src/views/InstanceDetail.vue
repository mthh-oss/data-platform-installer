<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import { instanceStatus, rolesOf, schemaOf } from '../utils/plugin'

const route = useRoute()
const router = useRouter()
const id = computed(() => Number(route.params.id))
const tab = ref('overview')
const cluster = ref(null)
const health = ref(null)
const overview = ref(null)
const plugins = ref([])
const hosts = ref([])
const error = ref('')
const confirm = ref('')

const status = computed(() => instanceStatus(cluster.value, health.value?.platforms || {}))
const pluginMap = computed(() => Object.fromEntries(plugins.value.map((p) => [p.id, p])))

async function refresh() {
  try {
    const list = await api.clusters()
    cluster.value = list.find((c) => c.id === id.value) || null
    if (!cluster.value) return
    health.value = await api.clusterHealth(id.value)
    overview.value = await api.overview(id.value)
    plugins.value = await api.plugins()
    hosts.value = await api.hosts()
  } catch (e) {
    error.value = e.message
  }
}

async function act(action) {
  if (['stop'].includes(action) && confirm.value !== action) {
    confirm.value = action
    return
  }
  try {
    if (action === 'start') await api.deploy(id.value)
    if (action === 'stop') await api.stop(id.value)
    if (action === 'restart') await api.restart(id.value)
    confirm.value = ''
    router.push('/tasks')
  } catch (e) {
    error.value = e.message
  }
}

const roleRows = computed(() => {
  const rows = []
  for (const pid of cluster.value?.platforms || []) {
    const p = pluginMap.value[pid]
    if (!p) continue
    const cfg = cluster.value?.configs?.[pid] || {}
    for (const r of rolesOf(p)) {
      const ids = cfg[r.key] || []
      if (!ids.length) {
        rows.push({ plugin: p.name, role: r.name, host: '-', ip: '-', status: status.value.text })
      } else {
        for (const hid of ids) {
          const h = hosts.value.find((x) => x.id === hid)
          rows.push({
            plugin: p.name,
            role: r.name,
            host: h?.name || `#${hid}`,
            ip: h?.ip || '-',
            status: status.value.text,
          })
        }
      }
    }
  }
  return rows
})

onMounted(refresh)
watch(id, refresh)
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>{{ cluster?.name || `实例#${id}` }}</h2>
        <p class="muted" style="margin:6px 0 0">
          通用实例模板 · 运行状态
          <span class="status-pill" :class="status.cls">{{ status.text }}</span>
        </p>
      </div>
      <div class="toolbar">
        <button class="btn" @click="router.push('/instances')">返回列表</button>
        <button class="btn primary" @click="act('restart')">重启</button>
        <button class="btn danger" @click="act('stop')">{{ confirm === 'stop' ? '确认停止？' : '停止' }}</button>
        <button class="btn" @click="act('start')">启动</button>
      </div>
    </div>

    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'overview' }" @click="tab = 'overview'">概览</button>
      <button class="tab" :class="{ active: tab === 'roles' }" @click="tab = 'roles'">角色实例</button>
      <button class="tab" :class="{ active: tab === 'config' }" @click="tab = 'config'">配置</button>
      <button class="tab" :class="{ active: tab === 'monitor' }" @click="tab = 'monitor'">监控</button>
      <button class="tab" :class="{ active: tab === 'logs' }" @click="tab = 'logs'">日志</button>
    </div>

    <div v-if="tab === 'overview'">
      <div class="stat-row">
        <div class="stat-card" v-for="n in (overview?.nodes || [])" :key="n.id">
          <div class="label">{{ n.name }}</div>
          <div class="value" style="font-size:16px">{{ n.ok ? '正常' : '异常' }}</div>
        </div>
      </div>
      <p class="muted">核心指标由插件 metrics 定义；一期展示健康探针结果。</p>
    </div>

    <div v-else-if="tab === 'roles'">
      <table class="table">
        <thead><tr><th>组件</th><th>角色</th><th>主机</th><th>IP</th><th>状态</th></tr></thead>
        <tbody>
          <tr v-for="(r, i) in roleRows" :key="i">
            <td>{{ r.plugin }}</td><td>{{ r.role }}</td><td>{{ r.host }}</td><td>{{ r.ip }}</td>
            <td><span class="status-pill" :class="status.cls">{{ r.status }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="tab === 'config'">
      <div v-for="pid in (cluster?.platforms || [])" :key="pid" style="margin-bottom:16px">
        <h3 style="margin:0 0 8px;font-size:14px">{{ pluginMap[pid]?.name || pid }}</h3>
        <div class="form-grid">
          <div class="field" v-for="(prop, key) in schemaOf(pluginMap[pid] || {}).properties" :key="key">
            <label>{{ prop.title || key }}</label>
            <input :value="JSON.stringify(cluster?.configs?.[pid]?.[key] ?? '')" readonly />
          </div>
        </div>
      </div>
      <p class="muted">修改下发与变更对比二期完善；当前为配置快照只读。</p>
    </div>

    <div v-else-if="tab === 'monitor'">
      <pre class="log">{{ JSON.stringify(health?.platforms || {}, null, 2) }}</pre>
    </div>

    <div v-else>
      <button class="btn" @click="api.downloadAbnormal(id)">下载异常日志包</button>
      <button class="btn" style="margin-left:8px" @click="router.push('/logs')">全局日志检索</button>
    </div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
