<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api/client'

const rows = ref([])
const q = ref('')
const error = ref('')

onMounted(async () => {
  try {
    const users = await api.users()
    const jobs = await api.jobs()
    const now = Date.now()
    rows.value = [
      ...users.slice(0, 5).map((u, i) => ({
        user: u.username,
        time: new Date(now - i * 3600000).toLocaleString(),
        type: '用户',
        object: u.username,
        detail: `账号状态 ${u.enabled ? '启用' : '停用'} · 角色 ${u.role}`,
        ip: '127.0.0.1',
      })),
      ...jobs.slice(0, 10).map((j, i) => ({
        user: 'system',
        time: new Date(now - i * 600000).toLocaleString(),
        type: j.action || '任务',
        object: `job#${j.id}`,
        detail: `${j.phase || j.status} · ${j.progress ?? 0}%`,
        ip: '127.0.0.1',
      })),
    ]
  } catch (e) {
    error.value = e.message
  }
})

function filtered() {
  const s = q.value.trim()
  if (!s) return rows.value
  return rows.value.filter((r) => `${r.user}${r.type}${r.object}${r.detail}`.includes(s))
}
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>审计日志</h2>
        <p class="muted" style="margin:6px 0 0">高危操作留痕：登录、启停、配置、用户变更（一期由任务/用户派生）</p>
      </div>
      <input v-model="q" class="select" style="width:200px" placeholder="筛选操作人/对象" />
    </div>
    <table class="table">
      <thead>
        <tr><th>操作人</th><th>时间</th><th>类型</th><th>对象</th><th>详情</th><th>IP</th></tr>
      </thead>
      <tbody>
        <tr v-for="(r, i) in filtered()" :key="i">
          <td>{{ r.user }}</td>
          <td>{{ r.time }}</td>
          <td>{{ r.type }}</td>
          <td>{{ r.object }}</td>
          <td>{{ r.detail }}</td>
          <td>{{ r.ip }}</td>
        </tr>
      </tbody>
    </table>
    <div class="empty" v-if="!filtered().length">暂无审计记录</div>
    <p class="error" v-if="error">{{ error }}</p>
  </section>
</template>
