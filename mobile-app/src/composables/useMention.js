// 输入框 ↔ MentionPopover 联动 composable
// 检测最后一个未关闭的 @/#/$ token，触发 popover open + 实时 query
// 选中后替换该 token 为 trigger + 完整名称 + 空格
// 同时跟踪 pendingRefs：用户选中 #/$ 时自动收集，发送时随消息附挂
import { ref, computed, watch } from 'vue'

const TRIGGERS = ['@', '#', '$']

export function useMention(inputRef) {
  const popoverVisible = ref(false)
  const popoverType = ref('@')
  const popoverQuery = ref('')

  // 待发引用（# 项目 / $ 客户），@ 人不挂卡所以不进
  const pendingRefs = ref([])

  // 内部状态：当前 token 的起始位置（用于替换）
  let tokenStart = -1

  /** input 值变化时调用，传入当前文本 + 光标位置 */
  function onInput(text, caretPos) {
    // 在 caret 之前向左找到最近的 trigger 字符
    const before = text.slice(0, caretPos)
    let foundIdx = -1
    let foundChar = ''
    for (let i = before.length - 1; i >= 0; i--) {
      const ch = before[i]
      // 如果遇到空格/换行，token 中断
      if (ch === ' ' || ch === '\n') break
      if (TRIGGERS.includes(ch)) {
        foundIdx = i
        foundChar = ch
        break
      }
    }

    if (foundIdx === -1) {
      popoverVisible.value = false
      tokenStart = -1
      return
    }

    // 检查 trigger 前一个字符必须是 空格 / 行首 / 标点（避免在邮箱里乱触发）
    const prev = foundIdx > 0 ? before[foundIdx - 1] : ''
    if (prev && !/[\s,，。、；;:：]/.test(prev)) {
      popoverVisible.value = false
      tokenStart = -1
      return
    }

    tokenStart = foundIdx
    popoverType.value = foundChar
    popoverQuery.value = before.slice(foundIdx + 1)
    popoverVisible.value = true
  }

  /** 用户在 popover 里点了一项，把 trigger+token 替换为 trigger+全称+空格 */
  function onSelect(payload, currentText, setText) {
    const { type, item } = payload
    if (tokenStart === -1) return
    const before = currentText.slice(0, tokenStart)
    const replacement = `${type}${item.name || item.no} `
    const afterStart = tokenStart + 1 + popoverQuery.value.length
    const after = currentText.slice(afterStart)
    const newText = before + replacement + after
    setText(newText)
    closePopover()
    // 自动收集 ref（@ 不挂卡）
    if (type !== '@') pendingRefs.value.push(payload)
    inputRef.value?.focus?.()
  }

  function removeRef(idx) {
    pendingRefs.value.splice(idx, 1)
  }
  function clearRefs() {
    pendingRefs.value = []
  }

  function switchType(t) {
    popoverType.value = t
  }

  function closePopover() {
    popoverVisible.value = false
    tokenStart = -1
    popoverQuery.value = ''
  }

  return {
    popoverVisible,
    popoverType,
    popoverQuery,
    pendingRefs,
    onInput,
    onSelect,
    switchType,
    closePopover,
    removeRef,
    clearRefs,
  }
}
