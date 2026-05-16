import client from './client'

// Task Center list (P1). params: tab(mine/created/shared/review) status sort page per
export const getTasks = (params = {}) =>
  client.get('/mobile/tasks', { params })
