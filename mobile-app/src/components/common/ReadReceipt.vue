<script setup>
// WhatsApp 风格已读回执
// status:
//   'sending'   → 单灰勾（本地发出，未到服务器）
//   'delivered' → 双灰勾（已到服务器，对方未读）
//   'read'      → 双蓝勾（对方已读）
defineProps({
  status: { type: String, default: '' },  // sending / delivered / read
})

const COLOR_GREY = '#9CA3AF'
const COLOR_BLUE = '#34B7F1'  // WhatsApp 蓝
</script>

<template>
  <!-- 单勾：发送中 -->
  <svg v-if="status === 'sending'" width="14" height="11" viewBox="0 0 14 11"
    style="display: inline-block; vertical-align: middle;">
    <path d="M1.5 6l3 3 7-7" :stroke="COLOR_GREY" stroke-width="1.4"
      fill="none" stroke-linecap="round" stroke-linejoin="round" />
  </svg>

  <!-- 双勾：已送达（灰）/ 已读（蓝） -->
  <svg v-else-if="status === 'delivered' || status === 'read'"
    width="17" height="11" viewBox="0 0 17 11"
    style="display: inline-block; vertical-align: middle;">
    <path d="M1 6l3 3 6-6" :stroke="status === 'read' ? COLOR_BLUE : COLOR_GREY"
      stroke-width="1.4" fill="none" stroke-linecap="round" stroke-linejoin="round" />
    <path d="M6 6l3 3 7-7" :stroke="status === 'read' ? COLOR_BLUE : COLOR_GREY"
      stroke-width="1.4" fill="none" stroke-linecap="round" stroke-linejoin="round" />
  </svg>
</template>
