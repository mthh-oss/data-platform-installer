<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import { rolesOf, schemaOf } from '../utils/plugin'

const route = useRoute()
const router = useRouter()
const pid = computed(() => String(route.params.pid))
const plugin = ref(null)
const error = ref('')

async function load() {
  try {
    const list = await api.plugins()
    plugin.value = list.find((p) => p.id === pid.value) || null
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)
watch(pid, load)
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>{{ plugin?.name || pid }}</h2>
        <p class="muted" style="margin:6px 0 0">插件元信息 / 角色 / 配置 Schema（通用渲染，无组件专属页）</p>
      </div>
      <button class="btn" @click="router.push('/plugins')">返回市场</button>
    </div>

    <div v-if="plugin">
      <div class="stat-row">
        <div class="stat-card"><div class="label">ID</div><div class="value" style="font-size:16px">{{ plugin.id }}</div></div>
        <div class="stat-card"><div class="label">版本</div><div class="value" style="font-size:16px">{{ plugin.version }}</div></div>
        <div class="stat-card"><div class="label">依赖</div><div class="value" style="font-size:14px">{{ plugin.dependencies?.join(', ') || '无' }}</div></div>
        <div class="stat-card"><div class="label">角色数</div><div class="value">{{ rolesOf(plugin).length }}</div></div>
      </div>
      <p>{{ plugin.description }}</p>

      <h3 style="font-size:14px">角色定义</h3>
      <table class="table">
        <thead><tr><th>角色</th><th>配置键</th><th>最少副本</th><th>主机标签</th></tr></thead>
        <tbody>
          <tr v-for="r in rolesOf(plugin)" :key="r.key">
            <td>{{ r.name }}</td><td>{{ r.key }}</td><td>{{ r.min }}</td><td>{{ r.hostLabel || '-' }}</td>
          </tr>
        </tbody>
      </table>

      <h3 style="font-size:14px">配置 Schema</h3>
      <pre class="log">{{ JSON.stringify(schemaOf(plugin), null, 2) }}</pre>
    </div>
    <div class="empty" v-else>插件不存在</div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
