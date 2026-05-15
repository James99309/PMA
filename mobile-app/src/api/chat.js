// 移动端聊天 API client
// 后端：/api/v1/mobile/chat/* （详见 app/api/v1/mobile_chat.py）
import axios from 'axios'
import client, { REGIONS } from './client'

// 会话
export const getConversations    = () => client.get('/mobile/chat/conversations')

// ─── 跨区域：用 peer 区的 token + baseURL 直接访问对端 NAS ─────────
// 用于"统一会话列表"：同时拉本区 + 对区 conversations / unread-count
export function getConversationsForRegion(regionId) {
  const region = REGIONS[regionId]
  const token = localStorage.getItem(`access_token_${regionId}`)
  if (!region || !token) return Promise.resolve({ data: { success: false, data: [] } })
  return axios.get(`${region.baseUrl}/api/v1/mobile/chat/conversations`, {
    headers: { Authorization: `Bearer ${token}` },
    timeout: 10000,
  }).catch(e => {
    console.warn(`[cross-region] getConversations(${regionId}) failed`, e?.message)
    return { data: { success: false, data: [] } }
  })
}

export function getUnreadCountForRegion(regionId) {
  const region = REGIONS[regionId]
  const token = localStorage.getItem(`access_token_${regionId}`)
  if (!region || !token) return Promise.resolve({ data: { success: false, data: { total_unread: 0 } } })
  return axios.get(`${region.baseUrl}/api/v1/mobile/chat/unread-count`, {
    headers: { Authorization: `Bearer ${token}` },
    timeout: 6000,
  }).catch(e => {
    console.warn(`[cross-region] getUnreadCount(${regionId}) failed`, e?.message)
    return { data: { success: false, data: { total_unread: 0 } } }
  })
}
export const getConversation     = id => client.get(`/mobile/chat/conversations/${id}`)
export const createConversation  = data => client.post('/mobile/chat/conversations', data)
export const deleteConversation  = id => client.delete(`/mobile/chat/conversations/${id}`)

// 消息
export const getMessages = (convId, params = {}) =>
  client.get(`/mobile/chat/conversations/${convId}/messages`, { params })
export const sendMessage = (convId, content, replyToId = null, refs = null, attachment = null) =>
  client.post(`/mobile/chat/conversations/${convId}/messages`, {
    content,
    reply_to_id: replyToId,
    ...(refs?.length ? { refs } : {}),
    ...(attachment ? {
      message_type: attachment.message_type,
      file_url: attachment.file_url,
      file_meta: attachment.file_meta,
    } : {}),
  })

// 上传附件到 NAS chat 桶（图片 / 文件 / 语音）
// kind: 'image' | 'file' | 'voice'
export function uploadChatFile(file, kind = 'file', filename = null) {
  const fd = new FormData()
  fd.append('file', file, filename || file.name || `chat_${kind}`)
  fd.append('kind', kind)
  return client.post('/mobile/chat/upload', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const markAsRead  = convId => client.post(`/mobile/chat/conversations/${convId}/read`)
export const recallMessage = msgId => client.post(`/mobile/chat/messages/${msgId}/recall`)
export const forwardMessage = (msgId, targetConvIds = [], userIds = [], note = null) =>
  client.post(`/mobile/chat/messages/${msgId}/forward`, {
    conversation_ids: targetConvIds, user_ids: userIds, note,
  })

// 未读
export const getUnreadCount = () => client.get('/mobile/chat/unread-count')

// 群成员
export const addParticipants = (convId, userIds) =>
  client.post(`/mobile/chat/conversations/${convId}/participants`, { user_ids: userIds })
export const removeParticipant = (convId, userId) =>
  client.delete(`/mobile/chat/conversations/${convId}/participants/${userId}`)

// @ 实体搜索
// scope: { conversationId? } 限制为该群成员；{ projectId? } 限制为该项目成员；
// 都不传 → 全员（用于新建聊天 / 添加成员等用户选择器场景）
export const searchUsers = (q, scope = {}) =>
  client.get('/mobile/chat/users/search', {
    params: {
      q,
      ...(scope.conversationId ? { conversation_id: scope.conversationId } : {}),
      ...(scope.projectId      ? { project_id: scope.projectId } : {}),
    },
  })
export const searchProjects  = q => client.get('/mobile/chat/entity/projects',  { params: { q } })
export const searchCompanies = q => client.get('/mobile/chat/entity/companies', { params: { q } })

// AI SSE（fetch + EventSource 都可，下面给 fetch 流式版）
// 用法：const reader = await streamAi({ content, conversationId, onEvent })
export async function streamAi({ content, conversationId, onEvent, signal }) {
  const token = localStorage.getItem('access_token')
  const baseURL = client.defaults.baseURL  // /api/v1
  const url = `${baseURL}/mobile/chat/ai/stream?token=${encodeURIComponent(token || '')}`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, conversation_id: conversationId }),
    signal,
  })
  if (!res.ok) {
    const text = await res.text()
    if (res.status === 401) {
      // token 失效，清掉跳登录
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.hash = '#/login'
    }
    throw new Error(`AI stream failed: ${res.status} ${text.slice(0, 200)}`)
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    // SSE: 事件以 \n\n 分割
    let idx
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const block = buffer.slice(0, idx).trim()
      buffer = buffer.slice(idx + 2)
      if (!block.startsWith('data:')) continue
      const json = block.slice(5).trim()
      try {
        const ev = JSON.parse(json)
        onEvent?.(ev)
      } catch (e) {
        console.warn('SSE parse fail:', json, e)
      }
    }
  }
}
