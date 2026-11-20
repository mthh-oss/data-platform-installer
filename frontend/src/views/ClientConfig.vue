<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'

const route = useRoute()
const clusterId = computed(() => Number(route.params.clusterId))
const plugins = ref([])
const service = ref('doris')
const msg = ref('')

onMounted(async () => {
  try {
    plugins.value = await api.plugins()
    if (plugins.value.length) service.value = plugins.value[0].id
  } catch {
    /* ignore */
  }
})

function generate() {
  const blob = new Blob(
    [
      `# client config for ${service.value}\n`,
      `# cluster=${clusterId.value}\n`,
      `# place under /opt/data-platform/client/${service.value}/\n`,
      `SERVICE=${service.value}\n`,
      `GENERATED_AT=${new Date().toISOString()}\n`,
    ],
    { type: 'text/plain' },
  )
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${service.value}-client-config.env`
  a.click()
  URL.revokeObjectURL(url)
  msg.value = '已生成并下载客户端配置包（骨架文件）'
}
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>客户端配置</h2>
        <p class="muted" style="margin:6px 0 0">给开发/数仓人员一键下载连接配置，不必翻服务详情。</p>
      </div>
    </div>
    <div class="form-grid" style="max-width:520px">
      <div class="field">
        <label>服务</label>
        <select v-model="service" class="select">
          <option v-for="p in plugins" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
      <div class="field full">
        <label>说明</label>
        <p class="muted" style="margin:0">配置包用途：客户端连接参数。建议部署路径：/opt/data-platform/client/&lt;服务&gt;/</p>
      </div>
    </div>
    <div class="actions">
      <button class="btn primary" @click="generate">生成并下载</button>
    </div>
    <p class="ok" v-if="msg">{{ msg }}</p>
  </section>
</template>
