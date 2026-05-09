<!--
  ExRow · 报销表单单行(label/value/sub/right)
  严格对齐 design_handoff/expense-list-form.jsx::RowEx (L428-440)
  - 卡片背景, padding 12/20, 顶部 1px dividerSoft
  - label: 84px 宽, 12px ink3
  - value: 14px ink, 行高 multi=1.55 / 否则 1.4
  - sub: 11px ink4, marginTop 2
-->
<template>
  <div
    class="flex"
    :style="{
      background: 'var(--color-ex-card)',
      padding: '12px 20px',
      borderTop: '1px solid var(--color-ex-divider-soft)',
      gap: '12px',
      alignItems: multi ? 'flex-start' : 'center',
    }"
  >
    <div
      class="flex-shrink-0"
      :style="{
        width: '84px',
        fontSize: '12px',
        color: 'var(--color-ex-ink3)',
        paddingTop: multi ? '2px' : '0',
      }"
    >{{ label }}</div>
    <div class="flex-1 min-w-0">
      <div
        :style="{
          fontSize: '14px',
          color: 'var(--color-ex-ink)',
          lineHeight: multi ? 1.55 : 1.4,
        }"
      >
        <slot>{{ value }}</slot>
      </div>
      <div
        v-if="sub"
        :style="{
          fontSize: '11px',
          color: 'var(--color-ex-ink4)',
          marginTop: '2px',
        }"
      >{{ sub }}</div>
    </div>
    <div v-if="$slots.right" :style="{ fontSize: '13px' }">
      <slot name="right" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '' },
  sub: { type: String, default: '' },
  multi: { type: Boolean, default: false },
})
</script>
