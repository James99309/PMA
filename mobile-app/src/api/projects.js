import client from './client'

export const getProjects = (params = {}) =>
  client.get('/mobile/projects', { params })

export const getProject = id =>
  client.get(`/mobile/projects/${id}`)

export const addProjectNote = (id, content) =>
  client.post(`/mobile/projects/${id}/notes`, { content })

export const getQuotationDetail = quotationId =>
  client.get(`/mobile/quotations/${quotationId}`)

export const checkProjectName = name =>
  client.post('/mobile/check-name/project', { name })

export const createProject = data =>
  client.post('/mobile/projects', data)

export const updateProject = (id, data) =>
  client.patch(`/mobile/projects/${id}`, data)
