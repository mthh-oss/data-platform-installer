<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { instanceStatus } from '../utils/plugin'

const router = useRouter()
const rows = ref([])
const plugins = ref([])
const healthMap = ref({})
const q = ref('')
const statusFilter = ref('all')
const typeFilter = ref('all')
const error = ref('')
const confirm = ref(null)
let timer = null

const filtered = computed(() =>
  rows.value.filter((c) => {
    const st = instanceStatus(c, healthMap.value[c.id]?.platforms || {})
    if (statusFilter.value !== 'all' && st.key !== statusFilter.value) return false
    if (typeFilter.value !== 'all' && !(c.platforms || []).includes(typeFilter.value)) return false
    if (q.value && !`${c.name}${(c.platforms || []).join('')}`.includes(q.value.trim())) return false
    return true
  }),
)

async function refresh() {
  try {
    rows.value = await api.clusters()
    plugins.value = await api.plugins()
    const map = {}
    await Promise.all(
      rows.value.map(async (c) => {
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

async function act(c, action) {
  if (['stop', 'uninstall'].includes(action) && confirm.value !== `${action}-${c.id}`) {
    confirm.value = `${action}-${c.id}`
    return
  }
  error.value = ''
  try {
    if (action === 'start') await api.deploy(c.id)
    if (action === 'stop') await api.stop(c.id)
    if (action === 'restart') await api.restart(c.id)
    if (action === 'uninstall') await api.stop(c.id)
    confirm.value = null
    router.push('/tasks')
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
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>实例管理</h2>
        <p class="muted" style="margin:6px 0 0">实例 = 编排成功产物；此处展示<strong>运行状态</strong>，不是部署任务状态。</p>
      </div>
      <div class="toolbar">
        <input v-model="q" class="select" style="width:160px" placeholder="搜索实例" />
        <select v-model="typeFilter" class="select" style="width:140px">
          <option value="all">全部组件</option>
          <option v-for="p in plugins" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <select v-model="statusFilter" class="select" style="width:120px">
          <option value="all">全部状态</option>
          <option value="ok">正常</option>
          <option value="alert">告警</option>
          <option value="offline">离线</option>
          <option value="stopped">停止</option>
        </select>
        <button class="btn ghost" @click="refresh">刷新</button>
        <button class="btn primary" @click="router.push('/orchestrate')">新建编排</button>
      </div>
    </div>

    <table class="table">
      <thead>
        <tr>
          <th>实例名称</th><th>组件类型</th><th>运行状态</th><th>主机相关</th><th>告警</th><th>创建时间</th><th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in filtered" :key="c.id">
          <td><strong>{{ c.name }}</strong></td>
          <td>{{ (c.platforms || []).join(', ') }}</td>
          <td>
            <span class="status-pill" :class="instanceStatus(c, healthMap[c.id]?.platforms || {}).cls">
              {{ instanceStatus(c, healthMap[c.id]?.platforms || {}).text }}
            </span>
          </td>
          <td>{{ (c.platforms || []).length }} 组件</td>
          <td>{{ Object.values(healthMap[c.id]?.platforms || {}).filter(p => p && !p.ok).length }}</td>
          <td>{{ c.created_at ? new Date(c.created_at).toLocaleString() : '-' }}</td>
          <td>
            <div class="toolbar">
              <button class="btn" @click="router.push(`/instances/${c.id}`)">详情</button>
              <button class="btn" @click="act(c, 'start')">启动</button>
              <button class="btn danger" @click="act(c, 'stop')">
                {{ confirm === `stop-${c.id}` ? '确认停止？' : '停止' }}
              </button>
              <button class="btn" @click="act(c, 'restart')">重载</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <div class="empty" v-if="!filtered.length">暂无实例</div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
