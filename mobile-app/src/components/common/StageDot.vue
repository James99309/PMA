<script setup>
import { computed } from 'vue'

// 严格对齐 customer-screens.jsx StageDot 配色（5 tone）
// + screens.jsx AStageDot 的 6 tone 补 'pre_tender' 与 'paused'
const TONE_MAP = {
  discover:   { color: '#7A7570', label: '发现' },
  embed:      { color: '#7A7570', label: '嵌入' },
  pre_tender: { color: '#7A7570', label: '预招标' },
  bidding:    { color: '#D97757', label: '招标中' },
  tendering:  { color: '#D97757', label: '招标中' },
  awarded:    { color: '#D97757', label: '授权' },
  quoted:     { color: '#D97757', label: '已报价' },
  won:        { color: '#1A1A1A', label: '签约' },
  signed:     { color: '#1A1A1A', label: '签约' },
  lost:       { color: '#C2BBB3', label: '丢单' },
  paused:     { color: '#C2BBB3', label: '暂停' },
}

const props = defineProps({
  tone:  { type: String, default: 'discover' },
  label: { type: String, default: '' },
})

const meta = computed(() => TONE_MAP[props.tone] || TONE_MAP.discover)
const text = computed(() => props.label || meta.value.label)
</script>

<template>
  <span class="inline-flex items-center gap-1.5 text-[12px] font-medium"
    :style="{ color: meta.color, letterSpacing: '0.2px' }">
    <span class="w-[5px] h-[5px] rounded-[3px]" :style="{ background: meta.color }" />
    {{ text }}
  </span>
</template>
