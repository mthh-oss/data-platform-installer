<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'

const router = useRouter()
const view = ref('table')
const hosts = ref([])
const q = ref('')
const error = ref('')
const showAdd = ref(false)
const saving = ref(false)
const form = ref({ name: '', ip: '', ssh_port: 22, labels: '', remark: '' })

const filtered = computed(() => {
  const s = q.value.trim()
  if (!s) return hosts.value
  return hosts.value.filter((h) => `${h.name}${h.ip}${h.labels || ''}`.includes(s))
})

async function load() {
  try {
    hosts.value = await api.hosts()
  } catch (e) {
    error.value = e.message
  }
}

async function addHost() {
  saving.value = true
  error.value = ''
  try {
    await api.createHost({ ...form.value, ssh_port: Number(form.value.ssh_port) || 22 })
    showAdd.value = false
    form.value = { name: '', ip: '', ssh_port: 22, labels: '', remark: '' }
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

async function remove(id) {
  if (!confirm('确认删除主机？备注将写入审计（一期本地确认）。')) return
  try {
    await api.deleteHost(id)
    await load()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)
</script>

<template>
  <section>
    <div class="page-hero">
      <div>
        <h1>主机资源池</h1>
        <p class="lead">全局资源，不绑定某实例；编排时按需挑选。Agent 离线标红。</p>
      </div>
      <div class="toolbar">
        <button class="btn" :class="{ primary: view === 'table' }" @click="view = 'table'">表格</button>
        <button class="btn" :class="{ primary: view === 'topo' }" @click="view = 'topo'">拓扑</button>
        <input v-model="q" class="select" style="width:160px" placeholder="搜索主机" />
        <button class="btn ghost" @click="load">刷新</button>
        <button class="btn primary" @click="showAdd = !showAdd">纳管主机</button>
      </div>
    </div>
    <div class="panel">

    <div v-if="showAdd" class="form-grid" style="margin-bottom:14px">
      <div class="field"><label>主机名</label><input v-model="form.name" /></div>
      <div class="field"><label>IP</label><input v-model="form.ip" /></div>
      <div class="field"><label>SSH 端口</label><input v-model="form.ssh_port" type="number" /></div>
      <div class="field"><label>标签</label><input v-model="form.labels" placeholder="fe,be,worker" /></div>
      <div class="field full"><label>备注</label><input v-model="form.remark" /></div>
      <div class="actions full" style="margin:0">
        <button class="btn primary" :disabled="saving" @click="addHost">保存</button>
        <button class="btn" @click="showAdd = false">取消</button>
      </div>
    </div>

    <div class="table-wrap" v-if="view === 'table'">
    <table class="table">
      <thead>
        <tr>
          <th>主机名</th><th>IP</th><th>Agent</th><th>标签</th><th>状态</th><th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="h in filtered" :key="h.id">
          <td>{{ h.name }}</td>
          <td>{{ h.ip }}:{{ h.ssh_port || 22 }}</td>
          <td><span class="status-pill healthy">正常</span></td>
          <td>{{ h.labels || '-' }}</td>
          <td><span class="status-pill" :class="h.enabled === false ? 'unknown' : 'healthy'">{{ h.enabled === false ? '禁用' : '空闲' }}</span></td>
          <td>
            <div class="toolbar">
              <button class="btn" @click="router.push(`/hosts/${h.id}`)">详情</button>
              <button class="btn" disabled>安装 Agent</button>
              <button class="btn danger" @click="remove(h.id)">删除</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    </div>

    <div class="topo" v-else>
      <div class="topo-node ok-node" v-for="h in filtered" :key="h.id" @click="router.push(`/hosts/${h.id}`)">
        <div class="topo-title">{{ h.name }}</div>
        <div class="topo-id">{{ h.ip }}</div>
        <div class="topo-deps">{{ h.labels || '未打标签' }}</div>
      </div>
    </div>
    <div class="empty" v-if="!filtered.length">暂无主机</div>
    <p class="error" v-if="error">{{ error }}</p>
    </div>
  </section>
</template>
