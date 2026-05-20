import '@fontsource/noto-serif-sc/chinese-simplified-400.css'
import '@fontsource/noto-serif-sc/chinese-simplified-700.css'
// Source Serif Pro：自托管 400 + 600 + 700
// 设计稿用 W500，Source Serif Pro 没有 W500 → 浏览器自动 fallback 到 W600
import '@fontsource/source-serif-pro/400.css'
import '@fontsource/source-serif-pro/600.css'
import '@fontsource/source-serif-pro/700.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import i18n from './locales'
import './style.css'

createApp(App).use(createPinia()).use(router).use(i18n).mount('#app')

// 已登录用户启动 App 时补一次 APNs push 注册 (login 流程会注册, 这里覆盖"已登录后冷启动")
const hasAnyToken = ['cn', 'sg'].some(r => localStorage.getItem(`access_token_${r}`)) ||
                    localStorage.getItem('access_token')
if (hasAnyToken) {
  import('@/utils/push').then(({ setupPushNotifications }) => {
    setupPushNotifications().catch(() => {})
  })
}

// ─── Capgo OTA：通知 native 端 web 已准备好（释放冷启等待，autoUpdate 会自动检查新版本）
import { CapacitorUpdater } from '@capgo/capacitor-updater'
CapacitorUpdater.notifyAppReady().catch(() => {})

// ─── Capacitor Keyboard：用 Body 模式让键盘弹起时压缩页面
// 防御性动态 import：如果原生层未安装该插件（旧 Xcode build），不会崩溃
import { Capacitor } from '@capacitor/core'
if (Capacitor.isNativePlatform()) {
  import('@capacitor/keyboard')
    .then(({ Keyboard, KeyboardResize }) => {
      // None 模式：webview/body 都不自动 resize → 由各页面 composer 用 kbOffset 同步 transform
      Keyboard.setResizeMode({ mode: KeyboardResize.None }).catch(() => {})
      // 让 iOS 自动滚动聚焦的输入框到可见区 (覆盖普通表单页) — 聊天 composer 用 kbOffset 自管, 不冲突
      Keyboard.setScroll({ isDisabled: false }).catch(() => {})
      Keyboard.addListener('keyboardWillShow', (info) => {
        // Capacitor keyboardHeight 已是键盘完整可见高度 (含 autocomplete bar / 候选词栏)
        document.documentElement.style.setProperty('--kb-height', `${info.keyboardHeight || 0}px`)
        document.documentElement.classList.add('kb-open')
      })
      Keyboard.addListener('keyboardWillHide', () => {
        document.documentElement.style.setProperty('--kb-height', '0px')
        document.documentElement.classList.remove('kb-open')
      })
    })
    .catch((e) => console.warn('Keyboard plugin not installed natively:', e?.message))
}
