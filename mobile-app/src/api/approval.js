import client from './client'

export const getPendingApprovals = () => client.get('/mobile/approval/pending')
export const getApprovalHistory = () => client.get('/mobile/approval/history')
export const getApprovalCc = () => client.get('/mobile/approval/cc')
export const getApprovalDetail = (instanceId) => client.get(`/mobile/approval/${instanceId}`)
export const doApprovalAction = (instanceId, action, comment = '') =>
  client.post(`/mobile/approval/${instanceId}/action`, { action, comment })
export const forwardApproval = (instanceId, targetUserId, comment = '') =>
  client.post(`/mobile/approval/${instanceId}/forward`, { target_user_id: targetUserId, comment })
