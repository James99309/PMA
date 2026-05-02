<script setup>
// 阶段推进卡 —— 严格对齐 chat-screens.jsx StageAdvance 内的核心 box (line 372-414)
// 用法：聊天流里作为系统消息 kind='stage-advance' 渲染
defineProps({
  fromStage: { type: String, required: true },
  toStage:   { type: String, required: true },
  byName:    { type: String, default: '' },
  byInitial: { type: String, default: '' },
  time:      { type: String, default: '' },
  note:      { type: String, default: '' },     // 备注（衬线斜体引用样式）
})
</script>

<template>
  <div class="px-5 py-4">
    <div class="rounded-2xl p-4 relative"
      style="background: var(--color-card); border: 1px solid var(--color-divider);">

      <!-- 浮标 "阶段推进" -->
      <div class="absolute -top-2 left-4 text-[10px] font-semibold uppercase px-2 py-px"
        style="color: var(--color-accent); background: var(--color-bg); letter-spacing: 1px;">阶段推进</div>

      <!-- 从 → 到 -->
      <div class="flex items-center gap-3 mt-1">
        <div class="flex-1">
          <div class="text-[11px] font-semibold uppercase"
            style="color: var(--color-ink-3); letter-spacing: 0.5px;">从</div>
          <div class="font-serif mt-0.5"
            style="font-size: 17px; font-weight: 500; color: var(--color-ink-2);">{{ fromStage }}</div>
        </div>
        <svg width="32" height="22" viewBox="0 0 32 22">
          <path d="M2 11h26m-6-6l6 6-6 6" stroke="var(--color-accent)" stroke-width="1.6"
            fill="none" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <div class="flex-1 text-right">
          <div class="text-[11px] font-semibold uppercase"
            style="color: var(--color-accent); letter-spacing: 0.5px;">到</div>
          <div class="font-serif mt-0.5"
            style="font-size: 17px; font-weight: 500; color: var(--color-ink);">{{ toStage }}</div>
        </div>
      </div>

      <!-- 操作人 + 时间 -->
      <div class="my-3.5 h-px" style="background: var(--color-divider);" />
      <div class="flex items-center gap-2">
        <div class="w-6 h-6 rounded-full inline-flex items-center justify-center font-serif text-[11px] font-semibold"
          style="background: var(--color-accent-soft); color: var(--color-accent);">{{ byInitial || (byName || '?').charAt(0) }}</div>
        <div class="flex-1 text-[12px]" style="color: var(--color-ink-2);">
          <span style="font-weight: 500;">{{ byName }}</span>
          <span class="font-serif italic" style="color: var(--color-ink-3);"> 推进了阶段</span>
        </div>
        <div class="text-[10px] tabular" style="color: var(--color-ink-3);">{{ time }}</div>
      </div>

      <!-- 备注（衬线斜体引用） -->
      <div v-if="note" class="mt-3 px-3 py-2.5 rounded-lg font-serif italic"
        style="background: var(--color-bg); font-size: 13px; color: var(--color-ink-2); line-height: 1.5;">
        「{{ note }}」
      </div>
    </div>
  </div>
</template>
