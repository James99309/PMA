// @ / # / $ 提及的统一渲染辅助
// 在 ProjectDetailView 项目讨论卡 / GroupChatView / DmChatView 共用
import ProjectRefCard from '@/components/common/refs/ProjectRefCard.vue'
import CustomerRefCard from '@/components/common/refs/CustomerRefCard.vue'

// 普通气泡（白底）下 token 颜色
export const TRIGGER_COLOR = {
  '@': 'var(--color-accent)',  // 人 - accent 橙
  '#': 'var(--color-ink)',     // 项目 - ink 黑
  '$': 'var(--color-accent)',  // 客户 - accent 橙
}

// 反色气泡（ink 黑底，"我"的消息）下 token 颜色 —— 浅色高对比
export const TRIGGER_COLOR_INVERTED = {
  '@': '#9FBEFF',
  '#': '#FFB87A',
  '$': '#9FBEFF',
}

// trigger → 引用卡组件
export const REF_COMPONENT = {
  '#': ProjectRefCard,
  '$': CustomerRefCard,
}

// 把消息文字按 @/#/$ token 切分成段，便于 v-for 着色渲染
export function parseMessageText(text) {
  if (!text) return []
  const regex = /([@#$][一-龥\w-]+)/g
  const parts = []
  let last = 0
  let m
  while ((m = regex.exec(text)) !== null) {
    if (m.index > last) parts.push({ kind: 'plain', text: text.slice(last, m.index) })
    parts.push({ kind: 'mention', trigger: m[0][0], text: m[0] })
    last = m.index + m[0].length
  }
  if (last < text.length) parts.push({ kind: 'plain', text: text.slice(last) })
  return parts
}
