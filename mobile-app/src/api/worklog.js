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
