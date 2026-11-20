async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  if (res.status === 204) return null
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) return res.json()
  return res.text()
}

export const api = {
  plugins: () => request('/api/plugins'),
  health: () => request('/api/health'),
  clusters: () => request('/api/clusters'),
  createCluster: (body) => request('/api/clusters', { method: 'POST', body: JSON.stringify(body) }),
  deploy: (id) => request(`/api/clusters/${id}/deploy`, { method: 'POST' }),
  stop: (id) => request(`/api/clusters/${id}/stop`, { method: 'POST' }),
  restart: (id) => request(`/api/clusters/${id}/restart`, { method: 'POST' }),
  clusterHealth: (id) => request(`/api/clusters/${id}/health`),
  jobs: (clusterId) => request(clusterId ? `/api/jobs?cluster_id=${clusterId}` : '/api/jobs'),
  job: (id) => request(`/api/jobs/${id}`),
  jobLogs: (id) => request(`/api/jobs/${id}/logs`),
}
