<script setup>
// 对齐 customer-screens.jsx EditField (line 484-499)
// focused 态：accent-bg 0.04 浅底 + accent label/光标
import { computed } from 'vue'

const props = defineProps({
  label:    { type: String, required: true },
  modelValue: { type: [String, Number], default: '' },
  focused:  { type: Boolean, default: false },
  arrow:    { type: Boolean, default: false },
  readonly: { type: Boolean, default: false },
  type:     { type: String, default: 'text' },
})
defineEmits(['update:modelValue', 'click'])

const labelColor = computed(() => props.focused ? 'var(--color-accent)' : 'var(--color-ink-3)')
const labelWeight = computed(() => props.focused ? 600 : 400)
const bg = computed(() => props.focused ? 'rgba(217,119,87,0.04)' : 'transparent')
</script>

<template>
  <div class="px-4 py-3" :style="{ background: bg, borderBottom: '1px solid var(--color-divider)' }">
    <div class="text-[11px] mb-1" :style="{ color: labelColor, fontWeight: labelWeight }">{{ label }}</div>
    <div class="flex items-center justify-between gap-2"
      @click="$emit('click')">
      <input v-if="!readonly && !arrow"
        :value="modelValue"
        :type="type"
        @input="$emit('update:modelValue', $event.target.value)"
        class="flex-1 text-[15px] outline-none bg-transparent"
        :style="{ color: 'var(--color-ink)' }" />
      <span v-else class="text-[15px] flex items-center" :style="{ color: 'var(--color-ink)' }">
        {{ modelValue || '—' }}
        <span v-if="focused" class="pma-caret" />
      </span>
      <svg v-if="arrow" width="7" height="11" viewBox="0 0 7 11" fill="none" class="shrink-0">
        <path d="M1 1l4 4.5L1 10" stroke="var(--color-ink-3)" stroke-width="1.4" stroke-linecap="round" />
      </svg>
    </div>
  </div>
</template>
