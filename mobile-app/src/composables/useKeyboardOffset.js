// 跨平台键盘高度订阅 — Capacitor Keyboard 优先，visualViewport 兜底
// 与 NoteSheet 用同一套逻辑，确保 composer 与键盘动画同步
//
// 使用方式 (推荐):
//   const { kbStyle } = useKeyboardOffset()
//   <div class="flex flex-col h-full" :style="kbStyle">  // 根容器自动随键盘抬起
//
// 兼容旧用法 (LoginView 用 translateY 手势):
//   const { kbOffset } = useKeyboardOffset()
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { Capacitor } from '@capacitor/core'

// Capacitor Resize.None 下 iOS WebView 不会自动 scroll 焦点 input 到可见区,
// 表单视图键盘升起时焦点 input 会被遮住。这里加焦点跟随 — 当 kbOffset
// 变化时, 把当前 focused 的 input/textarea 滚到视野中央。
function _scrollFocusedIntoView() {
  const el = document.activeElement
  if (!el) return
  const tag = (el.tagName || '').toLowerCase()
  if (tag !== 'input' && tag !== 'textarea' && el.contentEditable !== 'true') return
  // 等 paddingBottom transition 起来再滚, 避免双重抖动
  setTimeout(() => {
    try {
      el.scrollIntoView({ block: 'center', behavior: 'smooth' })
    } catch {
      el.scrollIntoView()
    }
  }, 60)
}

export function useKeyboardOffset() {
  const kbOffset = ref(0)
  let kbShowHandle, kbHideHandle

  function recomputeFromVV() {
    const vv = window.visualViewport
    if (!vv) return
    const diff = window.innerHeight - vv.height - vv.offsetTop
    kbOffset.value = diff > 50 ? diff : 0
  }

  // 键盘升起时自动滚动当前焦点 input 到视野中央
  watch(kbOffset, (newVal, oldVal) => {
    if (newVal > 0 && newVal !== oldVal) _scrollFocusedIntoView()
  })

  // 焦点跳到另一个 input 时也滚 (键盘已开, kbOffset 不变, 但需要重新滚)
  function onFocusIn(e) {
    if (!kbOffset.value) return
    const t = e.target
    const tag = (t?.tagName || '').toLowerCase()
    if (tag === 'input' || tag === 'textarea' || t?.contentEditable === 'true') {
      _scrollFocusedIntoView()
    }
  }

  onMounted(async () => {
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', recomputeFromVV)
      window.visualViewport.addEventListener('scroll', recomputeFromVV)
    }
    document.addEventListener('focusin', onFocusIn)
    if (Capacitor.isNativePlatform?.()) {
      try {
        const { Keyboard } = await import('@capacitor/keyboard')
        kbShowHandle = await Keyboard.addListener('keyboardWillShow', e => {
          if (e.keyboardHeight) kbOffset.value = e.keyboardHeight
        })
        kbHideHandle = await Keyboard.addListener('keyboardWillHide', () => {
          kbOffset.value = 0
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
    kbShowHandle?.remove?.()
    kbHideHandle?.remove?.()
  })

  // 现成的样式对象 — 直接绑到 <div :style="kbStyle"> 即可让根容器随键盘抬起
  const kbStyle = computed(() => ({
    paddingBottom: kbOffset.value + 'px',
    transition: 'padding-bottom 0.25s cubic-bezier(.25,.46,.45,.94)',
  }))

  return { kbOffset, kbStyle }
}
