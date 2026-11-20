<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, getUser } from '../api/client'

const router = useRouter()
const view = ref('table')
const hosts = ref([])
const q = ref('')
const error = ref('')
const showAdd = ref(false)
const saving = ref(false)
const pendingDelete = ref(null)
const deleting = ref(false)
const me = ref(getUser())
const form = ref({
  name: '',
  ip: '',
  ssh_port: 22,
  ssh_user: 'root',
  ssh_password: '',
  is_local: false,
  skip_ssh_check: false,
  labels: '',
  remark: '',
})

const canWrite = computed(() => me.value?.role === 'admin' || me.value?.role === 'operator')

const filtered = computed(() => {
  const s = q.value.trim()
  if (!s) return hosts.value
  return hosts.value.filter((h) => `${h.name}${h.ip}${h.labels || ''}`.includes(s))
})

function agentCls(h) {
  if (h.agent_status === 'verified') return 'healthy'
  if (h.agent_status === 'offline') return 'unhealthy'
  return 'unknown'
}

function agentText(h) {
  if (h.agent_status === 'verified') return '已校验'
  if (h.agent_status === 'offline') return '离线'
  if (h.has_password) return '未校验'
  return '无密码'
}

async function load() {
  error.value = ''
  try {
    me.value = getUser() || (await api.me())
    hosts.value = await api.hosts()
  } catch (e) {
    error.value = e.message
  }
}

async function addHost() {
  if (!canWrite.value) {
    error.value = '当前账号无纳管权限'
    return
  }
  if (!form.value.is_local && !form.value.ssh_password.trim()) {
    error.value = '远程主机必须填写 SSH 密码'
    return
  }
  saving.value = true
  error.value = ''
  try {
    await api.createHost({
      ...form.value,
      ssh_port: Number(form.value.ssh_port) || 22,
    })
    showAdd.value = false
    form.value = {
      name: '',
      ip: '',
      ssh_port: 22,
      ssh_user: 'root',
      ssh_password: '',
      is_local: false,
      skip_ssh_check: false,
      labels: '',
      remark: '',
    }
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

async function confirmDelete() {
  if (!pendingDelete.value) return
  deleting.value = true
  error.value = ''
  try {
    await api.deleteHost(pendingDelete.value.id)
    pendingDelete.value = null
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    deleting.value = false
  }
}

onMounted(load)
</script>

<template>
  <section>
    <div class="page-hero">
      <div>
        <h1>主机资源池</h1>
        <p class="lead">纳管需填写 SSH 账号密码并校验连通；无密码不能视为已接入。详情页只读库存，不等于已登录主机。</p>
      </div>
      <div class="toolbar">
        <button class="btn" :class="{ primary: view === 'table' }" @click="view = 'table'">表格</button>
        <button class="btn" :class="{ primary: view === 'topo' }" @click="view = 'topo'">拓扑</button>
        <input v-model="q" class="select" style="width:160px" placeholder="搜索主机" />
        <button class="btn ghost" @click="load">刷新</button>
        <button class="btn primary" :disabled="!canWrite" @click="showAdd = !showAdd">纳管主机</button>
      </div>
    </div>
    <div class="panel">

    <div v-if="showAdd" class="form-grid" style="margin-bottom:14px">
      <div class="field"><label>主机名</label><input v-model="form.name" /></div>
      <div class="field"><label>IP</label><input v-model="form.ip" /></div>
      <div class="field"><label>SSH 端口</label><input v-model="form.ssh_port" type="number" /></div>
      <div class="field"><label>SSH 用户</label><input v-model="form.ssh_user" /></div>
      <div class="field">
        <label>SSH 密码 <span class="muted">（必填，加密存储，列表不回显）</span></label>
        <input v-model="form.ssh_password" type="password" autocomplete="new-password" :disabled="form.is_local" />
      </div>
      <div class="field"><label>标签</label><input v-model="form.labels" placeholder="fe,be,worker" /></div>
      <div class="field full"><label>备注</label><input v-model="form.remark" /></div>
      <div class="field full" style="display:flex;gap:16px;flex-wrap:wrap">
        <label style="display:flex;gap:8px;align-items:center;font-size:13px;color:var(--text-2)">
          <input type="checkbox" v-model="form.is_local" /> 本机节点（跳过 SSH，仅 Docker 本机部署）
        </label>
        <label style="display:flex;gap:8px;align-items:center;font-size:13px;color:var(--text-2)">
          <input type="checkbox" v-model="form.skip_ssh_check" :disabled="form.is_local" /> 跳过连通校验（仍要求填密码）
        </label>
      </div>
      <div class="actions full" style="margin:0">
        <button class="btn primary" :disabled="saving" @click="addHost">{{ saving ? '校验并保存…' : '校验并纳管' }}</button>
        <button class="btn" @click="showAdd = false">取消</button>
      </div>
    </div>

    <div class="table-wrap" v-if="view === 'table'">
    <table class="table">
      <thead>
        <tr>
          <th>主机名</th><th>IP</th><th>SSH 状态</th><th>标签</th><th>状态</th><th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="h in filtered" :key="h.id">
          <td>{{ h.name }}</td>
          <td>{{ h.ip }}:{{ h.ssh_port || 22 }}</td>
          <td><span class="status-pill" :class="agentCls(h)">{{ agentText(h) }}</span></td>
          <td>{{ h.labels || '-' }}</td>
          <td><span class="status-pill" :class="h.enabled === false ? 'unknown' : 'healthy'">{{ h.enabled === false ? '禁用' : '空闲' }}</span></td>
          <td>
            <div class="toolbar">
              <button class="btn" @click="router.push(`/hosts/${h.id}`)">详情</button>
              <button class="btn" disabled title="需已校验 SSH 后安装">安装 Agent</button>
              <button class="btn danger" :disabled="!canWrite" @click="pendingDelete = h">删除</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    </div>

    <div class="topo" v-else>
      <div class="topo-node" :class="h.agent_status === 'verified' ? 'ok-node' : 'bad-node'" v-for="h in filtered" :key="h.id" @click="router.push(`/hosts/${h.id}`)">
        <div class="topo-title">{{ h.name }}</div>
        <div class="topo-id">{{ h.ip }}</div>
        <div class="topo-deps">{{ agentText(h) }} · {{ h.labels || '未打标签' }}</div>
      </div>
    </div>
    <div class="empty" v-if="!filtered.length">暂无主机</div>
    <p class="error" v-if="error">{{ error }}</p>
    </div>

    <div v-if="pendingDelete" class="modal-mask" @click.self="pendingDelete = null">
      <div class="modal-card">
        <h3>确认删除主机？</h3>
        <p class="muted">将删除「{{ pendingDelete.name }}」({{ pendingDelete.ip }})。此操作写入审计。</p>
        <div class="actions" style="justify-content:flex-end">
          <button class="btn" @click="pendingDelete = null">取消</button>
          <button class="btn danger" :disabled="deleting" @click="confirmDelete">{{ deleting ? '删除中…' : '确认删除' }}</button>
        </div>
      </div>
    </div>
  </section>
</template>
