<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const clusterId = computed(() => Number(route.params.clusterId))
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
      <button class="btn" @click="router.push(`/c/${clusterId}/hosts`)">返回列表</button>
    </div>

    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'overview' }" @click="tab = 'overview'">概览</button>
      <button class="tab" :class="{ active: tab === 'disk' }" @click="tab = 'disk'">磁盘分区</button>
      <button class="tab" :class="{ active: tab === 'proc' }" @click="tab = 'proc'">进程列表</button>
      <button class="tab" :class="{ active: tab === 'roles' }" @click="tab = 'roles'">角色实例</button>
      <button class="tab" :class="{ active: tab === 'monitor' }" @click="tab = 'monitor'">监控</button>
      <button class="tab" :class="{ active: tab === 'logs' }" @click="tab = 'logs'">主机日志</button>
    </div>

    <div v-if="!host" class="empty">主机不存在或已删除</div>
    <template v-else>
      <div v-if="tab === 'overview'" class="stat-row">
        <div class="stat-card"><div class="label">IP</div><div class="value" style="font-size:16px">{{ host.ip }}</div></div>
        <div class="stat-card"><div class="label">SSH</div><div class="value">{{ host.ssh_port || 22 }}</div></div>
        <div class="stat-card"><div class="label">Agent</div><div class="value" style="font-size:16px">在线</div></div>
        <div class="stat-card"><div class="label">备注</div><div class="value" style="font-size:14px">{{ host.remark || '-' }}</div></div>
      </div>
      <div v-else-if="tab === 'disk'" class="empty">磁盘分区信息一期占位（待 Agent 采集）</div>
      <div v-else-if="tab === 'proc'" class="empty">管控进程列表一期占位</div>
      <div v-else-if="tab === 'roles'">
        <p>当前标签推断角色：<strong>{{ host.labels || '未标记' }}</strong></p>
        <p class="muted">fe → Doris FE；be → Doris BE；其他标签用于筛选。</p>
      </div>
      <div v-else-if="tab === 'monitor'" class="empty">主机 CPU/内存/磁盘/网络时序图二期接入</div>
      <div v-else class="empty">Agent 日志检索二期接入</div>
    </template>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
