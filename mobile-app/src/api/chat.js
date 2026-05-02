// 移动端聊天 API client
// 后端：/api/v1/mobile/chat/* （详见 app/api/v1/mobile_chat.py）
import client from './client'

// 会话
export const getConversations    = () => client.get('/mobile/chat/conversations')
export const getConversation     = id => client.get(`/mobile/chat/conversations/${id}`)
export const createConversation  = data => client.post('/mobile/chat/conversations', data)
export const deleteConversation  = id => client.delete(`/mobile/chat/conversations/${id}`)

// 消息
export const getMessages = (convId, params = {}) =>
  client.get(`/mobile/chat/conversations/${convId}/messages`, { params })
export const sendMessage = (convId, content, replyToId = null) =>
  client.post(`/mobile/chat/conversations/${convId}/messages`, { content, reply_to_id: replyToId })
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
