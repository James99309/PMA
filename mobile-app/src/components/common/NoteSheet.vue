<script setup>
// 通用「添加跟进记录」底部弹层，被 ProjectDetailView / CustomerDetailView 共用
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // 提交回调：传入 text，需返回 Promise；resolve 后自动关闭并清空
  submit:     { type: Function, required: true },
  title:      { type: String, default: '添加跟进记录' },
  placeholder:{ type: String, default: '输入跟进内容...' },
})
const emit = defineEmits(['update:modelValue'])

const text = ref('')
const submitting = ref(false)
const textareaRef = ref(null)

watch(() => props.modelValue, async (v) => {
  if (v) {
    await nextTick()
    textareaRef.value?.focus()
  } else {
    text.value = ''
  }
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
      <div v-if="modelValue" class="fixed inset-0 z-50 flex flex-col justify-end">
        <div class="absolute inset-0 bg-black/40" @click="close" />
        <div class="relative rounded-t-3xl px-5 pt-4"
          :style="{ background: 'var(--color-bg)', paddingBottom: 'calc(16px + env(safe-area-inset-bottom))' }">
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
