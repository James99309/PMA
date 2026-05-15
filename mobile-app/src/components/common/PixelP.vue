<script setup>
// PMA 像素 P logo —— 严格对齐 splash-login.jsx PIXEL_P + cellColor
import { computed } from 'vue'

const props = defineProps({
  size:    { type: Number, default: 200 },
  state:   { type: String, default: 'static' }, // 'static' | 'splash' (build-in animation)
  rounded: { type: Boolean, default: true },
  bg:      { type: String, default: 'transparent' }, // 整体背景；splash 内圆形可用 navy
})

// PIXEL_P 数据（splash-login.jsx line 16-24）
// 18 格，6 行 × 5 列；t: b=亮蓝 / d=深蓝 / w=白 / h=洞（与 bg 同色）
const PIXEL_P = [
  { r: 0, c: 1, t: 'b' }, { r: 0, c: 2, t: 'b' }, { r: 0, c: 3, t: 'b' }, { r: 0, c: 4, t: 'b' },
  { r: 1, c: 1, t: 'b' }, { r: 1, c: 4, t: 'b' },
  { r: 2, c: 1, t: 'b' }, { r: 2, c: 3, t: 'w' }, { r: 2, c: 4, t: 'h' }, { r: 2, c: 5, t: 'b' },
  { r: 3, c: 1, t: 'b' }, { r: 3, c: 2, t: 'b' }, { r: 3, c: 3, t: 'b' }, { r: 3, c: 4, t: 'b' },
  { r: 4, c: 1, t: 'b' }, { r: 4, c: 2, t: 'd' },
  { r: 5, c: 1, t: 'b' }, { r: 5, c: 2, t: 'd' },
]

const COLOR = {
  b: '#4D82E0',  // 亮蓝
  d: '#2F66D6',  // 深蓝
  w: '#FFFFFF',  // 白
  h: '#0E1828',  // 洞（深 navy）
}

const cell    = computed(() => props.size / 6.6)
const gap     = computed(() => cell.value * 0.16)
const radius  = computed(() => props.rounded ? cell.value * 0.18 : 0)
const totalW  = computed(() => cell.value * 6 + gap.value * 5)
</script>

<template>
  <div :class="['pixel-p-wrap', state === 'splash' ? 'splash' : '']"
    :style="{
      width: totalW + 'px', height: totalW + 'px',
      position: 'relative',
      background: bg,
    }">
    <div v-for="(p, i) in PIXEL_P" :key="`${p.r}-${p.c}`"
      :class="['pixel-cell', state === 'splash' ? 'splash-anim' : '']"
      :style="{
        position: 'absolute',
        left: (p.c * (cell + gap)) + 'px',
        top:  (p.r * (cell + gap)) + 'px',
        width: cell + 'px', height: cell + 'px',
        borderRadius: radius + 'px',
        background: COLOR[p.t],
        animationDelay: state === 'splash' ? (i * 50) + 'ms' : '0ms',
      }" />
  </div>
</template>

<style scoped>
.pixel-cell.splash-anim {
  opacity: 0;
  transform: scale(0.4);
  animation: pixelPop 500ms cubic-bezier(.34, 1.56, .64, 1) forwards;
}
@keyframes pixelPop {
  0%   { opacity: 0; transform: scale(0.4); }
  60%  { opacity: 1; transform: scale(1.12); box-shadow: 0 0 20px rgba(77, 130, 224, 0.6); }
  100% { opacity: 1; transform: scale(1); box-shadow: none; }
}
</style>
