<script setup>
// 对齐 customer-screens.jsx FilledField (12px label / 15px or 17px value / arrow / pin)
defineProps({
  label:       { type: String, default: '' },
  value:       { type: String, default: '' },
  big:         { type: Boolean, default: false },  // 公司名等：衬线 17px
  arrow:       { type: Boolean, default: false },
  pin:         { type: Boolean, default: false },
  accent:      { type: Boolean, default: false },  // value 用 accent 色（如 A 类）
  placeholder: { type: String, default: '' },
})
</script>

<template>
  <div class="px-4 py-3 border-b" style="border-color: var(--color-divider);">
    <div class="text-[11px] mb-1" style="color: var(--color-ink-3);">{{ label }}</div>
    <div class="flex items-center justify-between gap-2">
      <span
        :class="['truncate', big ? 'font-serif text-[17px] font-medium' : 'text-[15px]']"
        :style="{ color: accent ? 'var(--color-accent)' : (value ? 'var(--color-ink)' : 'var(--color-ink-3)') }">
        {{ value || placeholder || '—' }}
      </span>
      <svg v-if="arrow" width="7" height="11" viewBox="0 0 7 11" fill="none" class="shrink-0">
        <path d="M1 1l4 4.5L1 10" stroke="var(--color-ink-3)" stroke-width="1.4" stroke-linecap="round" />
      </svg>
      <svg v-if="pin" width="14" height="14" viewBox="0 0 14 14" fill="none" class="shrink-0">
        <path d="M7 1c2.5 0 4 1.8 4 4 0 3-4 7-4 7s-4-4-4-7c0-2.2 1.5-4 4-4z"
          stroke="var(--color-accent)" stroke-width="1.3" />
        <circle cx="7" cy="5" r="1.3" fill="var(--color-accent)" />
      </svg>
    </div>
  </div>
</template>
