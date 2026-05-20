// 跨平台键盘高度订阅 — 主要给 fixed 浮层(NoteSheet/LocationSheet/Approval/...) 用。
//
// 自 build 10 起 Capacitor `Keyboard.resize: 'native'` 模式让 iOS WKWebView 自己 resize
// 到键盘上方, window.innerHeight + visualViewport 自动变小, h-full / 100% 全屏容器
// 自然跟着缩 — 全屏页 (chat / form 等) **不需要** 手动 paddingBottom = kbOffset。
//
// 但 position: fixed 的 sheet 在某些 iOS 版本仍参考物理屏幕, 不跟随 keyboard, 因此
// 我们仍提供 kbOffset / kbStyle 供这些场景手动抬起。
//
// 使用:
//   const { kbStyle } = useKeyboardOffset()
//   <div class="fixed inset-x-0 bottom-0" :style="kbStyle">  // fixed sheet
//
// 钩子: onKeyboardWillShow(cb) — 键盘**将要**弹起那一帧触发, 用于 scrollToBottom 等
//                                跟 native resize 动画同步的操作。
//
// 副作用:
//   - 键盘升起时自动 scrollIntoView 当前 focused input (表单页避免遮挡)
//   - 点击键盘外的纯展示区域 → 自动 dismiss 键盘 (iOS 中文键盘没有 Done 键)

import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { Capacitor } from '@capacitor/core'

// 全局共享: 跨视图记住上次拿到的真实键盘高度, 兜底首次 willShow keyboardHeight=0
let _globalLastKbHeight = 0

function _scrollFocusedIntoView() {
  const el = document.activeElement
  if (!el) return
  const tag = (el.tagName || '').toLowerCase()
  if (tag !== 'input' && tag !== 'textarea' && el.contentEditable !== 'true') return
  setTimeout(() => {
    try { el.scrollIntoView({ block: 'center', behavior: 'smooth' }) } catch { el.scrollIntoView() }
  }, 60)
}

export function useKeyboardOffset() {
  const kbOffset = ref(0)
  let kbShowHandle, kbHideHandle
  const _willShowCallbacks = []
  const _didShowCallbacks = []
  const _willHideCallbacks = []
  function onKeyboardWillShow(cb) { _willShowCallbacks.push(cb) }
  function onKeyboardDidShow(cb) { _didShowCallbacks.push(cb) }
  function onKeyboardWillHide(cb) { _willHideCallbacks.push(cb) }

  // resize:None 下 visualViewport 键盘弹起时不变 (diff≈0), 不能用它清零 kbOffset
  // —— 否则会盖掉 keyboardWillShow 拿到的原生 keyboardHeight。 仅当 vv 真算出正值
  // (resize:native 等环境) 时作为加成更新; 归零交给 keyboardWillHide。
  function recomputeFromVV() {
    const vv = window.visualViewport
    if (!vv) return
    const diff = window.innerHeight - vv.height - vv.offsetTop
    if (diff > 50) kbOffset.value = diff
  }

  watch(kbOffset, (newVal, oldVal) => {
    if (newVal > 0 && newVal !== oldVal) _scrollFocusedIntoView()
  })

  function onFocusIn(e) {
    if (!kbOffset.value) return
    const t = e.target
    const tag = (t?.tagName || '').toLowerCase()
    if (tag === 'input' || tag === 'textarea' || t?.contentEditable === 'true') {
      _scrollFocusedIntoView()
    }
  }

  // 点击键盘外纯展示区域 → 收起键盘 (iOS 中文键盘无 Done)
  // 不在 button / a / input 上 dismiss, 避免动画期间按钮位移导致 click 落空
  function onTapOutside(e) {
    if (!kbOffset.value) return
    const t = e.target
    if (!t) return
    const tag = (t.tagName || '').toLowerCase()
    const isEditable = tag === 'input' || tag === 'textarea' || tag === 'select'
      || t.contentEditable === 'true'
      || (t.closest && t.closest('[contenteditable="true"]'))
    if (isEditable) return
    const isInteractive = tag === 'button' || tag === 'a'
      || (t.closest && t.closest('button, a, [role="button"]'))
    if (isInteractive) return
    const active = document.activeElement
    const activeTag = (active?.tagName || '').toLowerCase()
    if (activeTag !== 'input' && activeTag !== 'textarea' && active?.contentEditable !== 'true') return
    active.blur()
    if (Capacitor.isNativePlatform?.()) {
      import('@capacitor/keyboard').then(({ Keyboard }) => { Keyboard.hide().catch(() => {}) }).catch(() => {})
    }
  }

  onMounted(async () => {
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', recomputeFromVV)
      window.visualViewport.addEventListener('scroll', recomputeFromVV)
    }
    document.addEventListener('focusin', onFocusIn)
    document.addEventListener('touchstart', onTapOutside, { capture: true, passive: true })
    document.addEventListener('mousedown', onTapOutside, { capture: true, passive: true })
    if (Capacitor.isNativePlatform?.()) {
      try {
        const { Keyboard } = await import('@capacitor/keyboard')
        // 全屏页用 CSS `100dvh` 自动响应键盘, 不需要手动 padding。 这里订阅事件仅为
        // 给消费者提供 onKeyboardWillShow hook (chat scrollToBottom 用)。 kbOffset 仍由
        // visualViewport 算, 供 fixed sheet 使用。
        kbShowHandle = await Keyboard.addListener('keyboardWillShow', e => {
          // 原生 keyboardHeight 是 resize:None 下唯一可靠的键盘高度 (与 main.js
          // 设的 --kb-height 同源)。 首次 willShow 偶发 keyboardHeight=0, 用全局
          // 上次值兜底, 让 kbStyle 对所有 fixed sheet 正确抬起。
          const h = (e && e.keyboardHeight) || _globalLastKbHeight
          if (h > 0) { _globalLastKbHeight = h; kbOffset.value = h }
          _willShowCallbacks.forEach(cb => { try { cb(e) } catch {} })
        })
        // didShow 时 padding transition 已完成, scrollEl 容器已缩小, scrollHeight 是最终值
        await Keyboard.addListener('keyboardDidShow', e => {
          _didShowCallbacks.forEach(cb => { try { cb(e) } catch {} })
        })
        kbHideHandle = await Keyboard.addListener('keyboardWillHide', () => {
          kbOffset.value = 0
          _willHideCallbacks.forEach(cb => { try { cb() } catch {} })
        })
      } catch { /* plugin missing on old build, ignore */ }
    }
  })

  onBeforeUnmount(() => {
    if (window.visualViewport) {
      window.visualViewport.removeEventListener('resize', recomputeFromVV)
      window.visualViewport.removeEventListener('scroll', recomputeFromVV)
    }
    document.removeEventListener('focusin', onFocusIn)
    document.removeEventListener('touchstart', onTapOutside, { capture: true })
    document.removeEventListener('mousedown', onTapOutside, { capture: true })
    kbShowHandle?.remove?.()
    kbHideHandle?.remove?.()
  })

  // paddingBottom 减 env(safe-area-inset-bottom): 键盘弹起时 home indicator 区域已被键盘
  // 覆盖, 不该再 padding 一遍 (env=21pt iPhone X+, env=0 其他)
  const kbStyle = computed(() => ({
    paddingBottom: kbOffset.value > 0
      ? `calc(${kbOffset.value}px - env(safe-area-inset-bottom))`
      : '0px',
    transition: 'padding-bottom 0.25s cubic-bezier(.25,.46,.45,.94)',
  }))

  return { kbOffset, kbStyle, onKeyboardWillShow, onKeyboardDidShow, onKeyboardWillHide }
}
