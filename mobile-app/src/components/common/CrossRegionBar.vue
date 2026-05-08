<script setup>
// 全局顶部琥珀条 — 当用户切到非本位区时常驻显示, 提醒并提供"切回 ›"快捷操作
defineProps({
  regionFlag: { type: String, required: true },
  regionLabel: { type: String, required: true },
})
defineEmits(['back'])
</script>

<template>
  <div class="flex items-center gap-2 px-4 py-2"
    style="background: #FBF1DF; border-bottom: 1px solid #F6E4BE;">
    <span style="font-size: 13px;">{{ regionFlag }}</span>
    <span style="font-size: 12.5px; color: #6E4814; font-weight: 500;">
      正在浏览 · <strong style="font-weight: 700;">{{ regionLabel }}库</strong>
    </span>
    <button @click="$emit('back')" class="ml-auto active:opacity-70"
      style="font-size: 12px; color: #B8762A; font-weight: 600;">
      切回 ›
    </button>
  </div>
</template>
