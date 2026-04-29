import client from './client'

export const getPendingApprovals = () =>
  client.get('/mobile/approval/pending')

export const doApprovalAction = (instanceId, action, comment = '') =>
  client.post(`/mobile/approval/${instanceId}/action`, { action, comment })

export const getApprovalHistory = () =>
  client.get('/mobile/approval/history')
