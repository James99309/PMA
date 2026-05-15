// vue-i18n 实例 — 单例, 跨组件共享 locale
// 优先级: localStorage('lang') → user.language_preference (login 后同步) → 设备 locale → 'zh'
import { createI18n } from 'vue-i18n'
import zh from './zh'
import en from './en'

function detectInitialLocale() {
  // 1. 用户上次手动选过的
  const saved = localStorage.getItem('lang')
  if (saved === 'zh' || saved === 'en') return saved
  // 2. 设备 locale
  try {
    const nav = (navigator.language || 'zh').toLowerCase()
    if (nav.startsWith('zh')) return 'zh'
    if (nav.startsWith('en')) return 'en'
  } catch {}
  return 'zh'
}

const i18n = createI18n({
  legacy: false,        // composition api 模式
  globalInjection: true, // template 里 $t 全局可用
  locale: detectInitialLocale(),
  fallbackLocale: 'zh',
  messages: { zh, en },
})

export default i18n

// 切换语言 + 持久化 (UI + 同步给 axios header / 后端 user.language_preference)
export function setLocale(lang) {
  if (lang !== 'zh' && lang !== 'en') return
  i18n.global.locale.value = lang
  localStorage.setItem('lang', lang)
  // 设备 lang attr (无障碍/SEO)
  if (typeof document !== 'undefined') {
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en'
  }
}

export function getLocale() {
  return i18n.global.locale.value
}
