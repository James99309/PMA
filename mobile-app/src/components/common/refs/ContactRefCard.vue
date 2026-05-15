<script setup>
// 严格对齐 chat-bridge.jsx ContactRefCard (line 293-319)
import { computed } from 'vue'

const props = defineProps({
  name:    { type: String, required: true },
  role:    { type: String, default: '' },
  company: { type: String, default: '' },
  phone:   { type: String, default: '' },
})
defineEmits(['call', 'add'])

const initial = computed(() => (props.name || '').charAt(0))
</script>

<template>
  <div class="rounded-xl p-3"
    style="background: var(--color-card); border: 1px solid var(--color-divider-strong);">
    <div class="flex gap-3 items-center">
      <div class="w-10 h-10 rounded-full inline-flex items-center justify-center font-serif font-semibold shrink-0"
        style="background: var(--color-accent-soft); color: var(--color-accent); font-size: 16px;">{{ initial }}</div>
      <div class="flex-1 min-w-0">
        <div class="text-[9px] font-bold uppercase" style="color: var(--color-ink-3); letter-spacing: 1px;">联系人</div>
        <div class="font-serif" style="font-size: 14px; font-weight: 500; line-height: 1.3;">
          {{ name }}<template v-if="role"> · <span class="text-[12px]" style="color: var(--color-ink-3);">{{ role }}</span></template>
        </div>
        <div v-if="company" class="text-[11px] mt-0.5 italic font-serif"
          style="color: var(--color-ink-3);">{{ company }}</div>
      </div>
    </div>
    <div v-if="phone" class="mt-2.5 pt-2.5 flex items-center gap-2.5"
      style="border-top: 1px dashed var(--color-divider);">
      <span class="text-[12px] font-medium tabular" style="color: var(--color-ink-2);">{{ phone }}</span>
      <div class="ml-auto flex gap-1.5">
        <button @click="$emit('call')"
          class="w-8 h-8 rounded-full inline-flex items-center justify-center active:opacity-70"
          style="border: 1px solid var(--color-divider-strong); background: transparent;">
          <svg width="13" height="13" viewBox="0 0 14 14">
            <path d="M3 2l2 3-1.5 1.5a8 8 0 004 4L9 9l3 2-1 2.5a1 1 0 01-1 .5C5.5 14 0 8.5 0 4a1 1 0 01.5-1L3 2z"
              fill="var(--color-ink-2)" />
          </svg>
        </button>
        <button @click="$emit('add')"
          class="w-8 h-8 rounded-full text-white text-[12px] font-bold inline-flex items-center justify-center active:opacity-80"
          style="background: var(--color-accent); border: none;">+</button>
      </div>
    </div>
  </div>
</template>
