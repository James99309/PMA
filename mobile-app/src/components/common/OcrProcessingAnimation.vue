<!--
  OcrProcessingAnimation · 通用 OCR 识别动画
  从 ReceiptProcessingView 提取, 名片扫描/发票识别等共用。

  视觉:
    - 上方: 卡片堆叠(单张/双张/三张可选) + 横向扫描线
    - 中间: 主标题 (serif 22)
    - 下方: 副标题 (12 ink3)
    - 字段揭示列表(stagger 250ms 淡入), 可选

  Props:
    cardCount   1 | 2 | 3        卡片堆叠张数, 默认 3
    title       主标题, e.g. "正在识别 1 张名片"
    subtitle    副标题, e.g. "通常 2-5 秒"
    fields      [{label, val, confident}] 字段揭示列表, 可选
    error       错误信息(显示后可重试)
    retryLabel  重拍按钮文案, 默认 "重拍"

  Events:
    @retry   用户点击"重拍"
-->
<template>
  <div class="flex flex-col items-center" :style="{ paddingTop: '32px', height: '100%' }">
    <!-- 卡片堆叠 + 扫描线 -->
    <div :style="{ width: '220px', height: '156px', position: 'relative', marginTop: '8px', marginBottom: '28px' }">
      <!-- 第三张(最底): cardCount === 3 -->
      <div v-if="cardCount >= 3"
        :style="{
          position: 'absolute', inset: 0, background: '#F5EFE3',
          transform: 'rotate(-2deg)',
          boxShadow: '0 18px 30px rgba(0,0,0,.18)',
          borderRadius: '4px',
        }"
      />
      <!-- 第二张: cardCount >= 2 -->
      <div v-if="cardCount >= 2"
        :style="{
          position: 'absolute', inset: 0, background: '#F5EFE3',
          transform: 'translate(8px, 6px) rotate(2deg)',
          boxShadow: '0 18px 30px rgba(0,0,0,.18)',
          borderRadius: '4px',
        }"
      />
      <!-- 第一张(总是有) -->
      <div
        :style="{
          position: 'absolute', inset: 0, background: '#F5EFE3',
          transform: cardCount === 1 ? 'rotate(0deg)' : 'translate(4px, 3px) rotate(-1deg)',
          boxShadow: '0 18px 30px rgba(0,0,0,.18)',
          borderRadius: '4px',
        }"
      />
      <!-- 扫描线(横向移动) -->
      <div
        class="ocr-scan-line"
        :style="{
          position: 'absolute', left: '-10px', right: '-10px',
          height: '2px', background: 'var(--color-ex-accent, #D97757)',
          boxShadow: '0 0 10px var(--color-ex-accent, #D97757), 0 0 20px var(--color-ex-accent, #D97757)',
        }"
      />
    </div>

    <!-- 主标题 -->
    <div :style="{
      fontSize: '22px', fontWeight: 500, fontFamily: 'var(--font-serif)',
      color: 'var(--color-ex-ink, #1A1A1A)', textAlign: 'center',
    }">{{ title }}</div>

    <!-- 副标题 -->
    <div v-if="subtitle"
      :style="{ fontSize: '13px', color: 'var(--color-ex-ink3, #7A7570)', marginTop: '6px', textAlign: 'center' }"
    >{{ subtitle }}</div>

    <!-- 字段揭示列表 -->
    <div v-if="fields && fields.length" :style="{ marginTop: '32px', width: '280px' }">
      <div
        v-for="(f, i) in fields" :key="i"
        class="flex justify-between"
        :style="{
          padding: '10px 0',
          borderBottom: i < fields.length - 1 ? '1px solid var(--color-ex-divider, #E5E0DA)' : 'none',
          opacity: visibleCount > i ? (0.4 + Math.min(visibleCount - i, 3) * 0.2) : 0,
          transform: visibleCount > i ? 'translateY(0)' : 'translateY(8px)',
          transition: 'opacity 250ms ease-out, transform 250ms ease-out',
        }">
        <span :style="{ fontSize: '12px', color: 'var(--color-ex-ink3, #7A7570)' }">{{ f.label }}</span>
        <span :style="{
          fontSize: '13px',
          color: f.confident ? 'var(--color-ex-ink, #1A1A1A)' : 'var(--color-ex-warn, #C57211)',
          fontWeight: 500,
        }">{{ f.val }}{{ !f.confident ? t('ocr.lowConfidence') : '' }}</span>
      </div>
    </div>

    <!-- 错误 + 重试 -->
    <template v-if="error">
      <div :style="{
        marginTop: '24px', fontSize: '13px',
        color: 'var(--color-ex-red, #B5453A)', textAlign: 'center', padding: '0 24px',
      }">{{ error }}</div>
      <button @click="$emit('retry')"
        :style="{
          marginTop: '16px', padding: '8px 24px', borderRadius: '999px',
          background: 'var(--color-ex-card, #FFFFFF)',
          border: '1px solid var(--color-ex-divider-strong, #D0CBC4)',
          color: 'var(--color-ex-ink2, #4A4641)', fontSize: '13px',
        }">{{ effectiveRetryLabel }}</button>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  cardCount:  { type: Number, default: 3 },
  title:      { type: String, required: true },
  subtitle:   { type: String, default: '' },
  fields:     { type: Array,  default: () => [] },
  error:      { type: String, default: '' },
  retryLabel: { type: String, default: '' },
})
const effectiveRetryLabel = computed(() => props.retryLabel || t('ocr.retry'))
defineEmits(['retry'])

// 字段揭示动画 - stagger 250ms
const visibleCount = ref(0)
let revealTimer = null

function startReveal() {
  if (!props.fields || props.fields.length === 0) return
  visibleCount.value = 0
  revealTimer = setInterval(() => {
    if (visibleCount.value < props.fields.length) {
      visibleCount.value += 1
    } else {
      clearInterval(revealTimer)
      revealTimer = null
    }
  }, 250)
}

onMounted(startReveal)
watch(() => props.fields?.length, () => {
  if (revealTimer) clearInterval(revealTimer)
  startReveal()
})
onUnmounted(() => { if (revealTimer) clearInterval(revealTimer) })
</script>

<style scoped>
@keyframes ocr-scan {
  0%   { top: 4px; opacity: 0.6; }
  50%  { top: 50%; opacity: 1; }
  100% { top: calc(100% - 4px); opacity: 0.6; }
}
.ocr-scan-line {
  animation: ocr-scan 1.6s ease-in-out infinite;
}
</style>
