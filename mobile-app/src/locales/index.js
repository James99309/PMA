// vue-i18n 实例 — 单例, 跨组件共享 locale
// 优先级: localStorage('lang') → user.language_preference (login 后同步) → 设备 locale → 'zh'
import { createI18n } from 'vue-i18n'
import zh from './zh'
import en from './en'

function detectInitialLocale() {
  // 1. 用户上次手动选过的 / 登录后 sync 的 user.language_preference (持久化在 localStorage)
  const saved = localStorage.getItem('lang')
  if (saved === 'zh' || saved === 'en') return saved
  // 2. 首次 (无 localStorage) 一律默认 zh。
  //    不读 navigator.language —— iOS WKWebView 首次启动它不可靠 (常误返回
  //    en-US, 跟设备实际语言无关), 导致首次登录页闪英文、退出重进才正常。
  //    PMA 主用户为中文; 英文用户登录后 user.language_preference 会 setLocale
  //    并持久化, 第二步的 saved 分支即命中, 后续启动正确。
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
