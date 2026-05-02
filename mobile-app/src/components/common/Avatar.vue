<script setup>
import { computed } from 'vue'

// 对齐 customer-screens.jsx 联系人头像 + SearchCustomerRow 客户首字母头像
// shape: 'circle' (40 圆联系人头像) | 'square' (42 圆角 12 客户首字母方头像)
const props = defineProps({
  text:    { type: String, default: '' },
  size:    { type: Number, default: 40 },
  shape:   { type: String, default: 'circle' }, // 'circle' | 'square'
  primary: { type: Boolean, default: false },   // 主联系人 ★
  badge:   { type: String, default: '' },        // 客户层级 A/B/C 等
  badgeColor: { type: String, default: '#1A1A1A' },
})

const initial = computed(() => (props.text || '').charAt(0))
const radius = computed(() => props.shape === 'square' ? 12 : props.size / 2)
const fontSize = computed(() => Math.round(props.size * 0.42))
</script>

<template>
  <div class="relative shrink-0 inline-flex items-center justify-center font-serif font-medium"
    :style="{
      width: size + 'px',
      height: size + 'px',
      borderRadius: radius + 'px',
      background: 'var(--color-accent-soft)',
      color: 'var(--color-accent)',
      fontSize: fontSize + 'px',
    }">
    {{ initial }}
    <span v-if="primary"
      class="absolute -top-[3px] -right-[3px] w-4 h-4 rounded-full text-white text-[9px] font-bold inline-flex items-center justify-center"
      style="background: var(--color-ink); box-shadow: 0 0 0 2px var(--color-card);">★</span>
    <span v-else-if="badge"
      class="absolute -bottom-[2px] -right-[2px] w-4 h-4 rounded-full text-white text-[9px] font-bold inline-flex items-center justify-center"
      :style="{ background: badgeColor, boxShadow: '0 0 0 2px var(--color-card)' }">{{ badge }}</span>
  </div>
</template>
