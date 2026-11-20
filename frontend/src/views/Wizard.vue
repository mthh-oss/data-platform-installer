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
  if (selected.value.includes(id)) {
    selected.value = selected.value.filter((x) => x !== id)
  } else {
    selected.value = [...selected.value, id]
  }
}

function fieldType(prop) {
  return prop.type === 'integer' ? 'number' : 'text'
}

async function submit() {
  error.value = ''
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
    <div class="steps">
      <div class="step" :class="{ active: step === 1, done: step > 1 }">1. 选择平台</div>
      <div class="step" :class="{ active: step === 2, done: step > 2 }">2. 填写配置</div>
      <div class="step" :class="{ active: step === 3 }">3. 确认部署</div>
    </div>

    <p class="muted" v-if="system">
      控制面正常 · Docker {{ system.docker_ok ? '可用' : '不可用' }} ·
      已加载插件 {{ (system.plugins || []).join(', ') || '无' }}
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
          <div class="deps" v-if="p.dependencies?.length">依赖：{{ p.dependencies.join(', ') }}</div>
        </button>
      </div>
      <div class="actions">
        <button class="btn primary" :disabled="!selected.length" @click="step = 2">下一步</button>
      </div>
    </div>

    <div v-else-if="step === 2">
      <div class="field" style="margin-bottom: 16px">
        <label>集群名称</label>
        <input v-model="clusterName" />
      </div>
      <div v-for="p in selectedPlugins" :key="p.id" style="margin-bottom: 22px">
        <h3 style="margin: 0 0 10px">{{ p.name }}</h3>
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
      <div class="actions">
        <button class="btn" @click="step = 1">上一步</button>
        <button class="btn primary" @click="step = 3">下一步</button>
      </div>
    </div>

    <div v-else>
      <p class="muted">将创建集群并异步执行 <code>docker compose up -d</code>。</p>
      <ul class="summary-list">
        <li>名称：{{ clusterName }}</li>
        <li>平台：{{ selected.join(', ') }}</li>
      </ul>
      <div class="actions">
        <button class="btn" @click="step = 2">上一步</button>
        <button class="btn primary" :disabled="loading" @click="submit">
          {{ loading ? '提交中…' : '开始部署' }}
        </button>
      </div>
    </div>

    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
