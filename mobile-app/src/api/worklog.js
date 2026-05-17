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
