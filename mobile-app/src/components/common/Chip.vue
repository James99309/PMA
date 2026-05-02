<script setup>
// 对齐 customer-screens.jsx Chip(active) + filter-screens.jsx Chip(closeable, count)
defineProps({
  label:     { type: String, required: true },
  active:    { type: Boolean, default: false },
  closeable: { type: Boolean, default: false },
  count:     { type: [Number, String], default: null },
})
defineEmits(['click', 'close'])
</script>

<template>
  <button
    type="button"
    @click="$emit('click')"
    class="inline-flex items-center gap-1.5 px-[13px] py-[7px] rounded-full text-[13px] transition-colors active:opacity-70"
    :style="active
      ? { background: 'var(--color-ink)', color: '#fff', border: 'none', fontWeight: 600 }
      : { background: 'var(--color-card)', color: 'var(--color-ink-2)', border: '1px solid var(--color-divider-strong)', fontWeight: 500 }">
    {{ label }}
    <span v-if="count != null"
      class="text-[10px] font-semibold px-1 rounded-full"
      :style="active ? { background: 'rgba(255,255,255,0.18)' } : { background: 'var(--color-divider)' }">
      {{ count }}
    </span>
    <span v-if="closeable && active"
      @click.stop="$emit('close')"
      class="text-[10px] opacity-70 -mr-1 ml-0.5 px-1">×</span>
  </button>
</template>
