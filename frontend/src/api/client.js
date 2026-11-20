const TOKEN_KEY = 'dpi_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(path, { ...options, headers })
  if (res.status === 401 && !path.startsWith('/api/auth/')) {
    setToken('')
    if (!location.pathname.startsWith('/login') && !location.pathname.startsWith('/setup')) {
      location.href = '/login'
    }
  }
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  if (res.status === 204) return null
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) return res.json()
  return res.text()
}

async function download(path, filename) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(path, { headers })
  if (!res.ok) {
    throw new Error(`下载失败: ${res.status}`)
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export const api = {
  authStatus: () => request('/api/auth/status'),
  setup: (body) => request('/api/auth/setup', { method: 'POST', body: JSON.stringify(body) }),
  login: (body) => request('/api/auth/login', { method: 'POST', body: JSON.stringify(body) }),
  me: () => request('/api/auth/me'),

  plugins: () => request('/api/plugins'),
  health: () => request('/api/health'),
  clusters: () => request('/api/clusters'),
  createCluster: (body) => request('/api/clusters', { method: 'POST', body: JSON.stringify(body) }),
  deploy: (id) => request(`/api/clusters/${id}/deploy`, { method: 'POST' }),
  stop: (id) => request(`/api/clusters/${id}/stop`, { method: 'POST' }),
  restart: (id) => request(`/api/clusters/${id}/restart`, { method: 'POST' }),
  clusterHealth: (id) => request(`/api/clusters/${id}/health`),
  overview: (id) => request(`/api/clusters/${id}/overview`),

  jobs: (clusterId) => request(clusterId ? `/api/jobs?cluster_id=${clusterId}` : '/api/jobs'),
  job: (id) => request(`/api/jobs/${id}`),
  jobLogs: (id) => request(`/api/jobs/${id}/logs`),

  downloadJobLogs: (id) => download(`/api/logs/jobs/${id}/download`, `job-${id}.log`),
  downloadAbnormal: (clusterId) =>
    download(`/api/logs/clusters/${clusterId}/abnormal/download`, `abnormal-cluster-${clusterId}.zip`),

  aiSettings: () => request('/api/ai/settings'),
  saveAiSettings: (body) => request('/api/ai/settings', { method: 'PUT', body: JSON.stringify(body) }),
  diagnose: (body) => request('/api/ai/diagnose', { method: 'POST', body: JSON.stringify(body) }),
}
