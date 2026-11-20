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

async function load() {
  try {
    const list = await api.hosts()
    host.value = list.find((h) => h.id === hid.value) || null
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)
watch(hid, load)
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>{{ host?.name || `主机#${hid}` }}</h2>
        <p class="muted" style="margin:6px 0 0">{{ host?.ip }} · {{ host?.labels || '无标签' }}</p>
      </div>
      <button class="btn" @click="router.push('/hosts')">返回资源池</button>
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
        <div class="stat-card"><div class="label">SSH</div><div class="value">{{ host.ssh_port || 22 }}</div></div>
        <div class="stat-card"><div class="label">Agent</div><div class="value" style="font-size:16px">正常</div></div>
        <div class="stat-card"><div class="label">备注</div><div class="value" style="font-size:14px">{{ host.remark || '-' }}</div></div>
      </div>
      <div v-else class="empty">{{ tab }} 数据采集由 Agent 上报（一期占位）</div>
    </template>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
