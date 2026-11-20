<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, getUser } from '../api/client'
import {
  defaultTaskName,
  rolesOf,
  schemaOf,
  validateSelection,
} from '../utils/plugin'

const router = useRouter()
const step = ref(1)
const plugins = ref([])
const hosts = ref([])
const selected = ref([])
const configs = reactive({})
const roleHosts = reactive({}) // pluginId -> roleKey -> hostId[]
const taskName = ref(defaultTaskName())
const remark = ref('')
const activeCfg = ref('')
const showAdvanced = ref(false)
const loading = ref(false)
const error = ref('')
const depErrors = ref([])
const roleErrors = ref([])
const cfgErrors = ref([])
const me = ref(getUser())
const confirmSubmit = ref(false)
const q = ref('')

const canWrite = computed(() => me.value?.role === 'admin' || me.value?.role === 'operator')
const selectedPlugins = computed(() => plugins.value.filter((p) => selected.value.includes(p.id)))
const filteredPlugins = computed(() => {
  const s = q.value.trim()
  if (!s) return plugins.value
  return plugins.value.filter((p) => `${p.name}${p.id}${p.description}`.includes(s))
})
const freeHosts = computed(() => hosts.value.filter((h) => h.enabled !== false))

const canNext1 = computed(() => selected.value.length > 0 && !depErrors.value.length)
const canNext2 = computed(() => !roleErrors.value.length && selected.value.length > 0)
const canNext3 = computed(() => !cfgErrors.value.length)

onMounted(async () => {
  try {
    me.value = await api.me()
    const disabled = JSON.parse(localStorage.getItem('dpi_plugin_disabled') || '[]')
    plugins.value = (await api.plugins()).filter((p) => !disabled.includes(p.id))
    hosts.value = await api.hosts()
    for (const p of plugins.value) {
      configs[p.id] = { ...(p.default_config || {}) }
      roleHosts[p.id] = {}
      for (const r of rolesOf(p)) {
        roleHosts[p.id][r.key] = Array.isArray(configs[p.id][r.key]) ? [...configs[p.id][r.key]] : []
      }
    }
    if (plugins.value.length) activeCfg.value = plugins.value[0].id
  } catch (e) {
    error.value = e.message
  }
})

function toggle(id) {
  if (selected.value.includes(id)) {
    selected.value = selected.value.filter((x) => x !== id)
  } else {
    selected.value = [...selected.value, id]
  }
  depErrors.value = validateSelection(plugins.value, selected.value)
  if (!activeCfg.value || !selected.value.includes(activeCfg.value)) {
    activeCfg.value = selected.value[0] || ''
  }
}

function removeSelected(id) {
  selected.value = selected.value.filter((x) => x !== id)
  depErrors.value = validateSelection(plugins.value, selected.value)
}

function hostOptions(role) {
  if (!role.hostLabel) return freeHosts.value
  return freeHosts.value.filter((h) => (h.labels || '').toLowerCase().includes(role.hostLabel.toLowerCase()))
}

function setRoleHost(pid, roleKey, hostId, checked) {
  const arr = roleHosts[pid][roleKey] || []
  if (checked) roleHosts[pid][roleKey] = [...new Set([...arr, hostId])]
  else roleHosts[pid][roleKey] = arr.filter((x) => x !== hostId)
  validateRoles()
}

function validateRoles() {
  const errs = []
  for (const p of selectedPlugins.value) {
    for (const r of rolesOf(p)) {
      if (r.min > 0 && (roleHosts[p.id][r.key] || []).length < r.min) {
        errs.push(`${p.name} · ${r.name} 至少需要 ${r.min} 台主机`)
      }
    }
  }
  roleErrors.value = errs
  return !errs.length
}

function autoAssign() {
  const pool = [...freeHosts.value]
  let i = 0
  for (const p of selectedPlugins.value) {
    for (const r of rolesOf(p)) {
      const need = Math.max(r.min, 1)
      const picks = []
      const opts = hostOptions(r)
      for (let n = 0; n < need; n++) {
        const h = opts[i % Math.max(opts.length, 1)] || pool[i % Math.max(pool.length, 1)]
        if (h) picks.push(h.id)
        i++
      }
      roleHosts[p.id][r.key] = [...new Set(picks)]
    }
  }
  validateRoles()
}

