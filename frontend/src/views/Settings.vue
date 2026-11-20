<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api/client'

const ai = ref({ provider: 'deepseek', has_api_key: false, providers: [] })
const apiKey = ref('')
const saving = ref(false)
const error = ref('')
const okMsg = ref('')

onMounted(async () => {
  try {
    ai.value = await api.aiSettings()
  } catch (e) {
    error.value = e.message
  }
})

async function save() {
  saving.value = true
  error.value = ''
  okMsg.value = ''
  try {
    ai.value = await api.saveAiSettings({ provider: ai.value.provider, api_key: apiKey.value })
    apiKey.value = ''
    okMsg.value = '已保存'
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>平台设置</h2>
        <p class="muted" style="margin:6px 0 0">AI / 主题 / 通知等；人员关系见「系统管理 → 人员关系」。</p>
      </div>
    </div>

    <div class="tabs">
      <button class="tab active">AI 配置</button>
    </div>

    <div class="form-grid">
      <div class="field">
        <label>模型 Provider</label>
        <select class="select" v-model="ai.provider">
          <option v-for="p in ai.providers" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
      <div class="field">
        <label>API Key {{ ai.has_api_key ? '（已配置，留空不改）' : '' }}</label>
        <input v-model="apiKey" type="password" placeholder="DeepSeek Key" />
      </div>
    </div>
    <div class="actions">
      <button class="btn primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
    </div>
    <p class="ok" v-if="okMsg">{{ okMsg }}</p>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
