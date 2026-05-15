<!--
  ExNav · 报销模块顶部导航条
  严格对齐 design_handoff/expense-list-form.jsx::ExNav (L5-19)
  - 位置: top=STATUS_PAD(54), height=48
  - 背景: EX.bg, 底部 1px 实色 divider
  - 返回箭头: 32x32, 字号 22, 颜色 ink2
  - 标题: 15/600 ink, sub 11 ink3
-->
<template>
  <div
    class="absolute left-0 right-0 z-[5] flex items-center px-3 border-b"
    :style="{
      top: '54px',
      height: '48px',
      background: 'var(--color-ex-bg)',
      borderColor: 'var(--color-ex-divider)',
    }"
  >
    <div
      v-if="back"
      class="flex items-center justify-center"
      :style="{ width: '32px', height: '32px', fontSize: '22px', color: 'var(--color-ex-ink2)' }"
      @click="$emit('back')"
    >
      ‹
    </div>
    <div class="flex-1 min-w-0" :style="{ paddingLeft: back ? '4px' : '12px' }">
      <div
        class="truncate"
        :style="{ fontSize: '15px', fontWeight: 600, color: 'var(--color-ex-ink)' }"
      >{{ title }}</div>
      <div
        v-if="sub"
        class="truncate"
        :style="{ fontSize: '11px', marginTop: '1px', color: 'var(--color-ex-ink3)' }"
      >{{ sub }}</div>
    </div>
    <div v-if="$slots.right" class="pr-1.5">
      <slot name="right" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  sub: { type: String, default: '' },
  back: { type: Boolean, default: true },
})
defineEmits(['back'])
</script>
