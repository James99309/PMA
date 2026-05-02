// 长按检测（移动端）—— 触发 callback(payload) 在 delay ms 后
// 用法：
//   const lp = useLongPress((m) => openActions(m))
//   <div @touchstart="lp.onTouchStart($event, m)"
//        @touchmove="lp.onTouchMove"
//        @touchend="lp.onTouchEnd"
//        @touchcancel="lp.onTouchEnd">
export function useLongPress(callback, delay = 500) {
  let timer = null
  let startX = 0
  let startY = 0

  function onTouchStart(e, payload) {
    const t = e.touches?.[0] || e
    startX = t.clientX || 0
    startY = t.clientY || 0
    clearTimeout(timer)
    timer = setTimeout(() => {
      timer = null
      callback(payload)
    }, delay)
  }

  function onTouchMove(e) {
    if (!timer) return
    const t = e.touches?.[0] || e
    const dx = (t.clientX || 0) - startX
    const dy = (t.clientY || 0) - startY
    if (Math.abs(dx) > 8 || Math.abs(dy) > 8) {
      clearTimeout(timer)
      timer = null
    }
  }

  function onTouchEnd() {
    clearTimeout(timer)
    timer = null
  }

  return { onTouchStart, onTouchMove, onTouchEnd, onTouchCancel: onTouchEnd }
}
