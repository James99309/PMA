import { defineStore } from 'pinia'

// 聊天状态共享 store —— 当前纯前端 mock，未来接后端时把 actions 改成 API 调用即可
// groupId 用 'proj-{projectId}' 形式（项目群）或 'g-{convId}' 形式（普通群）
export const useChatStore = defineStore('chat', {
  state: () => ({
    // groupId -> [{ id, kind, from, initial, time, text, mention?, italic?, body? }]
    groupMessages: {},
  }),

  actions: {
    /** 取群消息；不存在时用 fallback 初始化（保证两端首次进入看到同样的种子数据） */
    getGroup(groupId, fallback = []) {
      if (!this.groupMessages[groupId]) {
        this.groupMessages[groupId] = [...fallback]
      }
      return this.groupMessages[groupId]
    },

    /** 追加一条消息到群（项目详情卡和群聊页都用） */
    appendToGroup(groupId, message) {
      if (!this.groupMessages[groupId]) this.groupMessages[groupId] = []
      this.groupMessages[groupId].push({
        id: message.id || Date.now() + Math.random(),
        ...message,
      })
    },

    /** 替换群内一条消息（AI thinking → 实际回复时用） */
    replaceMessage(groupId, msgId, patch) {
      const list = this.groupMessages[groupId]
      if (!list) return
      const idx = list.findIndex(m => m.id === msgId)
      if (idx >= 0) list[idx] = { ...list[idx], ...patch }
    },
  },
})
