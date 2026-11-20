<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const clusterId = computed(() => Number(route.params.clusterId))
const plugins = ref([])
const current = ref(null)
const advanced = ref(false)
const preview = ref(false)
const error = ref('')

const propsList = computed(() => {
  const p = current.value
  if (!p) return []
  const schema = p.schema || p.config_schema || { properties: {} }
  return Object.entries(schema.properties || {}).map(([key, meta]) => ({
    key,
    title: meta.title || key,
    desc: meta.description || '',
    def: p.default_config?.[key],
    advanced: /password|secret|advanced|jvm|extra/i.test(key),
  }))
})

const visible = computed(() =>
  propsList.value.filter((x) => advanced.value || !x.advanced),
)

onMounted(async () => {
  try {
    plugins.value = await api.plugins()
    current.value = plugins.value[0] || null
  } catch (e) {
    error.value = e.message
  }
})

function save() {
  preview.value = true
}
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>配置中心</h2>
        <p class="muted" style="margin:6px 0 0">左侧服务树 · 右侧表单；保存前预览变更</p>
      </div>
      <div class="toolbar">
        <label style="font-size:13px;color:var(--sub)">
          <input type="checkbox" v-model="advanced" /> 显示高级配置
        </label>
        <button class="btn primary" @click="save">预览并保存</button>
      </div>
    </div>

    <div class="jobs-layout">
      <div>
        <button
          v-for="p in plugins"
          :key="p.id"
          class="choice"
          style="width:100%;margin-bottom:8px"
          :class="{ selected: current?.id === p.id }"
          @click="current = p"
        >
          <h3>{{ p.name }}</h3>
          <p>{{ p.id }}</p>
        </button>
      </div>
      <div>
        <div class="field" v-for="item in visible" :key="item.key" style="margin-bottom:12px">
          <label>{{ item.title }} <span class="muted" v-if="item.advanced">(高级)</span></label>
          <input :value="item.def" readonly />
          <p class="muted" style="margin:4px 0 0">{{ item.desc || '默认值只读预览；实际修改请走部署向导。' }}</p>
        </div>
        <div class="empty" v-if="!visible.length">暂无配置项</div>
        <div v-if="preview" class="launch-box">
          <div>
            <strong>保存后是否重启服务？</strong>
            <p class="muted" style="margin:6px 0 0">高危操作将写入审计，并进入任务中心跟踪。</p>
          </div>
          <div class="actions" style="margin:0">
            <button class="btn" @click="preview = false">仅保存</button>
            <button class="btn primary" @click="router.push(`/c/${clusterId}/tasks`)">滚动重启</button>
          </div>
        </div>
      </div>
    </div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
