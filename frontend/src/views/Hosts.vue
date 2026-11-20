<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const clusterId = computed(() => Number(route.params.clusterId))
const view = ref('table')
const hosts = ref([])
const q = ref('')
const error = ref('')
const form = ref({ name: '', ip: '', ssh_port: 22, labels: '', remark: '' })
const showAdd = ref(false)
const saving = ref(false)

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
  if (!confirm('确认删除该主机？')) return
  try {
    await api.deleteHost(id)
    await load()
  } catch (e) {
    error.value = e.message
  }
}

function loadColor(h) {
  const tags = (h.labels || '').toLowerCase()
  if (tags.includes('be') || tags.includes('fe')) return 'ok-node'
  return ''
}

onMounted(load)
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>主机管理</h2>
        <p class="muted" style="margin:6px 0 0">表格 + 拓扑双视图；Doris FE/BE 通过 labels 标记</p>
      </div>
      <div class="toolbar">
        <button class="btn" :class="{ primary: view === 'table' }" @click="view = 'table'">表格视图</button>
        <button class="btn" :class="{ primary: view === 'topo' }" @click="view = 'topo'">拓扑视图</button>
        <input v-model="q" class="select" style="width:160px" placeholder="搜索主机" />
        <button class="btn ghost" @click="load">刷新</button>
        <button class="btn primary" @click="showAdd = !showAdd">添加主机</button>
      </div>
    </div>

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

    <table class="table" v-if="view === 'table'">
      <thead>
        <tr>
          <th>主机名</th><th>IP</th><th>Agent</th><th>标签</th><th>备注</th><th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="h in filtered" :key="h.id">
          <td>{{ h.name }}</td>
          <td>{{ h.ip }}:{{ h.ssh_port || 22 }}</td>
          <td><span class="status-pill healthy">在线</span></td>
          <td>{{ h.labels || '-' }}</td>
          <td>{{ h.remark || '-' }}</td>
          <td>
            <div class="toolbar">
              <button class="btn" @click="router.push(`/c/${clusterId}/hosts/${h.id}`)">详情</button>
              <button class="btn danger" @click="remove(h.id)">删除</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="topo" v-else>
      <div class="topo-node" :class="loadColor(h)" v-for="h in filtered" :key="h.id" @click="router.push(`/c/${clusterId}/hosts/${h.id}`)">
        <div class="topo-title">{{ h.name }}</div>
        <div class="topo-id">{{ h.ip }}</div>
        <div class="topo-deps">角色标签：{{ h.labels || '未标记' }}</div>
      </div>
    </div>

    <div class="empty" v-if="!filtered.length">暂无主机，请添加后用于 Doris FE/BE 分配。</div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
