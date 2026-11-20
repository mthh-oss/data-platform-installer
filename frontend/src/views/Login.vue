<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, setToken, setUser } from '../api/client'

const router = useRouter()
const mode = ref('login')
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
    setUser({
      username: res.username,
      role: res.role,
      display_name: res.display_name || res.username,
    })
    router.replace('/')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-wrap">
    <section class="auth-card">
      <h1>{{ mode === 'setup' ? '初始化管理员' : '登录数据平台' }}</h1>
      <p class="sub">
        {{ mode === 'setup'
          ? '首次使用请创建主账号。密码至少 8 位，需含字母，不能全是数字。'
          : '请使用已授权账号登录。' }}
      </p>
      <div class="form-grid" style="grid-template-columns:1fr">
        <div class="field">
          <label>用户名</label>
          <input v-model="username" autocomplete="username" />
        </div>
        <div class="field">
          <label>密码</label>
          <input v-model="password" type="password" autocomplete="current-password" @keyup.enter="submit" />
        </div>
      </div>
      <div class="actions">
        <button class="btn primary" style="width:100%" :disabled="loading" @click="submit">
          {{ loading ? '提交中…' : mode === 'setup' ? '创建并进入' : '登录' }}
        </button>
      </div>
      <p class="error" v-if="error">{{ error }}</p>
    </section>
  </div>
</template>
