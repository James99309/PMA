<script setup>
// 对齐 customer-screens.jsx FilterGroup
defineProps({
  label: { type: String, required: true },
})
</script>

<template>
  <div class="py-3">
    <div class="text-[11px] font-semibold uppercase mb-2.5"
      style="color: var(--color-ink-3); letter-spacing: 1px;">{{ label }}</div>
    <div class="flex flex-wrap gap-2">
      <slot />
    </div>
  </div>
</template>
