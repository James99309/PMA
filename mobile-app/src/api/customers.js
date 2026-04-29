import client from './client'

export const getCustomers = (params = {}) =>
  client.get('/mobile/customers', { params })

export const getCustomer = id =>
  client.get(`/mobile/customers/${id}`)

export const addCustomerNote = (id, content) =>
  client.post(`/mobile/customers/${id}/notes`, { content })

export const addContact = (companyId, data) =>
  client.post(`/mobile/customers/${companyId}/contacts`, data)

export const searchContacts = q =>
  client.get('/mobile/contacts/search', { params: { q } })
