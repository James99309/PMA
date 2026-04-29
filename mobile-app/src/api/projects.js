import client from './client'

export const getProjects = (params = {}) =>
  client.get('/mobile/projects', { params })

export const getProject = id =>
  client.get(`/mobile/projects/${id}`)

export const addProjectNote = (id, content) =>
  client.post(`/mobile/projects/${id}/notes`, { content })
