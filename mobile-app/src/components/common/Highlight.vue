<script setup>
import { computed } from 'vue'

// 对齐 customer-screens.jsx Highlight：accentBg 底 + accent 文字
const props = defineProps({
  text:  { type: String, default: '' },
  query: { type: String, default: '' },
})

const parts = computed(() => {
  const t = props.text
  const q = props.query
  if (!q) return [{ text: t, hit: false }]
  const idx = t.indexOf(q)
  if (idx < 0) return [{ text: t, hit: false }]
  return [
    { text: t.slice(0, idx), hit: false },
    { text: q,                hit: true  },
    { text: t.slice(idx + q.length), hit: false },
  ]
})
</script>

<template>
  <span>
    <template v-for="(p, i) in parts" :key="i">
      <span v-if="p.hit" class="px-[2px] rounded-[3px]"
        style="background: var(--color-accent-bg); color: var(--color-accent);">{{ p.text }}</span>
      <template v-else>{{ p.text }}</template>
    </template>
  </span>
</template>
