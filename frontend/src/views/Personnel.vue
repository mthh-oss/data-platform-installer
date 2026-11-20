<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api, getUser } from '../api/client'

const me = ref(getUser())
const rows = ref([])
const error = ref('')
const saving = ref(false)
const editing = ref(null)

const form = reactive({
  username: '',
  password: '',
  display_name: '',
  department: '',
  title: '',
  role: 'operator',
  manager_id: null,
})

const isAdmin = computed(() => me.value?.role === 'admin')
const managerOptions = computed(() => rows.value.filter((u) => u.enabled))

async function load() {
  error.value = ''
  try {
    me.value = await api.me()
    rows.value = await api.users()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)

function resetForm() {
  editing.value = null
  form.username = ''
  form.password = ''
  form.display_name = ''
  form.department = ''
  form.title = ''
  form.role = 'operator'
  form.manager_id = null
}

function startEdit(u) {
  editing.value = u.id
  form.display_name = u.display_name || ''
  form.department = u.department || ''
  form.title = u.title || ''
  form.role = u.role
  form.manager_id = u.manager_id
  form.password = ''
}

async function createPerson() {
  if (!isAdmin.value) return
  saving.value = true
  error.value = ''
  try {
    await api.createUser({
      username: form.username,
      password: form.password,
      display_name: form.display_name || form.username,
      department: form.department,
      title: form.title,
      role: form.role,
      manager_id: form.manager_id || null,
    })
    resetForm()
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

async function saveEdit() {
  if (!editing.value) return
  saving.value = true
  error.value = ''
  try {
    const body = {
      display_name: form.display_name,
      department: form.department,
      title: form.title,
      role: form.role,
      manager_id: form.manager_id || null,
    }
    if (form.password) body.password = form.password
    await api.updateUser(editing.value, body)
    resetForm()
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

async function toggleEnabled(u) {
  try {
    await api.updateUser(u.id, { enabled: !u.enabled })
    await load()
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>人员关系</h2>
        <p class="muted" style="margin:6px 0 0">配置人员、部门、岗位与上下级关系，用于权限隔离基础。</p>
      </div>
      <button class="btn" @click="load">刷新</button>
    </div>

    <table class="table">
      <thead>
        <tr>
          <th>姓名</th>
          <th>账号</th>
          <th>部门</th>
          <th>岗位</th>
          <th>上级</th>
          <th>角色</th>
          <th>状态</th>
          <th v-if="isAdmin">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in rows" :key="u.id">
          <td>{{ u.display_name || '-' }}</td>
          <td>{{ u.username }}</td>
          <td>{{ u.department || '-' }}</td>
          <td>{{ u.title || '-' }}</td>
          <td>{{ u.manager_name || '-' }}</td>
          <td>{{ u.role }}</td>
          <td>
            <span class="status-pill" :class="u.enabled ? 'healthy' : 'unhealthy'">
              {{ u.enabled ? '启用' : '停用' }}
            </span>
          </td>
          <td v-if="isAdmin">
            <div class="toolbar">
              <button class="btn" @click="startEdit(u)">编辑</button>
              <button class="btn" @click="toggleEnabled(u)">{{ u.enabled ? '停用' : '启用' }}</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="config-block" v-if="isAdmin">
      <h3>{{ editing ? '编辑人员关系' : '新增人员' }}</h3>
      <div class="form-grid">
        <div class="field" v-if="!editing">
          <label>登录账号</label>
          <input v-model="form.username" placeholder="如 zhangsan" />
        </div>
        <div class="field">
          <label>姓名</label>
          <input v-model="form.display_name" placeholder="如 张三" />
        </div>
        <div class="field">
          <label>部门</label>
          <input v-model="form.department" placeholder="如 数据平台组" />
        </div>
        <div class="field">
          <label>岗位</label>
          <input v-model="form.title" placeholder="如 运维工程师" />
        </div>
        <div class="field">
          <label>上级</label>
          <select class="select" v-model="form.manager_id">
            <option :value="null">无</option>
            <option v-for="u in managerOptions" :key="u.id" :value="u.id" :disabled="u.id === editing">
              {{ u.display_name || u.username }}
            </option>
          </select>
        </div>
        <div class="field">
          <label>角色权限</label>
          <select class="select" v-model="form.role">
            <option value="admin">管理员</option>
            <option value="operator">运维</option>
            <option value="viewer">只读</option>
          </select>
        </div>
        <div class="field" :class="{ full: !!editing }">
          <label>{{ editing ? '重置密码（可选）' : '初始密码' }}</label>
          <input v-model="form.password" type="password" placeholder="至少8位，含字母，不能全数字" />
        </div>
      </div>
      <div class="actions">
        <button class="btn primary" :disabled="saving" @click="editing ? saveEdit() : createPerson()">
          {{ saving ? '保存中…' : editing ? '保存修改' : '新增人员' }}
        </button>
        <button class="btn" v-if="editing" @click="resetForm">取消</button>
      </div>
    </div>

    <p class="muted" v-if="!isAdmin" style="margin-top:14px">当前账号无管理权限，仅可查看人员关系。</p>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
