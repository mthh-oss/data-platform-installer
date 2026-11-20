<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api/client'

const open = ref(false)
const input = ref('')
const loading = ref(false)
const error = ref('')
const configured = ref(true)
const instances = ref([])
const instanceId = ref(null)
const withContext = ref(true)
const messages = ref([
  { role: 'assistant', text: '我是 DataStack 运维诊断助手。只给建议，不直接执行启停/卸载/改配置。' },
])

onMounted(async () => {
  try {
    const ai = await api.aiSettings()
    configured.value = !!ai.has_api_key && ai.enabled !== false
    instances.value = await api.clusters()
    if (instances.value.length) instanceId.value = instances.value[0].id
  } catch {
    configured.value = false
  }
})

async function send(text, mode = 'chat') {
  if (!configured.value) {
    messages.value.push({ role: 'assistant', text: 'AI 助手未配置，请联系管理员在「平台设置 → AI 助手」填写 Provider。' })
    return
  }
  const content = (text || input.value || '').trim()
  if (!content || loading.value) return
  messages.value.push({ role: 'user', text: content })
  input.value = ''
  loading.value = true
  error.value = ''
  try {
    let answer = ''
    if (mode === 'diagnose') {
      const res = await api.diagnose({ cluster_id: instanceId.value, question: content })
      answer = res.answer
    } else {
      const res = await api.chat({
        message: content,
        cluster_id: instanceId.value,
        with_context: withContext.value,
      })
      answer = res.answer
    }
    messages.value.push({ role: 'assistant', text: answer })
  } catch (e) {
    error.value = e.message
    messages.value.push({ role: 'assistant', text: `调用失败：${e.message}` })
  } finally {
    loading.value = false
  }
}

function selfCheck() {
  send('请根据当前实例健康与异常日志做诊断，给出可能原因与修复建议（不要执行变更）', 'diagnose')
}
</script>

<template>
  <button v-if="!open" class="ai-ball" :title="configured ? 'AI 助手' : 'AI 未配置'" @click="open = true">
    AI
  </button>
  <div v-else class="ai-panel">
    <div class="ai-panel-head">
      <strong>DataStack AI 助手</strong>
      <div class="actions" style="margin:0">
        <button class="btn" @click="selfCheck" :disabled="loading || !configured">诊断</button>
        <button class="btn" @click="open = false">最小化</button>
      </div>
    </div>
    <div class="ai-panel-body">
      <div v-for="(m, i) in messages" :key="i" class="ai-msg" :class="m.role">
        <div class="bubble">{{ m.text }}</div>
      </div>
    </div>
    <div class="ai-panel-foot">
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        <select v-model.number="instanceId" class="select" style="flex:1;min-width:140px">
          <option v-for="c in instances" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <label style="font-size:12px;color:var(--sub)"><input type="checkbox" v-model="withContext" /> 带上下文</label>
      </div>
      <div style="display:flex;gap:8px">
        <input v-model="input" class="select" placeholder="输入问题…" @keyup.enter="send()" />
        <button class="btn primary" :disabled="loading" @click="send()">发送</button>
      </div>
      <p class="error" v-if="error" style="margin:0">{{ error }}</p>
    </div>
  </div>
</template>