function applyRolesToConfig() {
  for (const p of selectedPlugins.value) {
    for (const r of rolesOf(p)) {
      if (r.key !== '_host') {
        configs[p.id][r.key] = [...(roleHosts[p.id][r.key] || [])]
      }
    }
  }
}

function validateConfigs() {
  const errs = []
  for (const p of selectedPlugins.value) {
    const schema = schemaOf(p)
    const req = schema.required || []
    for (const key of req) {
      const v = configs[p.id][key]
      if (v === undefined || v === null || v === '' || (Array.isArray(v) && !v.length)) {
        errs.push(`${p.name}: ${schema.properties?.[key]?.title || key} 必填`)
      }
    }
  }
  cfgErrors.value = errs
  return !errs.length
}

function goStep(n) {
  if (n === 2) {
    depErrors.value = validateSelection(plugins.value, selected.value)
    if (!canNext1.value) return
  }
  if (n === 3) {
    if (!validateRoles()) return
    applyRolesToConfig()
    activeCfg.value = selected.value[0] || ''
  }
  if (n === 4) {
    applyRolesToConfig()
    if (!validateConfigs()) return
  }
  step.value = n
}

const assignmentRows = computed(() => {
  const rows = []
  for (const p of selectedPlugins.value) {
    for (const r of rolesOf(p)) {
      for (const hid of roleHosts[p.id][r.key] || []) {
        const h = hosts.value.find((x) => x.id === hid)
        rows.push({
          plugin: p.name,
          role: r.name,
          ip: h?.ip || '-',
          host: h?.name || `#${hid}`,
        })
      }
    }
  }
  return rows
})

const configSummary = computed(() => {
  const lines = []
  for (const p of selectedPlugins.value) {
    const schema = schemaOf(p)
    const props = schema.properties || {}
    const bits = []
    for (const [k, meta] of Object.entries(props)) {
      if (meta['x-ui'] === 'host-multi') continue
      if (String(k).toLowerCase().includes('password')) continue
      const v = configs[p.id][k]
      if (v !== undefined && v !== '') bits.push(`${meta.title || k}=${v}`)
    }
    lines.push(`${p.name}: ${bits.slice(0, 4).join('，') || '默认配置'}`)
  }
  return lines
})

function fieldType(prop) {
  if (prop.type === 'integer' || prop.type === 'number') return 'number'
  if (String(prop.title || '').includes('密码') || String(prop.type) === 'password') return 'password'
  return 'text'
}

function isAdvanced(key, prop) {
  return /password|secret|jvm|advanced|extra|edit_log/i.test(key) || prop['x-advanced'] === true
}

