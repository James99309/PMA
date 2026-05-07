// 跨平台键盘高度订阅 — Capacitor Keyboard 优先，visualViewport 兜底
// 与 NoteSheet 用同一套逻辑，确保 composer 与键盘动画同步
//
// 使用方式 (推荐):
//   const { kbStyle } = useKeyboardOffset()
//   <div class="flex flex-col h-full" :style="kbStyle">  // 根容器自动随键盘抬起
//
// 兼容旧用法 (LoginView 用 translateY 手势):
//   const { kbOffset } = useKeyboardOffset()
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
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

  // 现成的样式对象 — 直接绑到 <div :style="kbStyle"> 即可让根容器随键盘抬起
  const kbStyle = computed(() => ({
    paddingBottom: kbOffset.value + 'px',
    transition: 'padding-bottom 0.25s cubic-bezier(.25,.46,.45,.94)',
  }))

  return { kbOffset, kbStyle }
}
