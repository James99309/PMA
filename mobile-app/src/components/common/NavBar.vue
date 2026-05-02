<script setup>
defineProps({
  backLabel: { type: String, default: '' },
  title:     { type: String, default: '' },
})
defineEmits(['back', 'more'])
</script>

<template>
  <div class="flex items-center justify-between px-5 py-2.5">
    <button @click="$emit('back')"
      class="flex items-center gap-1 text-ink-2 text-[15px] active:opacity-60">
      <slot name="left">
        <svg width="9" height="14" viewBox="0 0 9 14">
          <path d="M7 1L1 7l6 6" fill="none" stroke="currentColor" stroke-width="1.6"
            stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        {{ backLabel }}
      </slot>
    </button>
    <div v-if="title" class="font-serif text-[16px] font-medium">{{ title }}</div>
    <button @click="$emit('more')" class="text-ink-3 text-[14px] active:opacity-60">
      <slot name="right">···</slot>
    </button>
  </div>
</template>