async function submit() {
  if (!canWrite.value) {
    error.value = '当前账号无编排权限'
    return
  }
  if (!confirmSubmit.value) {
    confirmSubmit.value = true
    return
  }
  error.value = ''
  loading.value = true
  try {
    applyRolesToConfig()
    const body = {
      name: taskName.value || defaultTaskName(),
      platforms: selected.value,
      configs: Object.fromEntries(selected.value.map((id) => [id, configs[id]])),
    }
    const cluster = await api.createCluster(body)
    const job = await api.deploy(cluster.id)
    router.push(`/tasks/${job.id}`)
  } catch (e) {
    error.value = e.message
    confirmSubmit.value = false
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section>
    <div class="page-hero">
      <div>
        <h1>组件编排</h1>
        <p class="lead">选组件 → 分配主机 → 参数配置 → 预览提交。组件列表来自已启用插件，表单由 Schema 渲染。</p>
      </div>
    </div>

    <div class="panel">
      <div class="steps">
        <button type="button" class="step" :class="{ active: step === 1, done: step > 1 }" @click="step > 1 && (step = 1)">
          <span class="step-num">1</span> 选择组件
        </button>
        <button type="button" class="step" :class="{ active: step === 2, done: step > 2 }" @click="step > 2 && (step = 2)">
          <span class="step-num">2</span> 分配主机
        </button>
        <button type="button" class="step" :class="{ active: step === 3, done: step > 3 }" @click="step > 3 && (step = 3)">
          <span class="step-num">3</span> 参数配置
        </button>
        <button type="button" class="step" :class="{ active: step === 4 }">
          <span class="step-num">4</span> 预览提交
        </button>
      </div>

      <!-- Step1 -->
      <div v-if="step === 1" class="orch-split">
        <div class="orch-pane">
          <div class="toolbar" style="margin-bottom:12px;justify-content:space-between">
            <span class="section-label" style="margin:0">可选组件</span>
            <input v-model="q" class="select" style="width:180px" placeholder="搜索组件" />
          </div>
          <div class="grid">
            <button
              v-for="p in filteredPlugins"
              :key="p.id"
              type="button"
              class="choice"
              :class="{ selected: selected.includes(p.id) }"
              @click="toggle(p.id)"
            >
              <div class="card-icon">{{ p.name.slice(0, 2) }}</div>
              <h3>{{ p.name }} <span class="muted">v{{ p.version }}</span></h3>
              <p>{{ p.description || '插件组件' }}</p>
              <p class="deps" v-if="p.dependencies?.length">依赖：{{ p.dependencies.join(', ') }}</p>
            </button>
          </div>
        </div>
        <div class="orch-pane">
          <span class="section-label">已选组件</span>
          <div class="empty" v-if="!selectedPlugins.length">从左侧勾选组件加入编排</div>
          <div v-for="p in selectedPlugins" :key="p.id" class="choice selected" style="margin-bottom:8px;cursor:default;transform:none">
            <div style="display:flex;justify-content:space-between;gap:8px;align-items:center">
              <h3 style="margin:0">{{ p.name }} <span class="muted">v{{ p.version }}</span></h3>
              <button class="btn" @click="removeSelected(p.id)">移除</button>
            </div>
            <p style="margin-top:8px">依赖：{{ p.dependencies?.length ? p.dependencies.join(', ') : '无' }}</p>
          </div>
          <div class="callout err" v-for="(e, i) in depErrors" :key="i">{{ e }}</div>
        </div>
      </div>

      <!-- Step2 -->
      <div v-else-if="step === 2" class="orch-split">
        <div class="orch-pane">
          <div class="toolbar" style="margin-bottom:12px;justify-content:space-between">
            <span class="section-label" style="margin:0">空闲主机池</span>
            <button class="btn" @click="autoAssign">一键自动分配</button>
          </div>
          <div class="choice" v-for="h in freeHosts" :key="h.id" style="margin-bottom:8px;cursor:default;transform:none">
            <h3>{{ h.name }}</h3>
            <p>{{ h.ip }} · Agent 正常 · {{ h.labels || '无标签' }}</p>
          </div>
          <div class="empty" v-if="!freeHosts.length">请先到「主机资源」纳管主机</div>
        </div>
        <div class="orch-pane">
          <span class="section-label">角色分配（插件 Schema 驱动）</span>
          <div v-for="p in selectedPlugins" :key="p.id" style="margin-bottom:16px">
            <h3 style="margin:0 0 10px;font-size:14px">{{ p.name }}</h3>
            <div v-for="r in rolesOf(p)" :key="r.key" class="field" style="margin-bottom:12px">
              <label>{{ r.name }} · 最少 {{ r.min }}</label>
              <div class="host-multi">
                <label v-for="h in hostOptions(r)" :key="h.id">
                  <input
                    type="checkbox"
                    :checked="(roleHosts[p.id][r.key] || []).includes(h.id)"
                    @change="setRoleHost(p.id, r.key, h.id, $event.target.checked)"
                  />
                  {{ h.name }} ({{ h.ip }})
                </label>
                <p class="muted" v-if="!hostOptions(r).length" style="margin:0">无匹配主机</p>
              </div>
            </div>
          </div>
          <div class="callout ok" v-if="!roleErrors.length && selectedPlugins.length">角色数量校验通过</div>
          <div class="callout err" v-for="(e, i) in roleErrors" :key="i">{{ e }}</div>
        </div>
      </div>

      <!-- Step3 -->
      <div v-else-if="step === 3" class="orch-split">
        <div class="orch-pane">
          <span class="section-label">组件树</span>
          <button
            v-for="p in selectedPlugins"
            :key="p.id"
            class="choice"
            style="width:100%;margin-bottom:8px"
            :class="{ selected: activeCfg === p.id }"
            @click="activeCfg = p.id"
          >
            <h3>{{ p.name }}</h3>
            <p>v{{ p.version }}</p>
          </button>
        </div>
        <div class="orch-pane" v-if="activeCfg">
          <div class="toolbar" style="justify-content:space-between;margin-bottom:12px">
            <span class="section-label" style="margin:0">{{ selectedPlugins.find(p => p.id === activeCfg)?.name }} 配置</span>
            <label style="font-size:13px;color:var(--sub)"><input type="checkbox" v-model="showAdvanced" /> 高级配置</label>
          </div>
          <div class="form-grid">
            <template v-for="(prop, key) in schemaOf(selectedPlugins.find(p => p.id === activeCfg)).properties" :key="key">
              <div
                class="field"
                v-if="prop['x-ui'] !== 'host-multi' && (showAdvanced || !isAdvanced(key, prop))"
              >
                <label>{{ prop.title || key }}</label>
                <input
                  v-model="configs[activeCfg][key]"
                  :type="fieldType(prop)"
                  @input="prop.type === 'integer' && (configs[activeCfg][key] = Number($event.target.value))"
                />
              </div>
            </template>
          </div>
          <div class="callout err" v-for="(e, i) in cfgErrors" :key="i">{{ e }}</div>
        </div>
      </div>

      <!-- Step4 -->
      <div v-else>
        <span class="section-label">本次编排汇总预览</span>
        <div class="launch-box" style="margin-top:0;margin-bottom:14px">
          <div>
            <strong>组件清单</strong>
            <p class="muted" style="margin:6px 0 0">{{ selectedPlugins.map(p => p.name).join('、') || '-' }}</p>
          </div>
        </div>
        <div class="table-wrap" style="margin-bottom:14px">
          <table class="table">
            <thead><tr><th>组件</th><th>角色</th><th>主机名</th><th>IP</th></tr></thead>
            <tbody>
              <tr v-for="(r, i) in assignmentRows" :key="i">
                <td>{{ r.plugin }}</td><td>{{ r.role }}</td><td>{{ r.host }}</td><td>{{ r.ip }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="muted" v-if="!assignmentRows.length" style="margin-bottom:14px">无可视化主机角色（部分插件为单机默认部署）</p>
        <ul class="summary-list" style="margin-bottom:16px">
          <li v-for="(l, i) in configSummary" :key="i">{{ l }}</li>
        </ul>
        <div class="form-grid">
          <div class="field"><label>任务名称</label><input v-model="taskName" /></div>
          <div class="field full"><label>备注（写入审计，选填）</label><textarea class="textarea" v-model="remark" /></div>
        </div>
        <div class="callout warn" v-if="confirmSubmit" style="margin-top:12px">请再次点击「提交部署」确认开始异步部署</div>
      </div>

      <div class="actions bar">
        <button class="btn" :disabled="step === 1" @click="step -= 1">上一步</button>
        <div class="toolbar">
          <button class="btn primary" v-if="step === 1" :disabled="!canNext1" @click="goStep(2)">下一步</button>
          <button class="btn primary" v-if="step === 2" :disabled="!canNext2" @click="goStep(3)">下一步</button>
          <button class="btn primary" v-if="step === 3" @click="goStep(4)">下一步</button>
          <button class="btn primary" v-if="step === 4" :disabled="loading || !canWrite" @click="submit">
            {{ loading ? '提交中…' : confirmSubmit ? '确认提交部署' : '提交部署' }}
          </button>
        </div>
      </div>
      <p class="error" v-if="error">{{ error }}</p>
    </div>
  </section>
</template>
