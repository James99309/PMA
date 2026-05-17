import client from './client'

// Task Center (P1). params: tab(mine/created/shared/review) status sort page per
export const getTasks = (params = {}) =>
  client.get('/mobile/tasks', { params })

export const getTask = id => client.get(`/mobile/tasks/${id}`)

export const createTask = payload => client.post('/mobile/tasks', payload)

export const updateTask = (id, payload) =>
  client.patch(`/mobile/tasks/${id}`, payload)

export const changeTaskStatus = (id, body) =>
  client.post(`/mobile/tasks/${id}/status`, body)

export const addTaskReply = (id, content, subtaskId = null) =>
  client.post(`/mobile/tasks/${id}/replies`,
    subtaskId ? { content, subtask_id: subtaskId, reply_type: 'update' } : { content })

export const setSubtaskStatus = (tid, sid, action) =>
  client.post(`/mobile/tasks/${tid}/subtasks/${sid}/status`, { action })

export const reviewTask = (id, body) =>
  client.post(`/mobile/tasks/${id}/review`, body)

export const uploadTaskAttachment = (id, formData) =>
  client.post(`/mobile/tasks/${id}/attachments`, formData,
    { headers: { 'Content-Type': 'multipart/form-data' } })

export const deleteTaskAttachment = (id, aid) =>
  client.delete(`/mobile/tasks/${id}/attachments/${aid}`)

export const deleteTask = id => client.delete(`/mobile/tasks/${id}`)

export const getTaskPerspectives = () =>
  client.get('/mobile/tasks/perspectives')

export const searchQuotations = q =>
  client.get('/mobile/quotations', { params: { q: q || '' } })

export const createSubtask = (tid, payload) =>
  client.post(`/mobile/tasks/${tid}/subtasks`, payload)

export const updateSubtask = (tid, sid, payload) =>
  client.patch(`/mobile/tasks/${tid}/subtasks/${sid}`, payload)

export const deleteSubtask = (tid, sid) =>
  client.delete(`/mobile/tasks/${tid}/subtasks/${sid}`)

export const confirmMilestone = (tid, sid, body) =>
  client.post(`/mobile/tasks/${tid}/subtasks/${sid}/milestone`, body)

export const resubmitReview = tid =>
  client.post(`/mobile/tasks/${tid}/resubmit-review`, {})

export const getNotifications = (params = {}) =>
  client.get('/mobile/notifications', { params })

export const getNotifUnread = () =>
  client.get('/mobile/notifications/unread-count')

export const markNotifRead = id =>
  client.post(`/mobile/notifications/${id}/read`, {})

export const markAllNotifRead = () =>
  client.post('/mobile/notifications/read-all', {})
