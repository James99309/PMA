<script setup>
// 严格对齐 chat-bridge.jsx ProjectRefCard (line 219-238)
defineProps({
  name:      { type: String, required: true },
  stage:     { type: String, default: '' },
  stageTone: { type: String, default: '#7A7570' },  // 阶段彩点颜色
  amount:    { type: [String, Number], default: '' },
  owner:     { type: String, default: '' },
  region:    { type: String, default: '' },
})
defineEmits(['click'])
</script>

<template>
  <div @click="$emit('click')"
    class="rounded-xl p-3 flex gap-3 active:opacity-80 cursor-pointer"
    style="background: var(--color-card); border: 1px solid var(--color-divider-strong);">
    <div class="w-9 h-9 rounded-[9px] inline-flex items-center justify-center text-[16px] font-bold shrink-0"
      style="background: var(--color-ink); color: #fff;">#</div>
    <div class="flex-1 min-w-0">
      <div class="text-[9px] font-bold uppercase" style="color: var(--color-ink-3); letter-spacing: 1px;">项目</div>
      <div class="font-serif mt-px truncate"
        style="font-size: 14px; font-weight: 500; line-height: 1.3;">{{ name }}</div>
      <div class="flex flex-wrap items-center gap-1.5 mt-1 text-[11px]"
        style="color: var(--color-ink-3);">
        <span class="font-semibold" :style="{ color: stageTone }">● {{ stage }}</span>
        <span>·</span>
        <span class="font-semibold tabular" style="color: var(--color-ink);">¥{{ amount }}万</span>
        <template v-if="owner || region">
          <span>·</span>
          <span>{{ [owner, region].filter(Boolean).join(' · ') }}</span>
        </template>
      </div>
    </div>
    <div class="self-center text-[18px]" style="color: var(--color-ink-3);">›</div>
  </div>
</template>
