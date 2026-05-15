// 输入框 ↔ MentionPopover 联动 composable
// - 输入 @ → 自动弹 popover（@ 通知是普遍习惯保留）
// - # / $ 不再走输入文字触发，由外部图标按钮调 openPicker('#') / openPicker('$')
// - @ 选中后留 @全名 token 在文字里；# / $ 选中后只挂卡片，不进文字
import { ref, computed, watch } from 'vue'

// 仅 @ 触发输入文字检测；# / $ 改用图标按钮主动调用
const TRIGGERS = ['@']

export function useMention(inputRef) {
  const popoverVisible = ref(false)
  const popoverType = ref('@')
  const popoverQuery = ref('')

  // 待发引用（# 项目 / $ 客户），@ 人不挂卡所以不进
  const pendingRefs = ref([])

  // 内部状态：当前 token 的起始位置（用于替换）；-1 = 无 token；-2 = 图标触发（无文字 token 要删）
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

  /** 由外部图标按钮调用：直接打开 # 或 $ 选择器，无文字 token */
  function openPicker(type) {
    if (type !== '#' && type !== '$') return
    popoverType.value = type
    popoverQuery.value = ''
    tokenStart = -2  // 图标触发，无 token 文字要删
    popoverVisible.value = true
  }

  /** 用户在 popover 里点了一项
   * - @ 用户：把 @xxx 替换为 @全名+空格 留在文字里（@ 通知功能要保留 token）
   * - # 项目 / $ 客户：仅挂卡片，不动输入文字（图标触发无 token；输入触发也直接清掉）
   */
  function onSelect(payload, currentText, setText) {
    const { type, item } = payload
    if (tokenStart === -1) return

    if (type === '@') {
      // @ 必走文字 token 替换
      if (tokenStart < 0) { closePopover(); return }
      const before = currentText.slice(0, tokenStart)
      const afterStart = tokenStart + 1 + popoverQuery.value.length
      const after = currentText.slice(afterStart)
      const replacement = `${type}${item.name || item.no} `
      setText(before + replacement + after)
    } else {
      // # / $ 只挂卡片
      if (tokenStart >= 0) {
        // 输入触发：清掉 #xxx 文字
        const before = currentText.slice(0, tokenStart)
        const afterStart = tokenStart + 1 + popoverQuery.value.length
        const after = currentText.slice(afterStart)
        setText(before + after)
      }
      pendingRefs.value.push(payload)
    }
    closePopover()
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
    openPicker,
    switchType,
    closePopover,
    removeRef,
    clearRefs,
  }
}
