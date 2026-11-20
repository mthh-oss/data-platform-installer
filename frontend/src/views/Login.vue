<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, setToken } from '../api/client'

const router = useRouter()
const mode = ref('login') // login | setup
const username = ref('admin')
const password = ref('')
const error = ref('')
const loading = ref(false)

onMounted(async () => {
  try {
    const st = await api.authStatus()
    mode.value = st.initialized ? 'login' : 'setup'
  } catch (e) {
    error.value = e.message
  }
})

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const fn = mode.value === 'setup' ? api.setup : api.login
    const res = await fn({ username: username.value, password: password.value })
    setToken(res.access_token)
    router.replace('/')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="panel auth-panel">
    <h2 style="margin-top:0">{{ mode === 'setup' ? '初始化主账号' : '运维登录' }}</h2>
    <p class="muted" v-if="mode === 'setup'">
      首次使用请设置主账号。密码至少 8 位，需包含字母，不能全是数字。
    </p>
    <p class="muted" v-else>仅运维人员可进入控制台。</p>

    <div class="form-grid" style="margin-top:16px">
      <div class="field">
        <label>用户名</label>
        <input v-model="username" autocomplete="username" />
      </div>
      <div class="field">
        <label>密码</label>
        <input v-model="password" type="password" autocomplete="new-password" @keyup.enter="submit" />
      </div>
    </div>

    <div class="actions">
      <button class="btn primary launch" :disabled="loading" @click="submit">
        {{ loading ? '提交中…' : mode === 'setup' ? '创建主账号并进入' : '登录' }}
      </button>
    </div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
