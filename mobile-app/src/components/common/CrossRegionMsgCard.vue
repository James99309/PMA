<script setup>
// 列表顶部琥珀卡 — 在本区聊天列表顶部显示对区有未读, 点击 → 切区
defineProps({
  regionFlag: { type: String, required: true },
  regionLabel: { type: String, required: true },
  unreadCount: { type: Number, default: 0 },
})
defineEmits(['goto'])
</script>

<template>
  <button @click="$emit('goto')"
    class="w-full flex items-center gap-3 active:opacity-80 text-left"
    style="margin: 8px 12px 4px; padding: 12px 14px;
           background: #FBF1DF; border: 1px solid #F6E4BE; border-radius: 12px;
           width: calc(100% - 24px);">
    <div class="shrink-0 inline-flex items-center justify-center"
      style="width: 38px; height: 38px; border-radius: 10px;
             background: #fff; border: 1px solid #F6E4BE; font-size: 20px;">
      {{ regionFlag }}
    </div>
    <div class="flex-1 min-w-0">
      <div class="flex items-baseline gap-1.5">
        <span style="font-size: 14px; font-weight: 600; color: #6E4814;">{{ regionLabel }}库</span>
        <span style="font-size: 13px; color: #6E4814; font-weight: 500;">· {{ unreadCount }} 条新消息</span>
      </div>
      <div style="font-size: 11.5px; color: #B8762A; margin-top: 3px; font-weight: 500;">
        点击切到 {{ regionLabel }}库查看
      </div>
    </div>
    <span class="shrink-0" style="font-size: 12.5px; color: #B8762A; font-weight: 600;">
      切去看 ›
    </span>
  </button>
</template>
