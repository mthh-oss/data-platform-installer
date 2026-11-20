<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api/client'

const open = ref(false)
const input = ref('')
const loading = ref(false)
const error = ref('')
const clusters = ref([])
const clusterId = ref(null)
const withContext = ref(true)
const messages = ref([
  { role: 'assistant', text: '你好，我是运维助手。可自检集群，也可直接粘贴报错让我帮你看。' },
])

onMounted(async () => {
  try {
    clusters.value = await api.clusters()
    if (clusters.value.length) clusterId.value = clusters.value[0].id
  } catch {
    /* ignore until logged in */
  }
})

async function send(text, mode = 'chat') {
  const content = (text || input.value || '').trim()
  if (!content || loading.value) return
  messages.value.push({ role: 'user', text: content })
  input.value = ''
  loading.value = true
  error.value = ''
  try {
    let answer = ''
    if (mode === 'diagnose') {
      const res = await api.diagnose({
        cluster_id: clusterId.value,
        question: content,
      })
      answer = res.answer
    } else {
      const res = await api.chat({
        message: content,
        cluster_id: clusterId.value,
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
  send('请根据当前集群健康与异常日志做自检，给出可能原因与处理建议', 'diagnose')
}
</script>

<template>
  <button v-if="!open" class="ai-ball" title="AI 助手" @click="open = true">AI</button>
  <div v-else class="ai-panel">
    <div class="ai-panel-head">
      <strong>AI 运维助手</strong>
      <div class="actions" style="margin:0">
        <button class="btn" @click="selfCheck" :disabled="loading">自检</button>
        <button class="btn" @click="open = false">缩成球</button>
      </div>
    </div>
    <div class="ai-panel-body">
      <div v-for="(m, i) in messages" :key="i" class="ai-msg" :class="m.role">
        <div class="bubble">{{ m.text }}</div>
      </div>
    </div>
    <div class="ai-panel-foot">
      <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
        <select v-model.number="clusterId" class="select" style="flex:1; min-width:140px">
          <option v-for="c in clusters" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <label style="font-size:12px;color:var(--muted);display:flex;gap:4px;align-items:center;">
          <input type="checkbox" v-model="withContext" /> 附带集群上下文
        </label>
      </div>
      <textarea
        class="textarea"
        rows="3"
        v-model="input"
        placeholder="粘贴报错 / 描述问题，回车发送可用 Ctrl+Enter"
        @keydown.ctrl.enter="send()"
      />
      <button class="btn primary" :disabled="loading" @click="send()">{{ loading ? '思考中…' : '发送' }}</button>
      <p class="error" v-if="error" style="margin:0">{{ error }}</p>
    </div>
  </div>
</template>
