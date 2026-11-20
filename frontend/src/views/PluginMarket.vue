<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { rolesOf } from '../utils/plugin'

const router = useRouter()
const plugins = ref([])
const disabled = ref(JSON.parse(localStorage.getItem('dpi_plugin_disabled') || '[]'))
const q = ref('')
const error = ref('')
const uploadMsg = ref('')

const cards = computed(() =>
  plugins.value
    .filter((p) => !q.value || `${p.name}${p.id}${p.description}`.includes(q.value.trim()))
    .map((p) => ({
      ...p,
      enabled: !disabled.value.includes(p.id),
      roles: rolesOf(p).map((r) => r.name),
    })),
)

async function load() {
  try {
    plugins.value = await api.plugins()
  } catch (e) {
    error.value = e.message
  }
}

function persistDisabled() {
  localStorage.setItem('dpi_plugin_disabled', JSON.stringify(disabled.value))
}

function toggle(id) {
  if (disabled.value.includes(id)) disabled.value = disabled.value.filter((x) => x !== id)
  else disabled.value = [...disabled.value, id]
  persistDisabled()
}

function onUpload(e) {
  const file = e.target.files?.[0]
  if (!file) return
  // 一期：前端校验提示；实际上传接口二期对接 plugin.zip
  if (!file.name.endsWith('.zip')) {
    uploadMsg.value = '请上传 plugin.zip（含 meta.json / roles.json / config-schema.json 等）'
    return
  }
  uploadMsg.value = `已选择 ${file.name}。后端插件包校验与热加载接口二期接入；当前内置插件仍来自服务端 registry。`
}

onMounted(load)
</script>

<template>
  <section>
    <div class="page-hero">
      <div>
        <h1>插件市场</h1>
        <p class="lead">独立扩展入口。上传合法插件后出现在编排 Step1；禁用只影响新编排，存量实例不受影响。</p>
      </div>
      <div class="toolbar">
        <input v-model="q" class="select" style="width:180px" placeholder="搜索插件" />
        <label class="btn primary" style="cursor:pointer">
          上传插件包
          <input type="file" accept=".zip" style="display:none" @change="onUpload" />
        </label>
      </div>
    </div>

    <div class="panel">
      <p class="muted" style="margin:0 0 14px">包规范：meta.json · roles.json · config-schema.json · deploy.sh · uninstall.sh · metrics.json · alert.json</p>
      <p class="ok" v-if="uploadMsg">{{ uploadMsg }}</p>
      <div class="grid">
        <div class="cluster-card" v-for="p in cards" :key="p.id" style="cursor:default;transform:none">
          <div class="card-icon">{{ p.name.slice(0, 2) }}</div>
          <div style="display:flex;justify-content:space-between;gap:8px;align-items:flex-start">
            <h3>{{ p.name }}</h3>
            <span class="status-pill" :class="p.enabled ? 'healthy' : 'unknown'">{{ p.enabled ? '已启用' : '禁用' }}</span>
          </div>
          <p style="margin-top:6px">v{{ p.version }} · {{ p.id }}</p>
          <p style="margin-top:8px">{{ p.description || '无简介' }}</p>
          <p style="margin-top:8px">角色：{{ p.roles.join('、') }}</p>
          <div class="actions">
            <button class="btn" @click="router.push(`/plugins/${p.id}`)">详情</button>
            <button class="btn" @click="toggle(p.id)">{{ p.enabled ? '禁用' : '启用' }}</button>
          </div>
        </div>
      </div>
      <p class="error" v-if="error">{{ error }}</p>
    </div>
  </section>
</template>
