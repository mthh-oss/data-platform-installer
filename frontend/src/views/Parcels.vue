<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const clusterId = computed(() => Number(route.params.clusterId))
const plugins = ref([])
const error = ref('')

const cards = computed(() =>
  plugins.value.map((p) => ({
    id: p.id,
    name: p.name,
    version: p.version || p.default_config?.image?.split(':')[1] || 'latest',
    components: Object.keys(p.schema?.properties || p.config_schema?.properties || {}).slice(0, 6),
    status: '已下载',
  })),
)

onMounted(async () => {
  try {
    plugins.value = await api.plugins()
  } catch (e) {
    error.value = e.message
  }
})
</script>

<template>
  <section>
    <div class="panel" style="margin-bottom:12px">
      <div class="panel-title">
        <div>
          <h2>版本包管理</h2>
          <p class="muted" style="margin:6px 0 0">对标 Parcel：组件镜像/版本清单。激活走异步任务中心。</p>
        </div>
        <button class="btn primary" @click="router.push(`/deploy?clusterId=${clusterId}`)">部署/激活组件</button>
      </div>
    </div>

    <div class="grid">
      <div class="cluster-card" v-for="c in cards" :key="c.id" style="cursor:default">
        <h3>{{ c.name }}</h3>
        <p>版本 {{ c.version }}</p>
        <div class="meta">
          <span class="status-pill healthy">{{ c.status }}</span>
        </div>
        <p>组件项：{{ c.components.join(', ') || '默认配置' }}</p>
        <div class="actions">
          <button class="btn" disabled>分配</button>
          <button class="btn primary" @click="router.push(`/c/${clusterId}/tasks`)">激活跟踪</button>
        </div>
      </div>
    </div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
