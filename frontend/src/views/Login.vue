<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, setToken, setUser } from '../api/client'

const router = useRouter()
const mode = ref('login')
const username = ref('admin')
const password = ref('')
const authType = ref('local')
const remember = ref(true)
const error = ref('')
const loading = ref(false)

onMounted(async () => {
  try {
    const st = await api.authStatus()
    mode.value = st.initialized ? 'login' : 'setup'
    const saved = localStorage.getItem('dpi_remember_user')
    if (saved) username.value = saved
  } catch (e) {
    error.value = e.message
  }
})

async function submit() {
  error.value = ''
  if (!username.value.trim()) {
    error.value = '请输入账号'
    return
  }
  if (!password.value) {
    error.value = '请输入密码'
    return
  }
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
    if (remember.value) localStorage.setItem('dpi_remember_user', username.value)
    else localStorage.removeItem('dpi_remember_user')
    router.replace('/workbench')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-wrap">
    <aside class="auth-brand">
      <div class="brand-mark" style="width:40px;height:40px;font-size:14px;margin-bottom:16px">DS</div>
      <h1>DataStack</h1>
      <p>插件化大数据底座编排平台。勾选组件、分配主机、一键部署；插件市场扩展，实例运维配套。</p>
    </aside>
    <div class="auth-form-wrap">
      <section class="auth-card">
        <h2>{{ mode === 'setup' ? '初始化管理员' : '账号登录' }}</h2>
        <p class="sub">
          {{ mode === 'setup'
            ? '首次使用请创建主账号。密码至少 8 位，需含字母。'
            : '本地账号登录；LDAP 在平台设置中对接。' }}
        </p>
        <div class="form-grid" style="grid-template-columns:1fr">
          <div class="field"><label>账号</label><input v-model="username" autocomplete="username" /></div>
          <div class="field">
            <label>密码</label>
            <input v-model="password" type="password" autocomplete="current-password" @keyup.enter="submit" />
          </div>
          <div class="field" v-if="mode === 'login'">
            <label>登录方式</label>
            <select v-model="authType">
              <option value="local">本地账号</option>
              <option value="ldap" disabled>LDAP（设置启用后可用）</option>
            </select>
          </div>
          <label v-if="mode === 'login'" style="display:flex;gap:8px;align-items:center;font-size:13px;color:var(--sub)">
            <input type="checkbox" v-model="remember" /> 记住账号
          </label>
        </div>
        <div class="actions">
          <button class="btn primary" style="width:100%" :disabled="loading" @click="submit">
            {{ loading ? '提交中…' : mode === 'setup' ? '创建并进入' : '登录' }}
          </button>
        </div>
        <p class="error" v-if="error">{{ error }}</p>
      </section>
    </div>
  </div>
</template>
