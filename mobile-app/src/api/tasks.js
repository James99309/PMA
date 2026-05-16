import client from './client'

// Task Center (P1). params: tab(mine/created/shared/review) status sort page per
export const getTasks = (params = {}) =>
  client.get('/mobile/tasks', { params })

export const getTask = id => client.get(`/mobile/tasks/${id}`)

export const createTask = payload => client.post('/mobile/tasks', payload)

export const changeTaskStatus = (id, body) =>
  client.post(`/mobile/tasks/${id}/status`, body)

export const addTaskReply = (id, content) =>
  client.post(`/mobile/tasks/${id}/replies`, { content })

export const reviewTask = (id, body) =>
  client.post(`/mobile/tasks/${id}/review`, body)
