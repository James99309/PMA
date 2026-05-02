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

export const checkCustomerName = name =>
  client.post('/mobile/check-name/customer', { name })

export const reverseGeocode = (latitude, longitude) =>
  client.post('/mobile/geocode/reverse', { latitude, longitude })

export const searchAddress = q =>
  client.get('/mobile/address/search', { params: { q } })

export const getAddressDetail = place_id =>
  client.get('/mobile/address/detail', { params: { place_id } })

export const createCustomer = data =>
  client.post('/mobile/customers', data)

export const updateCustomer = (id, data) =>
  client.put(`/mobile/customers/${id}`, data)

export const archiveCustomer = id =>
  client.delete(`/mobile/customers/${id}`)
