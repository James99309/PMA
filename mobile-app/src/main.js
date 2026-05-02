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
import './style.css'

createApp(App).use(createPinia()).use(router).mount('#app')

// ─── Capgo OTA：通知 native 端 web 已准备好（释放冷启等待，autoUpdate 会自动检查新版本）
import { CapacitorUpdater } from '@capgo/capacitor-updater'
CapacitorUpdater.notifyAppReady().catch(() => {})

// iOS WebView 键盘弹起会把整个 WebView frame 上推（默认 KeyboardResize.Native 行为），
// 导致顶部头被推进状态栏区域。下面强制把 window.scrollTop 锁回 0，
// 让 iOS 不再上推，输入框依然由底部 flex 布局保持可见。
function lockScroll() {
  if (window.scrollY !== 0) window.scrollTo(0, 0)
  if (document.scrollingElement) document.scrollingElement.scrollTop = 0
  if (document.body) document.body.scrollTop = 0
}
window.addEventListener('focusin', (e) => {
  const tag = e.target?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA') {
    // 聚焦后多次回调，对抗 iOS 异步 reflow
    requestAnimationFrame(lockScroll)
    setTimeout(lockScroll, 0)
    setTimeout(lockScroll, 100)
    setTimeout(lockScroll, 300)
  }
})
window.addEventListener('focusout', () => {
  setTimeout(lockScroll, 0)
})
window.addEventListener('scroll', lockScroll, { passive: true })
