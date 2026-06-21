import client from './client'

export const getCustomers = (params = {}) =>
  client.get('/mobile/customers', { params })

export const getCustomerOwners = () =>
  client.get('/mobile/customers/owners')

export const getCustomer = id =>
  client.get(`/mobile/customers/${id}`)

// Sharing (reuses web SharingService: candidate users + current selection)
export const getCustomerSharing = id =>
  client.get(`/mobile/customers/${id}/sharing`)

export const updateCustomerSharing = (id, sharedWithUsers) =>
  client.post(`/mobile/customers/${id}/sharing`, { shared_with_users: sharedWithUsers })

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

// 名片扫描: multipart 上传裁剪后的图, 后端返回 OCR JSON + NAS file_url
export function scanBusinessCard(blob, filename = 'business_card.jpg') {
  const fd = new FormData()
  fd.append('file', blob, filename)
  return client.post('/mobile/customers/scan-business-card', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000,
  })
}

// 联系人重复检测 (phone / email 精确匹配)
export const checkContactDuplicate = (phone, email) =>
  client.post('/mobile/contacts/check-duplicate', { phone, email })

// 合并扫描结果到现有联系人 (空字段才填, 名片图覆盖)
export const mergeContactFromCard = (contactId, data) =>
  client.post(`/mobile/contacts/${contactId}/merge-from-card`, data)

// 联系人 CRUD
export const getContact = id => client.get(`/mobile/contacts/${id}`)
export const updateContact = (id, data) => client.put(`/mobile/contacts/${id}`, data)
export const deleteContact = id => client.delete(`/mobile/contacts/${id}`)
