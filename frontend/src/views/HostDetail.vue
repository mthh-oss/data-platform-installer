<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const hid = computed(() => Number(route.params.hid))
const tab = ref('overview')
const host = ref(null)
const error = ref('')
const verifying = ref(false)

async function load() {
  error.value = ''
  try {
    const list = await api.hosts()
    host.value = list.find((h) => h.id === hid.value) || null
  } catch (e) {
    error.value = e.message
  }
}

async function reverify() {
  verifying.value = true
  error.value = ''
  try {
    host.value = await api.verifyHost(hid.value)
  } catch (e) {
    error.value = e.message
    await load()
  } finally {
    verifying.value = false
  }
}

function agentText(h) {
  if (!h) return '-'
  if (h.agent_status === 'verified') return 'SSH 已校验'
  if (h.agent_status === 'offline') return 'SSH 离线'
  if (h.has_password) return '有密码但未校验'
  return '无 SSH 密码（未真正接入）'
}

onMounted(load)
watch(hid, load)
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>{{ host?.name || `主机#${hid}` }}</h2>
        <p class="muted" style="margin:6px 0 0">
          {{ host?.ip }} · {{ host?.labels || '无标签' }} · {{ agentText(host) }}
        </p>
      </div>
      <div class="toolbar">
        <button class="btn" :disabled="verifying || !host?.has_password" @click="reverify">
          {{ verifying ? '校验中…' : '重新 SSH 校验' }}
        </button>
        <button class="btn" @click="router.push('/hosts')">返回资源池</button>
      </div>
    </div>

    <div class="callout warn" v-if="host && (!host.has_password || host.agent_status !== 'verified')" style="margin-bottom:14px">
      当前页面只是库存档案，不是已登录该主机的 Shell。
      未配置或未通过 SSH 密码校验前，不能安装 Agent，也不能当作已纳管机器使用。
    </div>

    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'overview' }" @click="tab = 'overview'">概览</button>
      <button class="tab" :class="{ active: tab === 'disk' }" @click="tab = 'disk'">磁盘</button>
      <button class="tab" :class="{ active: tab === 'roles' }" @click="tab = 'roles'">角色</button>
      <button class="tab" :class="{ active: tab === 'monitor' }" @click="tab = 'monitor'">监控</button>
      <button class="tab" :class="{ active: tab === 'logs' }" @click="tab = 'logs'">Agent 日志</button>
    </div>
    <div v-if="!host" class="empty">主机不存在</div>
    <template v-else>
      <div v-if="tab === 'overview'" class="stat-row">
        <div class="stat-card"><div class="label">IP</div><div class="value" style="font-size:16px">{{ host.ip }}</div></div>
        <div class="stat-card"><div class="label">SSH</div><div class="value" style="font-size:16px">{{ host.ssh_user }}@{{ host.ssh_port || 22 }}</div></div>
        <div class="stat-card"><div class="label">凭据</div><div class="value" style="font-size:16px">{{ host.has_password ? '已加密存储' : '未配置' }}</div></div>
        <div class="stat-card"><div class="label">校验状态</div><div class="value" style="font-size:16px">{{ agentText(host) }}</div></div>
      </div>
      <div v-else class="empty">{{ tab }} 数据采集需 Agent 在线（SSH 校验通过后安装）</div>
    </template>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
