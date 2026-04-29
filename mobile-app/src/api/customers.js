import client from './client'

export const getCustomers = (params = {}) =>
  client.get('/mobile/customers', { params })

export const getCustomer = id =>
  client.get(`/mobile/customers/${id}`)

export const searchContacts = q =>
  client.get('/mobile/contacts/search', { params: { q } })
