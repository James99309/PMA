<!--
  ExDefRow · 定义列表行(详情卡用)
  严格对齐 design_handoff/expense-list-form.jsx::DefRow (L449-457)
  - padding 11/20, gap 12, 底部 1px dividerSoft (last 隐藏)
  - label 84px 12px ink3
  - value 13/ink, lineHeight 1.55
-->
<template>
  <div
    class="flex"
    :style="{
      padding: '11px 20px',
      gap: '12px',
      borderBottom: last ? 'none' : '1px solid var(--color-ex-divider-soft)',
    }"
  >
    <div
      class="flex-shrink-0"
      :style="{
        width: '84px',
        fontSize: '12px',
        color: 'var(--color-ex-ink3)',
      }"
    >{{ label }}</div>
    <div
      class="flex-1"
      :style="{
        fontSize: '13px',
        color: 'var(--color-ex-ink)',
        lineHeight: 1.55,
      }"
    >
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  last: { type: Boolean, default: false },
})
</script>
