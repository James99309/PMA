// 聊天消息时间格式化
// 入：ISO 字符串 '2026-02-23T16:41:04.139812Z'
// 出：'09:32' / '昨天 17:42' / '周二 09:18' / '04-15 09:18'
const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

function pad(n) { return String(n).padStart(2, '0') }

export function formatChatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  const now = new Date()
  const hhmm = `${pad(d.getHours())}:${pad(d.getMinutes())}`

  // 同一天
  const sameDay = d.getFullYear() === now.getFullYear()
    && d.getMonth() === now.getMonth()
    && d.getDate() === now.getDate()
  if (sameDay) return hhmm

  // 昨天
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (d.getFullYear() === yesterday.getFullYear()
    && d.getMonth() === yesterday.getMonth()
    && d.getDate() === yesterday.getDate()) {
    return `昨天 ${hhmm}`
  }

  // 7 天内：周几
  const diffDays = Math.floor((now - d) / 86400000)
  if (diffDays < 7) return `${WEEKDAYS[d.getDay()]} ${hhmm}`

  // 同年：月-日
  if (d.getFullYear() === now.getFullYear()) {
    return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${hhmm}`
  }
  // 跨年：年-月-日
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

// 当天分隔条用：'今天' / '昨天' / '周二' / '04-15'
export function formatDayDivider(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const sameDay = d.getFullYear() === now.getFullYear()
    && d.getMonth() === now.getMonth()
    && d.getDate() === now.getDate()
  if (sameDay) return '今天'

  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (d.getFullYear() === yesterday.getFullYear()
    && d.getMonth() === yesterday.getMonth()
    && d.getDate() === yesterday.getDate()) return '昨天'

  const diffDays = Math.floor((now - d) / 86400000)
  if (diffDays < 7) return WEEKDAYS[d.getDay()]
  if (d.getFullYear() === now.getFullYear()) return `${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}
