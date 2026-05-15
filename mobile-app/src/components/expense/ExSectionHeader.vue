<!--
  ExSectionHeader · 区块标题(eyebrow)
  严格对齐 design_handoff/expense-list-form.jsx::SectionHeader (L442-447)
  - padding 20/20/6, 11/600 ink3, letterSpacing 0.6, uppercase
-->
<template>
  <div
    :style="{
      padding: '20px 20px 6px',
      fontSize: '11px',
      fontWeight: 600,
      color: 'var(--color-ex-ink3)',
      letterSpacing: '0.6px',
      textTransform: 'uppercase',
    }"
  >
    <slot />
  </div>
</template>
