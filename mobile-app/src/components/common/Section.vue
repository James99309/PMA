<script setup>
defineProps({
  title: { type: String, required: true },
})
</script>

<template>
  <div class="px-7 pt-5">
    <div class="flex items-center justify-between mb-3">
      <div class="text-[11px] font-semibold text-ink-3 uppercase"
        style="letter-spacing:1px">{{ title }}</div>
      <slot name="action" />
    </div>
    <slot />
  </div>
</template>
