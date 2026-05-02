// 跨平台键盘高度订阅 — Capacitor Keyboard 优先，visualViewport 兜底
// 与 NoteSheet 用同一套逻辑，确保 composer 与键盘动画同步
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Capacitor } from '@capacitor/core'

export function useKeyboardOffset() {
  const kbOffset = ref(0)
  let kbShowHandle, kbHideHandle

  function recomputeFromVV() {
    const vv = window.visualViewport
    if (!vv) return
    const diff = window.innerHeight - vv.height - vv.offsetTop
    kbOffset.value = diff > 50 ? diff : 0
  }

  onMounted(async () => {
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', recomputeFromVV)
      window.visualViewport.addEventListener('scroll', recomputeFromVV)
    }
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
    kbShowHandle?.remove?.()
    kbHideHandle?.remove?.()
  })

  return { kbOffset }
}
