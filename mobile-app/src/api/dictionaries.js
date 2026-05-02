// 字典 API client
// 后端：GET /api/v1/dictionary/<type>?active_only=true
import client from './client'

export const fetchDictionary = (type, activeOnly = true) =>
  client.get(`/dictionary/${type}`, { params: { active_only: activeOnly } })
