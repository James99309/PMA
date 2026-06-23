import client from './client'

// Work Calendar / daily log — read side (C-BE2 endpoints).
// owner_id optional on items/day/month to view a colleague's calendar.

// FullCalendar-style event source + meta (type groups / score levels / improvements)
export const getWorklogItems = (params = {}) =>
  client.get('/mobile/worklog/items', { params })

// One day: classified work items + smart hours + activities + quality (localized)
export const getWorklogDay = (params = {}) =>
  client.get('/mobile/worklog/day', { params })

// Month heatmap: per-date type breakdown + log status dots
export const getWorklogMonth = (params = {}) =>
  client.get('/mobile/worklog/month', { params })

// Switchable accounts: self / subordinates / others with this-week item count
export const getWorklogAccounts = () =>
  client.get('/mobile/worklog/accounts')

// 内嵌图片上传(工作描述/日报正文「插入图片」),返回 { url }
export function uploadWorklogImage(file, filename = null) {
  const fd = new FormData()
  fd.append('file', file, filename || file.name || `img_${Date.now()}.jpg`)
  return client.post('/mobile/worklog/upload-image', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// ── write side (C3): single source = backend worklog_service ──
export const createWorklogItem = payload =>
  client.post('/mobile/worklog/items', payload)

export const getWorklogItem = id =>
  client.get(`/mobile/worklog/items/${id}`)

export const updateWorklogItem = (id, payload) =>
  client.put(`/mobile/worklog/items/${id}`, payload)

export const deleteWorklogItem = id =>
  client.delete(`/mobile/worklog/items/${id}`)

export const completeWorklogItem = (id, payload = {}) =>
  client.post(`/mobile/worklog/items/${id}/complete`, payload)

export const cancelWorklogItem = (id, payload = {}) =>
  client.post(`/mobile/worklog/items/${id}/cancel`, payload)

// daily log write (C4)
export const updateWorklogDayDraft = (date, payload = {}) =>
  client.put('/mobile/worklog/day', payload, { params: { date } })

export const submitWorklogDay = (date, payload = {}) =>
  client.post('/mobile/worklog/day/submit', payload, { params: { date } })
