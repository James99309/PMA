<script setup>
// 语音消息卡 —— 严格对齐 chat-screens.jsx DMChat 语音波形 (line 451-467)
// 14 根波形条 + ▶ 播放按钮 + 时长 tabular
import { ref, computed } from 'vue'

const props = defineProps({
  duration: { type: String, default: '00:00' },  // '00:08'
  // 波形（mock，14 根 5-20px 高度）—— 真实接入时由后端 / WebAudio 出频谱
  waveform: {
    type: Array,
    default: () => [6, 11, 8, 15, 12, 18, 9, 14, 7, 11, 5, 9, 12, 8],
  },
  inverted: { type: Boolean, default: false },   // 我的消息黑底
})

const playing = ref(false)
function toggle() {
  playing.value = !playing.value
  // 真接入后这里 audio.play()/pause()
}
</script>

<template>
  <div class="rounded-2xl px-3.5 py-2.5 inline-flex items-center gap-2.5"
    :style="inverted
      ? { background: 'var(--color-ink)', borderTopRightRadius: '4px', border: 'none' }
      : { background: 'var(--color-card)', borderTopLeftRadius: '4px', border: '1px solid var(--color-divider)' }">
    <!-- 播放按钮 -->
    <button @click="toggle"
      class="w-[26px] h-[26px] rounded-full inline-flex items-center justify-center text-[10px] text-white shrink-0 active:opacity-80"
      style="background: var(--color-accent);">
      {{ playing ? '❚❚' : '▶' }}
    </button>
    <!-- 波形 -->
    <div class="inline-flex items-end gap-[2px] h-5">
      <div v-for="(h, i) in waveform" :key="i"
        :style="{
          width: '2px',
          height: h + 'px',
          background: inverted ? '#fff' : 'var(--color-ink-2)',
          borderRadius: '1px',
          opacity: playing && i < waveform.length / 2 ? 0.6 : 1,
        }" />
    </div>
    <!-- 时长 -->
    <span class="text-[11px] tabular shrink-0"
      :style="{ color: inverted ? 'rgba(255,255,255,0.65)' : 'var(--color-ink-3)' }">
      {{ duration }}
    </span>
  </div>
</template>
