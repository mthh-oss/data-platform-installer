<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, getUser } from '../api/client'

const router = useRouter()
const step = ref(1)
const plugins = ref([])
const hosts = ref([])
const selected = ref([])
const configs = reactive({})
const clusterName = ref(`demo-${Date.now().toString().slice(-6)}`)
const loading = ref(false)
const error = ref('')
const system = ref(null)
const me = ref(getUser())

const selectedPlugins = computed(() =>
  plugins.value.filter((p) => selected.value.includes(p.id)),
)

const canWrite = computed(() => me.value?.role === 'admin' || me.value?.role === 'operator')

onMounted(async () => {
  try {
    me.value = await api.me()
    system.value = await api.health()
    plugins.value = await api.plugins()
    hosts.value = await api.hosts()
    for (const p of plugins.value) {
      configs[p.id] = { ...p.default_config }
      // ensure array fields
      for (const [k, meta] of Object.entries(p.schema?.properties || p.config_schema?.properties || {})) {
        if (meta.type === 'array' && !Array.isArray(configs[p.id][k])) configs[p.id][k] = []
      }
    }
  } catch (e) {
    error.value = e.message
  }
})

function schemaOf(p) {
  return p.schema || p.config_schema || { properties: {} }
}

function toggle(id) {
  const plugin = plugins.value.find((p) => p.id === id)
  if (selected.value.includes(id)) {
    selected.value = selected.value.filter((x) => x !== id)
    return
  }
  const next = new Set(selected.value)
  next.add(id)
  for (const dep of plugin?.dependencies || []) next.add(dep)
  selected.value = [...next]
}

function fieldType(prop) {
  return prop.type === 'integer' ? 'number' : 'text'
}

function toggleHost(pid, key, hostId) {
  const arr = Array.isArray(configs[pid][key]) ? [...configs[pid][key]] : []
  const i = arr.indexOf(hostId)
  if (i >= 0) arr.splice(i, 1)
  else arr.push(hostId)
  configs[pid][key] = arr
}

function hostOptions(prop) {
  const label = (prop['x-host-label'] || '').toLowerCase()
  if (!label) return hosts.value.filter((h) => h.enabled)
  return hosts.value.filter((h) => h.enabled && String(h.labels || '').toLowerCase().includes(label))
}

function goConfig() {
  error.value = ''
  if (!canWrite.value) {
    error.value = '当前账号只读，无法部署'
    return
  }
  if (!selected.value.length) {
    error.value = '请至少选择一个组件'
    return
  }
  step.value = 2
}

async function oneClickStart() {
  error.value = ''
  if (!canWrite.value) {
    error.value = '当前账号只读，无法部署'
    return
  }
  if (!system.value?.docker_ok) {
    error.value = 'Docker 不可用，无法一键下载并启动。'
    return
  }
  loading.value = true
  try {
    const body = {
      name: clusterName.value,
      platforms: selected.value,
      configs: Object.fromEntries(selected.value.map((id) => [id, configs[id]])),
    }
    const cluster = await api.createCluster(body)
    const job = await api.deploy(cluster.id)
    router.push(`/jobs/${job.id}`)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="panel">
    <h2 style="margin-top:0">一键搭建</h2>
    <p class="muted">挑选组件并配置，一键下载镜像并启动。Doris 可分别选择 FE / BE 机器。</p>

    <div class="steps" style="margin-top:14px">
      <div class="step" :class="{ active: step === 1, done: step > 1 }">1. 挑选组件</div>
      <div class="step" :class="{ active: step === 2 }">2. 配置并启动</div>
    </div>

    <p class="muted" v-if="system">
      Docker
      <span :class="system.docker_ok ? 'ok' : 'error'">{{ system.docker_ok ? '可用' : '不可用' }}</span>
      · 角色 {{ me?.role }}
    </p>

    <div v-if="step === 1">
      <div class="grid" style="margin-top: 12px">
        <button
          v-for="p in plugins"
          :key="p.id"
          class="choice"
          :class="{ selected: selected.includes(p.id) }"
          type="button"
          @click="toggle(p.id)"
        >
          <h3>{{ p.name }}</h3>
          <p>{{ p.description || p.id }} · v{{ p.version }}</p>
          <div class="deps" v-if="p.dependencies?.length">依赖：{{ p.dependencies.join(', ') }}</div>
        </button>
      </div>
      <div class="actions">
        <button class="btn primary" :disabled="!selected.length" @click="goConfig">下一步：配置</button>
      </div>
    </div>

    <div v-else>
      <div class="field" style="margin-bottom: 12px">
        <label>集群名称</label>
        <input v-model="clusterName" />
      </div>
      <div class="selected-tags">
        <span v-for="id in selected" :key="id" class="tag">{{ id }}</span>
      </div>

      <div v-for="p in selectedPlugins" :key="p.id" class="config-block">
        <h3>{{ p.name }} 配置</h3>
        <div class="form-grid">
          <div class="field" v-for="(prop, key) in schemaOf(p).properties" :key="key">
            <label>{{ prop.title || key }}</label>

            <div v-if="prop['x-ui'] === 'host-multi'" class="host-multi">
              <label v-for="h in hostOptions(prop)" :key="h.id">
                <input
                  type="checkbox"
                  :checked="(configs[p.id][key] || []).includes(h.id)"
                  @change="toggleHost(p.id, key, h.id)"
                />
                {{ h.name }} ({{ h.ip }}) {{ h.labels ? '['+h.labels+']' : '' }}
              </label>
              <p class="muted" v-if="!hostOptions(prop).length" style="margin:0">
                暂无可用主机，请先到「设置 → 主机库存」添加。
              </p>
            </div>

            <input
              v-else
              v-model="configs[p.id][key]"
              :type="fieldType(prop)"
              @input="prop.type === 'integer' && (configs[p.id][key] = Number($event.target.value))"
            />
          </div>
        </div>
      </div>

      <div class="launch-box">
        <div>
          <strong>将执行</strong>
          <p class="muted" style="margin:6px 0 0">下载镜像 → 按依赖启动 → 进度页跟踪</p>
        </div>
        <div class="actions" style="margin:0">
          <button class="btn" @click="step = 1">返回挑选</button>
          <button class="btn primary launch" :disabled="loading || !canWrite" @click="oneClickStart">
            {{ loading ? '提交中…' : '一键下载并启动' }}
          </button>
        </div>
      </div>
    </div>

    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
