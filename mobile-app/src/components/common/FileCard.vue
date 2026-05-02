<script setup>
// 文件附件卡 —— 严格对齐 chat-screens.jsx DMChat (line 433-447) 风格
// 在「我的消息」黑底气泡里 inverted=true，对方消息白底 inverted=false
import { computed } from 'vue'

const props = defineProps({
  name:     { type: String, required: true },
  size:     { type: String, default: '' },        // '2.4 MB'
  pages:    { type: [String, Number], default: '' }, // 12
  type:     { type: String, default: 'PDF' },     // PDF / DOC / XLS / IMG
  inverted: { type: Boolean, default: false },    // 我的消息黑底
})
defineEmits(['click'])

const meta = computed(() => [props.size, props.pages ? `${props.pages} 页` : ''].filter(Boolean).join(' · '))
</script>

<template>
  <button @click="$emit('click')"
    class="rounded-2xl px-3 py-2.5 inline-flex items-center gap-2.5 max-w-[260px] active:opacity-80 text-left"
    :style="inverted
      ? { background: 'var(--color-ink)', color: '#fff', borderTopRightRadius: '4px', border: 'none' }
      : { background: 'var(--color-card)', color: 'var(--color-ink)', borderTopLeftRadius: '4px', border: '1px solid var(--color-divider)' }">
    <!-- 文件类型角标 -->
    <div class="w-9 h-11 rounded-md inline-flex items-center justify-center text-[9px] font-semibold shrink-0"
      :style="inverted
        ? { background: 'rgba(255,255,255,0.12)', color: '#fff', letterSpacing: '0.5px' }
        : { background: 'var(--color-accent-soft)', color: 'var(--color-accent)', letterSpacing: '0.5px' }">
      {{ type }}
    </div>
    <div class="flex-1 min-w-0">
      <div class="font-serif truncate" style="font-size: 13px; line-height: 1.3;">{{ name }}</div>
      <div class="text-[10px] mt-0.5 tabular"
        :style="{ opacity: inverted ? 0.6 : 1, color: inverted ? '#fff' : 'var(--color-ink-3)' }">
        {{ meta }}
      </div>
    </div>
  </button>
</template>
