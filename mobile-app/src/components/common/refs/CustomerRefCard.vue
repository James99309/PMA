<script setup>
// 严格对齐 chat-bridge.jsx CustomerRefCard (line 240-264)
defineProps({
  name:    { type: String, required: true },
  tier:    { type: String, default: '' },     // A/B/C，可选
  status:  { type: String, default: '活跃' },
  value:   { type: [String, Number], default: 0 },
  contact: { type: String, default: '' },
})
defineEmits(['click'])
</script>

<template>
  <div @click="$emit('click')"
    class="rounded-xl p-3 flex gap-3 active:opacity-80 cursor-pointer"
    style="background: var(--color-card); border: 1px solid var(--color-divider-strong);">
    <div class="relative shrink-0 w-9 h-9 rounded-[9px] inline-flex items-center justify-center text-[14px] font-bold"
      style="background: var(--color-accent); color: #fff;">
      $
      <span v-if="tier"
        class="absolute -bottom-[3px] -right-[3px] w-[14px] h-[14px] rounded-full text-white text-[8px] font-bold inline-flex items-center justify-center"
        style="background: var(--color-ink); box-shadow: 0 0 0 2px var(--color-card);">{{ tier }}</span>
    </div>
    <div class="flex-1 min-w-0">
      <div class="text-[9px] font-bold uppercase" style="color: var(--color-ink-3); letter-spacing: 1px;">客户</div>
      <div class="font-serif mt-px truncate"
        style="font-size: 14px; font-weight: 500; line-height: 1.3;">{{ name }}</div>
      <div class="flex items-center gap-1.5 mt-1 text-[11px]" style="color: var(--color-ink-3);">
        <span class="font-semibold" style="color: var(--color-green);">● {{ status }}</span>
        <span>·</span>
        <span class="font-semibold tabular" style="color: var(--color-ink);">¥{{ value }}万</span>
      </div>
      <div v-if="contact" class="text-[11px] mt-0.5 italic font-serif"
        style="color: var(--color-ink-3);">{{ contact }}</div>
    </div>
    <div class="self-center text-[18px]" style="color: var(--color-ink-3);">›</div>
  </div>
</template>
