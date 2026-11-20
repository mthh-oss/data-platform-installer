<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api/client'

const settings = ref(null)
const provider = ref('deepseek')
const apiKey = ref('')
const clusters = ref([])
const clusterId = ref(null)
const question = ref('请根据当前集群健康与异常日志做自检，给出可能原因与处理建议')
const answer = ref('')
const context = ref('')
const error = ref('')
const saving = ref(false)
const diagnosing = ref(false)

onMounted(async () => {
  try {
    settings.value = await api.aiSettings()
    provider.value = settings.value.provider || 'deepseek'
    clusters.value = await api.clusters()
    if (clusters.value.length) clusterId.value = clusters.value[0].id
  } catch (e) {
    error.value = e.message
  }
})

async function save() {
  error.value = ''
  saving.value = true
  try {
    settings.value = await api.saveAiSettings({
      provider: provider.value,
      api_key: apiKey.value,
    })
    apiKey.value = ''
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

async function runDiagnose() {
  error.value = ''
  diagnosing.value = true
  answer.value = ''
  try {
    const res = await api.diagnose({
      cluster_id: clusterId.value,
      question: question.value,
    })
    answer.value = res.answer
    context.value = res.context_summary
  } catch (e) {
    error.value = e.message
  } finally {
    diagnosing.value = false
  }
}
</script>

<template>
  <section class="panel">
    <h2 style="margin-top:0">AI 运维自检</h2>
    <p class="muted">当前支持 DeepSeek；Provider 可扩展（`backend/ai_providers/`）。</p>

    <div class="config-block">
      <h3>AI 设置</h3>
      <div class="form-grid">
        <div class="field">
          <label>Provider</label>
          <select v-model="provider" class="select" style="width:100%">
            <option v-for="p in (settings?.providers || [])" :key="p.id" :value="p.id">{{ p.name }} ({{ p.id }})</option>
          </select>
        </div>
        <div class="field">
          <label>API Key {{ settings?.has_api_key ? '（已配置，留空则不修改）' : '（必填）' }}</label>
          <input v-model="apiKey" type="password" placeholder="sk-..." />
        </div>
      </div>
      <div class="actions">
        <button class="btn primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存设置' }}</button>
      </div>
    </div>

    <div class="config-block">
      <h3>自检</h3>
      <div class="form-grid">
        <div class="field">
          <label>集群</label>
          <select v-model.number="clusterId" class="select" style="width:100%">
            <option v-for="c in clusters" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>问题描述</label>
          <textarea v-model="question" rows="3" class="textarea"></textarea>
        </div>
      </div>
      <div class="actions">
        <button class="btn primary launch" :disabled="diagnosing || !clusterId" @click="runDiagnose">
          {{ diagnosing ? '分析中…' : '开始自检' }}
        </button>
      </div>
      <p class="muted" v-if="context">上下文：{{ context }}</p>
      <div class="log" v-if="answer">{{ answer }}</div>
    </div>

    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
