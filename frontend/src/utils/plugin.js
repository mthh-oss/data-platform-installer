/** 插件驱动通用工具：禁止写死组件专属逻辑 */

export function schemaOf(plugin) {
  return plugin?.schema || plugin?.config_schema || { properties: {}, required: [] }
}

/** 从 config-schema 推导角色（x-ui=host-multi），无则回退「主实例」 */
export function rolesOf(plugin) {
  const props = schemaOf(plugin).properties || {}
  const roles = []
  for (const [key, meta] of Object.entries(props)) {
    if (meta?.['x-ui'] === 'host-multi') {
      roles.push({
        key,
        name: meta.title || key,
        min: 1,
        hostLabel: meta['x-host-label'] || '',
      })
    }
  }
  if (!roles.length) {
    roles.push({ key: '_host', name: '主实例', min: 0, hostLabel: '' })
  }
  return roles
}

export function missingDeps(plugin, selectedIds) {
  const deps = plugin?.dependencies || []
  return deps.filter((d) => !selectedIds.includes(d))
}

export function validateSelection(plugins, selectedIds) {
  const errors = []
  for (const id of selectedIds) {
    const p = plugins.find((x) => x.id === id)
    if (!p) continue
    const miss = missingDeps(p, selectedIds)
    if (miss.length) {
      errors.push(`${p.name} 依赖 ${miss.join(', ')}，请一并勾选`)
    }
  }
  return errors
}

/** 部署任务状态（禁止与实例运行状态混用） */
export function deployStatus(job) {
  const s = (job?.status || '').toLowerCase()
  const phase = (job?.phase || '').toLowerCase()
  if (s === 'cancelled' || phase === 'cancelled') return { key: 'cancelled', text: '已取消', cls: 'unknown' }
  if (s === 'failed' || phase === 'failed') return { key: 'failed', text: '失败', cls: 'unhealthy' }
  if (s === 'succeeded' || phase === 'ready') return { key: 'success', text: '成功', cls: 'healthy' }
  if (['downloading', 'starting', 'running'].includes(phase) || s === 'running') {
    return { key: 'deploying', text: '部署中', cls: 'unknown' }
  }
  return { key: 'queued', text: '排队', cls: 'unknown' }
}

/** 实例运行状态 */
export function instanceStatus(cluster, healthPlatforms = {}) {
  const st = (cluster?.status || '').toLowerCase()
  if (st === 'stopped' || st === 'stop') return { key: 'stopped', text: '停止', cls: 'unknown' }
  const plats = cluster?.platforms || []
  if (!plats.length) return { key: 'offline', text: '离线', cls: 'unhealthy' }
  const checks = plats.map((id) => healthPlatforms[id])
  if (checks.some((c) => c && c.ok === false)) return { key: 'alert', text: '告警', cls: 'unhealthy' }
  if (checks.length && checks.every((c) => c && c.ok)) return { key: 'ok', text: '正常', cls: 'healthy' }
  if (st === 'running' || st === 'ready') return { key: 'ok', text: '正常', cls: 'healthy' }
  return { key: 'offline', text: '离线', cls: 'unhealthy' }
}

export function defaultTaskName() {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `编排-${y}${m}${day}-${String(d.getTime()).slice(-4)}`
}
