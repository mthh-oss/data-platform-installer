<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, getUser } from '../api/client'

const tab = ref('ai')
const me = ref(getUser())
const error = ref('')

const ai = ref({ provider: 'deepseek', has_api_key: false, providers: [] })
const apiKey = ref('')
const savingAi = ref(false)

const users = ref([])
const newUser = ref({ username: '', password: '', role: 'operator', display_name: '' })

const hosts = ref([])
const hostForm = ref({
  name: '', ip: '', ssh_port: 22, ssh_user: 'root', is_local: false, labels: 'fe,be', remark: '', enabled: true,
})

const isAdmin = computed(() => me.value?.role === 'admin')

async function load() {
  error.value = ''
  try {
    me.value = await api.me()
    ai.value = await api.aiSettings()
    hosts.value = await api.hosts()
    if (isAdmin.value) users.value = await api.users()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)

async function saveAi() {
  savingAi.value = true
  error.value = ''
  try {
    ai.value = await api.saveAiSettings({ provider: ai.value.provider, api_key: apiKey.value })
    apiKey.value = ''
  } catch (e) {
    error.value = e.message
  } finally {
    savingAi.value = false
  }
}

async function createUser() {
  error.value = ''
  try {
    await api.createUser(newUser.value)
    newUser.value = { username: '', password: '', role: 'operator', display_name: '' }
    users.value = await api.users()
  } catch (e) {
    error.value = e.message
  }
}

async function toggleUser(u) {
  try {
    await api.updateUser(u.id, { enabled: !u.enabled })
    users.value = await api.users()
  } catch (e) {
    error.value = e.message
  }
}

async function createHost() {
  error.value = ''
  try {
    await api.createHost({
      ...hostForm.value,
      ssh_port: Number(hostForm.value.ssh_port),
    })
    hostForm.value = {
      name: '', ip: '', ssh_port: 22, ssh_user: 'root', is_local: false, labels: 'fe,be', remark: '', enabled: true,
    }
    hosts.value = await api.hosts()
  } catch (e) {
    error.value = e.message
  }
}

async function removeHost(id) {
  try {
    await api.deleteHost(id)
    hosts.value = await api.hosts()
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <section class="panel">
    <h2 style="margin-top:0">设置</h2>
    <p class="muted">系统配置集中管理：AI、用户权限、主机库存。</p>

    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'ai' }" @click="tab = 'ai'">AI 配置</button>
      <button class="tab" :class="{ active: tab === 'hosts' }" @click="tab = 'hosts'">主机库存</button>
      <button class="tab" :class="{ active: tab === 'users' }" @click="tab = 'users'" v-if="isAdmin">用户与权限</button>
    </div>

    <div v-if="tab === 'ai'">
      <div class="form-grid">
        <div class="field">
          <label>Provider（可扩展）</label>
          <select class="select" v-model="ai.provider">
            <option v-for="p in ai.providers" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>API Key {{ ai.has_api_key ? '（已配置，留空不改）' : '' }}</label>
          <input v-model="apiKey" type="password" placeholder="DeepSeek sk-..." />
        </div>
      </div>
      <div class="actions">
        <button class="btn primary" :disabled="savingAi" @click="saveAi">保存 AI 设置</button>
      </div>
      <p class="muted" style="margin-top:10px">扩展其他模型：复制 `backend/ai_providers/_example_openai` 为新目录并实现 provider。</p>
    </div>

    <div v-else-if="tab === 'hosts'">
      <p class="muted">先登记机器，Doris 配置时可分别选择 FE / BE 节点，节点通过 IP 互通。</p>
      <table class="table">
        <thead>
          <tr><th>名称</th><th>IP</th><th>标签</th><th>本机</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="h in hosts" :key="h.id">
            <td>{{ h.name }}</td>
            <td>{{ h.ip }}</td>
            <td>{{ h.labels }}</td>
            <td>{{ h.is_local ? '是' : '否' }}</td>
            <td><button class="btn danger" v-if="isAdmin" @click="removeHost(h.id)">删除</button></td>
          </tr>
        </tbody>
      </table>

      <div class="config-block">
        <h3>新增主机</h3>
        <div class="form-grid">
          <div class="field"><label>名称</label><input v-model="hostForm.name" /></div>
          <div class="field"><label>IP</label><input v-model="hostForm.ip" placeholder="192.168.1.10" /></div>
          <div class="field"><label>标签</label><input v-model="hostForm.labels" placeholder="fe,be" /></div>
          <div class="field"><label>SSH 用户</label><input v-model="hostForm.ssh_user" /></div>
          <label style="display:flex;gap:8px;align-items:center;font-size:13px;">
            <input type="checkbox" v-model="hostForm.is_local" /> 控制面本机（可直接 compose）
          </label>
        </div>
        <div class="actions">
          <button class="btn primary" @click="createHost">添加主机</button>
        </div>
      </div>
    </div>

    <div v-else-if="tab === 'users' && isAdmin">
      <p class="muted">角色：admin（全量）/ operator（可部署自己的集群）/ viewer（只读）。</p>
      <table class="table">
        <thead>
          <tr><th>用户</th><th>角色</th><th>状态</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.display_name || u.username }} ({{ u.username }})</td>
            <td>{{ u.role }}</td>
            <td>{{ u.enabled ? '启用' : '禁用' }}</td>
            <td><button class="btn" @click="toggleUser(u)">{{ u.enabled ? '禁用' : '启用' }}</button></td>
          </tr>
        </tbody>
      </table>
      <div class="config-block">
        <h3>新建用户</h3>
        <div class="form-grid">
          <div class="field"><label>用户名</label><input v-model="newUser.username" /></div>
          <div class="field"><label>显示名</label><input v-model="newUser.display_name" /></div>
          <div class="field"><label>密码</label><input v-model="newUser.password" type="password" /></div>
          <div class="field">
            <label>角色</label>
            <select class="select" v-model="newUser.role">
              <option value="admin">admin</option>
              <option value="operator">operator</option>
              <option value="viewer">viewer</option>
            </select>
          </div>
        </div>
        <div class="actions"><button class="btn primary" @click="createUser">创建</button></div>
      </div>
    </div>

    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
