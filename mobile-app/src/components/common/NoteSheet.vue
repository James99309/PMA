<script setup>
// 通用「添加跟进记录」底部弹层，被 ProjectDetailView / CustomerDetailView 共用
// 键盘弹起时使用 visualViewport API（最可靠跨平台）+ Capacitor Keyboard 双保险
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { Keyboard } from '@capacitor/keyboard'
import { Capacitor } from '@capacitor/core'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  submit:     { type: Function, required: true },
  title:      { type: String, default: '添加跟进记录' },
  placeholder:{ type: String, default: '输入跟进内容...' },
})
const emit = defineEmits(['update:modelValue'])

const text = ref('')
const submitting = ref(false)
const textareaRef = ref(null)
const kbOffset = ref(0)  // 键盘遮挡 panel 底部需要抬起的像素

watch(() => props.modelValue, async (v) => {
  if (v) {
    await nextTick()
    textareaRef.value?.focus()
  } else {
    text.value = ''
  }
})

// ─── visualViewport：当键盘弹起，window.innerHeight - visualViewport.height = 键盘高度
function recomputeFromVV() {
  const vv = window.visualViewport
  if (!vv) return
  const diff = window.innerHeight - vv.height - vv.offsetTop
  kbOffset.value = diff > 50 ? diff : 0
}

// ─── Capacitor Keyboard 事件作为兜底（iOS native resize 模式下 vv 可能不变）
let kbShowHandle, kbHideHandle
onMounted(async () => {
  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', recomputeFromVV)
    window.visualViewport.addEventListener('scroll', recomputeFromVV)
  }
  if (Capacitor.isNativePlatform?.()) {
    try {
      kbShowHandle = await Keyboard.addListener('keyboardWillShow', e => {
        if (e.keyboardHeight) kbOffset.value = e.keyboardHeight
      })
      kbHideHandle = await Keyboard.addListener('keyboardWillHide', () => {
        kbOffset.value = 0
      })
    } catch { /* ignore */ }
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

function close() {
  if (submitting.value) return
  emit('update:modelValue', false)
}

async function onSubmit() {
  const t = text.value.trim()
  if (!t || submitting.value) return
  submitting.value = true
  try {
    await props.submit(t)
    text.value = ''
    emit('update:modelValue', false)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="modelValue" class="fixed inset-0 z-50">
        <div class="absolute inset-0 bg-black/40" @click="close" />
        <!-- 用 bottom 直接定位到键盘上方，比 padding 方案更可靠 -->
        <div class="absolute left-0 right-0 rounded-t-3xl px-5 pt-4 pb-4"
          :style="{
            bottom: `${kbOffset}px`,
            background: 'var(--color-bg)',
            paddingBottom: kbOffset > 0 ? '12px' : 'calc(16px + env(safe-area-inset-bottom))',
            transition: 'bottom 0.2s ease',
          }">
          <div class="w-10 h-1 rounded-full mx-auto mb-4"
            style="background: var(--color-divider-strong);" />
          <p class="font-serif text-[17px] font-semibold mb-3"
            style="color: var(--color-ink);">{{ title }}</p>
          <textarea ref="textareaRef" v-model="text" rows="4"
            :placeholder="placeholder"
            class="w-full rounded-xl px-3 py-2.5 outline-none resize-none"
            style="font-size:16px; background: var(--color-card); border: 1px solid var(--color-divider); color: var(--color-ink);" />
          <div class="flex gap-2 mt-3">
            <button @click="close"
              class="flex-1 rounded-xl py-2.5 text-sm active:opacity-60"
              style="border: 1px solid var(--color-divider); color: var(--color-ink-2);">
              取消
            </button>
            <button @click="onSubmit" :disabled="submitting || !text.trim()"
              class="flex-1 rounded-xl py-2.5 text-sm font-semibold text-white disabled:opacity-50 active:opacity-90"
              style="background: var(--color-accent);">
              {{ submitting ? '提交中…' : '提交' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.sheet-enter-active, .sheet-leave-active { transition: opacity .2s ease; }
.sheet-enter-from, .sheet-leave-to       { opacity: 0; }
</style>
