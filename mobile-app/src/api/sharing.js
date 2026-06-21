import client from './client'

// Generic sharing API — one pair for all shareable models (customer/project/...).
// model: 'customer' | 'project' | ...
export const getSharing = (model, id) =>
  client.get(`/mobile/sharing/${model}/${id}`)

export const updateSharing = (model, id, sharedWithUsers) =>
  client.post(`/mobile/sharing/${model}/${id}`, { shared_with_users: sharedWithUsers })
