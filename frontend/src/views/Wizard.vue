<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'

const router = useRouter()
const step = ref(1)
const plugins = ref([])
const selected = ref([])
const configs = reactive({})
const clusterName = ref(`demo-${Date.now().toString().slice(-6)}`)
const loading = ref(false)
const error = ref('')
const system = ref(null)

const selectedPlugins = computed(() =>
  plugins.value.filter((p) => selected.value.includes(p.id)),
)

const missingDeps = computed(() => {
  const miss = []
  for (const p of selectedPlugins.value) {
    for (const dep of p.dependencies || []) {
      if (!selected.value.includes(dep)) miss.push(`${p.id} → ${dep}`)
    }
  }
  return [...new Set(miss)]
})

onMounted(async () => {
  try {
    system.value = await api.health()
    plugins.value = await api.plugins()
    for (const p of plugins.value) {
      configs[p.id] = { ...p.default_config }
    }
  } catch (e) {
    error.value = e.message
  }
})

function toggle(id) {
  const plugin = plugins.value.find((p) => p.id === id)
  if (selected.value.includes(id)) {
    selected.value = selected.value.filter((x) => x !== id)
    return
  }
  const next = new Set(selected.value)
  next.add(id)
  // auto pick dependencies
  for (const dep of plugin?.dependencies || []) next.add(dep)
  selected.value = [...next]
}

function fieldType(prop) {
  return prop.type === 'integer' ? 'number' : 'text'
}

function goConfig() {
  error.value = ''
  if (!selected.value.length) {
    error.value = '请至少选择一个组件'
    return
  }
  if (missingDeps.value.length) {
    error.value = `缺少依赖：${missingDeps.value.join('；')}`
    return
  }
  if (!system.value?.docker_ok) {
    error.value = '当前机器 Docker 不可用，无法下载/启动组件。请先安装并启动 Docker。'
  }
  step.value = 2
}

async function oneClickStart() {
  error.value = ''
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
    <div class="hero-line">
      <h2 style="margin:0">一键搭建数据平台</h2>
      <p class="muted" style="margin:8px 0 0">挑选组件 → 填写配置 → 一键下载镜像并启动（体验对齐 Flink 式启动）</p>
    </div>

    <div class="steps" style="margin-top:18px">
      <div class="step" :class="{ active: step === 1, done: step > 1 }">1. 挑选组件</div>
      <div class="step" :class="{ active: step === 2 }">2. 配置并一键启动</div>
    </div>

    <p class="muted" v-if="system">
      Docker
      <span :class="system.docker_ok ? 'ok' : 'error'">{{ system.docker_ok ? '可用' : '不可用' }}</span>
      · 可选项：{{ (system.plugins || []).join(', ') || '无' }}
    </p>

    <div v-if="step === 1">
      <div class="grid" style="margin-top: 16px">
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
          <div class="deps" v-if="p.dependencies?.length">依赖：{{ p.dependencies.join(', ') }}（勾选时自动带上）</div>
        </button>
      </div>
      <div class="actions">
        <button class="btn primary" :disabled="!selected.length" @click="goConfig">下一步：配置</button>
      </div>
    </div>

    <div v-else>
      <div class="field" style="margin-bottom: 16px">
        <label>集群名称</label>
        <input v-model="clusterName" />
      </div>

      <div class="selected-tags">
        <span v-for="id in selected" :key="id" class="tag">{{ id }}</span>
      </div>

      <div v-for="p in selectedPlugins" :key="p.id" class="config-block">
        <h3>{{ p.name }} 配置</h3>
        <div class="form-grid">
          <div class="field" v-for="(prop, key) in (p.schema || p.config_schema).properties" :key="key">
            <label>{{ prop.title || key }}</label>
            <input
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
          <p class="muted" style="margin:6px 0 0">
            1) 下载所选组件镜像 &nbsp; 2) 按依赖顺序启动 &nbsp; 3) 进入进度页实时查看
          </p>
        </div>
        <div class="actions" style="margin:0">
          <button class="btn" @click="step = 1">返回挑选</button>
          <button class="btn primary launch" :disabled="loading" @click="oneClickStart">
            {{ loading ? '提交中…' : '一键下载并启动' }}
          </button>
        </div>
      </div>
    </div>

    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
