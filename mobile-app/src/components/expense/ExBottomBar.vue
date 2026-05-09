<!--
  ExBottomBar · 表单底部 CTA
  严格对齐 design_handoff/expense-list-form.jsx::ExBottomBar (L488-505)
  - 绝对底部, padding 12/16/28(留 home indicator)
  - 卡片背景, 顶部 1px divider
  - 左 secondary: flex-1, 46px 高, 23 圆角, 1.5px divider 边
  - 右 primary: flex-2, 46px 高, ink 背景白字; disabled → divider 背景 ink4 字
-->
<template>
  <div
    class="absolute bottom-0 left-0 right-0 flex"
    :style="{
      padding: '12px 16px 28px',
      background: 'var(--color-ex-card)',
      borderTop: '1px solid var(--color-ex-divider)',
      gap: '10px',
    }"
  >
    <div
      class="flex-1 flex items-center justify-center"
      :style="{
        height: '46px',
        borderRadius: '23px',
        background: 'var(--color-ex-card)',
        border: '1.5px solid var(--color-ex-divider)',
        color: 'var(--color-ex-ink2)',
        fontSize: '14px',
        fontWeight: 600,
      }"
      @click="$emit('secondary')"
    >
      {{ secondary }}
    </div>
    <div
      class="flex items-center justify-center"
      :style="{
        flex: 2,
        height: '46px',
        borderRadius: '23px',
        background: disabled ? 'var(--color-ex-divider)' : 'var(--color-ex-ink)',
        color: disabled ? 'var(--color-ex-ink4)' : 'var(--color-ex-card)',
        fontSize: '14px',
        fontWeight: 600,
      }"
      @click="!disabled && $emit('primary')"
    >
      {{ primary }}
    </div>
  </div>
</template>

<script setup>
defineProps({
  primary: { type: String, required: true },
  secondary: { type: String, required: true },
  disabled: { type: Boolean, default: false },
})
defineEmits(['primary', 'secondary'])
</script>
