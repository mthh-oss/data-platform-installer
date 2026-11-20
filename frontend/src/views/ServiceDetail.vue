<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const clusterId = computed(() => Number(route.params.clusterId))
const sid = computed(() => String(route.params.sid))
const tab = ref('overview')
const overview = ref(null)
const health = ref(null)
const hosts = ref([])
const error = ref('')
const confirmAct = ref('')

const node = computed(() => (overview.value?.nodes || []).find((n) => n.id === sid.value))
const nodeHealth = computed(() => health.value?.platforms?.[sid.value])

async function refresh() {
  try {
    overview.value = await api.overview(clusterId.value)
    health.value = await api.clusterHealth(clusterId.value)
    hosts.value = await api.hosts()
  } catch (e) {
    error.value = e.message
  }
}

async function doAct(action) {
  if (!confirmAct.value) {
    confirmAct.value = action
    return
  }
  if (confirmAct.value !== action) {
    confirmAct.value = action
    return
  }
  error.value = ''
  try {
    if (action === 'start') await api.deploy(clusterId.value)
    if (action === 'stop') await api.stop(clusterId.value)
    if (action === 'restart') await api.restart(clusterId.value)
    confirmAct.value = ''
    router.push(`/c/${clusterId.value}/tasks`)
  } catch (e) {
    error.value = e.message
  }
}

onMounted(refresh)
watch([clusterId, sid], refresh)
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>{{ node?.name || sid }}</h2>
        <p class="muted" style="margin:6px 0 0">
          <span class="status-pill" :class="(nodeHealth?.ok ?? node?.ok) ? 'healthy' : 'unhealthy'">
            {{ nodeHealth?.status || node?.status || 'unknown' }}
          </span>
        </p>
      </div>
      <div class="toolbar">
        <button class="btn" @click="router.push(`/c/${clusterId}/services`)">返回列表</button>
        <button class="btn primary" @click="doAct('restart')">
          {{ confirmAct === 'restart' ? '确认重启？' : '重启' }}
        </button>
        <button class="btn danger" @click="doAct('stop')">
          {{ confirmAct === 'stop' ? '确认停止？' : '停止' }}
        </button>
      </div>
    </div>

    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'overview' }" @click="tab = 'overview'">概览</button>
      <button class="tab" :class="{ active: tab === 'roles' }" @click="tab = 'roles'">角色实例</button>
      <button class="tab" :class="{ active: tab === 'config' }" @click="tab = 'config'">配置</button>
      <button class="tab" :class="{ active: tab === 'monitor' }" @click="tab = 'monitor'">监控</button>
      <button class="tab" :class="{ active: tab === 'logs' }" @click="tab = 'logs'">日志</button>
      <button class="tab" :class="{ active: tab === 'history' }" @click="tab = 'history'">变更历史</button>
    </div>

    <div v-if="tab === 'overview'">
      <div class="stat-row">
        <div class="stat-card"><div class="label">服务 ID</div><div class="value" style="font-size:16px">{{ sid }}</div></div>
        <div class="stat-card"><div class="label">依赖数</div><div class="value">{{ node?.dependencies?.length || 0 }}</div></div>
        <div class="stat-card"><div class="label">健康检查</div><div class="value" style="font-size:16px">{{ (nodeHealth?.ok ?? node?.ok) ? '通过' : '失败' }}</div></div>
        <div class="stat-card"><div class="label">主机库存</div><div class="value">{{ hosts.length }}</div></div>
      </div>
      <p class="muted">极简拓扑：依赖 {{ (node?.dependencies || []).join(' → ') || '无' }} → {{ sid }}</p>
    </div>

    <div v-else-if="tab === 'roles'">
      <table class="table">
        <thead>
          <tr><th>角色</th><th>类型</th><th>说明</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-if="sid === 'doris'">
            <td>FE</td><td>Frontend</td><td>由主机库存 labels=fe 分配</td>
            <td><button class="btn" @click="router.push(`/c/${clusterId}/hosts`)">查看主机</button></td>
          </tr>
          <tr v-if="sid === 'doris'">
            <td>BE</td><td>Backend</td><td>由主机库存 labels=be 分配</td>
            <td><button class="btn" @click="router.push(`/c/${clusterId}/hosts`)">查看主机</button></td>
          </tr>
          <tr v-if="sid === 'flink'">
            <td>JobManager</td><td>JM</td><td>Flink 管控进程</td><td>—</td>
          </tr>
          <tr v-if="sid === 'flink'">
            <td>TaskManager</td><td>TM</td><td>Flink 执行进程</td><td>—</td>
          </tr>
          <tr v-if="!['doris','flink'].includes(sid)">
            <td>{{ sid }}</td><td>主进程</td><td>Compose 单角色实例</td><td>—</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="tab === 'config'">
      <p class="muted">配置编辑请走「配置中心」或重新部署向导。</p>
      <button class="btn primary" @click="router.push(`/c/${clusterId}/config`)">打开配置中心</button>
    </div>

    <div v-else-if="tab === 'monitor'">
      <p class="muted">监控图表一期展示健康探针结果；细粒度时序后续接入。</p>
      <pre class="log">{{ JSON.stringify(nodeHealth || node || {}, null, 2) }}</pre>
    </div>

    <div v-else-if="tab === 'logs'">
      <p class="muted">跨服务日志请使用「日志检索」；异常打包从下方下载。</p>
      <button class="btn" @click="api.downloadAbnormal(clusterId)">下载异常日志包</button>
    </div>

    <div v-else>
      <div class="empty">变更历史将对接审计日志（谁/何时/改了什么）。</div>
    </div>

    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
