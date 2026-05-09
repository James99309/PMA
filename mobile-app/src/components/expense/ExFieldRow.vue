<!--
  ExFieldRow · OCR 核对字段行
  严格对齐 design_handoff/expense-receipt.jsx::FieldRow (L293-306)
  - 卡片背景, warn 时切 warnSoft 背景
  - padding 12/20, 顶部 1px dividerSoft
  - label 84px 12px ink3 (paddingTop 2)
  - value 14/500, warn 时 warn 颜色
  - note 10px ink4 (warn 时同色 warn)
  - 末尾: lock 时 🔒, 否则 ›
-->
<template>
  <div
    class="flex"
    :style="{
      background: warn ? 'var(--color-ex-warn-soft)' : 'var(--color-ex-card)',
      padding: '12px 20px',
      borderTop: '1px solid var(--color-ex-divider-soft)',
      gap: '12px',
      alignItems: 'flex-start',
    }"
  >
    <div
      class="flex-shrink-0"
      :style="{
        width: '84px',
        fontSize: '12px',
        color: 'var(--color-ex-ink3)',
        paddingTop: '2px',
      }"
    >{{ label }}</div>
    <div class="flex-1">
      <div
        :style="{
          fontSize: '14px',
          fontWeight: 500,
          color: warn ? 'var(--color-ex-warn)' : 'var(--color-ex-ink)',
        }"
      >
        <slot>{{ value }}</slot>
      </div>
      <div
        v-if="note"
        :style="{
          fontSize: '10px',
          marginTop: '3px',
          color: warn ? 'var(--color-ex-warn)' : 'var(--color-ex-ink4)',
        }"
      >{{ note }}</div>
    </div>
    <div
      v-if="lock"
      :style="{ fontSize: '12px', color: 'var(--color-ex-ink4)' }"
    >🔒</div>
    <div
      v-else
      :style="{ fontSize: '13px', color: 'var(--color-ex-ink4)' }"
    >›</div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '' },
  note: { type: String, default: '' },
  warn: { type: Boolean, default: false },
  lock: { type: Boolean, default: false },
})
</script>
