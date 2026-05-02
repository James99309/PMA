<script setup>
// 消息文字渲染（含 @/#/$/§ token 自动着色）
// 用法：放在 bubble 内部替代直接 {{ m.text }}
import { computed } from 'vue'
import { parseMessageText, TRIGGER_COLOR, TRIGGER_COLOR_INVERTED } from '@/utils/mentionRender'

const props = defineProps({
  text:     { type: String, default: '' },
  inverted: { type: Boolean, default: false },  // 黑底气泡 → 用浅色 token
})

const segments = computed(() => parseMessageText(props.text))
const colorMap = computed(() => props.inverted ? TRIGGER_COLOR_INVERTED : TRIGGER_COLOR)
</script>

<template>
  <template v-for="(seg, i) in segments" :key="i">
    <span v-if="seg.kind === 'mention'" class="font-semibold"
      :style="{ color: colorMap[seg.trigger] }">{{ seg.text }}</span>
    <template v-else>{{ seg.text }}</template>
  </template>
</template>
